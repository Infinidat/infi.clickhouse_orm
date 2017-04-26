Contributing
============

After cloning the project, run the following commands:

    easy_install -U infi.projector
    cd infi.clickhouse_orm
    projector devenv build

To run the tests, ensure that the ClickHouse server is running on <http://localhost:8123/> (this is the default), and run:

    bin/nosetests

To see test coverage information run:

    bin/nosetests --with-coverage --cover-package=infi.clickhouse_orm
