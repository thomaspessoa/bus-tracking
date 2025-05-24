import json
from tests.base import BaseTestCase
from app import db, Trip, User # Import necessary models
from datetime import datetime

class LocationTests(BaseTestCase):

    def _start_active_trip(self, username='testdriver', password='driverpass', 
                           destino='Rota de Teste API', horario='Agora Mesmo API', 
                           numero_onibus_val='API-BUS', nome_viagem_val='API Test Driver'):
        """Helper to log in a driver and start a trip with all required fields."""
        self.login(username, password)
        response = self.client.post('/start_trip', data={
            'destino': destino, 
            'horario_viagem': horario,
            'numero_onibus': numero_onibus_val,
            'nome_motorista_viagem': nome_viagem_val
        }, follow_redirects=True)
        self.assertIn(b'Viagem iniciada com sucesso!', response.data) 
        with self.app.app_context(): 
            driver_user = User.query.filter_by(username=username).first()
            active_trip = Trip.query.filter_by(driver_id=driver_user.id, status='active').first()
            self.assertIsNotNone(active_trip, "Helper falhou ao criar uma viagem ativa.")
            return active_trip.id # Return trip_id for further use

    def test_driver_update_location_success(self):
        """Test driver successfully updating location for an active trip."""
        trip_id = self._start_active_trip() # Uses testdriver
        
        latitude, longitude = 34.0522, -118.2437
        response = self.client.post('/update_location', 
                                     json={'latitude': latitude, 'longitude': longitude})
        
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(json_response['status'], 'success')
        self.assertEqual(json_response['message'], 'Localização atualizada.') # Translated

        with self.app.app_context(): 
            trip = db.session.get(Trip, trip_id)
            self.assertIsNotNone(trip)
            self.assertEqual(trip.current_latitude, latitude)
            self.assertEqual(trip.current_longitude, longitude)
            self.assertIsNotNone(trip.last_location_update)
        self.logout()

    def test_driver_update_location_no_active_trip(self):
        """Test driver attempting to update location with no active trip."""
        self.login('testdriver', 'driverpass') # Login, but don't start a trip
        
        response = self.client.post('/update_location', 
                                     json={'latitude': 34.0, 'longitude': -118.0})
        
        self.assertEqual(response.status_code, 404) # Not Found
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(json_response['status'], 'error')
        self.assertIn('Nenhuma viagem ativa encontrada.', json_response['message']) # Translated
        self.logout()

    def test_driver_update_location_invalid_data(self):
        """Test driver attempting to update location with invalid/missing data."""
        self._start_active_trip() # Uses testdriver
        
        # Missing latitude
        response = self.client.post('/update_location', json={'longitude': -118.0})
        self.assertEqual(response.status_code, 400)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertIn('Latitude ou longitude ausente.', json_response['message']) # Translated

        # Invalid latitude type
        response = self.client.post('/update_location', json={'latitude': 'not-a-float', 'longitude': -118.0})
        self.assertEqual(response.status_code, 400)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertIn('Formato de latitude ou longitude inválido.', json_response['message']) # Corrected Unicode
        self.logout()

    def test_update_location_not_driver(self):
        """Test non-driver (admin) attempting to update location."""
        self.login('testadmin', 'adminpass') # Login as admin
        response = self.client.post('/update_location', 
                                     json={'latitude': 34.0, 'longitude': -118.0})
        self.assertEqual(response.status_code, 403) # Forbidden
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertIn('Acesso negado: Somente motoristas.', json_response['message']) # Translated
        self.logout()
        
    def test_update_location_unauthenticated(self):
        """Test unauthenticated user attempting to update location."""
        response = self.client.post('/update_location', 
                                     json={'latitude': 34.0, 'longitude': -118.0},
                                     follow_redirects=True) # Will follow redirect to login
        self.assertEqual(response.status_code, 200) # Due to redirect to login page
        self.assertIn(b'Login - Rastreador de \xc3\x94nibus Pro', response.data) # Translated
        # The actual API would have returned 401 if not for Flask-Login redirecting


    def test_api_active_buses_locations_empty(self):
        """Test /api/active_buses_locations when no buses are active."""
        self.login('testadmin', 'adminpass')
        response = self.client.get('/api/active_buses_locations')
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(json_response, [])
        self.logout()

    def test_api_active_buses_locations_with_data(self):
        """Test /api/active_buses_locations with an active bus."""
        # Driver starts a trip using the helper with all fields
        test_destino_api = "Destino API Central"
        test_horario_api = "11:30"
        test_onibus_api = "BUS-API-01"
        test_nome_viagem_api = "Motorista da API"
        expected_schedule_api = f"Destino: {test_destino_api} - Horário: {test_horario_api} - Ônibus: {test_onibus_api}"

        trip_id = self._start_active_trip(
            username='testdriver', password='driverpass', 
            destino=test_destino_api, horario=test_horario_api,
            numero_onibus_val=test_onibus_api, nome_viagem_val=test_nome_viagem_api
        )
        
        # Driver updates location
        latitude, longitude = 35.0, -119.0
        self.client.post('/update_location', json={'latitude': latitude, 'longitude': longitude})
        self.logout() # Logout driver

        # Admin fetches locations
        self.login('testadmin', 'adminpass')
        response = self.client.get('/api/active_buses_locations')
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.data.decode('utf-8'))
        
        self.assertEqual(len(json_response), 1)
        bus_data = json_response[0]
        self.assertEqual(bus_data['trip_id'], trip_id)
        self.assertEqual(bus_data['driver_username'], 'testdriver') 
        self.assertEqual(bus_data['nome_motorista_viagem'], test_nome_viagem_api) # Verify new field
        self.assertEqual(bus_data['schedule'], expected_schedule_api) # Verify simplified schedule
        self.assertEqual(bus_data['latitude'], latitude)
        self.assertEqual(bus_data['longitude'], longitude)
        self.assertIsNotNone(bus_data['last_update'])
        self.logout()

    def test_api_active_buses_locations_trip_no_location(self):
        """Test API when a trip is active but has no location data yet."""
        self._start_active_trip(
            username='testdriver', password='driverpass', 
            destino='Rota Sem Localizacao', horario='10:00',
            numero_onibus_val='BUS-NOLOC', nome_viagem_val='Driver NoLoc'
        )
        # Location is not updated for this trip
        self.logout() # Logout driver

        self.login('testadmin', 'adminpass')
        response = self.client.get('/api/active_buses_locations')
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(json_response, []) # Should be empty as trip has no lat/lon
        self.logout()


    def test_api_active_buses_locations_not_admin(self):
        """Test non-admin (driver) attempting to access /api/active_buses_locations."""
        self.login('testdriver', 'driverpass')
        response = self.client.get('/api/active_buses_locations')
        self.assertEqual(response.status_code, 403) # Forbidden
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertIn('Acesso negado: Somente administradores.', json_response['message']) # Translated
        self.logout()
        
    def test_api_active_buses_locations_unauthenticated(self):
        """Test unauthenticated user attempting to access /api/active_buses_locations."""
        response = self.client.get('/api/active_buses_locations', follow_redirects=True)
        self.assertEqual(response.status_code, 200) # Due to redirect to login page
        self.assertIn(b'Login - Rastreador de \xc3\x94nibus Pro', response.data) # Translated

if __name__ == '__main__':
    unittest.main()
