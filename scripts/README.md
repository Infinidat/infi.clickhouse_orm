This directory contains various scripts for use while developing.

generate_toc
------------
Generates the table of contents (toc.md)
Usage:
    cd docs
    ../scripts/generate_toc.sh


gh-md-toc
---------
Used by generate_toc.


docs2html
---------
Converts markdown docs to html for preview. Requires Pandoc.
Usage:

    cd docs
    ../scripts/docs2html.sh


test_python3
------------
Creates a Python 3 virtualenv, clones the project into it, and runs the tests.
Usage:

    ./test_python3.sh
