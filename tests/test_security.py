import unittest
from flask import session
from .base import BaseTestCase
from app.models.user import User
from app import db

class TestSecurityFeatures(BaseTestCase):
    """Test case for security features like CSRF protection and password security"""
    
    def test_csrf_token_in_forms(self):
        """Test that CSRF tokens are present in forms"""
        # Check login form
        response = self.client.get('/auth/login')
        self.assert200(response)
        self.assertIn(b'csrf_token', response.data)
        
        # Check registration form
        response = self.client.get('/auth/register')
        self.assert200(response)
        self.assertIn(b'csrf_token', response.data)
        
        # Check profile form
        # Login first
        self.client.post('/auth/login', data={
            'email': 'test@example.com',
            'password': 'password123'
        })
        
        # Check profile page
        response = self.client.get('/auth/profile')
        self.assert200(response)
        self.assertIn(b'csrf_token', response.data)
    
    def test_password_complexity(self):
        """Test password complexity requirements"""
        # Create a new user with a weak password
        response = self.client.post('/auth/register', data={
            'username': 'weakpassuser',
            'email': 'weak@example.com',
            'password': 'short',
            'confirm_password': 'short'
        }, follow_redirects=True)
        
        # Should be rejected due to password complexity
        self.assertIn(b'Password must be at least 8 characters', response.data)
        
        # Try with a better password
        response = self.client.post('/auth/register', data={
            'username': 'strongpassuser',
            'email': 'strong@example.com',
            'password': 'SecurePassword123!',
            'confirm_password': 'SecurePassword123!'
        }, follow_redirects=True)
        
        # Should succeed
        self.assertIn(b'Account created', response.data)
    
    def test_secure_session_config(self):
        """Test secure session configuration"""
        with self.client as client:
            # Login to create a session
            client.post('/auth/login', data={
                'email': 'test@example.com',
                'password': 'password123'
            })
            
            # Check session cookie settings
            cookie = next((c for c in client.cookie_jar if c.name == 'session'), None)
            self.assertIsNotNone(cookie)
            
            # In a testing environment, secure might not be set, but httponly should be
            self.assertTrue(cookie.has_nonstandard_attr('HttpOnly'))
    
    def test_sql_injection_protection(self):
        """Test protection against SQL injection attacks"""
        # Try login with SQL injection in email field
        response = self.client.post('/auth/login', data={
            'email': "' OR 1=1 --",
            'password': 'anything'
        }, follow_redirects=True)
        
        # Should not log in successfully
        self.assertIn(b'Invalid email or password', response.data)
        
        # Try login with SQL injection in password field
        response = self.client.post('/auth/login', data={
            'email': 'test@example.com',
            'password': "' OR 1=1 --"
        }, follow_redirects=True)
        
        # Should not log in successfully
        self.assertIn(b'Invalid email or password', response.data)
    
    def test_xss_protection(self):
        """Test protection against XSS attacks"""
        # Login first
        self.client.post('/auth/login', data={
            'email': 'test@example.com',
            'password': 'password123'
        })
        
        # Try to create a travel plan with XSS payload
        xss_payload = '<script>alert("XSS")</script>'
        
        response = self.client.post('/planner/create', data={
            'title': xss_payload,
            'destination': 'Safe City',
            'start_date': '2023-08-01',
            'end_date': '2023-08-10',
            'budget': '1000',
            'interests': 'safety, security',
            'lat': '40.7128',
            'lng': '-74.0060',
        }, follow_redirects=True)
        
        # The response should escape the script tag
        self.assertNotIn(b'<script>alert("XSS")</script>', response.data)
        
        # Should be escaped and shown as text, not interpreted as HTML
        self.assertIn(b'&lt;script&gt;alert', response.data)

if __name__ == '__main__':
    unittest.main()
