import datetime
import decimal
import json
import os
import threading
import unittest

from Cryptodome.Cipher import AES, Blowfish
from django.test import TestCase

from pgcrypto import aes_pad_key, armor, dearmor, pad, unpad, is_encrypted

from pgcrypto.models import BaseCryptoModel
from .models import Employee, PlainModel, EmployeeEncrypted


class FieldEncryptionTest(TestCase):
    def test_get_crypto_fields(self):
        obj = PlainModel(name="abc", encrypted="123")
        fields = BaseCryptoModel.get_crypto_fields(obj)
        self.assertEqual(list(fields), [PlainModel._meta.get_field(field) for field in ('encrypted', 'email', )])

    def test_decrypt_immediately(self):
        obj = Employee.objects.create(cipher_key=b"1234", name="example", salary=2000, ssn="OneTwo")
        obj2 = Employee.objects.create(cipher_key=b"abcd", name="example", salary=2000, ssn="OneTwo")

        self.assertEqual(obj.name, "example")
        self.assertEqual(obj.salary, 2000)
        self.assertEqual(obj.ssn, "OneTwo")

    def test_create_different_keys(self):
        first = Employee.objects.create(cipher_key=b"1234567890123456", name="example", salary=2000, ssn="OneTwo")
        second = Employee.objects.create(cipher_key=b"abcdefghijklmnop", name="example", salary=2000, ssn="OneTwo")

        first_enc = EmployeeEncrypted.objects.get(id=first.id)
        second_enc = EmployeeEncrypted.objects.get(id=second.id)

        self.assertNotEqual(first_enc.salary, second_enc.salary)
        self.assertNotEqual(first_enc.ssn, second_enc.ssn)

    def test_encrypted_without_manager(self):
        obj = Employee(cipher_key=b"1234", name="example", salary=2000, ssn="OneTwo")
        obj.save()

        encrypted = EmployeeEncrypted.objects.get(id=obj.id)

        self.assertEqual(obj.name, encrypted.name)
        self.assertFalse(is_encrypted(encrypted.name))

        self.assertNotEqual(obj.salary, encrypted.salary)
        self.assertTrue(is_encrypted(encrypted.salary))

        self.assertNotEqual(obj.ssn, encrypted.ssn)
        self.assertTrue(is_encrypted(encrypted.ssn))

    def test_encrypted_with_manager(self):
        obj = Employee.objects.create(cipher_key=b"1234", name="example", salary=2000, ssn="OneTwo")

        encrypted = EmployeeEncrypted.objects.get(id=obj.id)

        self.assertEqual(obj.name, encrypted.name)
        self.assertFalse(is_encrypted(encrypted.name))

        self.assertNotEqual(obj.salary, encrypted.salary)
        self.assertTrue(is_encrypted(encrypted.salary))

        self.assertNotEqual(obj.ssn, encrypted.ssn)
        self.assertTrue(is_encrypted(encrypted.ssn))

    def test_retrieve_encrypted_get(self):
        cipher_key = b"1234"
        obj = Employee.objects.create(cipher_key=cipher_key, name="example",
                                      salary=2000, ssn="OneTwo")
        obj2 = Employee.objects.create(cipher_key=b"abcd", name="example2",
                                      salary=3000, ssn="OneTwo")

        retrieved = Employee.objects.decipher(cipher_key).get(id=obj.id)

        self.assertEqual(obj.name, retrieved.name)
        self.assertEqual(obj.salary, retrieved.salary)
        self.assertEqual(obj.ssn, retrieved.ssn)

    def test_retrieve_encrypted_filter(self):
        obj_key = b"1234"
        obj = Employee.objects.create(cipher_key=obj_key, name="example", salary=2000, ssn="OneTwo")

        obj2_key = b"abcd"
        obj2 = Employee.objects.create(cipher_key=obj2_key, name="example2", salary=3000, ssn="OneTwo")

        retrieved = Employee.objects.decipher(obj_key).filter(name="example").first()

        self.assertEqual(obj.name, retrieved.name)
        self.assertEqual(obj.salary, retrieved.salary)
        self.assertEqual(obj.ssn, retrieved.ssn)

    def test_modify_value(self):
        first_ssn = "OneTwo"
        second_ssn = first_ssn + "XXX"
        obj = Employee.objects.create(cipher_key=b"1234", name="example", salary=2000, ssn=first_ssn)

        obj.ssn = second_ssn
        obj.save()

        retrieved = Employee.objects.decipher(b"1234").get(id=obj.id)
        self.assertEqual(retrieved.ssn, second_ssn)

    def test_refresh_from_db(self):
        expected_salary = 2000
        expected_name = "example"
        expected_ssn = "OneTwo"
        obj = Employee.objects.create(cipher_key=b"1234", name=expected_name, salary=expected_salary, ssn=expected_ssn)

        retrieved = Employee.objects.get(id=obj.id)
        retrieved.refresh_from_db()

        self.assertEqual(expected_salary, retrieved.salary)
        self.assertEqual(expected_name, retrieved.name)
        self.assertEqual(expected_ssn, retrieved.ssn)


class CryptoTests (TestCase):
    def setUp(self):
        # This is the expected Blowfish-encrypted value, according to the following pgcrypto call:
        #     select encrypt('sensitive information', 'pass', 'bf');
        self.encrypt_bf = b'{\xd4\xa7\xb7\xa17{+#"\xc7r\xc0\xd9$\x17Wj8\x1e\xf9\x00,B'
        # The basic "encrypt" call assumes an all-NUL IV of the appropriate block size.
        self.iv_blowfish = b"\0" * Blowfish.block_size
        # This is the expected AES-encrypted value, according to the following pgcrypto call:
        #     select encrypt('sensitive information', 'pass', 'aes');
        self.encrypt_aes = b"\263r\011\033]Q1\220\340\247\317Y,\321q\224KmuHf>Z\011M\032\316\376&z\330\344"
        # The basic "encrypt" call assumes an all-NUL IV of the appropriate block size.
        self.iv_aes = b"\0" * AES.block_size
        # When encrypting a string whose length is a multiple of the block size, pgcrypto
        # tacks on an extra block of padding, so it can reliably unpad afterwards. This
        # data was generated from the following query (string length = 16):
        #     select encrypt('xxxxxxxxxxxxxxxx', 'secret', 'aes');
        self.encrypt_aes_padded = b"5M\304\316\240B$Z\351\021PD\317\213\213\234f\225L \342\004SIX\030\331S\376\371\220\\"

    def test_encrypt(self):
        c = Blowfish.new(b'passw', Blowfish.MODE_CBC, self.iv_blowfish)
        self.assertEqual(c.encrypt(pad(b'sensitive information', c.block_size)), self.encrypt_bf)

    def test_decrypt(self):
        c = Blowfish.new(b'passw', Blowfish.MODE_CBC, self.iv_blowfish)
        self.assertEqual(unpad(c.decrypt(self.encrypt_bf), c.block_size), b'sensitive information')

    def test_armor_dearmor(self):
        a = armor(self.encrypt_bf)
        self.assertEqual(dearmor(a), self.encrypt_bf)

    def test_aes(self):
        c = AES.new(aes_pad_key(b'pass'), AES.MODE_CBC, self.iv_aes)
        self.assertEqual(c.encrypt(pad(b'sensitive information', c.block_size)), self.encrypt_aes)

    def test_aes_pad(self):
        c = AES.new(aes_pad_key(b'secret'), AES.MODE_CBC, self.iv_aes)
        self.assertEqual(unpad(c.decrypt(self.encrypt_aes_padded), c.block_size), b'xxxxxxxxxxxxxxxx')



# NOTE: Testing on a specific database as in https://gist.github.com/btimby/5811298
_LOCALS = threading.local()

# TODO: Test with postgres!
@unittest.skip("not implemented yet")
class FieldTestsPostgres (TestCase):
    # fixtures = ('employees',)
    multi_db = True

    def setUp(self):
        setattr(_LOCALS, 'test_db_name', 'postgres')

        try:
            from django.db import connections
            c = connections['postgres'].cursor()
            c.execute('CREATE EXTENSION pgcrypto')
        except:
            self.skipTest("Postgres config didn't worked. Maybe not intalled.")

    def tearDown(self):
        try:
            delattr(_LOCALS, 'test_db_name')
        except AttributeError:
            pass

    def test_query(self):
        fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures', 'employees.json')
        fixture = (obj for obj in json.load(open(fixture_path, 'r')))
        employees = (obj for obj in fixture if obj['model'] == 'core.employee')

        for obj in employees:
            e = Employee.objects.get(ssn=obj['fields']['ssn'])
            self.assertEqual(e.pk, int(obj['pk']))
            self.assertEqual(e.salary, decimal.Decimal(obj['fields']['salary']))
            self.assertEqual(e.date_hired.isoformat(), obj['fields']['date_hired'])

    def test_decimal_lookups(self):
        self.assertEqual(Employee.objects.filter(salary=decimal.Decimal('75248.77')).count(), 1)
        self.assertEqual(Employee.objects.filter(salary__gte=decimal.Decimal('75248.77')).count(), 1)
        self.assertEqual(Employee.objects.filter(salary__gt=decimal.Decimal('75248.77')).count(), 0)
        self.assertEqual(Employee.objects.filter(salary__gte=decimal.Decimal('70000.00')).count(), 1)
        self.assertEqual(Employee.objects.filter(salary__lte=decimal.Decimal('70000.00')).count(), 1)
        self.assertEqual(Employee.objects.filter(salary__lt=decimal.Decimal('52000')).count(), 0)

    def test_date_lookups(self):
        self.assertEqual(Employee.objects.filter(date_hired='1999-01-23').count(), 1)
        self.assertEqual(Employee.objects.filter(date_hired='1999-01-23').first().date_hired, datetime.date(1999,1,23))
        self.assertEqual(Employee.objects.filter(date_hired__gte='1999-01-01').count(), 1)
        self.assertEqual(Employee.objects.filter(date_hired__gt='1981-01-01').count(), 2)

    def test_multi_lookups(self):
        self.assertEqual(Employee.objects.filter(date_hired__gt='1981-01-01', salary__lt=60000).count(), 1)
