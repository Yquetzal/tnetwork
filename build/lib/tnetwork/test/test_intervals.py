import unittest

from tnetwork.utils.intervals import Intervals
import numpy as np


class ReadWriteTestCase(unittest.TestCase):

    def test_oneInterval(self):
        anInt = Intervals()
        anInt.add_interval((2, 3))
        results = anInt.periods()
        self.assertEqual(results,[(2,3)])

    def test_addingIntervals(self):
        anInt = Intervals()
        anInt.add_interval((2, 3))
        anInt.add_interval((5, 7))
        results = anInt.periods()
        self.assertEqual(results,[(2,3),(5,7)])

    def test_addingOverlappingIntervals(self):
        anInt = Intervals()
        anInt.add_interval((2, 3))
        anInt.add_interval((2, 5))
        results = anInt.periods()
        self.assertEqual(results,[(2,5)])

    def test_addingOverlappingIntervals2(self):
        anInt = Intervals()
        anInt.add_interval((2, 3))
        anInt.add_interval((0, 5))
        results = anInt.periods()
        self.assertEqual(results,[(0,5)])

    def test_addingIntervalsComplex(self):
        anInt = Intervals()
        anInt.add_interval((2, 3))

        anInt.add_interval((5, 6))
        self.assertEqual(anInt.periods(), [(2, 3), (5, 6)])

        anInt.add_interval((6, 10))
        self.assertEqual(anInt.periods(), [(2, 3), (5, 10)])

        anInt.add_interval((20, 100))
        self.assertEqual(anInt.periods(), [(2, 3), (5, 10), (20, 100)])

        anInt.add_interval((101, 201))
        self.assertEqual(anInt.periods(), [(2, 3), (5, 10), (20, 100), (101, 201)])

        anInt.add_interval((100, 101))
        self.assertEqual(anInt.periods(), [(2, 3), (5, 10), (20, 201)])

        anInt.add_interval((3, 300))
        self.assertEqual(anInt.periods(), [(2, 300)])

    def test_delete(self):
        anInt = Intervals()
        anInt.add_interval((10, 100))

        anInt.remove_interval((20, 30))
        self.assertEqual(anInt.periods(), [(10, 20), (30, 100)])

    def test_delete2(self):
        anInt = Intervals()
        anInt.add_interval((10, 100))
        anInt.add_interval((200, 300))

        anInt.remove_interval((0, 5))
        anInt.remove_interval((150, 160))
        anInt.remove_interval((350, 450))

        self.assertEqual(anInt.periods(), [(10, 100), (200, 300)])

    def test_deleteComplete(self):
        anInt = Intervals()
        anInt.add_interval((10, 100))
        anInt.add_interval((200, 300))

        anInt.remove_interval((5, 15))
        self.assertEqual([(15, 100),(200,300)], anInt.periods())

        anInt.remove_interval((20, 30))
        self.assertEqual([(15, 20),(30,100),(200,300)], anInt.periods())

        anInt.remove_interval((0, 300))
        self.assertEqual([], anInt.periods())

    def test_inf(self):
        print("--------------------")

        anInt = Intervals()
        anInt.add_interval((10, np.inf))
        anInt.add_interval((20, np.inf))
        self.assertEqual([(10, np.inf)], anInt.periods())
        anInt.remove_interval((20, np.inf))
        self.assertEqual([(10, 20)], anInt.periods())




if __name__ == '__main__':
    unittest.main()
