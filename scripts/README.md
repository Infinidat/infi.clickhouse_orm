This directory contains various scripts for use while developing.

docs2html
---------
Converts markdown docs to html for preview. Requires Pandoc.
Usage:

    cd docs
    ../scripts/docs2html.sh


gh-md-toc
---------
Used by docs2html to generate the table of contents.


test_python3
------------
Creates a Python 3 virtualenv, clones the project into it, and runs the tests.
Usage:

    ./test_python3.sh
