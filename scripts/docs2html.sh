
mkdir -p ../htmldocs

find ./ -iname "*.md" -type f -exec sh -c 'echo "Converting ${0}"; pandoc "${0}" -s -o "../htmldocs/${0%.md}.html"' {} \;

echo "Converting README.md"
pandoc ../README.md -s -o "../htmldocs/README.html"

echo "Converting CHANGELOG.md"
pandoc ../CHANGELOG.md -s -o "../htmldocs/CHANGELOG.html"

echo "Fixing links"
sed -i 's/\.md/\.html/g' ../htmldocs/*.html
