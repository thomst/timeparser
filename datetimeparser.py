"""
Parse strings to datetime.time-, -date- or -datetime-objects.
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
    # this gives me a MIDDLE_ENDIAN-date instead of a LITTLE_ENDIAN.
    # For now I use unix's date-command.
    datestring = subprocess.check_output(shlex.split('date +%x'))
    one, two, three = DIGITS.findall(datestring)
    if int(one) == datetime.date.today().year: return BIG_ENDIAN
    else: return LITTLE_ENDIAN

setEndian(guessEndian())
setToday(datetime.date.today())

def getTimeFormats(seps=None):
    seps = seps or TIME_SEPS
    formats = ['%X', '%H']
    no_sec = ['%H', '%M']
    codes = ['%H', '%M', '%S']
    for sep in seps:
        formats.append(sep.join(no_sec))
        formats.append(sep.join(codes))
        formats.append(sep.join(codes) + '.%f')
        formats.append(sep.join(codes) + ' %f')
    return formats

def getDateFormats(seps=None, endian=None):
    seps = seps or DATE_SEPS
    endian = endian or ENDIAN
    formats = ['%x', '%d']
    code_map = {
        BIG_ENDIAN : ['%y', '%m', '%d'],
        LITTLE_ENDIAN : ['%d', '%m', '%y'],
        MIDDLE_ENDIAN : ['%m', '%d', '%y'],
        }
    codes = code_map[endian]
    no_year = codes[:]
    no_year.remove('%y')

    #first the no_year-formats, because %m%d should be checked before %y%m%d
    #otherwise 1124 would be 4.2.2011 instead of 24.11.2013
    for sep in seps:
        formats.append(sep.join(no_year))
        formats.append(sep.join(no_year).replace('m', 'b'))
        formats.append(sep.join(no_year).replace('m', 'B'))
        formats.append(sep.join(codes))
        formats.append(sep.join(codes).replace('y', 'Y'))
        formats.append(sep.join(codes).replace('m', 'b'))
        formats.append(sep.join(codes).replace('m', 'B'))
    return formats

def getDatetimeFormats(seps=None, date_formats=list(), time_formats=list(), endian=None):
    seps = seps or DATE_TIME_SEPS
    endian = endian or ENDIAN
    df = date_formats or getDateFormats(endian=endian)
    tf = time_formats or getTimeFormats()
    datetime_formats = list()
    for sep in seps:
        datetime_formats += [sep.join((d, t)) for d in df for t in tf]
    return datetime_formats


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
    formats = formats or getTimeFormats()
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
    formats = formats or getDateFormats()
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
    formats = formats or getDatetimeFormats()
    if not formats:
        df = DATE_FORMATS
        tf = TIME_FORMATS
        for delimiter in DATE_TIME_SEPS:
            formats += [delimiter.join((d, t)) for d in df for t in tf]
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



