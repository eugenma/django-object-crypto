Welcome to django-object-crypto's documentation!
===========================================

Quickstart
----------

There are several encrypted versions of Django fields that you can use (mostly) as you would use a normal Django field::

    from django.db import models
    import pgcrypto
    
    class Employee (pgcrypto.BaseCryptoModel):
        name = models.CharField(max_length=100)
        ssn = pgcrypto.EncryptedTextField()
        pay_rate = pgcrypto.EncryptedDecimalField()
        date_hired = pgcrypto.EncryptedDateField()

Fields are encrypted according to the following settings:

``PGCRYPTO['VALID_CIPHERS']`` (default: ``('AES', 'Blowfish')``):
    A list of valid PyCrypto cipher names. Currently only AES and Blowfish are supported, so this setting is mostly for future-proofing.

``PGCRYPTO['CIPHER']`` (default: ``'Blowfish'``):
    The PyCrypto cipher to use when encrypting fields.


Furthermore it is required that the model inherit from ``pgcrypto.BaseCryptoModel``.


Creating
------------
In Django there are two possibilities how to create a model object. On encryption models is is required to provide
the ``cipher_key`` along with other fields::

    employee1 = Employee.objects.create(cipher_key=b"abcd", name="example", salary=2000, ssn="OneTwo")
    employee2 = Employee(cipher_key=b"abcd", name="example", salary=2000, ssn="OneTwo")
    employee2.save()


Querying
--------

With Django 1.7 and on postgres databases, it is possible to filter on encrypted fields as you would normal fields via
``exact``, ``gt``, ``gte``, ``lt``, and ``lte`` lookups. For example, querying the model above is possible like so.
On other databases only ``exact`` is working. Since PostgreSQL supports native decryption.

Querying happens with a custom ``pgcrypto.PgCryptoQuerySet`` query set.
::

    Employee.objects.decrypt(b"abcd").filter(date_hired__gt='1981-01-01', salary__lt=60000)


.. toctree::
   :maxdepth: 2



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

