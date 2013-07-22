"""
Parse strings to objects of :mod:`datetime`.

This module intends to make string-parsing to :mod:`datetime`-objects as
easy as possible while allowing a fine configuration about which kind of formats
are supported:

Parsing any kind of string is as easy as:

    >>> date = parsedate('3 Jan 2013')
    datetime.date(2013, 1, 3)

Now suppose you don't want to allow parsing strings with literal month-names:

    >>> DateFormats.config(allow_month_name=False)
    >>> date = parsedate('3 Jan 2013')
    ValueError: couldn't parse '3 Jan 2013' as date

Most of the time you will use `format-classes`_ only to alter their configuration.
The `parser-functions`_ (except :func:`parsetimedelta`) use the `format-classes`_
to recieve a list of format-strings and try to parse the string with them using
:meth:`datetime.datetime.strptime`.

:func:`parsetimedelta` breaks with that concept. It don't need format-strings at
all and has his own :func:`logic <parsetimedelta>`.

A closer look at `format-classes`_
----------------------------------

`Format-classes`_ are actual :obj:`list`-types that provides two main-features:
    * They produce themselves as lists of format-strings accordingly to a set of
      parameters,
    * and they are configurable in regard to these parameters.

To create a list with an altered configuration you can either pass keyword-
arguments to the constructor:

    >>> formats = TimeFormats(seps=['-', ':', ';'], allow_microsec=True)

or change the default-configuration on class-level:

    >>> TimeFormats.config(seps=['-', ':', ';'], allow_microsec=True)
    >>> formats = TimeFormats()

Both will result in the same list of formats, but the former way doesn't touch
the default-configuration.

If you just call the constructor the format-class will produce a list of all
formats for the actual configuration:

    >>> formats = DateFormats()
    >>> len(formats)
    77

But if you look for formats for a specific string you can pass the string to the
constructor:

    >>> DateFormats('3 Jan 2013')
    ['%d %b %Y']

That is what the `parser-functions`_ do to minimize the amount of formats they
have to try to parse the string with.

Producing formats for a specific string also respects the current setting:

    >>> set(DateFormats('3 Jan 2013')) < set(DateFormats())
    True
    >>> DateFormats.config(allow_month_name=False)
    >>> DateFormats('3 jan 2013')
    ValueError: no proper format for '3 jan 2013'
"""

import datetime
import re
import subprocess
import shlex
import inspect

import warnings
warnings.simplefilter('default')

__version__ = '0.6.0'

class Today:
    """
    Today emulates a :class:`datetime.date`-object that could be changed through
    :meth:`set`.

    On creation Today will be set to :meth:`datetime.date.today`.
    
    Because :obj:`datetime.date`-objects are not mutable (but Today-instance has
    to be), Today imitates a :obj:`datetime.date` just saving one as
    :attr:`Today.dateobj` and let :attr:`Today.year`, :attr:`Today.month` and
    :attr:`Today.day` returning its values.
    """
    def __init__(self): self.set()

    def set(self, *args, **kwargs):
        """
        Change TODAY.

        :arg int year:      year
        :arg int month:     month
        :arg int day:       day
        """
        if args or kwargs: self._dateobj = datetime.date(*args, **kwargs)
        else: self._dateobj = datetime.date.today()
        for a in ('month', 'year', 'day', 'replace', '__repr__', '__eq__'):
            setattr(self, a, getattr(self._dateobj, a))


TODAY = Today()
"""
TODAY is an instance of :class:`Today` and is used to complement dates that were
parsed with an incomplete format-string:

    >>> TODAY
    TODAY(2013, 5, 9)
    >>> parsedate('20 Apr')
    datetime.date(2013, 4, 20)

or even:

    >>> TODAY
    TODAY(2013, 5, 9)
    >>> parsedate('20')
    datetime.date(2013, 5, 20)

TODAY defaults to :meth:`datetime.date.today`, but can be changed through
:meth:`Today.set`:

    >>> TODAY.set(2000, 1, 1)
    >>> parsedate('20')
    datetime.date(2000, 1, 20)
"""

class Endian:
    """
    Endian emulates a tuple, which represents the order of a date.

    Dates can be ordered in three different ways:
    
        * little-endian:    ``('day', 'month', 'year')``
        * big-endian:       ``('year', 'month', 'day')``
        * middle-endian:    ``('month', 'day', 'year')``

    On creation a local default-order is guessed (either little- or big-endian).
    To change it use :meth:`set`.
    """
    OPTIONS = dict(
        little = ('day', 'month', 'year'),
        big = ('year', 'month', 'day'),
        middle = ('month', 'day', 'year')
        )
    def __init__(self): self.set()

    def set(self, key=None):
        """
        Set ENDIAN to little-, big- or middle-endian.

        :arg key:       A string matching 'little', 'big' or 'middle'.
        :type key:      str or None

        If key is None the local-default-order is guessed.
        """
        self._key = self._check_key(key) or self._guess()
        for m in ('__iter__', '__getitem__', '__repr__', 'index'):
            setattr(self, m, getattr(self.OPTIONS[self._key], m))

    def get(self, no_year=False, key=None):
        key = self._check_key(key) or self._key
        if no_year:
            if key in ['little', 'middle']: return self.OPTIONS[key][:-1]
            else: return self.OPTIONS[key][1:]
        endian = self.__class__()
        endian.set(self._check_key(key) or self._key)
        return endian

    @classmethod
    def _check_key(cls, key):
        if not key: return None
        for k in cls.OPTIONS.keys():
            if re.match(key, k): return k
        else: raise ValueError("'%s' is an invalid key" % key)

    @staticmethod
    def _guess():
        # today.strftime('%x') returns a middle-endian-date. Therefore I use the
        # unix's date-command.
        # (Mind that this won't work if date +%x returns a datestring with a
        # two-digit-year.)
        #TODO: find a more solid way (which could also regard 'middle')
        datestring = subprocess.check_output(shlex.split('date +%x'))
        one, two, three = re.findall('[-+]?\d+', datestring)
        if int(one) == datetime.date.today().year: return 'big'
        else: return 'little'

ENDIAN = Endian()
"""
In generell dates could have one of three orders:
    * little-endian:    *day, month, year*
    * big-endian:       *year, month, day*
    * middle-endian:    *month, day, year*

ENDIAN is an instance of :class:`Endian` and defines the order that should be
applied:

    >>> ENDIAN
    ('day', 'month', 'year')
    >>> parsedate('26/4/13')
    datetime.date(2013, 4, 26)

On creation a local-default-order is guessed, but could be changed through
:meth:`Endian.set`:

    >>> ENDIAN.set('big')
    >>> ENDIAN
    ('year', 'month', 'day')
    >>> parsedate('26/4/13')
    datetime.date(2026, 4, 13)

.. warning::

    Guessing the local default is in a provisional state and a middle-endian-
    order is not regarded at all.
"""


#TODO: implement a try-hard-option for generating string-specific formats.
class BaseFormats(list):
    """
    Base-class for format-classes; inherit from :class:`list`.

    :keyword string:            Pre-select formats for string.
    :keyword seps:              Allowed separators for formats.
    :keyword allow_no_sep:      Allows formats without any separator.
    :keyword figures:           List of three booleans that predicts how many
                                digits formats are allowed to have.

                                * figures[0]: allows a one-digit format ('%H')
                                * figures[1]: allows two-digit-fmts (e.g. '%H:%M')
                                * figures[2]: allows three-digit-fmts (e.g. '%H:%M:%S')

    :type seps:                 list
    :type allow_no_sep:         bool
    :type figures:              list

    :raises:                    ValueError if no format could be produced for
                                *string*.
    """
    ALLOW_NO_SEP = True
    """Allows formats without any separator ('%H%M%S')."""
    FIGURES = [True, True, True]
    """
    List of three booleans that predicts how many digits formats are allowed
    to have:

    * figures[0]: Allows the one-digit format '%H'.
    * figures[1]: Allows two-digit-formats like '%H:%M'.
    * figures[2]: Allows three-digit-formats like '%H:%M:%S'.
    """
    SFORMATS = list()
    ERR_MSG = "no proper format for '%s'"

    def __init__(self, string=None, seps=None, allow_no_sep=None, figures=None):
        super(BaseFormats, self).__init__()

        self._figures = figures or self.FIGURES[:]
        if isinstance(seps, list): self._seps = seps[:]
        else: self._seps = self.SEPS[:]
        if allow_no_sep is None: self._allow_no_sep = self.ALLOW_NO_SEP
        else: self._allow_no_sep = allow_no_sep
        self._sformats = self.SFORMATS

        self._check_config()

        if string:
            self._for_string(string)
            try: self._check_config()
            except Exception: raise ValueError(self.ERR_MSG % string)
        else: self._all()

    def _check_config(self):
        if not any(self._figures): raise Exception('invalid configuration')

    @classmethod
    def config(cls, seps=None, allow_no_sep=None, figures=None):
        """
        Modify class-configuration.

        :keyword seps:              Allowed separators for formats.
        :keyword allow_no_sep:      Allows formats without any separator.
        :keyword figures:           List of three booleans that predicts how many
                                    digits formats are allowed to have.

        :type seps:                 list
        :type allow_no_sep:         bool
        :type figures:              list
        """
        if seps: cls.SEPS = seps
        if not allow_no_sep is None: cls.ALLOW_NO_SEP = allow_no_sep
        if figures: cls.FIGURES = figures
        if not any(cls.FIGURES): raise Exception('invalid configuration')

    def _for_string(self, string):
        """
        While the generic parameters predict the range of all possible formats,
        the string (if given) is used to precice this range for the specific
        string. E.g. if string is '23:44:02' only formats with ':' as separator
        are produced.
        """

    def _get_code_list(self):
        """
        Builds and returns a list of code-lists (like ['%d', '%b', '%Y']).
        These code-lists will be joined to format-strings by self._all().
        """

    def _special_formats(self):
        #TODO: rework this...
        formats = list()
        for l in self._sformats:
            l += [[str()] for x in range(7 - len(l))]
            formats.extend([
                a+b+c+d+e+f+g
                for a in l[0]
                for b in l[1]
                for c in l[2]
                for d in l[3]
                for e in l[4]
                for f in l[5]
                for g in l[6]
                ])
        return formats

    def _formats(self):
        formats = list()
        code_list = self._get_code_list()
        if self._allow_no_sep: self._seps.append(str())
        for s in self._seps:
            for codes in code_list:
                formats.append(s.join(codes))
        return formats

    def _all(self):
        """
        Generates the formats and populate the list-instance.
        """
        if self._seps or self._allow_no_sep: self.extend(self._formats())
        if self._sformats: self.extend(self._special_formats())


class TimeFormats(BaseFormats):
    """
    A list of time-string-formats that generates himself.

    :keyword string:            Pre-select formats for string.
    :keyword seps:              Allowed separators for formats.
    :keyword allow_no_sep:      Allows formats without any separator.
    :keyword figures:           List of three booleans (s. :attr:`FIGURES`).
    :keyword allow_microsec:    Allows formats with microseconds (%f).

    :type string:               str
    :type seps:                 list
    :type allow_no_sep:         bool
    :type figures:              list
    :type allow_microsec:       bool

    :raises:                    ValueError if no format could be produced for
                                *string*.
    """
    CODES = ['%H', '%M', '%S', '%f']
    SEPS = [':', ' ']
    """A list of separators, formats are produced with."""
    ALLOW_NO_SEP = True
    """Allows formats without any separator ('%H%M%S')."""
    FIGURES = [True, True, True]
    """
    List of three booleans that predicts how many digits formats are allowed
    to have:

    * figures[0]: Allows the one-digit format '%H'.
    * figures[1]: Allows two-digit-formats like '%H:%M'.
    * figures[2]: Allows three-digit-formats like '%H:%M:%S'.
    """
    ALLOW_MICROSEC = False
    """Allows formats with microseconds (%f)."""
    SFORMATS = [
        [['%H'], [':'], ['%M'], [':'], ['%S'], ['h', ' h']],
        [['%H'], [':', ''], ['%M'], ['h', ' h']],
        [['%H'], ['h', ' h']],
        ]
    MFORMATS = [
        [['%H'], [':'], ['%M'], [':'], ['%S'], ['.'], ['%f']],
        [['%H'], [''], ['%M'], [''], ['%S'], ['.'], ['%f']],
        ]

    def __init__(self, string=None, seps=None, allow_no_sep=None, figures=None,
                allow_microsec=None):
        if allow_microsec is None: self._allow_microsec = self.ALLOW_MICROSEC
        else: self._allow_microsec = allow_microsec
        super(TimeFormats, self).__init__(string, seps, allow_no_sep, figures)

    @classmethod
    def config(cls, allow_microsec=None, *args, **kwargs):
        """
        Modify class-configuration.

        :keyword seps:              Allowed separators for formats.
        :keyword allow_no_sep:      Allows formats without any separator.
        :keyword figures:           List of three booleans (s. :attr:`FIGURES`).
        :keyword allow_microsec:    Allowes formats with microseconds (%f)

        :type seps:                 list
        :type allow_no_sep:         bool
        :type figures:              list
        :type allow_microsec:       bool
        """
        if not allow_microsec is None: cls.ALLOW_MICROSEC = allow_microsec
        super(TimeFormats, cls).config(*args, **kwargs)

    def _for_string(self, string):
        """
        While the generic parameters predict the range of all possible formats,
        the string (if given) is used to precice this range for the specific
        string. E.g. if string is '23:44:02' only formats with ':' as separator
        are produced.
        """
        fmask = lambda f: map(lambda x,y: y if x else x, self._figures, f)

        digits = re.findall('[\d]+', string)
        nondigit = re.findall('[\D]+', string)

        #TODO: seperate the concepts of parser with _formats and _sformats more
        # accurate.

        if 4 >= len(digits) >= 3: self._figures = fmask([False, False, True])
        elif len(digits) == 2: self._figures = fmask([False, True, False])
        elif len(digits) == 1:
            if self._allow_no_sep:
                v = digits[0]
                if len(v) >= 5: self._figures = fmask([False, False, True])
                elif 3 <= len(v) <= 4: self._figures = fmask([False, True, True])
                elif len(v) == 2: self._figures = fmask([True, True, False])
                elif len(v) == 1: self._figures = fmask([True, False, False])
            else: self._figures = fmask([True, False, False])
        else: raise ValueError(self.ERR_MSG % string)

        #TODO: This could be generelized for TimeFormats and DateFormats.
        if not nondigit and self._allow_no_sep:
            self._seps = list()
            self.extend(self._formats())
        elif len(set(nondigit)) == 1 and nondigit[0] in self._seps:
            self._seps = [nondigit[0]]
            self._allow_no_sep = False
            self.extend(self._formats())
        else:
            if self._allow_microsec and len(digits) == 4: clist = [self.CODES[:]]
            else: clist = self._get_code_list()
            formats = list()
            for codes in clist:
                if len(digits) == 1: codes = [''.join(codes)]
                formats.append(''.join(map(lambda v,s: v+s if s else v, codes, nondigit)))

            common = set(formats) & set(self._special_formats())
            if common: self.extend(list(common))
            else: raise ValueError(self.ERR_MSG % string)

    def _get_code_list(self):
        code_list = list()
        if self._figures[0]: code_list.append(self.CODES[:1])
        if self._figures[1]: code_list.append(self.CODES[:2])
        if self._figures[2]: code_list.append(self.CODES[:3])
        return code_list

    def _special_formats(self):
        if self._allow_microsec: self._sformats += self.MFORMATS
        return super(TimeFormats, self)._special_formats()


class DateFormats(BaseFormats):
    """
    A list of date-string-formats that generates himself.

    :keyword string:            Pre-select formats for string.
    :keyword seps:              Allowed separators for formats.
    :keyword allow_no_sep:      Allows formats without any separator.
    :keyword figures:           List of three booleans (s. :attr:`FIGURES`).
    :keyword allow_month_name:  Allows formats with month-names (%b or %B)

    :type string:               str
    :type seps:                 list
    :type allow_no_sep:         bool
    :type figures:              list
    :type allow_month_name:     bool

    :raises:                    ValueError if no format could be produced for
                                *string*.
    """
    CODES = ['%d', '%m', '%y']
    CODE_DICT = {
        'year' : ['%y', '%Y'], 
        'month' : ['%m', '%b', '%B'],
        'day' : ['%d']
        }
    SEPS = ['.', '-', '/', ' ', '. ']
    """A list of separators, formats are produced with."""
    ALLOW_NO_SEP = True
    """Allows formats without any separator ('%d%m%y')."""
    FIGURES = [True, True, True]
    """
    List of three booleans that predicts how many digits formats are allowed
    to have:

    * figures[0]: Allows the one-digit format '%d'.
    * figures[1]: Allows two-digit-formats like '%d/%m'.
    * figures[2]: Allows three-digit-formats like '%d/%m/%y'.
    """
    MONTH_CODE = [True, True, True]
    YEAR_CODE = [True, True]

    SFORMATS_OPTIONS = {
        'little' : [
            [['%d'], ['.']],
            [['%d'], ['.', '. '], ['%m', '%b'], ['.']],
            [['%d'], ['.'], ['%m', '%b'], ['. '], ['%y', '%Y']],
            [['%d'], ['.', '. '], ['%b', '%B'], [' '], ['%y', '%Y']],
            ],
        'big' : [
            [['%d'], ['.']],
            [['%m', '%b'], ['.', '. '], ['%d'], ['.']],
            [['%b', '%B'], [' '], ['%d'], ['.']],
            [['%y', '%Y'], [' '], ['%m', '%b'], ['.', '. '], ['%d'], ['.']],
            [['%y', '%Y'], [' '], ['%b', '%B'], [' '], ['%d'], ['.']],
            ],
        'middle' : [
            ]
        }

    SFORMATS = list()

    def __init__(self, string=None, seps=None, allow_no_sep=None, figures=None,
                allow_month_name=None):
        if allow_month_name is False:
            self._month_code = [True, False, False]
        elif allow_month_name is True:
            self._month_code = [True, True, True]
        else: self._month_code = self.MONTH_CODE
        self._year_code = self.YEAR_CODE
        self.SFORMATS = self.SFORMATS_OPTIONS[ENDIAN._key]

        super(DateFormats, self).__init__(string, seps, allow_no_sep, figures)

    @classmethod
    def config(cls, allow_month_name=None, *args, **kwargs):
        """
        Modify class-configuration.

        :keyword seps:              Allowed separators for formats.
        :keyword allow_no_sep:      Allows formats without any separator.
        :keyword figures:           List of three booleans (s. :attr:`FIGURES`).
        :keyword allow_month_name:  Allows formats with month-names (%b or %B)

        :type seps:                 list
        :type allow_no_sep:         bool
        :type figures:              list
        :type allow_month_name:     bool
        """
        if allow_month_name is False:
            cls.MONTH_CODE = [True, False, False]
        elif allow_month_name is True:
            cls.MONTH_CODE = [True, True, True]

        super(DateFormats, cls).config(*args, **kwargs)
        for c in [cls.MONTH_CODE, cls.YEAR_CODE]:
            if not any(c): raise Exception('invalid configuration')

    def _check_config(self):
        for c in [self._month_code, self._year_code, self._figures]:
            if not any(c): raise Exception('invalid configuration')

    def _for_string(self, string):
        """
        Checks string for literal month-name and calls the
        super-class-_for_string-method.
        """
        values = re.findall('[^\W_]+', string)
        seps = re.findall('[\W_]+', string)

        #masks:
        fmask = lambda f: map(lambda x,y: y if x else x, self._figures, f)
        ymask = lambda y: map(lambda x,y: y if x else x, self._year_code, y)
        mmask = lambda m: map(lambda x,y: y if x else x, self._month_code, m)

        #check month-code:
        if re.search('(?<![a-zA-Z])[a-zA-Z]{3}(?![a-zA-Z])', string):
            self._month_code = mmask([False, True, False])
        elif re.search('(?<![a-zA-Z])[a-zA-Z]{4,9}(?![a-zA-Z])', string):
            self._month_code = mmask([False, False, True])
        elif not re.search('[a-zA-Z]+', string):
            self._month_code = mmask([True, False, False])
        else: raise ValueError(self.ERR_MSG % string)

        #check values:
        if len(values) == 3:
            if len(values[ENDIAN.index('year')]) == 2: self._year_code = ymask([True, False])
            else: self._year_code = ymask([False, True])
            self._figures = fmask([False, False, True])
        elif len(values) == 2: self._figures = fmask([False, True, False])
        elif len(values) == 1:
            value = values[0]
            if seps: self._figures = fmask([True, False, False])
            elif not seps and self._allow_no_sep:
                if any(self._month_code[1:]):
                    if value[-1].isalpha(): self._figures = fmask([False, True, False])
                    else: self._figures = fmask([False, False, True])
                elif len(value) == 1: self._figures = fmask([True, False, False])
                elif len(value) <= 3: self._figures = fmask([True, True, False])
                else:
                    if len(value) <= 4: self._figures = fmask([False, True, True])
                    else: self._figures = fmask([False, False, True])
                    if len(value) <= 5: self._year_code = ymask([True, False])
                    elif len(value) >= 7: self._year_code = ymask([False, True])
            else: raise ValueError(self.ERR_MSG % string)
        else: raise ValueError(self.ERR_MSG % string)

        #check separators:
        if not seps and self._allow_no_sep:
            self._seps = list()
            self.extend(self._formats())
        #check if it fits a format of self._formats
        elif len(set(seps)) == 1 and len(seps) < len(values) and seps[0] in self._seps:
            self._seps = [seps[0]]
            self._allow_no_sep = False
            self.extend(self._formats())
        #check if it fits a format of self._special_formats
        else:
            clist = self._get_code_list()
            formats = list()
            for codes in clist:
                formats.append(''.join(map(lambda v,s: v+s if s else v, codes, seps)))
            common = set(formats) & set(self._special_formats())
            if common: self.extend(list(common))
            else: raise ValueError(self.ERR_MSG % string)

    def _get_code_list(self):
        def get_code(key):
            if key == 'month':
                mcodes = self.CODE_DICT['month']
                return filter(lambda c: self._month_code[mcodes.index(c)], mcodes)
            elif key == 'year':
                ycodes = self.CODE_DICT['year']
                return filter(lambda c: self._year_code[ycodes.index(c)], ycodes)
            elif key == 'day': return ['%d']

        code_list = list()
        if self._figures[0]: code_list.append(get_code('day'))
        if self._figures[1]:
            cc = map(get_code, ENDIAN.get(no_year=True))
            code_list.extend([(x,y) for x in cc[0] for y in cc[1]])
        if self._figures[2]:
            cc = map(get_code, ENDIAN)
            code_list.extend([(x,y,z) for x in cc[0] for y in cc[1] for z in cc[2]])

        return code_list



class DatetimeFormats(BaseFormats):
    """
    A list of datetime-string-formats that generates himself.

    :keyword string:            Pre-select formats for string.
    :keyword seps:              Allowed separators for formats.
    :keyword allow_no_sep:      Allows formats without any separator.
    :keyword date_config:       kwargs :class:`DateFormats` are initialized with
    :keyword time_config:       kwargs :class:`TimeFormats` are initialized with

    :type string:               str
    :type seps:                 list
    :type allow_no_sep:         bool
    :type date_config:          dict
    :type time_config:          dict

    :raises:                    ValueError if no format could be produced for
                                *string*.
    """
    SEPS = [' ', ',', '_', ';']
    """A list of separators, formats are produced with."""
    ALLOW_NO_SEP = True
    """Allows formats without any separator ('%H%M%S')."""

    def __init__(self, string=None, seps=None, allow_no_sep=None,
                date_config=dict(), time_config=dict()):
        self._date_config = dict(
            seps = DateFormats.SEPS,
            allow_no_sep = DateFormats.ALLOW_NO_SEP,
            figures = DateFormats.FIGURES,
            allow_month_name = DateFormats.MONTH_CODE[-1],
            )
        self._time_config = dict(
            seps = TimeFormats.SEPS,
            allow_no_sep = TimeFormats.ALLOW_NO_SEP,
            figures = TimeFormats.FIGURES,
            allow_microsec = TimeFormats.ALLOW_MICROSEC,
            )
        self._date_config.update(date_config)
        self._time_config.update(time_config)
        super(DatetimeFormats, self).__init__(string, seps, allow_no_sep)

    @classmethod
    def config(self, *args, **kwargs):
        """
        Modify class-configuration.

        :keyword seps:              Allowed separators for formats.
        :keyword allow_no_sep:      Allows formats without any separator.
        :keyword date_config:       kwargs :class:`DateFormats` are initialized with
        :keyword time_config:       kwargs :class:`TimeFormats` are initialized with

        :type seps:                 list
        :type allow_no_sep:         bool
        :type date_config:          dict
        :type time_config:          dict
        """
        super(DatetimeFormats, self).config(*args, **kwargs)

    def _for_string(self, string):
        """
        Try to reduce the amount of seps for all three format-classes.
        time-seps and date-seps will be passed to the respective constructor.
        """
        formats = list()
        pairs = list()
        for s in self._seps:
            i = 0
            while i <= len(string):
                try: i = string.index(s, i+1)
                except ValueError: break
                else: pairs.append((string[:i], s, string[i:].strip(s)))

        if not pairs:
            if not self._allow_no_sep: raise ValueError(self.ERR_MSG % string)
            elif re.findall('[_\W]+', string): raise ValueError(self.ERR_MSG % string)
            else:
                i = len(string)
                while i > 1:
                    i -= 1
                    pairs.append((string[:i], str(), string[i:]))

        for d, s, t in pairs:
            try:
                df = DateFormats(d)
                tf = TimeFormats(t)
            except ValueError: continue
            else: formats.extend([d + s + t for d in df for t in tf])

        self.extend([f for i,f in enumerate(formats) if not f in formats[:i]])

    def _all(self):
        """
        Generate datetime-formats by combining date- and time-formats.
        """
        formats = list()
        date_fmt = DateFormats(**self._date_config)
        time_fmt = TimeFormats(**self._time_config)
        for s in self._seps:
            formats += [s.join((d, t)) for d in date_fmt for t in time_fmt]
        self.extend(formats)
        if self._allow_no_sep:
            formats = list()
            #TODO: warrant that no sformats are included
            self._date_config['allow_no_sep'] = True
            self._time_config['allow_no_sep'] = True
            self._date_config['seps'] = list()
            self._time_config['seps'] = list()
            date_fmt = DateFormats(**self._date_config)
            time_fmt = TimeFormats(**self._time_config)
            formats += [str().join((d, t)) for d in date_fmt for t in time_fmt]
            self.extend(formats)



def parsetime(string, formats=list()):
    """
    Parse a string to a :class:`datetime.time` -object.

    :arg str string:        String to be parsed.
    :keyword list formats:  Optional list of formats-string.

    :rtype:                 :class:`datetime.time`
    :raises:                ValueError, if string couldn't been parsed

    The string is tried to be parsed with every format of *formats*.
    If *formats* not given :class:`TimeFormats`\ (string) is used.
    """
    formats = formats or TimeFormats(string=string)
    for f in formats:
        try: return datetime.datetime.strptime(string, f).time()
        except ValueError: continue
    raise ValueError("couldn't parse '%s' as time" % string)


def parsedate(string, formats=list(), today=None):
    """
    Parse a string to a :class:`datetime.date`-object.

    :arg str string:        String to be parsed.
    :keyword list formats:  Optional list of formats-string.
    :keyword today:         optional date
    :type today:            datetime.date

    :rtype:                 :class:`datetime.date`
    :raises:                ValueError, if string couldn't been parsed

    *string* is tried to be parsed with every format of *formats*.
    If *formats* not given :class:`DateFormats`\ (string) is used.

    If *string* is parsed with an incomplete format (missing year or year and
    month), the date will be completed by *today* or :attr:`timeparser.TODAY`.
    """
    formats = formats or DateFormats(string=string)
    today = today or TODAY
    for f in formats:
        try: date = datetime.datetime.strptime(string, f).date()
        except ValueError: continue
        else:
            if '%y' not in f.lower():
                date = date.replace(year=today.year)
            if '%m' not in f and '%b' not in f.lower():
                date = date.replace(month=today.month)
            return date
    raise ValueError("couldn't parse '%s' as date" % string)


def parsedatetime(string, formats=list(), today=None):
    """
    Parse a string to a :class:`datetime.datetime`-object.

    :arg str string:        String to be parsed.
    :keyword list formats:  Optional list of formats-string.
    :keyword today:         Optional date
    :type today:            datetime.datetime

    :rtype:                 :class:`datetime.datetime`
    :raises:                ValueError, if string couldn't been parsed

    *string* is tried to be parsed with every format of *formats*.
    If *formats* not given :class:`DatetimeFormats`\ (string) is used.

    If *string* is parsed with an incomplete format (missing year or year and
    month), the date will be completed by *today* or :attr:`timeparser.TODAY`.
    """
    formats = formats or DatetimeFormats(string=string)
    today = today or TODAY
    for f in formats:
        try: dtime = datetime.datetime.strptime(string, f)
        except ValueError: continue
        else:
            if '%y' not in f.lower():
                dtime = dtime.replace(year=today.year)
            if '%m' not in f and '%b' not in f.lower():
                dtime = dtime.replace(month=today.month)
            return dtime
    raise ValueError("couldn't parse '%s' as datetime" % string)


def parsetimedelta(string, key='weeks'):
    #TODO: rework the key-word-docstring-part.
    """
    Parse a string to a :class:`datetime.timedelta`-object.

    :arg str string:    String to be parsed.
    :keyword str key:   String that contains or matches a timedelta-keyword
                        (defaults to 'weeks').

    :rtype:             :class:`datetime.timedelta`
    :raises:            ValueError, if string couldn't been parsed

    parsetimedelta looks for digits in *string*, that could be seperated. These
    digits will be the arguments for :class:`datetime.timedelta`. Thereby *key*
    is used to determine the *unit* of the first argument, which could be one of
    the keywords for :class:`datetime.timedelta` ('weeks', 'days', 'hours',
    'minutes', 'seconds'). The following arguments get each the next lesser
    *unit*:

    >>> parsetimedelta('1, 2, 3', 'h') == datetime.timedelta(hours=1, minutes=2, seconds=3)
    True

    Another way is to just place keyword-matching literals within the string:
    
    >>> parsetimedelta('1h 2m 3s') == datetime.timedelta(hours=1, minutes=2, seconds=3)
    True
    """
    kws = ('weeks', 'days', 'hours', 'minutes', 'seconds')
    msg = "couldn't parse '%s' as timedelta"
    key_msg = "couldn't find a timedelta-key for '%s'"

    rkey = key.lower()

    values = [int(x) for x in re.findall('[-+]?\d+', string)]
    rkeys = re.findall('[a-zA-Z]+', string)

    try: key = [k for k in kws if k in rkey or re.match(rkey, k)][0]
    except IndexError: raise ValueError(key_msg % key)
    try: keys = map(lambda r: [k for k in kws if re.match(r, k)][0], rkeys)
    except IndexError: raise ValueError(msg % string)

    if len(keys) == len(values): kwargs = dict(zip(keys, values))
    elif keys: raise ValueError(msg % string)
    else: kwargs = dict(zip(kws[kws.index(key):], values))

    try: timedelta = datetime.timedelta(**kwargs)
    except: raise ValueError(msg % string)
    else: return timedelta




