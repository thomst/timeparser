import unittest
import datetime
import timeparser
import argparse

from argparse import ArgumentError

from timeparser import AppendTimeOrDatetime
from timeparser import ParseTimeOrDatetime
from timeparser import ParseDatetime
from timeparser import ParseTimedelta
from timeparser import ParseDate
from timeparser import ParseTime


class ParserTests(unittest.TestCase):
    def test_type(self):
        self.assertIsInstance(timeparser.parsetime('23:44'), datetime.time)
        self.assertIsInstance(timeparser.parsedate('24.3.2013'), datetime.date)
        self.assertIsInstance(timeparser.parsedatetime('24.3.2013,23:44'), datetime.datetime)
        self.assertIsInstance(timeparser.parsetimedelta('24.3.2013,23:44'), datetime.timedelta)

    def test_exceptions(self):
        self.assertRaises(ValueError, timeparser.parsetime, '23;44')
        self.assertRaises(ValueError, timeparser.parsedate, '2013-4.24')
        self.assertRaises(ValueError, timeparser.parsedatetime, '13.04.24#23:44')
        self.assertRaises(ValueError, timeparser.parsetime, str())
        self.assertRaises(TypeError, timeparser.parsedate, None)
        self.assertRaises(TypeError, timeparser.parsedatetime, None)
        self.assertRaises(TypeError, timeparser.parsetimedelta, None)
        timeparser.TimeFormats.config(allow_no_sep=False)
        self.assertRaises(ValueError, timeparser.parsetime, '2344')
        timeparser.DateFormats.config(allow_month_name=False)
        self.assertRaises(ValueError, timeparser.parsedate, '24 Apr 2013')

    def test_parsetime(self):
        parser = timeparser.parsetime
        time = datetime.time
        self.assertEqual(parser('2344'), time(23,44))

    def test_parsedate(self):
        parser = timeparser.parsedate
        date = datetime.date
        timeparser.TimeFormats.config(allow_no_sep=True)
        timeparser.DateFormats.config(allow_month_name=True)

        self.assertEqual(parser('24032013'), date(2013,3,24))
        self.assertEqual(parser('24 Apr 2013'), date(2013,4,24))

        today = date.today()
        self.assertEqual(parser('2403'), date(today.year, 3, 24))
        self.assertEqual(parser('24'), date(today.year, today.month, 24))
        self.assertEqual(parser('243'), date(today.year, 3, 24))

        today = date(1, 2, 3)
        self.assertEqual(parser('2403', today=today), date(today.year, 3, 24))
        self.assertEqual(parser('24', today=today), date(today.year, today.month, 24))
        self.assertEqual(parser('243', today=today), date(today.year, 3, 24))

    def test_parsedatetime(self):
        parser = timeparser.parsedatetime
        dtime = datetime.datetime
        self.assertEqual(parser('24.3.2013,23:44'), dtime(2013,3,24,23,44))

    def test_parsetimedelta(self):
        parser = timeparser.parsetimedelta
        delta = datetime.timedelta
        self.assertEqual(parser('w3 h4 s20'), delta(weeks=3, hours=4, seconds=20))
        self.assertEqual(parser('w3 h4 s20', 'min'), delta(weeks=3, hours=4, seconds=20))
        self.assertEqual(parser('1,2,3', 'H'), delta(hours=1, minutes=2, seconds=3))
        self.assertEqual(parser('1 2 3', 'delta-hours'), delta(hours=1, minutes=2, seconds=3))
        self.assertRaises(ValueError, parser, '20h 0s 4')


class TestTimeParser(unittest.TestCase):
    def setUp(self):
        self.parser = argparse.ArgumentParser()

    def test_ParseTimedelta(self):
        self.parser.add_argument(
            '--weeks',
            action=ParseTimedelta,
            nargs='+',
            )
        self.assertEqual(datetime.timedelta(weeks=-20, hours=-4), self.parser.parse_args('--weeks -20 0 -4'.split()).weeks)
        self.assertRaises(SystemExit, self.parser.parse_args, ('--weeks 20z 0 -4'.split()))

    def test_ParseTime(self):
        self.parser.add_argument(
            '--time',
            action=ParseTime,
            nargs='+',
            )
        self.assertEqual(datetime.time(10, 45, 22), self.parser.parse_args('--time 104522'.split()).time)

    def test_ParseDate(self):
        self.parser.add_argument(
            '--date',
            action=ParseDate,
            nargs='+',
            )
        self.assertEqual(datetime.date(2013, 4, 22), self.parser.parse_args('--date 22.4.13'.split()).date)
        self.assertEqual(datetime.date(2013, 4, 22), self.parser.parse_args('--date 220413'.split()).date)
        self.assertEqual(datetime.date(2013, 4, 22), self.parser.parse_args('--date 22042013'.split()).date)

    def test_ParseDatetime(self):
        self.parser.add_argument(
            '--datetime',
            action=ParseDatetime,
            nargs='+',
            )
        self.assertEqual(
            datetime.datetime(2013, 4, 22, 22, 3, 16),
            self.parser.parse_args('--datetime 22.4 220316'.split()).datetime
            )

    def test_ParseDatetimeOrTime(self):
        self.parser.add_argument(
            '--datetime',
            action=ParseTimeOrDatetime,
            nargs='+',
            )
        self.assertEqual(
            datetime.datetime(2013, 4, 22, 22, 3, 16),
            self.parser.parse_args('--datetime 22.4 220316'.split()).datetime
            )
        self.assertEqual(
            datetime.time(22, 3, 16),
            self.parser.parse_args('--datetime 220316'.split()).datetime
            )

    def test_AppendDatetimeOrTime(self):
        self.parser.add_argument(
            '--datetime',
            action=AppendTimeOrDatetime,
            nargs='+',
            )
        self.assertEqual(
            [datetime.time(22, 3, 16), datetime.time(13, 3)],
            self.parser.parse_args('--datetime 220316 --datetime 1303'.split()).datetime
            )


if __name__ == '__main__':
    unittest.main()
