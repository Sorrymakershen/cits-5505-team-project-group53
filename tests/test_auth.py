import unittest
from .base import BaseTestCase
from app.models.user import User
from app import db

class TestUserModel(BaseTestCase):
    """Test case for the User model"""
    
    def test_password_hashing(self):
        """Test that passwords are correctly hashed"""
        user = User.query.filter_by(username="testuser").first()
        self.assertTrue(user.check_password("password123"))
        self.assertFalse(user.check_password("wrongpassword"))
    
    def test_user_creation(self):
        """Test that users can be created and saved to the database"""
        self.assertTrue(User.query.filter_by(username="testuser").first() is not None)
        self.assertTrue(User.query.filter_by(email="test@example.com").first() is not None)
    
    def test_password_not_stored_in_plaintext(self):
        """Test that passwords are not stored in plaintext"""
        user = User.query.filter_by(username="testuser").first()
        self.assertNotEqual(user.password_hash, "password123")

class TestAuth(BaseTestCase):
    """Test cases for authentication functionality"""
    
    def test_login_success(self):
        """Test successful user login"""
        response = self.client.post('/auth/login', data={
            'email': 'test@example.com',
            'password': 'password123'
        }, follow_redirects=True)
        self.assert200(response)
        self.assertIn(b'Welcome back', response.data)
    
    def test_login_wrong_password(self):
        """Test login with wrong password"""
        response = self.client.post('/auth/login', data={
            'email': 'test@example.com',
            'password': 'wrongpassword'
        }, follow_redirects=True)
        self.assert200(response)
        self.assertIn(b'Invalid email or password', response.data)
    
    def test_login_nonexistent_user(self):
        """Test login with a nonexistent user"""
        response = self.client.post('/auth/login', data={
            'email': 'nonexistent@example.com',
            'password': 'password123'
        }, follow_redirects=True)
        self.assert200(response)
        self.assertIn(b'Invalid email or password', response.data)
    
    def test_logout(self):
        """Test user logout"""
        # Login first
        self.client.post('/auth/login', data={
            'email': 'test@example.com',
            'password': 'password123'
        })
        
        # Then logout
        response = self.client.get('/auth/logout', follow_redirects=True)
        self.assert200(response)
        self.assertIn(b'Log in', response.data)

if __name__ == '__main__':
    unittest.main()
