import unittest
import sys
import os

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import test modules
from tests.test_auth import TestUserModel, TestAuth
from tests.test_planner import TestPlannerModel, TestPlannerRoutes
from tests.test_memories import TestMemoryModel, TestMemoryRoutes
from tests.test_security import TestSecurityFeatures

# Skip Selenium tests unless specifically requested
if '--with-selenium' in sys.argv:
    from tests.test_selenium import TestAuthSelenium, TestPlannerSelenium

def create_test_suite():
    """Create a test suite with all the test cases"""
    test_suite = unittest.TestSuite()
    
    # Add auth tests
    test_suite.addTest(unittest.makeSuite(TestUserModel))
    test_suite.addTest(unittest.makeSuite(TestAuth))
    
    # Add planner tests
    test_suite.addTest(unittest.makeSuite(TestPlannerModel))
    test_suite.addTest(unittest.makeSuite(TestPlannerRoutes))
    
    # Add memory tests
    test_suite.addTest(unittest.makeSuite(TestMemoryModel))
    test_suite.addTest(unittest.makeSuite(TestMemoryRoutes))
    
    # Add security tests
    test_suite.addTest(unittest.makeSuite(TestSecurityFeatures))
    
    # Add Selenium tests if requested
    if '--with-selenium' in sys.argv:
        test_suite.addTest(unittest.makeSuite(TestAuthSelenium))
        test_suite.addTest(unittest.makeSuite(TestPlannerSelenium))
    
    return test_suite

if __name__ == '__main__':
    # Run all tests
    runner = unittest.TextTestRunner(verbosity=2)
    test_suite = create_test_suite()
    runner.run(test_suite)
