A fork of [infi.clikchouse_orm](https://github.com/Infinidat/infi.clickhouse_orm) aimed at more frequent maintenance and bugfixes.

This repository expects to use more type hints, and will drop support for Python 2.x.

Supports both synchronous and asynchronous ways to interact with the clickhouse server. Means you can use asyncio to perform asynchronous queries, although the asynchronous mode is not well tested.


| Build       | [![Python 3.7 Tests](https://github.com/sswest/ch-orm/workflows/Python%203.7%20Tests/badge.svg)](https://github.com/sswest/ch-orm/actions?query=Python+3.7+Tests)[![Python 3.8 Tests](https://github.com/sswest/ch-orm/workflows/Python%203.8%20Tests/badge.svg)](https://github.com/sswest/ch-orm/actions?query=Python+3.8+Tests)[![Python 3.9 Tests](https://github.com/sswest/ch-orm/workflows/Python%203.9%20Tests/badge.svg)](https://github.com/sswest/ch-orm/actions?query=Python+3.9+Tests)[![Python 3.10 Tests](https://github.com/sswest/ch-orm/workflows/Python%203.10%20Tests/badge.svg)](https://github.com/sswest/ch-orm/actions?query=Python+3.10+Tests) |
| ----------- |-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Package** | [![PyPI](https://img.shields.io/pypi/v/ch-orm.svg)](https://pypi.python.org/pypi/ch-orm)[![PyPI version](https://img.shields.io/pypi/pyversions/ch-orm.svg)](https://pypi.python.org/pypi/ch-orm)[![PyPI Wheel](https://img.shields.io/pypi/wheel/ch-orm.svg)](https://pypi.python.org/pypi/ch-orm)[![Coverage Status](https://coveralls.io/repos/github/sswest/ch-orm/badge.svg?branch=master)](https://coveralls.io/github/sswest/ch-orm?branch=master)[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)|
| **Docs**    | [![Documentation](https://camo.githubusercontent.com/bbb44987324f9324879ccae8ff5ad5c30b7e8b37ccee7235841a9628772595fe/68747470733a2f2f72656164746865646f63732e6f72672f70726f6a656374732f73616e69632f62616467652f3f76657273696f6e3d6c6174657374)](https://sswest.github.io/ch-orm)|

Introduction
============

This project is simple ORM for working with the [ClickHouse database](https://clickhouse.yandex/).

It allows you to define model classes whose instances can be written to the database and read from it.

This and other examples can be found in the `examples` folder.

To learn more please visit the [documentation](https://sswest.github.io/ch-orm/).

