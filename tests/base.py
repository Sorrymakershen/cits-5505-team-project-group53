import os
import sys
import unittest
from flask_testing import TestCase
from datetime import datetime, timedelta

# Add application to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db, create_app
from app.models.user import User
from app.models.travel_plan import TravelPlan, ItineraryItem

class BaseTestCase(TestCase):
    """Base test case with setup and teardown for all tests"""
    
    def create_app(self):
        """Configure the Flask application for testing"""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF tokens for testing
        return app

    def setUp(self):
        """Set up test database before each test"""
        db.create_all()
        self._create_test_data()

    def tearDown(self):
        """Clean up after each test"""
        db.session.remove()
        db.drop_all()
    
    def _create_test_data(self):
        """Create test users and data for testing"""
        # Create test user
        test_user = User(username="testuser", email="test@example.com")
        test_user.set_password("password123")
        
        # Create test admin
        admin_user = User(username="admin", email="admin@example.com")
        admin_user.set_password("adminpass")
        
        db.session.add(test_user)
        db.session.add(admin_user)
        db.session.commit()

if __name__ == '__main__':
    unittest.main()
