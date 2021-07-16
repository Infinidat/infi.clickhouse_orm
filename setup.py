
SETUP_INFO = dict(
    name = 'infi.clickhouse_orm',
    version = '2.1.0.post15',
    author = 'James Greenhill',
    author_email = 'fuziontech@gmail.com',

    url = 'https://github.com/Infinidat/infi.clickhouse_orm',
    license = 'BSD',
    description = """A Python library for working with the ClickHouse database""",

    # http://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers = [
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.4",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Database"
    ],

    install_requires = [
'iso8601 >= 0.1.12',
'pytz',
'requests',
'setuptools'
],
    namespace_packages = ['infi'],

    package_dir = {'': 'src'},
    package_data = {'': []},
    include_package_data = True,
    zip_safe = False,

    entry_points = dict(
        console_scripts = [],
        gui_scripts = [],
        ),
)

if SETUP_INFO['url'] is None:
    _ = SETUP_INFO.pop('url')

def setup():
    from setuptools import setup as _setup
    from setuptools import find_packages
    SETUP_INFO['packages'] = find_packages('src')
    _setup(**SETUP_INFO)

if __name__ == '__main__':
    setup()

