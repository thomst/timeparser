timeparser
==========

Parse strings to objects of the datetime-module.

This module intends to make string-parsing to objects of the datetime-module as
easy as possible while allowing a fine configuration about which kind of formats
are supported.


Latest Version
--------------
The latest version of this project can be found at : http://github.com/thomst/timeparser.


Installation
------------
* Option 1 : Install via pip ::

    pip install timeparser

* Option 2 : If you have downloaded the source ::

    python setup.py install


Dokumentaion:
-------------
Please visit the documentation on readthedocs.org:
https://timeparser.readthedocs.org/en/latest/index.html


Usage
-----
How to use? ::

    >>> import timeparser
    >>>
    >>> timeparser.parsedate('24.4.13')
    datetime.date(2013, 4, 24)
    >>>
    >>> timeparser.parsedate('24 Apr 2013')
    datetime.date(2013, 4, 24)
    >>>
    >>> timeparser.parsetime('234405')
    datetime.time(23, 44, 5)
    >>>
    >>> timeparser.TimeFormats.config(allow_no_sep=False)
    >>> timeparser.parsetime('234405')
    ValueError: couldn't parse 234405 as time
    >>>
    >>> timeparser.parsedatetime('24-04-13_23:44:05')
    datetime.datetime(2013, 4, 24, 23, 44, 5)


Changes in v0.7
---------------
The formats-classes accept an keyword try_hard, which means they try
to build formats for what ever kind of string was passed -regardless
of any configuration


Reporting Bugs
--------------
Please report bugs at github issue tracker:
https://github.com/thomst/timeparser/issues


Author
------
thomst <thomaslfuss@gmx.de>
Thomas Leichtfuß

* http://github.com/thomst
