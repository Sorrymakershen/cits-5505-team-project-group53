"""
Performance tests for critical application functionality
Tests response times and resource usage for key application routes and functions
"""
import unittest
import time
from .base import BaseTestCase
from app.models.user import User
from app.models.travel_plan import TravelPlan
from app import db, create_app
from datetime import datetime, timedelta
import random


class TestApplicationPerformance(BaseTestCase):
    """Test case for measuring application performance"""
    
    def setUp(self):
        """Set up test database with a large dataset to test performance"""
        super().setUp()
        self.user = User.query.filter_by(username="testuser").first()
        
        # Set home location for user
        self.user.home_address = "Performance Test Home"
        self.user.home_lat = 35.6762
        self.user.home_lng = 139.6503
        
        # Generate a large number of travel plans for performance testing
        print("Generating test data for performance testing...")
        self._generate_test_travel_plans(50)  # Adjust number as needed
        
        # Login for tests that require authentication
        self.client.post('/auth/login', data={
            'email': 'test@example.com',
            'password': 'password123'
        })
    
    def _generate_test_travel_plans(self, count):
        """Generate a specified number of travel plans for testing"""
        # List of sample destinations for random selection
        destinations = [
            {"name": "Tokyo", "lat": 35.6762, "lng": 139.6503},
            {"name": "New York", "lat": 40.7128, "lng": -74.0060},
            {"name": "Paris", "lat": 48.8566, "lng": 2.3522},
            {"name": "London", "lat": 51.5074, "lng": -0.1278},
            {"name": "Sydney", "lat": -33.8688, "lng": 151.2093},
            {"name": "Rome", "lat": 41.9028, "lng": 12.4964},
            {"name": "Cairo", "lat": 30.0444, "lng": 31.2357},
            {"name": "Rio de Janeiro", "lat": -22.9068, "lng": -43.1729},
            {"name": "Bangkok", "lat": 13.7563, "lng": 100.5018},
            {"name": "Cape Town", "lat": -33.9249, "lng": 18.4241}
        ]
        
        # Generate travel plans with random dates and destinations
        for i in range(count):
            # Random dates within next 2 years
            start_offset = random.randint(-180, 365)  # Some in past, some in future
            duration = random.randint(3, 21)  # 3 to 21 days
            
            start_date = datetime.now() + timedelta(days=start_offset)
            end_date = start_date + timedelta(days=duration)
            
            # Random destination
            dest = random.choice(destinations)
            
            # Create plan
            plan = TravelPlan(
                title=f"Performance Test Trip {i+1} to {dest['name']}",
                destination=dest['name'],
                dest_lat=dest['lat'],
                dest_lng=dest['lng'],
                start_date=start_date,
                end_date=end_date,
                user_id=self.user.id,
                completed=(start_offset < 0)  # Mark as completed if in the past
            )
            
            db.session.add(plan)
        
        db.session.commit()

    def test_dashboard_load_time(self):
        """Test the load time of the dashboard page"""
        start_time = time.time()
        response = self.client.get('/')
        end_time = time.time()
        
        self.assert200(response)
        
        load_time = end_time - start_time
        print(f"Dashboard load time: {load_time:.4f} seconds")
        
        # Adjust this threshold based on expected performance
        self.assertLess(load_time, 2.0, "Dashboard load time should be under 2 seconds")
    
    def test_statistics_load_time(self):
        """Test the load time of the statistics page with many travel plans"""
        start_time = time.time()
        response = self.client.get('/statistics/')
        end_time = time.time()
        
        self.assert200(response)
        
        load_time = end_time - start_time
        print(f"Statistics page load time: {load_time:.4f} seconds")
        
        # Adjust threshold as needed
        self.assertLess(load_time, 3.0, "Statistics page load time should be under 3 seconds with many travel plans")
    
    def test_destinations_api_response_time(self):
        """Test the response time of the destinations API with many travel plans"""
        start_time = time.time()
        response = self.client.get('/statistics/api/destinations')
        end_time = time.time()
        
        self.assert200(response)
        
        response_time = end_time - start_time
        print(f"Destinations API response time: {response_time:.4f} seconds")
        
        self.assertLess(response_time, 1.0, "Destinations API response should be under 1 second")
    
    def test_travel_plans_listing_time(self):
        """Test the load time of the travel plans listing page"""
        start_time = time.time()
        response = self.client.get('/planner/')
        end_time = time.time()
        
        self.assert200(response)
        
        load_time = end_time - start_time
        print(f"Travel plans listing load time: {load_time:.4f} seconds")
        
        self.assertLess(load_time, 2.0, "Travel plans listing should load under 2 seconds with many plans")
    
    def test_search_performance(self):
        """Test the performance of the travel plans search functionality"""
        # Test search with different query parameters
        search_terms = ["Tokyo", "2025", "vacation"]
        
        for term in search_terms:
            start_time = time.time()
            response = self.client.get(f'/planner/search?q={term}')
            end_time = time.time()
            
            self.assert200(response)
            
            search_time = end_time - start_time
            print(f"Search for '{term}' time: {search_time:.4f} seconds")
            
            self.assertLess(search_time, 1.5, f"Search for '{term}' should complete under 1.5 seconds")


class TestDatabasePerformance(BaseTestCase):
    """Test case for database query performance"""
    
    def setUp(self):
        """Set up a large test database for performance testing"""
        super().setUp()
        self.user = User.query.filter_by(username="testuser").first()
        
        # Generate a much larger dataset for database performance testing
        print("Generating large dataset for database performance testing...")
        self._generate_large_dataset(200)  # Adjust number as needed
    
    def _generate_large_dataset(self, travel_plan_count):
        """Generate a large dataset with many users and travel plans"""
        # Create additional test users
        for i in range(10):  # Create 10 additional users
            user = User(
                username=f"perfuser{i}",
                email=f"perfuser{i}@example.com"
            )
            user.set_password("password123")
            db.session.add(user)
        
        db.session.commit()
        
        # Get all users
        users = User.query.all()
        
        # List of sample destinations
        destinations = [
            {"name": "Tokyo", "lat": 35.6762, "lng": 139.6503},
            {"name": "New York", "lat": 40.7128, "lng": -74.0060},
            {"name": "Paris", "lat": 48.8566, "lng": 2.3522},
            {"name": "London", "lat": 51.5074, "lng": -0.1278},
            {"name": "Sydney", "lat": -33.8688, "lng": 151.2093},
            {"name": "Rome", "lat": 41.9028, "lng": 12.4964},
            {"name": "Cairo", "lat": 30.0444, "lng": 31.2357},
            {"name": "Rio de Janeiro", "lat": -22.9068, "lng": -43.1729},
            {"name": "Bangkok", "lat": 13.7563, "lng": 100.5018},
            {"name": "Cape Town", "lat": -33.9249, "lng": 18.4241}
        ]
        
        # Generate many travel plans distributed among users
        for i in range(travel_plan_count):
            # Assign to random user
            user = random.choice(users)
            
            # Random dates within 3 years (past and future)
            start_offset = random.randint(-365, 730)
            duration = random.randint(2, 30)
            
            start_date = datetime.now() + timedelta(days=start_offset)
            end_date = start_date + timedelta(days=duration)
            
            # Random destination
            dest = random.choice(destinations)
            
            # Create plan
            plan = TravelPlan(
                title=f"DB Test Trip {i+1} to {dest['name']}",
                destination=dest['name'],
                dest_lat=dest['lat'],
                dest_lng=dest['lng'],
                start_date=start_date,
                end_date=end_date,
                user_id=user.id,
                completed=(start_offset < 0)
            )
            
            db.session.add(plan)
            
            # Commit in batches to avoid memory issues
            if i % 50 == 0:
                db.session.commit()
        
        # Final commit
        db.session.commit()
    
    def test_travel_plans_query_performance(self):
        """Test the performance of queries that filter travel plans"""
        # Test various common database queries
        
        # Test 1: Get all plans for a user
        start_time = time.time()
        plans = TravelPlan.query.filter_by(user_id=self.user.id).all()
        query_time = time.time() - start_time
        
        print(f"Query for all plans for one user: {query_time:.4f} seconds, found {len(plans)} plans")
        self.assertLess(query_time, 0.5, "User's plans query should be under 0.5 seconds")
        
        # Test 2: Get upcoming plans
        start_time = time.time()
        upcoming = TravelPlan.query.filter(
            TravelPlan.start_date >= datetime.now(),
            TravelPlan.user_id == self.user.id
        ).all()
        query_time = time.time() - start_time
        
        print(f"Query for upcoming plans: {query_time:.4f} seconds, found {len(upcoming)} plans")
        self.assertLess(query_time, 0.5, "Upcoming plans query should be under 0.5 seconds")
        
        # Test 3: Get completed plans
        start_time = time.time()
        completed = TravelPlan.query.filter_by(
            user_id=self.user.id,
            completed=True
        ).all()
        query_time = time.time() - start_time
        
        print(f"Query for completed plans: {query_time:.4f} seconds, found {len(completed)} plans")
        self.assertLess(query_time, 0.5, "Completed plans query should be under 0.5 seconds")
        
        # Test 4: Search query
        start_time = time.time()
        search_results = TravelPlan.query.filter(
            TravelPlan.title.ilike("%Tokyo%")
        ).all()
        query_time = time.time() - start_time
        
        print(f"Search query: {query_time:.4f} seconds, found {len(search_results)} plans")
        self.assertLess(query_time, 0.5, "Search query should be under 0.5 seconds")


if __name__ == '__main__':
    unittest.main()
