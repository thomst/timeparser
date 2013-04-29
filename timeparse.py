"""
Parse strings to time-, date-, datetime- or timedelta-objects of the datetime-module.
"""
import datetime
import re
import subprocess
import shlex


DIGITS = re.compile('(?<!\w)([-+]?\w+)(?![-+\w])')
DELTA_KEYS = ('weeks', 'days', 'hours', 'minutes', 'seconds')
WEEKS = 0
DAYS = 1
HOURS = 2
MINUTES = 3
SECONDS = 4

TIME_SEPS = [':', ' ', '']
DATE_SEPS = ['.', '-', '/', ' ', '']
DATE_TIME_SEPS = [' ', ',', '_', ';', '']

LITTLE_ENDIAN = 10
BIG_ENDIAN = 20
MIDDLE_ENDIAN = 30

def setToday(value):
    global TODAY
    if isinstance(value, datetime.date): TODAY = value
    else: raise ValueError("'%s' is no datetime.date-instance" % value)

def setEndian(value):
    global ENDIAN
    if value in [LITTLE_ENDIAN, BIG_ENDIAN, MIDDLE_ENDIAN]: ENDIAN = value
    else:  raise ValueError("wrong endian-value")

#TODO: find a more solid way (which could also regard MIDDLE_ENDIAN)
def guessEndian():
    # one, two, three = DIGITS.findall(today.strftime('%x'))
    # returns a MIDDLE_ENDIAN-date instead of a LITTLE_ENDIAN.
    # For now I use unix's date-command.
    datestring = subprocess.check_output(shlex.split('date +%x'))
    one, two, three = DIGITS.findall(datestring)
    if int(one) == datetime.date.today().year: return BIG_ENDIAN
    else: return LITTLE_ENDIAN

setEndian(guessEndian())
setToday(datetime.date.today())


class BaseFormats(list):
    def __init__(self, formats=list(), seps=list(), allow_no_sep=True,
                    figures=[True, True, True], string=None):
        super(BaseFormats, self).__init__(formats)
        self._seps = seps or self.SEPS[:]
        self._allow_no_sep = allow_no_sep
        self._figures = figures
        self._sep = None
        self._index = 0
        if string: self._evaluate_string(string)
        if self and string: self._weed()
        elif not self: self._generate()

    def _evaluate_string(self, string):
        try: self._sep = [s for s in self._seps if s in string][0]
        except IndexError:
            if self._allow_no_sep: self._seps = list()
            else: self._figures = [True, False, False]
        else:
            figures = string.split(self._sep)
            if len(figures) == 3: self._figures = [False, False, True]
            elif len(figures) == 2: self._figures = [False, True, False]

    def _weed(self):
        #TODO: this doesn't work properly with _evaluate_string...
        for f in self[:]:
            if self._sep and not self._sep in f: self.remove(f)
            if not self._figures[2] and self.FIGURES[2] in f: self.remove(f)
            if not self._figures[1] and self.FIGURES[1] in f: self.remove(f)

    def _get_code_list(self):
        pass

    def _generate(self):
        formats = list()
        code_list = self._get_code_list()
        if self._figures[0]: formats.append(self.FIGURES[0])
        if self._allow_no_sep: self._seps.append(str())
        for s in self._seps:
            for codes in code_list: formats.append(s.join(codes))
        self.extend(formats)


class TimeFormats(BaseFormats):
    SEPS = [':', ' ']
    MICROSEC_SEPS = ['.', ' ']
    CODES = ['%H', '%M', '%S', '%f']
    FIGURES = ['%H', '%M', '%S']

    def __init__(self, four_figure=False, *args, **kwargs):
        self._four_figure = four_figure
        super(TimeFormats, self).__init__(*args, **kwargs)

    def _get_code_list(self):
        code_list = list()
        if self._figures[1]: code_list.append(self.CODES[:2])
        if self._figures[2]: code_list.append(self.CODES[:3])
        if self._four_figure:
            for sep in self.MICROSEC_SEPS:
                code_list.append(self.CODES[:2] + [sep.join(self.CODES[2:])])
        return code_list


class DateFormats(BaseFormats):
    SEPS = ['.', '-', '/', ' ']
    CODES = {
        'year' : ['%y', '%Y'], 
        'month' : ['%m', '%b', '%B'],
        'day' : ['%d']
        }
    FIGURES = ['%d', '%m', '%y']

    def __init__(self, allow_month_name=True, endian=None, *args, **kwargs):
        self._allow_month_name = allow_month_name
        self._endian = endian or ENDIAN
        super(DateFormats, self).__init__(*args, **kwargs)

    @staticmethod
    def _get_order(endian):
        if endian == LITTLE_ENDIAN: return ('day', 'month', 'year')
        if endian == BIG_ENDIAN: return ('year', 'month', 'day')
        if endian == MIDDLE_ENDIAN: return ('month', 'day', 'year')

    def _get_code_list(self):
        code_list = list()
        order = self._get_order(self._endian)
        code_dict = dict([(k, self.CODES[k][0]) for k in order])

        def get_month_name(order):
            c_dict = code_dict.copy()
            c_list = list()
            for month in self.CODES['month']:
                c_dict['month'] = month
                c_list.append([c_dict[k] for k in order])
            return c_list

        if self._figures[1]:
            incomplete = list(order)
            incomplete.remove('year')
            if self._allow_month_name: code_list.extend(get_month_name(incomplete))
            else: code_list.append([code_dict[k] for k in incomplete])

        if self._figures[2]:
            for year in self.CODES['year']:
                code_dict['year'] = year
                if self._allow_month_name: code_list.extend(get_month_name(order))
                else: code_list.append([code_dict[k] for k in order])

        return code_list


class DatetimeFormats(BaseFormats):
    SEPS = [' ', ',', '_', ';']
    DATE_SEPS = DateFormats.SEPS
    TIME_SEPS = TimeFormats.SEPS

    def __init__(self, seps=list(), allow_no_sep=True, string=None, date_kwargs=dict(), time_kwargs=dict()):
        self._seps = seps or self.SEPS
        self._allow_no_sep = allow_no_sep
        self._date_kwargs = date_kwargs
        self._time_kwargs = time_kwargs
        if string: self._evaluate_string(string)
        self._generate()

    def _evaluate_string(self, string):
        #try hard to split the string...
#        used_seps = re.findall('\W+', string)
#        common_seps = set(used_seps) & set(self._seps)

        date_seps = self._date_kwargs.get('seps', None) or self.DATE_SEPS
        time_seps = self._time_kwargs.get('seps', None) or self.TIME_SEPS

        #reduce seps for time- and date-formats:
        self._seps = [s for s in self._seps if s in string]
        self._date_kwargs['seps'] = [s for s in date_seps if s in string]
        self._time_kwargs['seps'] = [s for s in time_seps if s in string]

    def _generate(self):
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
        string (str):    string to parse
        formats (list): list of timecode-formats

    Parsing string is tried out with every format in formats. If formats not
    given DateTimeParser.TIME_FORMATS is used instead.
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
        string (str):    string to parse
        formats (list): list of timecode-formats

    Parsing string is tried out with every format in formats. If formats not
    given DateTimeParser.DATE_FORMATS is used instead.
    The first format that fits is used.

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
        string (str):    string to parse
        formats (list): list of timecode-formats

    Parsing string is tried out with every format in formats. If formats not
    given DateTimeParser.DATETIME_FORMATS is used instead. If this is an
    list (which it is by default), a format-list is generated by combining
    every DATE_FORMAT with every TIME_FORMAT using every delimiter defined
    in DateTimeParser.DATETIME_DELIMITER.
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
    """Convert a string to a timedelta-object.
    """
    try: delta = [int(x) for x in DIGITS.findall(string)]
    except: raise ValueError("couldn't parse %s as timedelta" % string)
    delta = dict(zip(DELTA_KEYS[key:], delta))
    delta = datetime.timedelta(**delta)
    return delta



