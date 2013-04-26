import unittest
import datetime
from datetimeparser import DateTimeParser


class DateTimeParserTests(unittest.TestCase, DateTimeParser):
    def test_type(self):
        self.assertIsInstance(self.parsetime('23:44'), datetime.time)
        self.assertIsInstance(self.parsedate('2013.04.24'), datetime.date)
        self.assertIsInstance(self.parsedatetime('13.04.24,23:44'), datetime.datetime)

    def test_exceptions(self):
        self.assertRaises(ValueError, self.parsetime, '23;44')
        self.assertRaises(ValueError, self.parsedate, '2013-4.24')
        self.assertRaises(ValueError, self.parsedatetime, '13.04.24#23:44')
        self.assertRaises(ValueError, self.parsetime, str())
        self.assertRaises(TypeError, self.parsedate, None)
        self.assertRaises(TypeError, self.parsedatetime, None)

    def test_values(self):
        self.assertEqual(self.parsetime('23:44'), datetime.time(23,44))
        self.assertEqual(self.parsedate('2013.04.24'), datetime.date(2013,4,24))
        self.assertEqual(self.parsedatetime('13.04.24,23:44'), datetime.datetime(2013,4,24,23,44))


if __name__ == '__main__':
    unittest.main()
