This directory contains various scripts for use while developing.

generate_toc
------------
Generates the table of contents (toc.md). Requires Pandoc.
Usage:

    cd docs
    ../scripts/generate_toc.sh


html_to_markdown_toc.py
-----------------------
Used by generate_toc.


docs2html
---------
Converts markdown docs to html for preview. Requires Pandoc.
Usage:

    cd docs
    ../scripts/docs2html.sh


generate_ref
------------
Generates a class reference.
Usage:

    cd docs
    ../bin/python ../scripts/generate_ref.py > class_reference.md


generate_all
------------
Does everything:
- Generates the class reference using generate_ref
- Generates the table of contents using generate_toc
- Converts to HTML for visual inspection using docs2html

Usage:

    cd docs
    ../scripts/generate_all.sh


test_python3
------------
Creates a Python 3 virtualenv, clones the project into it, and runs the tests.
Usage:

    ./test_python3.sh
