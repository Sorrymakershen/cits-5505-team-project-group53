"""
Test file for statistics functionality
Tests the routes, data calculations, and API endpoints for statistics
"""
import unittest
import json
from datetime import datetime, timedelta
from .base import BaseTestCase
from app.models.user import User
from app.models.travel_plan import TravelPlan
from app import db


class TestStatisticsRoutes(BaseTestCase):
    """Test case for the statistics routes"""
    
    def setUp(self):
        """Set up test database with travel plan data needed for statistics"""
        super().setUp()
        self.user = User.query.filter_by(username="testuser").first()
        
        # Set home location for user
        self.user.home_address = "Test Home Address"
        self.user.home_lat = 35.6762
        self.user.home_lng = 139.6503
        
        # Create several test travel plans with varied data for statistics
        plans = [
            TravelPlan(
                title="Japan Trip",
                destination="Tokyo",
                dest_lat=35.6762,
                dest_lng=139.6503,
                start_date=datetime.now() + timedelta(days=30),
                end_date=datetime.now() + timedelta(days=40),
                user_id=self.user.id
            ),
            TravelPlan(
                title="France Trip",
                destination="Paris",
                dest_lat=48.8566,
                dest_lng=2.3522,
                start_date=datetime.now() + timedelta(days=60),
                end_date=datetime.now() + timedelta(days=70),
                user_id=self.user.id
            ),
            TravelPlan(
                title="Past Trip",
                destination="Rome",
                dest_lat=41.9028,
                dest_lng=12.4964,
                start_date=datetime.now() - timedelta(days=40),
                end_date=datetime.now() - timedelta(days=30),
                user_id=self.user.id,
                completed=True
            )
        ]
        
        for plan in plans:
            db.session.add(plan)
        
        db.session.commit()
    
    def test_statistics_page_access(self):
        """Test that authenticated user can access the statistics page"""
        # First login
        self.client.post('/auth/login', data={
            'email': 'test@example.com',
            'password': 'password123'
        })
        
        # Then access statistics page
        response = self.client.get('/statistics/', follow_redirects=True)
        self.assert200(response)
        self.assertIn(b'Travel Statistics', response.data)
    
    def test_statistics_unauthenticated(self):
        """Test that unauthenticated users are redirected to login"""
        response = self.client.get('/statistics/', follow_redirects=True)
        self.assertIn(b'Please log in to access this page', response.data)
        self.assertIn(b'Login', response.data)
    
    def test_set_home_location(self):
        """Test setting user home location"""
        # First login
        self.client.post('/auth/login', data={
            'email': 'test@example.com',
            'password': 'password123'
        })
        
        # Set home location
        response = self.client.post('/statistics/set-home-location', data={
            'address': 'New Test Address',
            'lat': '40.7128',
            'lng': '-74.0060'
        }, follow_redirects=True)
        
        self.assert200(response)
        
        # Verify the user's home location was updated in the database
        updated_user = User.query.filter_by(username="testuser").first()
        self.assertEqual(updated_user.home_address, 'New Test Address')
        self.assertEqual(updated_user.home_lat, 40.7128)
        self.assertEqual(updated_user.home_lng, -74.0060)
    
    def test_destinations_api(self):
        """Test the destinations API endpoint"""
        # First login
        self.client.post('/auth/login', data={
            'email': 'test@example.com',
            'password': 'password123'
        })
        
        # Access destinations API
        response = self.client.get('/statistics/api/destinations')
        self.assert200(response)
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertGreaterEqual(len(data['destinations']), 3)
        
        # Verify destinations include our test plans
        destinations = [d['name'] for d in data['destinations']]
        self.assertIn('Tokyo', destinations)
        self.assertIn('Paris', destinations)
        self.assertIn('Rome', destinations)
    
    def test_validate_address(self):
        """Test the address validation API endpoint"""
        # First login
        self.client.post('/auth/login', data={
            'email': 'test@example.com',
            'password': 'password123'
        })
        
        # This test requires mocking external API calls
        # For now, we'll just verify the endpoint exists and returns expected structure
        response = self.client.post('/statistics/validate-address', 
                                    json={'address': 'New York City'},
                                    content_type='application/json')
        
        self.assert200(response)
        data = json.loads(response.data)
        self.assertIn('success', data)
    
    def test_recommendations_api(self):
        """Test the recommendations API endpoint"""
        # First login
        self.client.post('/auth/login', data={
            'email': 'test@example.com',
            'password': 'password123'
        })
        
        # Access recommendations API
        response = self.client.get('/statistics/api/recommendations')
        self.assert200(response)
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIsInstance(data['recommendations'], list)


class TestStatisticsCalculations(BaseTestCase):
    """Test case for the statistics calculation functions"""
    
    def setUp(self):
        """Set up test database with travel plan data needed for statistics"""
        super().setUp()
        self.user = User.query.filter_by(username="testuser").first()
        
        # Set home location for user
        self.user.home_address = "Test Home Address"
        self.user.home_lat = 35.6762
        self.user.home_lng = 139.6503
        
        # Create travel plans with carefully selected data for predictable statistics
        plans = [
            # Plan 1: Winter trip
            TravelPlan(
                title="Winter Trip",
                destination="Hokkaido",
                dest_lat=43.2203,
                dest_lng=142.8635,
                start_date=datetime(2025, 1, 15),
                end_date=datetime(2025, 1, 25),
                user_id=self.user.id,
                completed=True
            ),
            # Plan 2: Summer trip
            TravelPlan(
                title="Summer Trip",
                destination="Okinawa",
                dest_lat=26.3344,
                dest_lng=127.8056,
                start_date=datetime(2025, 7, 10),
                end_date=datetime(2025, 7, 20),
                user_id=self.user.id
            ),
            # Plan 3: Another winter trip
            TravelPlan(
                title="Winter Trip 2",
                destination="Sapporo",
                dest_lat=43.0618,
                dest_lng=141.3545,
                start_date=datetime(2025, 12, 10),
                end_date=datetime(2025, 12, 20),
                user_id=self.user.id
            )
        ]
        
        for plan in plans:
            db.session.add(plan)
        
        db.session.commit()
    
    def test_seasonal_travel_preferences(self):
        """Test that seasonal travel preferences are calculated correctly"""
        # First login
        self.client.post('/auth/login', data={
            'email': 'test@example.com',
            'password': 'password123'
        })
        
        # Access statistics page with calculated stats
        response = self.client.get('/statistics/')
        self.assert200(response)
        
        # Check winter is the most popular season based on our test data
        self.assertIn(b'Winter', response.data)
        
        # We can't perform more detailed assertions without parsing HTML or 
        # modifying the routes to expose calculation results directly
    
    def test_distance_calculations(self):
        """Test the distance calculations for travel statistics"""
        # This would ideally test internal calculation functions directly
        # For now we just verify the statistics page loads with our test data
        self.client.post('/auth/login', data={
            'email': 'test@example.com',
            'password': 'password123'
        })
        
        response = self.client.get('/statistics/')
        self.assert200(response)
        
        # Future enhancement: Make calculation functions testable directly


if __name__ == '__main__':
    unittest.main()
