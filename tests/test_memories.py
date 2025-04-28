import unittest
from datetime import datetime
from io import BytesIO
from PIL import Image
from .base import BaseTestCase
from app.models.user import User
from app.models.memory import Memory
from app import db

class TestMemoryModel(BaseTestCase):
    """Test case for the Memory model"""
    
    def setUp(self):
        """Set up test database with memory data"""
        super().setUp()
        self.user = User.query.filter_by(username="testuser").first()
        
        # Create a test memory
        self.memory = Memory(
            title="Test Memory",
            description="This is a test memory description",
            location="Test Location",
            date_of_memory=datetime.now(),
            user_id=self.user.id,
            image_filename="test_image.jpg"
        )
        db.session.add(self.memory)
        db.session.commit()
    
    def test_memory_creation(self):
        """Test that memories can be created and saved to the database"""
        memory = Memory.query.filter_by(title="Test Memory").first()
        self.assertIsNotNone(memory)
        self.assertEqual(memory.location, "Test Location")
        self.assertEqual(memory.user_id, self.user.id)
    
    def test_memory_user_relationship(self):
        """Test the relationship between memories and users"""
        memory = Memory.query.filter_by(title="Test Memory").first()
        self.assertEqual(memory.user.username, "testuser")
        
        # Check reverse relationship
        user_memories = self.user.memories.all()
        self.assertEqual(len(user_memories), 1)
        self.assertEqual(user_memories[0].title, "Test Memory")

class TestMemoryRoutes(BaseTestCase):
    """Test cases for memory routes"""
    
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
    
    def test_create_memory_view(self):
        """Test viewing the create memory page"""
        response = self.client.get('/memories/create')
        self.assert200(response)
        self.assertIn(b'Create New Memory', response.data)
    
    def test_view_memories(self):
        """Test viewing memories list"""
        # Create a test memory first
        memory = Memory(
            title="Test Memory View",
            description="This is a test memory for viewing",
            location="Test View Location",
            date_of_memory=datetime.now(),
            user_id=self.user.id,
            image_filename="test_view_image.jpg"
        )
        db.session.add(memory)
        db.session.commit()
        
        # Test viewing the memories list
        response = self.client.get('/memories/')
        self.assert200(response)
        self.assertIn(b'Test Memory View', response.data)
        self.assertIn(b'Test View Location', response.data)
    
    def test_memory_detail_view(self):
        """Test viewing a memory's details"""
        # Create a test memory first
        memory = Memory(
            title="Test Memory Detail",
            description="This is a test memory for detail viewing",
            location="Test Detail Location",
            date_of_memory=datetime.now(),
            user_id=self.user.id,
            image_filename="test_detail_image.jpg"
        )
        db.session.add(memory)
        db.session.commit()
        
        # Test viewing the memory detail
        response = self.client.get(f'/memories/{memory.id}')
        self.assert200(response)
        self.assertIn(b'Test Memory Detail', response.data)
        self.assertIn(b'This is a test memory for detail viewing', response.data)
        self.assertIn(b'Test Detail Location', response.data)

if __name__ == '__main__':
    unittest.main()
