import unittest
from app import create_app, db, User # Import create_app and db, User model
from werkzeug.security import generate_password_hash
import os

class BaseTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing') # Create app instance with test config
        self.client = self.app.test_client()
        
        self.app_context = self.app.app_context()
        self.app_context.push() # Push application context
        
        db.create_all() # Create tables
        self._create_default_users() # Create default users

    def tearDown(self):
        db.session.remove() # Remove session
        db.drop_all() # Drop all tables
        self.app_context.pop() # Pop the application context

    def _create_default_users(self):
        # This helper is called in setUp
        # For :memory: db, it's clean each time, so direct creation is fine.
        
        hashed_password_admin = generate_password_hash('adminpass', method='pbkdf2:sha256')
        admin_user = User(username='testadmin', password=hashed_password_admin, role='admin')
        db.session.add(admin_user)
        
        hashed_password_driver = generate_password_hash('driverpass', method='pbkdf2:sha256')
        driver_user = User(username='testdriver', password=hashed_password_driver, role='driver')
        db.session.add(driver_user)
        
        db.session.commit()

    def login(self, username, password):
        return self.client.post('/login', data=dict(
            username=username,
            password=password
        ), follow_redirects=True)

    def logout(self):
        return self.client.get('/logout', follow_redirects=True)

# Removed if __name__ == '__main__': unittest.main() as it's better to run tests via discover
