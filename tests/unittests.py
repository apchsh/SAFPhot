import unittest
import sys; sys.path.append("..")

from params import Options, KeyValueError, KeyMissingError

class TestParams(unittest.TestCase): 

    def test_par(self):

        d = {"HELP":"ME"}
        with self.assertRaises(KeyMissingError):
            Options(d)


if __name__ == "__main__":

    unittest.main() 

