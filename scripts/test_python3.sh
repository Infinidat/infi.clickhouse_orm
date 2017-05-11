#!/bin/bash
cd /tmp
rm -rf /tmp/orm_env*
virtualenv -p python3 /tmp/orm_env
cd /tmp/orm_env
source bin/activate
pip install infi.projector
git clone https://github.com/Infinidat/infi.clickhouse_orm.git
cd infi.clickhouse_orm 
projector devenv build
bin/nosetests
