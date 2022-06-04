Async Databases
====================

Databases in async mode have basically the same API. In most cases you just need to add `await`.

Insert from the AioDatabase
-------------------------

To write your instances to ClickHouse, you need a `AioDatabase` instance:

```python
from clickhouse_orm.aio.database import AioDatabase

db = AioDatabase('my_test_db')

async def main():
    await db.init()
    ...
```

**Unlike the previous Database instance, you have to use an asynchronous method to initialize the db.**


Using the `AioDatabase` instance you can create a table for your model, and insert instances to it:
```python
from clickhouse_orm.aio.database import AioDatabase

db = AioDatabase('my_test_db')

async def main():
    await db.init()
    await db.create_table(Person)
    await db.insert([dan, suzy])
```

The `insert` method can take any iterable of model instances, but they all must belong to the same model class.

Reading from the AioDatabase
-------------------------

Loading model instances from the database is easy, use the `async for` keyword:
```python
async for person in db.select("SELECT * FROM my_test_db.person", model_class=Person):
    print(person.first_name, person.last_name)
```
**Note: AioDatabase does not support QuerySet value by index**

```python
async def main():
    await db.init()

    # incorrect example
    person = await Person.objects_in(db).filter[5]
    
    # correct
    person = [_ async for _ in Person.objects_in(db).filter[5:5]][0]
```


[<< Models and Databases](models_and_databases.md) | [Table of Contents](toc.md) | [Expressions >>](expressions.md)