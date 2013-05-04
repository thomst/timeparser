timeparser
==========

A python-module to parse strings to time-, date-, datetime- or timedelta-objects.
Which formats are accepted is configurable.


Latest Version
--------------
The latest version of this project can be found at : http://github.com/thomst/timeparser.


Installation
------------
* Option 1 : Install via pip ::

    pip install timeparser

* Option 2 : If you have downloaded the source ::

    python setup.py install


Documentation
-------------
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
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "timeparser.py", line 398, in parsetime
        raise ValueError("couldn't parse %s as time" % string)
    ValueError: couldn't parse 234405 as time
    >>>
    >>> timeparser.parsedatetime('24-04-13_23:44:05')
    datetime.datetime(2013, 4, 24, 23, 44, 5)


Reporting Bugs
--------------
Please report bugs at github issue tracker:
https://github.com/thomst/timeparser/issues


Author
------
thomst <thomaslfuss@gmx.de>
Thomas Leichtfuß

* http://github.com/thomst
