import unittest
import datetime
import timeparser


#TODO: write more tests!

class ParserTests(unittest.TestCase):
    def setUp(self):
        timeparser.ENDIAN.set('little')
        timeparser.TODAY.set()

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

    def test_formatlists(self):
        self.assertIsInstance(timeparser.TimeFormats(), list)
        self.assertIsInstance(timeparser.DatetimeFormats(), list)
        self.assertIsInstance(timeparser.DateFormats(), list)

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
        self.assertEqual(parser('24.03.'), date(today.year, 3, 24))
        self.assertEqual(parser('24'), date(today.year, today.month, 24))
        self.assertEqual(parser('243'), date(today.year, 3, 24))
        self.assertEqual(parser('24.'), date(today.year, today.month, 24))

        today = date(1, 2, 3)
        self.assertEqual(parser('2403', today=today), date(today.year, 3, 24))
        self.assertEqual(parser('24', today=today), date(today.year, today.month, 24))
        self.assertEqual(parser('243', today=today), date(today.year, 3, 24))

        timeparser.ENDIAN.set('big')
        self.assertEqual(parser('13 jan 4.'), date(2013, 1, 4))
        self.assertEqual(parser('jan 4.', today=today), date(today.year, 1, 4))
        self.assertEqual(parser('1. 4.', today=today), date(today.year, 1, 4))
        self.assertEqual(parser('13 1.4.'), date(2013, 1, 4))

    def test_parsedatetime(self):
        parser = timeparser.parsedatetime
        dtime = datetime.datetime
        today = datetime.date.today()
        self.assertEqual(parser('24.3.2013,23:44'), dtime(2013,3,24,23,44))
        self.assertEqual(parser('24.3.2013,23:44'), dtime(2013,3,24,23,44))
        self.assertEqual(parser('24.3.2013,23:44'), dtime(2013,3,24,23,44))
        self.assertEqual(parser('24.3. 23:44'), dtime(today.year,3,24,23,44))
        self.assertEqual(parser('24. 23:44'), dtime(today.year,today.month,24,23,44))

    def test_parsetimedelta(self):
        parser = timeparser.parsetimedelta
        delta = datetime.timedelta
        self.assertEqual(parser('w3 h4 s20'), delta(weeks=3, hours=4, seconds=20))
        self.assertEqual(parser('w3 h4 s20', 'min'), delta(weeks=3, hours=4, seconds=20))
        self.assertEqual(parser('1,2,3', 'H'), delta(hours=1, minutes=2, seconds=3))
        self.assertEqual(parser('1 2 3', 'delta-hours'), delta(hours=1, minutes=2, seconds=3))
        self.assertRaises(ValueError, parser, '20h 0s 4')


class EndianTests(unittest.TestCase):
    def test_endian(self):
        endian = timeparser.ENDIAN
        endian.set('l')
        self.assertEqual(endian[0], 'day')
        endian.set('b')
        self.assertEqual(endian[0], 'year')
        endian.set('m')
        self.assertEqual(endian[0], 'month')


class TodayTests(unittest.TestCase):
    def setUp(self):
        timeparser.TODAY.set()

    def test_endian(self):
        today = timeparser.TODAY
        self.assertEqual(today, datetime.date.today())
        today.set()
        self.assertEqual(today, datetime.date.today())
        today.set(1,2,3)
        self.assertEqual(today, datetime.date(1,2,3))



if __name__ == '__main__':
    unittest.main()
