
Importing ORM Classes
=====================

The ORM supports different styles of importing and referring to its classes, so choose what works for you from the options below.

Importing Everything
--------------------

It is safe to use `import *` from `infi.clickhouse_orm` or its submodules. Only classes that are needed by users of the ORM will get imported, and nothing else:
```python
from infi.clickhouse_orm import *
```
This is exactly equivalent to the following import statements:
```python
from infi.clickhouse_orm.database import *
from infi.clickhouse_orm.engines import *
from infi.clickhouse_orm.fields import *
from infi.clickhouse_orm.funcs import *
from infi.clickhouse_orm.migrations import *
from infi.clickhouse_orm.models import *
from infi.clickhouse_orm.query import *
from infi.clickhouse_orm.system_models import *
```
By importing everything, all of the ORM's public classes can be used directly. For example:
```python
from infi.clickhouse_orm import *

class Event(Model):

    name = StringField(default="EVENT")
    repeated = UInt32Field(default=1)
    created = DateTimeField(default=F.now())

    engine = Memory()
```

Importing Everything into a Namespace
-------------------------------------

To prevent potential name clashes and to make the code more readable, you can import the ORM's classes into a namespace of your choosing, e.g. `orm`. For brevity, it is recommended to import the `F` class explicitly:
```python
import infi.clickhouse_orm as orm
from infi.clickhouse_orm import F

class Event(orm.Model):

    name = orm.StringField(default="EVENT")
    repeated = orm.UInt32Field(default=1)
    created = orm.DateTimeField(default=F.now())

    engine = orm.Memory()
```

Importing Specific Submodules
-----------------------------

It is possible to import only the submodules you need, and use their names to qualify the ORM's class names. This option is more verbose, but makes it clear where each class comes from. For example:
```python
from infi.clickhouse_orm import models, fields, engines, F

class Event(models.Model):

    name = fields.StringField(default="EVENT")
    repeated = fields.UInt32Field(default=1)
    created = fields.DateTimeField(default=F.now())

    engine = engines.Memory()
```

Importing Specific Classes
--------------------------

If you prefer, you can import only the specific ORM classes that you need directly from `infi.clickhouse_orm`:
```python
from infi.clickhouse_orm import Model, StringField, UInt32Field, DateTimeField, F, Memory

class Event(Model):

    name = StringField(default="EVENT")
    repeated = UInt32Field(default=1)
    created = DateTimeField(default=F.now())

    engine = Memory()
```

---

[<< Expressions](expressions.md) | [Table of Contents](toc.md) | [Querysets >>](querysets.md)
