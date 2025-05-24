from tests.base import BaseTestCase
from app import db, Trip, User # Import necessary models
from datetime import datetime, timedelta

class TripManagementTests(BaseTestCase):

    def test_driver_start_trip_success(self):
        """Test driver successfully starting a new trip."""
        self.login('testdriver', 'driverpass')
        destino_val = "Centro da Cidade"
        horario_val = "10:00 AM"
        onibus_val = "BUS123"
        nome_viagem_val = "Motorista Teste Turno 1"
        expected_schedule_str = f"Destino: {destino_val} - Horário: {horario_val} - Ônibus: {onibus_val}"
        
        response = self.client.post('/start_trip', data={
            'destino': destino_val, 
            'horario_viagem': horario_val,
            'numero_onibus': onibus_val,
            'nome_motorista_viagem': nome_viagem_val
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Viagem iniciada com sucesso!', response.data) 
        
        with self.app.app_context(): 
            driver_user = User.query.filter_by(username='testdriver').first()
            trip = Trip.query.filter_by(driver_id=driver_user.id, status='active').first()
            self.assertIsNotNone(trip)
            self.assertEqual(trip.schedule, expected_schedule_str)
            self.assertEqual(trip.numero_onibus, onibus_val)
            self.assertEqual(trip.nome_motorista_viagem, nome_viagem_val)
            self.assertIsNotNone(trip.start_time)
            self.assertIsNone(trip.end_time)
        self.logout()

    def test_driver_start_trip_missing_fields(self):
        """Test driver attempting to start a trip with missing required fields."""
        self.login('testdriver', 'driverpass')
        
        base_data = {
            'destino': 'Destino Teste',
            'horario_viagem': '14:00',
            'numero_onibus': 'BUS007',
            'nome_motorista_viagem': 'Nome Teste Viagem'
        }
        
        required_fields = ['destino', 'horario_viagem', 'numero_onibus', 'nome_motorista_viagem']
        # Correct UTF-8 byte string for: "Todos os campos, incluindo Seu Nome para a viagem, são obrigatórios."
        flash_msg = b'Todos os campos, incluindo Seu Nome para a viagem, s\xc3\xa3o obrigat\xc3\xb3rios.'

        for field_to_omit in required_fields:
            data_copy = base_data.copy()
            data_copy[field_to_omit] = '' # Set one field to empty
            
            with self.subTest(missing_field=field_to_omit):
                response = self.client.post('/start_trip', data=data_copy, follow_redirects=True)
                self.assertEqual(response.status_code, 200)
                self.assertIn(flash_msg, response.data) # Check for the specific flash message
                self.assertIn(b'Painel do Motorista', response.data) 

        with self.app.app_context(): 
            driver_user = User.query.filter_by(username='testdriver').first()
            trip = Trip.query.filter_by(driver_id=driver_user.id, status='active').first()
            self.assertIsNone(trip) 
        self.logout()

    def test_driver_start_trip_already_active(self):
        """Test driver attempting to start a new trip when one is already active."""
        self.login('testdriver', 'driverpass')
        # Start one trip
        initial_destino = 'Primeira Viagem Dest'
        initial_horario = '11:00'
        initial_onibus = 'BUS-A'
        initial_nome_viagem = 'Condutor A'
        expected_initial_schedule = f"Destino: {initial_destino} - Horário: {initial_horario} - Ônibus: {initial_onibus}"

        self.client.post('/start_trip', data={
            'destino': initial_destino, 
            'horario_viagem': initial_horario,
            'numero_onibus': initial_onibus,
            'nome_motorista_viagem': initial_nome_viagem
        }, follow_redirects=True)
        
        # Attempt to start another
        response = self.client.post('/start_trip', data={
            'destino': 'Segunda Viagem Dest', 
            'horario_viagem': '12:00',
            'numero_onibus': 'BUS-B',
            'nome_motorista_viagem': 'Condutor B'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Voc\xc3\xaa j\xc3\xa1 possui uma viagem ativa.', response.data) 
        
        with self.app.app_context(): 
            driver_user = User.query.filter_by(username='testdriver').first()
            active_trips_count = Trip.query.filter_by(driver_id=driver_user.id, status='active').count()
            self.assertEqual(active_trips_count, 1) 
            
            first_trip = Trip.query.filter_by(driver_id=driver_user.id, status='active').first()
            self.assertIsNotNone(first_trip)
            self.assertEqual(first_trip.schedule, expected_initial_schedule)
            self.assertEqual(first_trip.nome_motorista_viagem, initial_nome_viagem)
            self.assertEqual(first_trip.numero_onibus, initial_onibus)
        self.logout()

    def test_driver_end_trip_success_with_observation(self):
        """Test driver successfully ending an active trip with an observation."""
        self.login('testdriver', 'driverpass')
        self.client.post('/start_trip', data={
            'destino': 'Viagem para Finalizar', 
            'horario_viagem': '15:00',
            'numero_onibus': 'BUS-C',
            'nome_motorista_viagem': 'Condutor C'
        }, follow_redirects=True)
        
        trip_to_end_id = -1
        with self.app.app_context(): 
            driver_user = User.query.filter_by(username='testdriver').first()
            trip_to_end = Trip.query.filter_by(driver_id=driver_user.id, status='active').first()
            self.assertIsNotNone(trip_to_end)
            trip_to_end_id = trip_to_end.id

        observacao_texto = "Muito trânsito hoje."
        response = self.client.post('/end_trip', data={'observacao': observacao_texto}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Viagem finalizada com sucesso.', response.data) 
        
        with self.app.app_context(): 
            ended_trip = db.session.get(Trip, trip_to_end_id) 
            self.assertEqual(ended_trip.status, 'completed')
            self.assertIsNotNone(ended_trip.end_time)
            self.assertEqual(ended_trip.observacao, observacao_texto)
        self.logout()

    def test_driver_end_trip_none_active(self):
        """Test driver attempting to end a trip when none is active."""
        self.login('testdriver', 'driverpass')
        response = self.client.post('/end_trip', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Nenhuma viagem ativa encontrada para finalizar.', response.data) # Translated
        self.logout()

    def test_admin_view_dashboard_no_active_trips(self):
        """Test admin dashboard when no trips are active."""
        self.login('testadmin', 'adminpass') 
        response = self.client.get('/admin')
        self.assertEqual(response.status_code, 200)
        # Correct UTF-8 byte string for: "Nenhum ônibus em rota atualmente."
        self.assertIn(b'Nenhum \xc3\xb4nibus em rota atualmente.', response.data) 
        self.logout()

    def test_admin_view_dashboard_with_active_trip(self):
        """Test admin dashboard when a trip is active."""
        # Driver starts a trip
        self.login('testdriver', 'driverpass')
        destino_val = "Viagem ao Vivo para Admin"
        horario_val = "Agora"
        onibus_val = "BUS-ADM"
        nome_viagem_val = "Admin Test Driver"
        expected_schedule_str = f"Destino: {destino_val} - Horário: {horario_val} - Ônibus: {onibus_val}"
        
        self.client.post('/start_trip', data={
            'destino': destino_val, 
            'horario_viagem': horario_val,
            'numero_onibus': onibus_val,
            'nome_motorista_viagem': nome_viagem_val
        }, follow_redirects=True)
        self.logout()

        # Admin logs in and views dashboard
        self.login('testadmin', 'adminpass') 
        response = self.client.get('/admin')
        self.assertEqual(response.status_code, 200)
        # Correct UTF-8 byte string for: "Nenhum ônibus em rota atualmente."
        self.assertNotIn(b'Nenhum \xc3\xb4nibus em rota atualmente.', response.data) 
        self.assertIn(b'testdriver', response.data) # Username of the User model
        self.assertIn(nome_viagem_val.encode('utf-8'), response.data) # nome_motorista_viagem
        self.assertIn(expected_schedule_str.encode('utf-8'), response.data) 
        self.assertIn(b'active', response.data) 
        self.logout()

if __name__ == '__main__':
    unittest.main()
