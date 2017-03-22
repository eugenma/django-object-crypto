from django.db import models
from django.utils.encoding import python_2_unicode_compatible

from pgcrypto import EncryptedEmailField, EncryptedDateField, EncryptedDecimalField, \
    EncryptedCharField, BaseEncryptedField


# import six
# from django.db import models
# from django.db.models import DEFERRED
# from django.utils.encoding import python_2_unicode_compatible, force_bytes
#
# from pgcrypto import armor, BaseEncryptedField, EncryptedEmailField, EncryptedDateField, EncryptedDecimalField, \
#     EncryptedCharField
# from pgcrypto import pad
# from pgcrypto.actions import set_key

from pgcrypto.models import BaseCryptoModel



@python_2_unicode_compatible
class Employee (BaseCryptoModel):
    name = models.CharField(max_length=200)
    ssn = EncryptedCharField('SSN')
    salary = EncryptedDecimalField()
    date_hired = EncryptedDateField()
    email = EncryptedEmailField(unique=True, null=True)


    def __str__(self):
        return self.name


class EmployeeEncrypted(models.Model):
    name = models.CharField(max_length=200)
    ssn = models.CharField('SSN', max_length=200)
    salary = models.CharField(max_length=200)
    date_hired = models.CharField(max_length=200)
    email = models.CharField(unique=True, null=True, max_length=200)

    def __str__(self):
        return self.name

    class Meta(object):
        db_table = Employee._meta.db_table
        managed = False


@python_2_unicode_compatible
class PlainModel (models.Model):
    name = models.CharField(max_length=200)
    encrypted = EncryptedCharField('encypted')
    email = EncryptedEmailField(unique=True, null=True)
