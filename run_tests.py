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
from tests.test_statistics import TestStatisticsRoutes, TestStatisticsCalculations

# Skip Selenium tests unless specifically requested
if '--with-selenium' in sys.argv:
    from tests.test_selenium import TestAuthSelenium, TestPlannerSelenium, TestSecuritySelenium
    from tests.test_statistics_js import TestStatisticsJS

# Skip performance tests unless specifically requested
if '--with-performance' in sys.argv:
    from tests.test_performance import TestApplicationPerformance, TestDatabasePerformance

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
    
    # Add statistics tests
    test_suite.addTest(unittest.makeSuite(TestStatisticsRoutes))
    test_suite.addTest(unittest.makeSuite(TestStatisticsCalculations))
    
    # Add Selenium tests if requested
    if '--with-selenium' in sys.argv:
        test_suite.addTest(unittest.makeSuite(TestAuthSelenium))
        test_suite.addTest(unittest.makeSuite(TestPlannerSelenium))
        test_suite.addTest(unittest.makeSuite(TestStatisticsJS))
        test_suite.addTest(unittest.makeSuite(TestSecuritySelenium))
    
    # Add performance tests if requested
    if '--with-performance' in sys.argv:
        test_suite.addTest(unittest.makeSuite(TestApplicationPerformance))
        test_suite.addTest(unittest.makeSuite(TestDatabasePerformance))
    
    return test_suite

if __name__ == '__main__':
    # Run all tests
    runner = unittest.TextTestRunner(verbosity=2)
    test_suite = create_test_suite()
    runner.run(test_suite)
