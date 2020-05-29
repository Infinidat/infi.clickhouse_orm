
generate_one() {
    # Converts Markdown to HTML using Pandoc, and then extracts the header tags
    pandoc "$1" | python "../scripts/html_to_markdown_toc.py" "$1" >> toc.md
}

printf "# Table of Contents\n\n" > toc.md

generate_one "index.md"
generate_one "models_and_databases.md"
generate_one "querysets.md"
generate_one "field_options.md"
generate_one "field_types.md"
generate_one "table_engines.md"
generate_one "schema_migrations.md"
generate_one "system_models.md"
generate_one "contributing.md"
generate_one "class_reference.md"
