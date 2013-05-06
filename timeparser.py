"""
Parse strings to time-, date-, datetime- or timedelta-objects of the datetime-module.
"""
import datetime
import re
import subprocess
import shlex



class TODAY(datetime.date):
    def __new__(cls, *args, **kwargs):
        try: date = datetime.date(*args, **kwargs)
        except: date = datetime.date.today()
        return datetime.date.__new__(cls, date.year, date.month, date.day)

    @classmethod
    def set(cls, *args, **kwargs):
        global TODAY
        TODAY = cls(*args, **kwargs)

TODAY = TODAY()


class ENDIAN:
    KEY = None
    OPTIONS = dict(
        little = ('day', 'month', 'year'),
        big = ('year', 'month', 'day'),
        middle = ('month', 'day', 'year')
        )

    def __init__(self):
        self.set()

    def __iter__(self):
        return self.OPTIONS[self.KEY].__iter__()

    def __getitem__(self, key):
        return self.OPTIONS[self.KEY].__getitem__(key)

    def __repr__(self):
        return str(self.OPTIONS[self.KEY])

    @classmethod
    def set(cls, key=None):
        if key: cls.KEY = cls._check_key(key)
        else: cls.KEY = cls._guess()

    @classmethod
    def _check_key(cls, key):
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

ENDIAN = ENDIAN()


class BaseFormats(list):
    """
    A list as base-class for the format-classes.
    Format-classes are lists that generates themself as a list of formats.

    These globals are defined:
        ALLOW_NO_SEP = True             #allows formats without separators
        FIGURES = [True, True, True]    #allows formats with one, two and three
                                        #codes ('%d', '%d.%m' and '%d.%m.%y')

    They can be changed via the config-classmethod.
    """
    FIGURES = [True, True, True]
    ALLOW_NO_SEP = True
    def __init__(self, string=None, seps=None, allow_no_sep=None, figures=None):
        """
        Constructor of BaseFormats.
        
        Kwargs:
            string (str):       string formats are generated for
            seps (list):        separators formats are generated with
            allow_no_sep (bool):    allows formats without separators ('%d%m%y')
            figures (list):     list of three boolean that predicts how many
                                single codes a format may have.
                                E.g.: [True, False, True] for date-formats could
                                be '%d' and '%d.%m.%y' but not '%d.%m'.

        seps, figures and allow_no_sep determine the generic range of formats that
        are accepted, while string is used to predict specific parameters that
        limit the generation of formats. This is much more performant because
        the parse-functions won't have to check too much formats.

        Parameters for the generic range of formats have all broad defaults
        (an exception is TimeFormats.ALLOW_MICROSEC which defaults to False).
        To become a more specific range of formats either pass accordant params
        to the constructor or use the config-class-method. The latter will change
        the class' configuration durably.
        """
        super(BaseFormats, self).__init__()
        self._figures = figures or self.FIGURES[:]
        if isinstance(seps, list): self._seps = seps[:]
        else: self._seps = self.SEPS[:]
        if allow_no_sep is None: self._allow_no_sep = self.ALLOW_NO_SEP
        else: self._allow_no_sep = allow_no_sep
        if string: self._evaluate_string(string)
        self._generate()

    @classmethod
    def config(cls, seps=None, allow_no_sep=None, figures=None):
        """
        Modify the configuration of the class.

        Kwargs:
            seps (list):        separators formats are generated with
            allow_no_sep (bool):    allows formats without separators ('%d%m%y')
            figures (list):     list of three boolean that predicts how many
                                digits the formats have.

        All these parameters exists as class-gobals.
        (The child-classes TimeFormats an DateFormats add specific globals.)
        """
        if seps: cls.SEPS = seps
        if not allow_no_sep is None: cls.ALLOW_NO_SEP = allow_no_sep
        if figures: cls.FIGURES = figures

    def _evaluate_string(self, string):
        """
        While the generic parameters predict the range of all possible formats,
        the string (if given) is used to precice this range for the specific
        string. E.g. if string is '23:44:02' only formats with ':' as separator
        are produced.
        """
        try: sep = [s for s in self._seps if s in string][0]
        except IndexError:
            if self._allow_no_sep: self._seps = list()
            elif self._figures[0]: self._figures = [True, False, False]
            else: raise ValueError("no proper format for '%s'" % string)
        else:
            self._allow_no_sep = False
            self._seps = [sep]
            figures = len(string.split(sep))
            if self._figures[2] and figures == 3:
                self._figures = [False, False, True]
            elif self._figures[1] and figures == 2:
                self._figures = [False, True, False]
            else: raise ValueError("no proper format for '%s'" % string)

    def _get_code_list(self):
        """
        Builds and returns a list of code-lists (like ['%d', '%b', '%Y']).
        These code-lists will be joined to format-strings by self._generate().
        """
        pass

    def _generate(self):
        """
        Generates the formats and populate the list-instance.
        """
        formats = list()
        code_list = self._get_code_list()
        if self._figures[0]: formats.append(self.CODES[0])
        if self._allow_no_sep: self._seps.append(str())
        for s in self._seps:
            for codes in code_list: formats.append(s.join(codes))
        self.extend(formats)


class TimeFormats(BaseFormats):
    """
    A time-formats-list that generates himself.

    Globals are:
        CODES = ['%H', '%M', '%S', '%f']    #codes used to produce formats
        SEPS = [':', ' ']                   #separators used to produce formats
        MICROSEC_SEPS = ['.', ' ']          #separators microsec are added with
        ALLOW_MICROSEC = False              #allow formats with '%f'

    SEPS and ALLOW_MICROSEC can be changed via TimeFormats.config
    """
    SEPS = [':', ' ']
    CODES = ['%H', '%M', '%S', '%f']
    MICROSEC_SEPS = ['.', ' ']
    ALLOW_MICROSEC = False

    def __init__(self, string=None, seps=None, allow_no_sep=None, figures=None,
                allow_microsec=None, *args, **kwargs):
        """
        Constructor of TimeFormats.
        
        Kwargs:
            string (str):       string formats are generated for
            seps (list):        separators formats are generated with
            allow_no_sep (bool):    allows formats without separators ('%d%m%y')
            figures (list):     list of three boolean that predicts how many
                                digits the formats have.
            allow_microsec (bool):    if True also formats with '%f' for microseconds
                                are produced.
        """
        if allow_microsec is None: self._allow_microsec = self.ALLOW_MICROSEC
        else: self._allow_microsec = allow_microsec
        super(TimeFormats, self).__init__(string, seps, allow_no_sep, figures)

    @classmethod
    def config(cls, allow_microsec=None, *args, **kwargs):
        """
        Modify class-configuration.

        Kwargs:
            allow_microsec (bool):    if True also formats with '%f' for microseconds
                                are produced.

        *args and **kwargs will be passed to BaseFormats.config.
        """
        if not allow_microsec is None: cls.ALLOW_MICROSEC = allow_microsec
        super(TimeFormats, cls).config(*args, **kwargs)

    def _get_code_list(self):
        code_list = list()
        if self._figures[1]: code_list.append(self.CODES[:2])
        if self._figures[2]: code_list.append(self.CODES[:3])
        if self._allow_microsec:
            for sep in self.MICROSEC_SEPS:
                code_list.append(self.CODES[:2] + [sep.join(self.CODES[2:])])
        return code_list


class DateFormats(BaseFormats):
    """
    A date-formats-list that generates himself.

    Globals are:
        CODES = ['%d', '%m', '%y']          #codes used to produce formats
        SEPS = ['.', '-', '/', ' ']         #separators used to produce formats
        ALLOW_MONTH_NAME = True             #allow formats with codes '%b', '%B'

    SEPS and ALLOW_MONTH_NAME can be changed via DateFormats.config
    """
    CODES = ['%d', '%m', '%y']
    SEPS = ['.', '-', '/', ' ']
    CODE_DICT = {
        'year' : ['%y', '%Y'], 
        'month' : ['%m', '%b', '%B'],
        'day' : ['%d']
        }
    ALLOW_MONTH_NAME = True

    def __init__(self, string=None, seps=None, allow_no_sep=None, figures=None,
                allow_month_name=None):
        """
        Constructor of DateFormats.

        Kwargs:
            string (str):       string formats are generated for
            seps (list):        separators formats are generated with
            allow_no_sep (bool):    allows formats without separators ('%d%m%y')
            figures (list):     list of three boolean that predicts how many
                                digits the formats have.
            allow_month_name (bool):    if True also '%b' and '%B' are used to
                                        produce formats.
        """
        if allow_month_name is None:
            self._allow_month_name = self.ALLOW_MONTH_NAME
        else: self._allow_month_name = allow_month_name
        super(DateFormats, self).__init__(string, seps, allow_no_sep, figures)

    @classmethod
    def config(cls, allow_month_name=None, *args, **kwargs):
        """
        Modify class-configuration.

        Kwargs:
            allow_month_name (bool):    if True also '%b' and '%B' are used to
                                        produce formats.

        *args and **kwargs will be passed to BaseFormats.config.
        """
        if not allow_month_name is None: cls.ALLOW_MONTH_NAME = allow_month_name
        super(DateFormats, cls).config(*args, **kwargs)

    def _evaluate_string(self, string):
        """
        Checks string for literal month-name and calls the
        super-class-_evaluate_string-method.
        """
        if self._allow_month_name:
            if not re.search('[a-zA-Z]+', string): self._allow_month_name = False
        super(DateFormats, self)._evaluate_string(string)

    def _get_code_list(self):
        code_list = list()
        code_dict = dict([(k, self.CODE_DICT[k][0]) for k in ENDIAN])

        def get_month_name(order):
            c_dict = code_dict.copy()
            c_list = list()
            for month in self.CODE_DICT['month']:
                c_dict['month'] = month
                c_list.append([c_dict[k] for k in ENDIAN])
            return c_list

        if self._figures[1]:
            incomplete = list(ENDIAN)
            incomplete.remove('year')
            if self._allow_month_name: code_list.extend(get_month_name(incomplete))
            else: code_list.append([code_dict[k] for k in incomplete])

        if self._figures[2]:
            for year in self.CODE_DICT['year']:
                code_dict['year'] = year
                if self._allow_month_name: code_list.extend(get_month_name(ENDIAN))
                else: code_list.append([code_dict[k] for k in ENDIAN])

        return code_list


class DatetimeFormats(BaseFormats):
    """
    A date-formats-list that generates himself.

    Globals are:
        SEPS = [' ', ',', '_', ';']         #separators used to produce formats

    SEPS can be changed via DateFormats.config
    """
    SEPS = [' ', ',', '_', ';']

    def __init__(self, string=None, seps=None, allow_no_sep=None,
                date_config=dict(), time_config=dict()):
        """
        Constructor of DatetimeFormats.

        Kwargs:
            string (str):           string formats are generated for
            seps (list):            separators formats are generated with
            allow_no_sep (bool):    allows formats without separators ('%d%m%y')
            date_config (dict):     kwargs passed to the DateFormats-constructor
            time_config (dict):     kwargs passed to the TimeFormats-constructor

        DatetimeFormats._gererate calles the DateFormats- and
        TimeFormats-constructor to combine those formats.
        """
        self._date_config = dict(
            seps = DateFormats.SEPS,
            allow_no_sep = DateFormats.ALLOW_NO_SEP,
            figures = DateFormats.FIGURES,
            allow_month_name = DateFormats.ALLOW_MONTH_NAME,
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

    def _evaluate_string(self, string):
        """
        Try to reduce the amount of seps for all three formats-classes.
        time-seps and date-seps will be passed to the respective constructor.
        """
        _used = re.findall('[_\W]+', string)
        used = set(_used)
        date_seps = set(self._date_config['seps']) & used
        time_seps = set(self._time_config['seps']) & used
        seps = set(self._seps) & used

        #first check the usage of wrong separators
        if not used <= date_seps | time_seps | seps:
            raise ValueError("no proper format for '%s'" % string)

        ordered = [s for i,s in enumerate(_used) if not s in _used[:i]]
        common = seps & (date_seps | time_seps)
        wanted = seps - (date_seps | time_seps)

        self._date_config['seps'] = list(date_seps)
        self._time_config['seps'] = list(time_seps)
        self._seps = list(seps)

        if len(wanted) == 1:
            self._allow_no_sep = False
            self._seps = list(wanted)
        elif len(ordered) >= 3:
            self._allow_no_sep = False
            self._seps = ordered[1:2]
        elif not wanted:
            if common: self._seps = list(common)
            else:
                if self._allow_no_sep: self._seps = list()
                else: raise ValueError("no proper format for '%s'" % string)
        else: raise ValueError("no proper format for '%s'" % string)

        if not self._allow_no_sep and len(self._seps) == 1:
            datestring, timestring = string.split(self._seps[0])
            self._date_config['string'] = datestring
            self._time_config['string'] = timestring
        else:
            #if string couldn't be splitted at least refine the config...
            if not re.search('[a-zA-Z]+', string):
                self._date_config['allow_month_name'] = False

    def _generate(self):
        """
        Generate datetime-formats by combining date- and time-formats.
        """
        formats = list()
        date_fmt = DateFormats(**self._date_config)
        time_fmt = TimeFormats(**self._time_config)
        if self._allow_no_sep: self._seps.append(str())
        for s in self._seps:
            formats += [s.join((d, t)) for d in date_fmt for t in time_fmt]
        self.extend(formats)



def parsetime(string, formats=list()):
    """
    Parse a string to a datetime.time-object.

    Args:
        string (str):       string to be parsed
        formats (list):     list of timecode-formats

    Parsing string is tried out with every format in formats. If formats not
    given a TimeFormats-list is used instead.
    The first format that fits is used.

    Return a datetime.time-object.
    Raises ValueError if string couldn't be parsed as time.
    """
    formats = formats or TimeFormats(string=string)
    for f in formats:
        try: return datetime.datetime.strptime(string, f).time()
        except ValueError: continue
    raise ValueError("couldn't parse %s as time" % string)


def parsedate(string, formats=list(), today=None):
    """
    Parse a string to a datetime.date-object.

    Args:
        string (str):       string to be parsed
        formats (list):     list of timecode-formats
        today (date):

    Parsing string is tried out with every format in formats. If formats not
    given a DateFormats-list is used instead.
    The first format that fits is used.

    If a year-code or a year- and a month-code is missing from the fitting format,
    values for year (and month) are complemented by the modules global TODAY.
    TODAY defaults to the actual date but can be changed with setToday.

    Return a datetime.date-object.
    Raises ValueError if string couldn't be parsed as date.
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
    raise ValueError("couldn't parse %s as date" % string)


def parsedatetime(string, formats=list(), today=None):
    """
    Parse a string to a datetime.datetime-object.

    Args:
        string (str):       string to be parsed
        formats (list):     list of timecode-formats
        today (date):

    Parsing string is tried out with every format in formats. If formats not
    given a DatetimeFormats-list is used instead.
    The first format that fits is used.

    Return a datetime.datetime-object.
    Raises ValueError if string couldn't be parsed as datetime.
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
    raise ValueError("couldn't parse %s as datetime" % string)


def parsetimedelta(string, key='weeks'):
    #TODO: rework the key-word-docstring-part.
    """
    Parse a string to a datetime.timedelta-object.

    Args:
        string (str):       string to be parsed
        key (str):          string that contains or is substring of a key for
                            the timedelta-kwargs.

    First the string is scanned for pointers to keywords that can be used with
    the leading or following values as kwargs for datetime.timedelta.
    If no pointers are found, the key-argument determines the unit for the first
    value found within string. Following values have each the next lesser unit.

    For the pointers or the key-argument it is sufficient either to be a
    substring of a keyword or containing one.
    keywords are 'weeks', 'days', 'hours', 'minutes' and 'seconds'.

    Return a datetime.timedelta-object.
    Raises ValueError if string couldn't be parsed as timedelta.
    """
    kws = ('weeks', 'days', 'hours', 'minutes', 'seconds')
    msg = "couldn't parse %s as timedelta"
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




