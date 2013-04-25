from distutils.core import setup

VERSION = "0.1"

setup(
    name = "datetimeparser", 
    version = VERSION, 
    author = "Thomas Leichtfuss", 
    author_email = "thomaslfuss@gmx.de",
    url = "https://github.com/thomst/datetimeparser",
    download_url = "https://pypi.python.org/packages/source/d/datetimeparser/datetimeparser-{version}.tar.gz".format(version=VERSION),
    description = 'little pymodule to parse strings to datetime.time-, -date- or -datetime-objects.',
    long_description = open('README.rst').read(),
    py_modules = ["datetimeparser"],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 2.7',
    ],
    license='GPL',
    keywords='parser datetime',
)
