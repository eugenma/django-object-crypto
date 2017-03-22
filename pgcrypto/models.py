import logging

from django.db import models
from django.utils.encoding import python_2_unicode_compatible

from pgcrypto import BaseEncryptedField

logger = logging.getLogger(__name__)


# TODO: Test with AES Encryption

class PgCryptoQuerySet(models.QuerySet):
    def decipher(self, cipher_key):
        qset = self.filter()
        qset.query.add_context('cipher_key', cipher_key)
        return qset


@python_2_unicode_compatible
class BaseCryptoModel(models.Model):
    class Meta(object):
        abstract = True

    def __init__(self, *args, **kwargs):
        cipher_key = self.__retrieve_cipher_key(args, kwargs)
        self.__dispatch_cipher_key(cipher_key)
        super(BaseCryptoModel, self).__init__(*args, **kwargs)

    def __dispatch_cipher_key(self, cipher_key):
        if not cipher_key:
            return

        crypto_fields = BaseCryptoModel.get_crypto_fields(self)
        for field in crypto_fields:
            field.cipher.cipher_key = cipher_key

    def __retrieve_cipher_key(self, args, kwargs):
        if len(args) == 0:
            return kwargs.pop('cipher_key')
        return None

    objects = PgCryptoQuerySet.as_manager()

    @staticmethod
    def get_crypto_fields(obj):
        all_fields = obj._meta.concrete_fields
        crypto_fields = (field for field in all_fields if isinstance(field, BaseEncryptedField))
        return crypto_fields
