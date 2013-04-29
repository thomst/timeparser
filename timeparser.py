"""
Parse strings to time-, date-, datetime- or timedelta-objects of the datetime-module.
"""
import datetime
import re
import subprocess
import shlex


DIGITS = re.compile('(?<!\w)([-+]?\w+)(?![-+\w])')
WEEKS = 0
DAYS = 1
HOURS = 2
MINUTES = 3
SECONDS = 4


LITTLE_ENDIAN = 10
BIG_ENDIAN = 20
MIDDLE_ENDIAN = 30

def setToday(date):
    """
    Change the value of TODAY.
    
    Args:
        date (datetime.date-obj):  new date for TODAY

    Raises TypeError if date is not a datetime.date-instance.
    """
    global TODAY
    if isinstance(date, datetime.date): TODAY = date
    else: raise TypeError("'%s' is no datetime.date-instance" % date)

setToday(datetime.date.today())


#TODO: find a more solid way (which could also regard MIDDLE_ENDIAN)
def guessEndian():
    """
    Try to guess which endian is the local standart.
    """
    # one, two, three = DIGITS.findall(today.strftime('%x'))
    # returns a MIDDLE_ENDIAN-date instead of a LITTLE_ENDIAN.
    # For now I use unix's date-command.
    # Mind that this won't work if date +%x returns a datestring with a
    # two-digit-year.
    datestring = subprocess.check_output(shlex.split('date +%x'))
    one, two, three = DIGITS.findall(datestring)
    if int(one) == datetime.date.today().year: return BIG_ENDIAN
    else: return LITTLE_ENDIAN





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
    def __init__(self, string=None, seps=None, figures=None, allow_no_sep=None):
        """
        Constructor of BaseFormats.
        
        Kwargs:
            string (str):       string formats are generated for
            seps (list):        separators formats are generated with
            figures (list):     list of three boolean that predicts how many
                                single codes a format may have.
                                E.g.: [True, False, True] for date-formats could
                                be '%d' and '%d.%m.%y' but not '%d.%m'.
            allow_no_sep (bool):    allows formats without separators ('%d%m%y')

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
        self._seps = seps or self.SEPS[:]
        self._figures = figures or self.FIGURES[:]
        if allow_no_sep is None: self._allow_no_sep = self.ALLOW_NO_SEP
        else: self._allow_no_sep = allow_no_sep
        self._sep = None
        if string: self._evaluate_string(string)
        self._generate()

    @classmethod
    def config(cls, seps=None, allow_no_sep=None, figures=None):
        """
        Modify the configuration of the class.

        Kwargs:
            seps (list):        separators formats are generated with
            figures (list):     list of three boolean that predicts how many
                                digits the formats have.
            allow_no_sep (bool):    allows formats without separators ('%d%m%y')

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
        try: self._sep = [s for s in self._seps if s in string][0]
        except IndexError:
            if self._allow_no_sep: self._seps = list()
            else: self._figures = [True, False, False]
        else:
            self._seps.append(self._sep)
            figures = string.split(self._sep)
            if len(figures) == 3: self._figures = [False, False, True]
            elif len(figures) == 2: self._figures = [False, True, False]

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

    def __init__(self, microsec=None, *args, **kwargs):
        """
        Constructor of TimeFormats.
        
        Kwargs:
            microsec (bool):    if True also formats with '%f' for microseconds
                                are produced.

        *args and **kwargs will be passed to BaseFormats.__init__.
        """
        if microsec is None: self._microsec = self.ALLOW_MICROSEC
        else: self._microsec = microsec
        super(TimeFormats, self).__init__(*args, **kwargs)

    @classmethod
    def config(cls, microsec=None, *args, **kwargs):
        """
        Modify class-configuration.

        Kwargs:
            microsec (bool):    if True also formats with '%f' for microseconds
                                are produced.

        *args and **kwargs will be passed to BaseFormats.config.
        """
        if not microsec is None: cls.ALLOW_MICROSEC = microsec
        super(TimeFormats, cls).config(*args, **kwargs)

    def _get_code_list(self):
        code_list = list()
        if self._figures[1]: code_list.append(self.CODES[:2])
        if self._figures[2]: code_list.append(self.CODES[:3])
        if self._microsec:
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
        ENDIAN = guessEndian()              #determines the order for dates

    SEPS, ALLOW_MONTH_NAME and ENDIAN can be changed via DateFormats.config
    """
    CODES = ['%d', '%m', '%y']
    SEPS = ['.', '-', '/', ' ']
    CODE_DICT = {
        'year' : ['%y', '%Y'], 
        'month' : ['%m', '%b', '%B'],
        'day' : ['%d']
        }
    ALLOW_MONTH_NAME = True
    ENDIAN = guessEndian()

    def __init__(self, allow_month_name=None, endian=None, *args, **kwargs):
        """
        Constructor of DateFormats.

        Kwargs:
            allow_month_name (bool):    if True also '%b' and '%B' are used to
                                        produce formats.
            endian (int):               determines the order for dates (s.b.)

        Endianness is the order in which day, month and year constitutes a date.
        This module defines three constants:
        LITTLE_ENDIAN (little first):   day, month, year
        BIG_ENDIAN (biggest first):     year, month, day
        MIDDLE_ENDIAN (middle first):   month, day, year
        Use one of these constants as value for the endian-parameter.

        *args and **kwargs will be passed to BaseFormats.__init__.
        """
        if allow_month_name is None:
            self._allow_month_name = self.ALLOW_MONTH_NAME
        else: self._allow_month_name = allow_month_name
        self._endian = endian or self.ENDIAN
        super(DateFormats, self).__init__(*args, **kwargs)

    @classmethod
    def config(cls, allow_month_name=None, endian=None, *args, **kwargs):
        """
        Modify class-configuration.

        Kwargs:
            allow_month_name (bool):    if True also '%b' and '%B' are used to
                                        produce formats.
            endian (int):               determines the order for dates (s.a.)

        *args and **kwargs will be passed to BaseFormats.config.
        """
        if not allow_month_name is None: cls.ALLOW_MONTH_NAME = allow_month_name
        if endian: cls.ENDIAN = endian
        super(DateFormats, cls).config(*args, **kwargs)

    @staticmethod
    def _get_order(endian):
        if endian == LITTLE_ENDIAN: return ('day', 'month', 'year')
        if endian == BIG_ENDIAN: return ('year', 'month', 'day')
        if endian == MIDDLE_ENDIAN: return ('month', 'day', 'year')

    def _evaluate_string(self, string):
        """
        Checks string for literal month-name and calls the
        super-class-_evaluate_string-method.
        """
        if not re.search('[a-zA-Z]+', string): self._allow_month_name = False
        super(DateFormats, self)._evaluate_string(string)

    def _get_code_list(self):
        code_list = list()
        order = self._get_order(self._endian)
        code_dict = dict([(k, self.CODE_DICT[k][0]) for k in order])

        def get_month_name(order):
            c_dict = code_dict.copy()
            c_list = list()
            for month in self.CODE_DICT['month']:
                c_dict['month'] = month
                c_list.append([c_dict[k] for k in order])
            return c_list

        if self._figures[1]:
            incomplete = list(order)
            incomplete.remove('year')
            if self._allow_month_name: code_list.extend(get_month_name(incomplete))
            else: code_list.append([code_dict[k] for k in incomplete])

        if self._figures[2]:
            for year in self.CODE_DICT['year']:
                code_dict['year'] = year
                if self._allow_month_name: code_list.extend(get_month_name(order))
                else: code_list.append([code_dict[k] for k in order])

        return code_list


class DatetimeFormats(BaseFormats):
    """
    A date-formats-list that generates himself.

    Globals are:
        SEPS = [' ', ',', '_', ';']         #separators used to produce formats

    SEPS can be changed via DateFormats.config
    """
    SEPS = [' ', ',', '_', ';']
    DATE_SEPS = DateFormats.SEPS
    TIME_SEPS = TimeFormats.SEPS

    def __init__(self, date_kwargs=dict(), time_kwargs=dict(), *args, **kwargs):
        """
        Constructor of DatetimeFormats.

        Kwargs:
            date_kwargs (dict):     kwargs passed to the DateFormats-constructor
            time_kwargs (dict):     kwargs passed to the TimeFormats-constructor

        DatetimeFormats._gererate calles the DateFormats- and
        TimeFormats-constructor to combine those formats.

        *args and **kwargs will be passed to BaseFormats.__init__.
        """
        self._date_kwargs = date_kwargs
        self._time_kwargs = time_kwargs
        super(DatetimeFormats, self).__init__(*args, **kwargs)

    def _evaluate_string(self, string):
        """
        Try to reduce the amount of seps for all three formats-classes.
        time-seps and date-seps will be passed to the respective constructor.
        """
        #TODO: try hard to split the string and pass the parts to the
        #constructors of TimeFormats and DateFormats.
#        used_seps = re.findall('\W+', string)
#        common_seps = set(used_seps) & set(self._seps)

        #reduce seps for time- and date-formats:
        date_seps = self._date_kwargs.get('seps', None) or self.DATE_SEPS
        time_seps = self._time_kwargs.get('seps', None) or self.TIME_SEPS
        self._seps = [s for s in self._seps if s in string]
        self._date_kwargs['seps'] = [s for s in date_seps if s in string]
        self._time_kwargs['seps'] = [s for s in time_seps if s in string]

    def _generate(self):
        """
        Generate datetime-formats by combining date- and time-formats.
        """
        formats = list()
        date_fmt = DateFormats(**self._date_kwargs)
        time_fmt = TimeFormats(**self._time_kwargs)
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


def parsedatetime(string, formats=list()):
    """
    Parse a string to a datetime.datetime-object.

    Args:
        string (str):       string to be parsed
        formats (list):     list of timecode-formats

    Parsing string is tried out with every format in formats. If formats not
    given a DatetimeFormats-list is used instead.
    The first format that fits is used.

    Return a datetime.datetime-object.
    Raises ValueError if string couldn't be parsed as datetime.
    """
    formats = formats or DatetimeFormats(string=string)
    for f in formats:
        try: return datetime.datetime.strptime(string, f)
        except ValueError: continue
    raise ValueError("couldn't parse %s as datetime" % string)


def parsetimedelta(string, key=WEEKS):
    """
    Parse a string to a datetime.timedelta-object.

    Args:
        string (str):       string to be parsed
        key (int):          index for the key-list

    Key-list is a list of keys
    From the keys of key-list and the values that could be extracted from string
    the kwargs for the datetime.timedelta-constructor will be built. The key-list
    is ('weeks', 'days', ... , 'seconds') and will be used from key-index on.
    Use the module-gobals WEEKS, DAYS, HOURS, MINUTES and SECONDS to pass to key.

    Return a datetime.timedelta-object.
    Raises ValueError if string couldn't be parsed as timedelta.
    """
    keys = ('weeks', 'days', 'hours', 'minutes', 'seconds')
    try: values = [int(x) for x in DIGITS.findall(string)]
    except ValueError: raise ValueError("couldn't parse %s as timedelta" % string)
    except TypeError: raise
    else:
        kwargs = dict(zip(keys[key:], values))
        timedelta = datetime.timedelta(**kwargs)
        return timedelta


