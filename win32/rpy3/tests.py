import unittest

import rpy3.robjects.tests
import rpy3.rinterface.tests
import rpy3.rlike.tests

import rpy3.tests_rpy_classic

def suite():
    suite_robjects = rpy2.robjects.tests.suite()
    suite_rinterface = rpy2.rinterface.tests.suite()
    suite_rlike = rpy2.rlike.tests.suite()

    suite_rpy_classic = rpy2.tests_rpy_classic.suite()

    alltests = unittest.TestSuite([suite_robjects, 
                                   suite_rinterface, 
                                   suite_rlike,
                                   suite_rpy_classic
                                   ])
    return alltests

if __name__ == "__main__":
    unittest.main(defaultTest = "suite")

