import os
import unittest
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime, timedelta
import sys

# Add application to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db, create_app
from app.models.user import User

class SeleniumBaseTestCase(unittest.TestCase):
    """Base test case for Selenium UI tests"""
    
    @classmethod
    def setUpClass(cls):
        """Set up the application and WebDriver before all tests"""
        # Configure Flask app for testing
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test_selenium.db'
        app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF tokens for testing
        app.config['SERVER_NAME'] = 'localhost:5000'
        
        # Set up database
        with app.app_context():
            db.create_all()
            
            # Create test user if it doesn't exist
            if not User.query.filter_by(email='selenium@example.com').first():
                test_user = User(username='seleniumuser', email='selenium@example.com')
                test_user.set_password('seleniumpass')
                db.session.add(test_user)
                db.session.commit()
        
        # Start Flask app in a separate thread
        import threading
        threading.Thread(target=lambda: app.run(use_reloader=False)).start()
        
        # Wait for app to start
        time.sleep(1)
        
        # Set up Chrome WebDriver with headless option
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        # Initialize WebDriver
        cls.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        cls.driver.implicitly_wait(10)
        
    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests"""
        # Close WebDriver
        cls.driver.quit()
        
        # Delete test database
        if os.path.exists('test_selenium.db'):
            os.remove('test_selenium.db')
    
    def login(self, email='selenium@example.com', password='seleniumpass'):
        """Helper method to log in a user"""
        self.driver.get('http://localhost:5000/auth/login')
        
        # Enter login credentials
        self.driver.find_element(By.ID, 'email').send_keys(email)
        self.driver.find_element(By.ID, 'password').send_keys(password)
        
        # Submit the form
        self.driver.find_element(By.TAG_NAME, 'button').click()
        
        # Wait for redirect
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'navbar'))
        )

class TestAuthSelenium(SeleniumBaseTestCase):
    """Selenium test case for authentication features"""
    
    def test_login_workflow(self):
        """Test the login workflow"""
        # Navigate to login page
        self.driver.get('http://localhost:5000/auth/login')
        
        # Verify login page loaded
        self.assertIn('Login', self.driver.title)
        
        # Enter login credentials
        self.driver.find_element(By.ID, 'email').send_keys('selenium@example.com')
        self.driver.find_element(By.ID, 'password').send_keys('seleniumpass')
        
        # Submit the form
        self.driver.find_element(By.TAG_NAME, 'button').click()
        
        # Wait for redirect
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'navbar'))
        )
        
        # Verify login was successful
        self.assertIn('Dashboard', self.driver.title)
        
        # Verify user-specific content appears
        navbar = self.driver.find_element(By.CLASS_NAME, 'navbar')
        self.assertIn('seleniumuser', navbar.text)
    
    def test_registration_workflow(self):
        """Test the user registration workflow"""
        # Navigate to registration page
        self.driver.get('http://localhost:5000/auth/register')
        
        # Verify registration page loaded
        self.assertIn('Register', self.driver.title)
        
        # Generate unique username and email
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        test_username = f'testuser{timestamp}'
        test_email = f'test{timestamp}@example.com'
        test_password = 'Password123!'
        
        # Enter registration details
        self.driver.find_element(By.ID, 'username').send_keys(test_username)
        self.driver.find_element(By.ID, 'email').send_keys(test_email)
        self.driver.find_element(By.ID, 'password').send_keys(test_password)
        self.driver.find_element(By.ID, 'confirm_password').send_keys(test_password)
        
        # Submit the form
        self.driver.find_element(By.TAG_NAME, 'button').click()
        
        # Wait for redirect to login page
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, 'email'))
        )
        
        # Verify registration was successful
        self.assertIn('Login', self.driver.title)
        
        # Attempt to login with new credentials
        self.driver.find_element(By.ID, 'email').send_keys(test_email)
        self.driver.find_element(By.ID, 'password').send_keys(test_password)
        self.driver.find_element(By.TAG_NAME, 'button').click()
        
        # Verify login with new account was successful
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'navbar'))
        )
        self.assertIn('Dashboard', self.driver.title)

class TestPlannerSelenium(SeleniumBaseTestCase):
    """Selenium test case for planner features"""
    
    def test_create_travel_plan(self):
        """Test creating a new travel plan"""
        # Login first
        self.login()
        
        # Navigate to create plan page
        self.driver.get('http://localhost:5000/planner/create')
        
        # Verify create plan page loaded
        self.assertIn('Create New Trip', self.driver.title)
        
        # Generate unique trip name
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        trip_name = f'Selenium Test Trip {timestamp}'
        
        # Enter plan details
        self.driver.find_element(By.ID, 'title').send_keys(trip_name)
        self.driver.find_element(By.ID, 'destination').send_keys('Paris, France')
        
        # Enter dates
        start_date = (datetime.now() + timedelta(days=10)).strftime('%Y-%m-%d')
        end_date = (datetime.now() + timedelta(days=15)).strftime('%Y-%m-%d')
        
        self.driver.find_element(By.ID, 'start_date').send_keys(start_date)
        self.driver.find_element(By.ID, 'end_date').send_keys(end_date)
        
        # Enter budget and interests
        self.driver.find_element(By.ID, 'budget').send_keys('2000')
        self.driver.find_element(By.ID, 'interests').send_keys('art, culture, food')
        
        # Make plan public
        self.driver.find_element(By.ID, 'is_public').click()
        
        # Submit the form
        self.driver.find_element(By.ID, 'submitBtn').click()
        
        # Wait for redirect to plan view page
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'card'))
        )
        
        # Verify plan creation was successful
        self.assertIn(trip_name, self.driver.page_source)
        self.assertIn('Paris, France', self.driver.page_source)
    
    def test_view_travel_plans(self):
        """Test viewing travel plans list"""
        # Login first
        self.login()
        
        # Create a plan first to ensure there's at least one
        self.test_create_travel_plan()
        
        # Navigate to plans list
        self.driver.get('http://localhost:5000/planner/')
        
        # Verify plans page loaded
        self.assertIn('Travel Plans', self.driver.title)
        
        # Verify at least one plan is displayed
        plans = self.driver.find_elements(By.CLASS_NAME, 'card')
        self.assertGreater(len(plans), 0)
        
        # Verify plan details are shown
        self.assertIn('Paris, France', self.driver.page_source)

class TestSecuritySelenium(SeleniumBaseTestCase):
    """Selenium test case for browser-based security features"""
    
    def test_password_complexity_ui(self):
        """Test password complexity requirements in the UI"""
        # Navigate to registration page
        self.driver.get('http://localhost:5000/auth/register')
        
        # Generate unique username and email
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        test_username = f'testuser{timestamp}'
        test_email = f'test{timestamp}@example.com'
        
        # Enter registration details with weak password
        self.driver.find_element(By.ID, 'username').send_keys(test_username)
        self.driver.find_element(By.ID, 'email').send_keys(test_email)
        self.driver.find_element(By.ID, 'password').send_keys('short')
        self.driver.find_element(By.ID, 'confirm_password').send_keys('short')
        
        # Submit the form
        self.driver.find_element(By.TAG_NAME, 'button').click()
        
        # Verify error message appears
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'alert-danger'))
        )
        
        error_message = self.driver.find_element(By.CLASS_NAME, 'alert-danger').text
        self.assertIn('Password must be at least 8 characters', error_message)
    
    def test_csrf_protection(self):
        """Test CSRF protection by attempting to submit a form without a token"""
        # Login first
        self.login()
        
        # Use JavaScript to create and submit a form without CSRF token
        script = """
        var form = document.createElement('form');
        form.method = 'POST';
        form.action = '/auth/profile';
        
        var input = document.createElement('input');
        input.type = 'text';
        input.name = 'username';
        input.value = 'hacked_name';
        form.appendChild(input);
        
        document.body.appendChild(form);
        form.submit();
        """
        
        self.driver.execute_script(script)
        
        # Wait for response
        time.sleep(1)
        
        # Should be rejected with 400 Bad Request or redirect to a page with error message
        current_url = self.driver.current_url
        self.assertTrue('error' in current_url or '400' in self.driver.page_source or 'CSRF' in self.driver.page_source)
    
    def test_xss_protection_ui(self):
        """Test XSS protection in the UI by attempting to inject script"""
        # Login first
        self.login()
        
        # Navigate to create plan page
        self.driver.get('http://localhost:5000/planner/create')
        
        # Create a plan with XSS payload
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        xss_payload = f'<script>alert("XSS {timestamp}")</script>'
        
        # Enter plan details with XSS payload in title
        self.driver.find_element(By.ID, 'title').send_keys(xss_payload)
        self.driver.find_element(By.ID, 'destination').send_keys('Paris, France')
        
        # Enter dates
        start_date = (datetime.now() + timedelta(days=10)).strftime('%Y-%m-%d')
        end_date = (datetime.now() + timedelta(days=15)).strftime('%Y-%m-%d')
        
        self.driver.find_element(By.ID, 'start_date').send_keys(start_date)
        self.driver.find_element(By.ID, 'end_date').send_keys(end_date)
        
        # Enter budget and interests
        self.driver.find_element(By.ID, 'budget').send_keys('2000')
        self.driver.find_element(By.ID, 'interests').send_keys('security testing')
        
        # Submit the form
        self.driver.find_element(By.ID, 'submitBtn').click()
        
        # If XSS works, an alert would appear and test would fail
        # If protected correctly, no alert will show and page will render safely
        
        # Wait for redirect to plan view page
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'card'))
        )
        
        # Verify plan creation was successful and content is escaped
        page_source = self.driver.page_source
        self.assertIn('&lt;script&gt;', page_source)
        self.assertNotIn(f'<script>alert("XSS {timestamp}")</script>', page_source)
    
    def test_session_fixation_protection(self):
        """Test protection against session fixation attacks"""
        # Get the initial session cookie
        self.driver.get('http://localhost:5000/')
        initial_session = self.driver.get_cookies()
        
        # Now login
        self.login()
        
        # Get the new session cookie
        new_session = self.driver.get_cookies()
        
        # Check if cookies changed after login (suggests session regeneration)
        initial_session_ids = [c['value'] for c in initial_session if c['name'] == 'session']
        new_session_ids = [c['value'] for c in new_session if c['name'] == 'session']
        
        if initial_session_ids and new_session_ids:
            self.assertNotEqual(initial_session_ids[0], new_session_ids[0], 
                               "Session ID should change after login to prevent session fixation attacks")

if __name__ == '__main__':
    unittest.main()
