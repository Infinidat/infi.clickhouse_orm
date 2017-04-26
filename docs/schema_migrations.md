Schema Migrations
=================

Over time, the ORM models in your application may change. Migrations provide a way to modify the database tables according to the changes in your models, without writing raw SQL.

The migrations that were applied to the database are recorded in the `infi_clickhouse_orm_migrations` table, so migrating the database will only apply any missing migrations.

Writing Migrations
------------------

To write migrations, create a Python package. Then create a python file for the initial migration. The migration files must begin with a four-digit number, and will be applied in sequence. For example::

    analytics
       |
       +-- analytics_migrations
              |
              +-- __init__.py
              |
              +-- 0001_initial.py
              |
              +-- 0002_add_user_agents_table.py

Each migration file is expected to contain a list of `operations`, for example::

    from infi.clickhouse_orm import migrations
    from analytics import models

    operations = [
        migrations.CreateTable(models.Visits),
        migrations.CreateTable(models.Visitors)
    ]

The following operations are supported:

**CreateTable**

A migration operation that creates a table for a given model class.

**DropTable**

A migration operation that drops the table of a given model class.

**AlterTable**

A migration operation that compares the table of a given model class to the model’s fields, and alters the table to match the model. The operation can:

-   add new columns
-   drop obsolete columns
-   modify column types

Default values are not altered by this operation.

Running Migrations
------------------

To migrate a database, create a `Database` instance and call its `migrate` method with the package name containing your migrations::

    Database('analytics_db').migrate('analytics.analytics_migrations')

Note that you may have more than one migrations package.