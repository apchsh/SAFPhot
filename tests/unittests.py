import unittest
import sys; sys.path.append("..")

from validate import Validator, KeyValueError, KeyMissingError, KeyNotKnownError

class TestParams(unittest.TestCase): 

    def test_par_few(self):
        '''Test to check that the correct exception is raised if too few 
        keyword parameters are passed to the Validator class.'''
        d = {"HELP":"ME"}
        with self.assertRaises(KeyMissingError):
            Validator(d)

    def test_par_many(self):
        '''Test to check what happens when a large number of header keywords are passed which don't match the list in the Validator class.'''

        d = {} 
        for count in range(0, 1000): d[str(count)] = count 

        with self.assertRaises(KeyNotKnownError):
            Validator(d)


if __name__ == "__main__":

    unittest.main() 

