import unittest
import datetime
import timeparse


class DateTimeParserTests(unittest.TestCase):
    def test_type(self):
        self.assertIsInstance(timeparse.parsetime('23:44'), datetime.time)
        self.assertIsInstance(timeparse.parsedate('24.3.2013'), datetime.date)
        self.assertIsInstance(timeparse.parsedatetime('24.3.2013,23:44'), datetime.datetime)
        self.assertIsInstance(timeparse.parsetimedelta('24.3.2013,23:44'), datetime.timedelta)

    def test_exceptions(self):
        self.assertRaises(ValueError, timeparse.parsetime, '23;44')
        self.assertRaises(ValueError, timeparse.parsedate, '2013-4.24')
        self.assertRaises(ValueError, timeparse.parsedatetime, '13.04.24#23:44')
        self.assertRaises(ValueError, timeparse.parsetime, str())
        self.assertRaises(TypeError, timeparse.parsedate, None)
        self.assertRaises(TypeError, timeparse.parsedatetime, None)
        self.assertRaises(TypeError, timeparse.parsetimedelta, None)
        timeparse.TimeFormats.config(allow_no_sep=False)
        self.assertRaises(ValueError, timeparse.parsetime, '2344')
        timeparse.DateFormats.config(allow_month_name=False)
        self.assertRaises(ValueError, timeparse.parsedate, '24 Apr 2013')

    def test_values(self):
        timeparse.TimeFormats.config(allow_no_sep=True)
        timeparse.DateFormats.config(allow_month_name=True)
        self.assertEqual(timeparse.parsetime('2344'), datetime.time(23,44))
        self.assertEqual(timeparse.parsedate('24032013'), datetime.date(2013,3,24))
        self.assertEqual(timeparse.parsedate('24 Apr 2013'), datetime.date(2013,4,24))
        self.assertEqual(timeparse.parsedatetime('24.3.2013,23:44'), datetime.datetime(2013,3,24,23,44))

        today = datetime.date.today()
        self.assertEqual(timeparse.parsedate('2403'), datetime.date(today.year, 3, 24))
        self.assertEqual(timeparse.parsedate('24'), datetime.date(today.year, today.month, 24))
        self.assertEqual(timeparse.parsedate('243'), datetime.date(today.year, 3, 24))

        today = datetime.date(1, 2, 3)
        timeparse.setToday(today)
        self.assertEqual(timeparse.parsedate('2403'), datetime.date(today.year, 3, 24))
        self.assertEqual(timeparse.parsedate('24'), datetime.date(today.year, today.month, 24))
        self.assertEqual(timeparse.parsedate('243'), datetime.date(today.year, 3, 24))


if __name__ == '__main__':
    unittest.main()
