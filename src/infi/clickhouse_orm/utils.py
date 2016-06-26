
SPECIAL_CHARS = {
    "\b" : "\\b",
    "\f" : "\\f",
    "\r" : "\\r",
    "\n" : "\\n",
    "\t" : "\\t",
    "\0" : "\\0",
    "\\" : "\\\\",
    "'"  : "\\'"
}


def escape(value, quote=True):
    if isinstance(value, basestring):
        chars = (SPECIAL_CHARS.get(c, c) for c in value)
        return "'" + "".join(chars) + "'" if quote else "".join(chars)
    return str(value)


def unescape(value):
    return value.decode('string_escape')


def parse_tsv(line):
    if line[-1] == '\n':
        line = line[:-1]
    return [unescape(value) for value in line.split('\t')]
