from six import string_types, binary_type, text_type, PY3
import codecs


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
    if isinstance(value, string_types):
        chars = (SPECIAL_CHARS.get(c, c) for c in value)
        value = "'" + "".join(chars) + "'" if quote else "".join(chars)
    return text_type(value)


def unescape(value):
    return codecs.escape_decode(value)[0].decode('utf-8')


def parse_tsv(line):
    if PY3 and isinstance(line, binary_type):
        line = line.decode()
    if line[-1] == '\n':
        line = line[:-1]
    return [unescape(value) for value in line.split('\t')]


def import_submodules(package_name):
    """
    Import all submodules of a module.
    """
    import importlib, pkgutil
    package = importlib.import_module(package_name)
    return {
        name: importlib.import_module(package_name + '.' + name)
        for _, name, _ in pkgutil.iter_modules(package.__path__)
    }
