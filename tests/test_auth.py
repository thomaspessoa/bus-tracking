from tests.base import BaseTestCase
from app import db, User # Assuming User model is needed for direct checks if any

class AuthTests(BaseTestCase):

    def test_login_logout_admin(self):
        """Test admin login and logout."""
        # Login
        response = self.login('testadmin', 'adminpass')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Painel do Administrador', response.data) # Translated
        self.assertIn(b'Bem-vindo(a), testadmin (Admin)!', response.data) # Translated

        # Logout
        response = self.logout()
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Login - Rastreador de \xc3\x94nibus Pro', response.data) # Translated title
        self.assertIn(b'Voc\xc3\xaa foi desconectado.', response.data) # Translated flash

    def test_login_logout_driver(self):
        """Test driver login and logout."""
        # Login
        response = self.login('testdriver', 'driverpass')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Painel do Motorista', response.data) # Translated
        self.assertIn(b'Bem-vindo(a), testdriver (Motorista)!', response.data) # Translated

        # Logout
        response = self.logout()
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Login - Rastreador de \xc3\x94nibus Pro', response.data) # Translated title
        self.assertIn(b'Voc\xc3\xaa foi desconectado.', response.data) # Translated flash

    def test_login_invalid_username(self):
        """Test login with an invalid username."""
        response = self.login('wronguser', 'adminpass')
        self.assertEqual(response.status_code, 200) # Stays on login page
        self.assertIn(b'Usu\xc3\xa1rio ou senha inv\xc3\xa1lido(a). Por favor, tente novamente.', response.data) # Translated
        self.assertIn(b'Login - Rastreador de \xc3\x94nibus Pro', response.data) # Translated


    def test_login_invalid_password(self):
        """Test login with an invalid password."""
        response = self.login('testadmin', 'wrongpassword')
        self.assertEqual(response.status_code, 200) # Stays on login page
        self.assertIn(b'Usu\xc3\xa1rio ou senha inv\xc3\xa1lido(a). Por favor, tente novamente.', response.data) # Translated
        self.assertIn(b'Login - Rastreador de \xc3\x94nibus Pro', response.data) # Translated

    def test_access_admin_dashboard_unauthenticated(self):
        """Test access to /admin by unauthenticated user."""
        response = self.client.get('/admin', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Login - Rastreador de \xc3\x94nibus Pro', response.data) # Translated
        # Flask-Login's default message "Please log in to access this page." is not easily translatable without custom handling.
        # For now, we assume this message might remain in English or we don't assert it if it's too complex to translate in tests.
        # The key check is redirection to the login page.
        # However, if Flask-Login is configured with a message_category, this might be different.
        # login_manager.login_message = "Por favor, fa\u00e7a login para acessar esta p\u00e1gina."
        # For now, I will assume the default English message or remove the check if it fails.
        # Let's check app.py if login_message is set. It's not. So default Flask-Login message.
        self.assertIn(b'Please log in to access this page.', response.data)


    def test_access_driver_dashboard_unauthenticated(self):
        """Test access to /driver by unauthenticated user."""
        response = self.client.get('/driver', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Login - Rastreador de \xc3\x94nibus Pro', response.data) # Translated
        self.assertIn(b'Please log in to access this page.', response.data) # Default Flask-Login message

    def test_access_admin_dashboard_as_admin(self):
        """Test access to /admin by authenticated admin."""
        self.login('testadmin', 'adminpass')
        response = self.client.get('/admin')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Painel do Administrador', response.data) # Translated
        self.logout()

    def test_access_driver_dashboard_as_driver(self):
        """Test access to /driver by authenticated driver."""
        self.login('testdriver', 'driverpass')
        response = self.client.get('/driver')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Painel do Motorista', response.data) # Translated
        self.logout()

    def test_access_admin_dashboard_as_driver(self):
        """Test access to /admin by authenticated driver (should be denied)."""
        self.login('testdriver', 'driverpass')
        response = self.client.get('/admin', follow_redirects=True)
        self.assertEqual(response.status_code, 403) # Check for 403 Forbidden
        self.assertIn(b'Forbidden', response.data) # Standard Werkzeug 403 page
        # Check for flash message if possible (might be tricky if abort(403) prevents flash rendering in test client)
        # For now, status code 403 is the primary check.
        # The flash message "Access denied: Admins only." is set before abort(403)
        # To check it, we would need to inspect the session or have a custom error handler.
        # Let's try to get the response without follow_redirects to check the flash before abort
        self.logout()
        self.login('testdriver', 'driverpass')
        response_no_redirect = self.client.get('/admin')
        self.assertEqual(response_no_redirect.status_code, 403)
        # Flask's abort(403) by default doesn't process further to render a template with flashes
        # So checking response.data for the flash message directly after abort(403) won't work.
        # The 403 status is the key indicator here.

    def test_access_driver_dashboard_as_admin(self):
        """Test access to /driver by authenticated admin (should be denied)."""
        self.login('testadmin', 'adminpass')
        response = self.client.get('/driver', follow_redirects=True)
        self.assertEqual(response.status_code, 403) # Check for 403 Forbidden
        self.assertIn(b'Forbidden', response.data)
        self.logout()

if __name__ == '__main__':
    unittest.main()
