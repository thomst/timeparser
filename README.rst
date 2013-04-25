datetimeparser
==============

Little python-module to parse strings to datetime.time-, -date- or -datetime-objects.

Latest Version
--------------
The latest version of this project can be found at : http://github.com/thomst/datetimeparser.


Installation
------------
* Option 1 : Install via pip ::

    pip install datetimeparser

* Option 2 : If you have downloaded the source ::

    python setup.py install


Documentation
-------------
How to use? ::

    >>>import datetime
    >>>from datetimeparser import DateTimeParser
    >>>
    >>> DateTimeParser.parsedate('2013.04.24')
    datetime.date(2013, 4, 24)
    >>>
    >>> DateTimeParser.parsetime('23:44:05')
    datetime.time(23, 44, 5)
    >>>
    >>> DateTimeParser.parsedatetime('13-04-24 23:44:05')
    datetime.datetime(2013, 4, 24, 23, 44, 5)



Reporting Bugs
--------------
Please report bugs at github issue tracker:
https://github.com/thomst/datetimeparser/issues


Author
------
thomst <thomaslfuss@gmx.de>
Thomas Leichtfuß

* http://github.com/thomst
