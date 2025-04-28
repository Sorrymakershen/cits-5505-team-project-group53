import unittest
from datetime import datetime, timedelta
from .base import BaseTestCase
from app.models.user import User
from app.models.travel_plan import TravelPlan, ItineraryItem
from app import db

class TestPlannerModel(BaseTestCase):
    """Test case for the TravelPlan model"""
    
    def setUp(self):
        """Set up test database with travel plan data"""
        super().setUp()
        self.user = User.query.filter_by(username="testuser").first()
        
        # Create a test travel plan
        self.plan = TravelPlan(
            title="Test Vacation",
            destination="Test City",
            dest_lat=40.7128,
            dest_lng=-74.0060,
            start_date=datetime.now() + timedelta(days=10),
            end_date=datetime.now() + timedelta(days=15),
            budget=1500.0,
            interests="sightseeing, food",
            is_public=False,
            user_id=self.user.id
        )
        db.session.add(self.plan)
        db.session.commit()
        
        # Create test itinerary items
        item1 = ItineraryItem(
            day=1,
            time="09:00",
            activity="Visit Museum",
            location="Test Museum",
            lat=40.7138,
            lng=-74.0080,
            cost=20.0,
            notes="Don't forget camera",
            travel_plan_id=self.plan.id
        )
        
        item2 = ItineraryItem(
            day=1,
            time="13:00",
            activity="Lunch",
            location="Test Restaurant",
            lat=40.7148,
            lng=-74.0090,
            cost=40.0,
            notes="Vegetarian options available",
            travel_plan_id=self.plan.id
        )
        
        db.session.add_all([item1, item2])
        db.session.commit()
    
    def test_travel_plan_creation(self):
        """Test that travel plans can be created and saved to the database"""
        plan = TravelPlan.query.filter_by(title="Test Vacation").first()
        self.assertIsNotNone(plan)
        self.assertEqual(plan.destination, "Test City")
        self.assertEqual(plan.budget, 1500.0)
    
    def test_itinerary_items(self):
        """Test that itinerary items can be created and linked to a travel plan"""
        plan = TravelPlan.query.filter_by(title="Test Vacation").first()
        items = plan.itinerary_items.all()
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0].activity, "Visit Museum")
        self.assertEqual(items[1].activity, "Lunch")
        
    def test_cost_calculation(self):
        """Test the total cost calculation feature"""
        plan = TravelPlan.query.filter_by(title="Test Vacation").first()
        items = plan.itinerary_items.all()
        total_cost = sum(item.cost for item in items if item.cost)
        self.assertEqual(total_cost, 60.0)

class TestPlannerRoutes(BaseTestCase):
    """Test cases for planner routes"""
    
    def setUp(self):
        """Set up test database with login"""
        super().setUp()
        
        # Login as test user
        self.client.post('/auth/login', data={
            'email': 'test@example.com',
            'password': 'password123'
        })
        
        # Get the user
        self.user = User.query.filter_by(username="testuser").first()
    
    def test_create_plan(self):
        """Test creating a new travel plan"""
        response = self.client.post('/planner/create', data={
            'title': 'New Test Trip',
            'destination': 'Paris, France',
            'start_date': (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
            'end_date': (datetime.now() + timedelta(days=37)).strftime('%Y-%m-%d'),
            'budget': '2000',
            'interests': 'art, history, food',
            'lat': '48.8566',
            'lng': '2.3522',
        }, follow_redirects=True)
        
        self.assert200(response)
        plan = TravelPlan.query.filter_by(title='New Test Trip').first()
        self.assertIsNotNone(plan)
        self.assertEqual(plan.destination, 'Paris, France')
    
    def test_view_plans(self):
        """Test viewing travel plans list"""
        # Create a test plan first
        self.test_create_plan()
        
        # Test viewing the plans list
        response = self.client.get('/planner/')
        self.assert200(response)
        self.assertIn(b'New Test Trip', response.data)
        self.assertIn(b'Paris, France', response.data)

if __name__ == '__main__':
    unittest.main()
