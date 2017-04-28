echo "Table of Contents" > toc.md
echo "=================" >> toc.md

../scripts/gh-md-toc \
    index.md \
    models_and_databases.md \
    querysets.md \
    field_types.md \
    table_engines.md \
    schema_migrations.md \
    system_models.md \
    contributing.md \
    >> toc.md
