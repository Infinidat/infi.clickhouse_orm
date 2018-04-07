Contributing
============

This project is hosted on GitHub - [https://github.com/Infinidat/infi.clickhouse_orm/](https://github.com/Infinidat/infi.clickhouse_orm/).

Please open an issue there if you encounter a bug or want to request a feature.
Pull requests are also welcome.

Building
--------

After cloning the project, run the following commands:

    easy_install -U infi.projector
    cd infi.clickhouse_orm
    projector devenv build

A `setup.py` file will be generated, which you can use to install the development version of the package:

    python setup.py install

Tests
-----

To run the tests, ensure that the ClickHouse server is running on <http://localhost:8123/> (this is the default), and run:

    bin/nosetests

To see test coverage information run:

    bin/nosetests --with-coverage --cover-package=infi.clickhouse_orm

To test with tox, ensure that the setup.py is present (otherwise run `bin/buildout buildout:develop= setup.py`) and run:

    pip install tox
    tox

---

[<< System Models](system_models.md) | [Table of Contents](toc.md) | [Class Reference >>](class_reference.md)