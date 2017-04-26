
mkdir -p ../htmldocs

echo "Generating table of contents"
../scripts/gh-md-toc \
    index.md \
    models_and_databases.md \
    querysets.md \
    field_types.md \
    table_engines.md \
    schema_migrations.md \
    system_models.md \
    contributing.md \
    > toc.md

find ./ -iname "*.md" -type f -exec sh -c 'echo "Converting ${0}"; pandoc "${0}" -s -o "../htmldocs/${0%.md}.html"' {} \;

echo "Fixing links"
sed -i 's/\.md/\.html/g' ../htmldocs/*.html
