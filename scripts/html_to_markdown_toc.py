from html.parser import HTMLParser
import sys


HEADER_TAGS = ('h1', 'h2', 'h3')


class HeadersToMarkdownParser(HTMLParser):

    inside = None
    text = ''

    def handle_starttag(self, tag, attrs):
        if tag.lower() in HEADER_TAGS:
            self.inside = tag

    def handle_endtag(self, tag):
        if tag.lower() in HEADER_TAGS:
            indent = '   ' * int(self.inside[1])
            fragment = self.text.lower().replace(' ', '-').replace('.', '')
            print('%s* [%s](%s#%s)' % (indent, self.text, sys.argv[1], fragment))
            self.inside = None
            self.text = ''

    def handle_data(self, data):
        if self.inside:
            self.text += data


HeadersToMarkdownParser().feed(sys.stdin.read())
print('')
