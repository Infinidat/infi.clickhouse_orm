
SETUP_INFO = dict(
    name = '${project:name}',
    version = '${infi.recipe.template.version:version}',
    author = '${infi.recipe.template.version:author}',
    author_email = '${infi.recipe.template.version:author_email}',

    url = ${infi.recipe.template.version:homepage},
    license = 'BSD',
    description = """${project:description}""",

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

    install_requires = ${project:install_requires},
    namespace_packages = ${project:namespace_packages},

    package_dir = {'': 'src'},
    package_data = {'': ${project:package_data}},
    include_package_data = True,
    zip_safe = False,

    entry_points = dict(
        console_scripts = ${project:console_scripts},
        gui_scripts = ${project:gui_scripts},
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

