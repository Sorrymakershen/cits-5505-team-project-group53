"""
Test file for statistics frontend functionality
Tests the JavaScript functionality for statistics visualization and map features
"""
import unittest
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from .base import BaseTestCase
from app.models.user import User
from app.models.travel_plan import TravelPlan
from app import db
from datetime import datetime, timedelta
import os


class TestStatisticsJS(unittest.TestCase):
    """Test case for statistics.js functionality using Selenium"""
    
    def setUp(self):
        """Set up test environment with a Chrome WebDriver"""
        # Set up headless Chrome for testing
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        # Optional: Set custom window size for tests
        chrome_options.add_argument("--window-size=1920,1080")
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
        except Exception as e:
            self.skipTest(f"Chrome WebDriver not available: {e}")
        
        # Create Flask test app to serve pages locally
        from app import create_app
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        
        # Use a temporary SQLite database
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        
        # Set up database with test data
        with self.app.app_context():
            db.create_all()
            
            # Create test user
            test_user = User(username="testuser", email="test@example.com")
            test_user.set_password("password123")
            test_user.home_address = "Test Home"
            test_user.home_lat = 35.6762
            test_user.home_lng = 139.6503
            
            # Create test travel plans
            plan1 = TravelPlan(
                title="Test Japan Trip",
                destination="Tokyo",
                dest_lat=35.6762,
                dest_lng=139.6503,
                start_date=datetime.now() + timedelta(days=30),
                end_date=datetime.now() + timedelta(days=40),
                user_id=1  # Will be assigned after commit
            )
            
            db.session.add(test_user)
            db.session.commit()
            
            plan1.user_id = test_user.id
            db.session.add(plan1)
            db.session.commit()
            
            # Start the Flask server in a separate thread
            self.server_thread = self.app.test_server()
            self.server_thread.start()
            time.sleep(1)  # Give the server time to start
    
    def tearDown(self):
        """Clean up after each test"""
        if hasattr(self, 'driver'):
            self.driver.quit()
        
        if hasattr(self, 'server_thread'):
            self.server_thread.shutdown()
            self.server_thread.join()
        
        # Remove test database
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
    
    def test_statistics_map_initialization(self):
        """Test that the statistics map initializes correctly"""
        # Login first
        self.driver.get("http://localhost:5000/auth/login")
        
        # Fill login form
        email_field = self.driver.find_element(By.ID, "email")
        password_field = self.driver.find_element(By.ID, "password")
        submit_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Login')]")
        
        email_field.send_keys("test@example.com")
        password_field.send_keys("password123")
        submit_button.click()
        
        # Wait for redirect and load statistics page
        self.driver.get("http://localhost:5000/statistics/")
        
        # Check if the map loads
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "statisticsMap"))
            )
            # Check if the Leaflet map is initialized
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "leaflet-container"))
            )
            map_initialized = True
        except:
            map_initialized = False
        
        self.assertTrue(map_initialized, "Statistics map should be initialized")
    
    def test_home_location_modal(self):
        """Test the home location modal functionality"""
        # Login first
        self.driver.get("http://localhost:5000/auth/login")
        
        # Fill login form and submit
        email_field = self.driver.find_element(By.ID, "email") 
        password_field = self.driver.find_element(By.ID, "password")
        submit_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Login')]")
        
        email_field.send_keys("test@example.com")
        password_field.send_keys("password123")
        submit_button.click()
        
        # Load statistics page
        self.driver.get("http://localhost:5000/statistics/")
        
        # Open the home location modal
        try:
            set_location_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "setHomeLocationBtn"))
            )
            set_location_button.click()
            
            # Wait for modal to appear
            WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.ID, "homeLocationModal"))
            )
            
            # Test address input
            address_input = self.driver.find_element(By.ID, "address")
            address_input.send_keys("New York City")
            
            # Test validate button
            validate_button = self.driver.find_element(By.ID, "validateAddressBtn")
            validate_button.click()
            
            # Wait for suggestions to appear (this would need a mock for the address API in production)
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.visibility_of_element_located((By.ID, "suggestions-container"))
                )
                modal_works = True
            except:
                modal_works = False
                
            self.assertTrue(modal_works, "Home location modal should function correctly")
        except Exception as e:
            self.fail(f"Home location modal test failed: {e}")


# Note: These tests require a running web server and browser, so they might
# need adjustment for your CI/CD environment. You might consider marking them
# with @unittest.skipIf based on environment variables.


if __name__ == '__main__':
    unittest.main()
