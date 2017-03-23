from setuptools import find_packages, setup

import os
import re


def get_version():
    with open(os.path.join(os.path.dirname(__file__), 'pgcrypto', 'base.py')) as fp:
        return re.match(r".*__version__ = '(.*?)'", fp.read(), re.S).group(1)

setup(
    name='django-object-crypto',
    version=get_version(),
    description='Python and Django utilities for per-object encryption using pgcrypto.',
    long_description='Code base is from the original `django-pgcrypto package <https://github.com/dcwatson/django-pgcrypto>`_',
    author='Eugen Massini, Dan Watson',
    author_email='eugen.massini@gmail.com',
    url='https://github.com/eugenma/django-object-crypto',
    license='BSD',
    packages=find_packages(),
    install_requires=[
        'pycryptodomex>=3.4',
    ],
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        #'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Topic :: Database',
        'Topic :: Security :: Cryptography',
    ]
)
