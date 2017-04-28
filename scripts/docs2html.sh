
mkdir -p ../htmldocs

find ./ -iname "*.md" -type f -exec sh -c 'echo "Converting ${0}"; pandoc "${0}" -s -o "../htmldocs/${0%.md}.html"' {} \;

echo "Converting README"
pandoc ../README -s -o "../htmldocs/README.html"

echo "Fixing links"
sed -i 's/\.md/\.html/g' ../htmldocs/*.html
