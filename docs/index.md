Overview
========

This project is simple ORM for working with the [ClickHouse database](https://clickhouse.tech/). It allows you to define model classes whose instances can be written to the database and read from it.

This repository expects to use more type hints, and will drop support for Python 2.x.

Supports both synchronous and asynchronous ways to interact with the clickhouse server. Means you can use asyncio to perform asynchronous queries, although the asynchronous mode is not well tested.

Installation
------------

To install clickhouse_orm:

    pip install ch-orm

---

[Table of Contents](toc.md) | [Models and Databases >>](models_and_databases.md)