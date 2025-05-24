from flask import Flask, render_template, request, redirect, url_for, flash, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import os
from datetime import datetime

# Inicializa extensões mas não as associa a uma aplicação ainda
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'login' # Rota para redirecionar para @login_required

# --- Modelo de Usuário (com UserMixin) ---
class User(UserMixin, db.Model): # db.Model será resolvido quando db for inicializado com a app
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False) # Comprimento aumentado para hash
    role = db.Column(db.String(20), nullable=False, default='driver') # 'admin' ou 'driver'

    def __repr__(self):
        return f'<User {self.username}>'
    
    # get_id() é fornecido por UserMixin se a chave primária for 'id'
    # is_authenticated, is_active, is_anonymous também são fornecidos por UserMixin
    # trips (backref) será adicionado pelo modelo Trip

# --- Modelo de Viagem ---
class Trip(db.Model): # db.Model será resolvido quando db for inicializado com a app
    id = db.Column(db.Integer, primary_key=True)
    driver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    schedule = db.Column(db.String(255), nullable=True) # Comprimento aumentado
    start_time = db.Column(db.DateTime, nullable=True)
    end_time = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), nullable=False, default='pending') # ex: 'pending', 'active', 'completed'
    current_latitude = db.Column(db.Float, nullable=True)
    current_longitude = db.Column(db.Float, nullable=True)
    last_location_update = db.Column(db.DateTime, nullable=True)
    numero_onibus = db.Column(db.String(50), nullable=True) # Novo campo para número do ônibus
    data_viagem = db.Column(db.Date, nullable=True) # Novo campo para data da viagem
    observacao = db.Column(db.Text, nullable=True) # Novo campo para observações ao finalizar
    nome_motorista_viagem = db.Column(db.String(100), nullable=False) # Nome específico do motorista para a viagem

    # Relacionamento com User (Motorista)
    driver = db.relationship('User', backref=db.backref('trips', lazy=True))

    def __repr__(self):
        return f'<Trip {self.id} by Driver {self.driver_id} - Status: {self.status}>'

# --- Carregador de Usuário para Flask-Login ---
# Precisa ser definido dentro de create_app ou registrado com login_manager após a inicialização da app
# Por simplicidade, definiremos globalmente, mas está ligado à instância login_manager.
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id)) # Atualizado para usar Session.get()

# --- Função de Inicialização do Banco de Dados ---
def init_database(app_instance):
    with app_instance.app_context():
        # Usa o db_file_path da configuração da app_instance
        db_file_path_local = app_instance.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        db_dir = os.path.dirname(db_file_path_local)
        
        if not app_instance.config['SQLALCHEMY_DATABASE_URI'] == 'sqlite:///:memory:': # Só cria o diretório se não for em memória
            if db_dir and not os.path.exists(db_dir): # Verifica se db_dir não está vazio (não é o caminho raiz)
                os.makedirs(db_dir)
                print(f"Diretório '{db_dir}' criado.")
        
        db.create_all() # Cria tabelas se não existirem

        # Verifica se usuários padrão precisam ser adicionados
        if not User.query.filter_by(username='rizzatti_adm').first(): # Verifica novo nome de admin
            # Remove admin antigo se existir de configurações anteriores (opcional, bom para limpeza)
            old_admin = User.query.filter_by(username='admin').first()
            if old_admin:
                db.session.delete(old_admin)
                print("Usuário 'admin' antigo removido.")

            hashed_password_admin = generate_password_hash('rizzatti_adm', method='pbkdf2:sha256') # Nova senha
            default_admin = User(username='rizzatti_adm', password=hashed_password_admin, role='admin') # Novo nome de usuário
            db.session.add(default_admin)
            print("Usuário administrador padrão 'rizzatti_adm' criado com senha hasheada.")
        elif User.query.filter_by(username='admin').first(): # Se novo admin existe, mas o antigo também por algum motivo
            old_admin = User.query.filter_by(username='admin').first()
            if old_admin:
                 db.session.delete(old_admin)
                 print("Usuário 'admin' antigo removido durante limpeza.")

        # Modificar credenciais do motorista padrão
        if not User.query.filter_by(username='motorista').first(): # Verificar novo nome de motorista
            # Remover motorista antigo se existir
            old_driver = User.query.filter_by(username='driver1').first()
            if old_driver:
                db.session.delete(old_driver)
                print("Usuário motorista 'driver1' antigo removido.")

            hashed_password_driver = generate_password_hash('rizzatti.motorista', method='pbkdf2:sha256') # Nova senha
            default_driver = User(username='motorista', password=hashed_password_driver, role='driver') # Novo username
            db.session.add(default_driver)
            print("Usuário motorista padrão 'motorista' criado com senha hasheada.")
        elif User.query.filter_by(username='driver1').first(): # Se novo motorista existe, mas o antigo também
            old_driver = User.query.filter_by(username='driver1').first()
            if old_driver:
                db.session.delete(old_driver)
                print("Usuário motorista 'driver1' antigo removido durante limpeza.")
        
        db.session.commit()
        print("Inicialização do banco de dados completa. Usuários verificados/adicionados.")

def create_app(config_name='default'):
    app = Flask(__name__)

    # --- Configuração ---
    if config_name == 'testing':
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:' # Banco de dados em memória para testes
        app.config['WTF_CSRF_ENABLED'] = False # Desabilita CSRF para testes
        app.config['SECRET_KEY'] = 'test_secret_key_for_testing_create_app' # Chave secreta para testes
        app.config['LOGIN_DISABLED'] = False # Garante que o login não está globalmente desabilitado para testes
    else: # Configuração Padrão/Produção
        app.secret_key = os.urandom(24) # Chave secreta aleatória
        BASE_DIR = os.path.abspath(os.path.dirname(__file__))
        db_file_path_local = os.path.join(BASE_DIR, 'database', 'app.db')
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_file_path_local
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # Suprime aviso

    # --- Inicializa Extensões ---
    db.init_app(app)
    login_manager.init_app(app)

    # --- Rotas ---
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            if current_user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif current_user.role == 'driver':
                return redirect(url_for('driver_dashboard'))
            else:
                return redirect(url_for('dashboard')) # Painel genérico de fallback
        return redirect(url_for('login')) # Se não autenticado, vai para login

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated: # Se já logado, redireciona para o painel apropriado
            if current_user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('driver_dashboard')) # Padrão para motorista ou outras funções

        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            user = User.query.filter_by(username=username).first()
            
            if user and check_password_hash(user.password, password):
                login_user(user)
                flash('Login bem-sucedido!', 'success') # Traduzido
                if user.role == 'admin':
                    return redirect(url_for('admin_dashboard'))
                elif user.role == 'driver':
                    return redirect(url_for('driver_dashboard'))
                else:
                    return redirect(url_for('dashboard')) # Fallback
            else:
                flash('Usuário ou senha inválido(a). Por favor, tente novamente.', 'danger') # Traduzido
                return redirect(url_for('login'))
                
        return render_template('login.html')

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('Você foi desconectado.', 'info') # Traduzido
        return redirect(url_for('login'))

    @app.route('/dashboard') # Painel genérico para qualquer usuário logado
    @login_required
    def dashboard():
        return render_template('dashboard.html')

    @app.route('/admin')
    @login_required
    def admin_dashboard():
        if current_user.role != 'admin':
            flash('Acesso negado: Somente administradores.', 'danger') # Traduzido
            abort(403) # Proibido
        active_trips = Trip.query.filter_by(status='active').all()
        return render_template('admin_dashboard.html', active_trips=active_trips)

    @app.route('/driver')
    @login_required
    def driver_dashboard():
        if current_user.role != 'driver':
            flash('Acesso negado: Somente motoristas.', 'danger') # Traduzido
            abort(403) # Proibido
        active_trip = Trip.query.filter_by(driver_id=current_user.id, status='active').first()
        return render_template('driver_dashboard.html', active_trip=active_trip)

    @app.route('/start_trip', methods=['POST'])
    @login_required
    def start_trip():
        if current_user.role != 'driver':
            flash('Acesso negado: Somente motoristas.', 'danger') # Traduzido
            abort(403)
        existing_active_trip = Trip.query.filter_by(driver_id=current_user.id, status='active').first()
        if existing_active_trip:
            flash('Você já possui uma viagem ativa. Por favor, finalize-a antes de iniciar uma nova.', 'warning') # Traduzido
            return redirect(url_for('driver_dashboard'))
        
        destino = request.form.get('destino')
        horario_viagem = request.form.get('horario_viagem')
        numero_onibus_form = request.form.get('numero_onibus')
        nome_digitado = request.form.get('nome_motorista_viagem')

        if not destino or not destino.strip() or \
           not horario_viagem or not horario_viagem.strip() or \
           not numero_onibus_form or not numero_onibus_form.strip() or \
           not nome_digitado or not nome_digitado.strip():
            flash('Todos os campos, incluindo Seu Nome para a viagem, são obrigatórios.', 'danger') # Atualizada mensagem
            return redirect(url_for('driver_dashboard'))

        # Simplificando schedule_info como nome_motorista_viagem é um campo separado
        schedule_info = f"Destino: {destino} - Horário: {horario_viagem} - Ônibus: {numero_onibus_form}"
        
        new_trip = Trip(
            driver_id=current_user.id,
            schedule=schedule_info, 
            numero_onibus=numero_onibus_form, 
            nome_motorista_viagem=nome_digitado, # Salva o nome específico da viagem
            start_time=datetime.utcnow(),
            data_viagem=datetime.utcnow().date(), 
            status='active'
        )
        db.session.add(new_trip)
        db.session.commit()
        flash('Viagem iniciada com sucesso!', 'success') # Traduzido
        return redirect(url_for('driver_dashboard'))

    @app.route('/end_trip', methods=['POST'])
    @login_required
    def end_trip():
        if current_user.role != 'driver':
            flash('Acesso negado: Somente motoristas.', 'danger') # Traduzido
            abort(403)
        
        observacao_texto = request.form.get('observacao') # Coleta a observação
        
        active_trip = Trip.query.filter_by(driver_id=current_user.id, status='active').first()
        if active_trip:
            active_trip.end_time = datetime.utcnow()
            active_trip.status = 'completed'
            active_trip.observacao = observacao_texto # Salva a observação
            db.session.commit()
            flash('Viagem finalizada com sucesso.', 'success') # Traduzido
        else:
            flash('Nenhuma viagem ativa encontrada para finalizar.', 'warning') # Traduzido
        return redirect(url_for('driver_dashboard'))

    @app.route('/update_location', methods=['POST'])
    @login_required
    def update_location():
        if current_user.role != 'driver':
            return jsonify({'status': 'error', 'message': 'Acesso negado: Somente motoristas.'}), 403 # Traduzido
        data = request.get_json()
        if not data or 'latitude' not in data or 'longitude' not in data:
            return jsonify({'status': 'error', 'message': 'Latitude ou longitude ausente.'}), 400 # Traduzido
        active_trip = Trip.query.filter_by(driver_id=current_user.id, status='active').first()
        if not active_trip:
            return jsonify({'status': 'error', 'message': 'Nenhuma viagem ativa encontrada.'}), 404 # Traduzido
        try:
            active_trip.current_latitude = float(data['latitude'])
            active_trip.current_longitude = float(data['longitude'])
            active_trip.last_location_update = datetime.utcnow()
            db.session.commit()
            return jsonify({'status': 'success', 'message': 'Localização atualizada.'}) # Traduzido
        except ValueError:
            return jsonify({'status': 'error', 'message': 'Formato de latitude ou longitude inválido.'}), 400 # Traduzido
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Erro ao atualizar localização: {e}") # Mantido, log de erro
            return jsonify({'status': 'error', 'message': 'Erro do servidor ao atualizar localização.'}), 500 # Traduzido
            
    @app.route('/api/active_buses_locations', methods=['GET'])
    @login_required
    def active_buses_locations():
        if current_user.role != 'admin':
            return jsonify({'status': 'error', 'message': 'Acesso negado: Somente administradores.'}), 403 # Traduzido
        active_trips_with_location = Trip.query.filter(
            Trip.status == 'active',
            Trip.current_latitude.isnot(None),
            Trip.current_longitude.isnot(None)
        ).all()
        buses_data = []
        for trip in active_trips_with_location:
            buses_data.append({
                'trip_id': trip.id,
                'driver_username': trip.driver.username if trip.driver else 'Motorista Desconhecido', 
                'nome_motorista_viagem': trip.nome_motorista_viagem, # Adicionado nome da viagem
                'latitude': trip.current_latitude,
                'longitude': trip.current_longitude,
                'schedule': trip.schedule, # Este é o schedule_info simplificado
                'last_update': trip.last_location_update.strftime('%Y-%m-%d %H:%M:%S UTC') if trip.last_location_update else 'N/D' 
            })
        return jsonify(buses_data)

    @app.route('/admin/historico_viagens', methods=['GET'])
    @login_required
    def admin_historico_viagens():
        if current_user.role != 'admin':
            flash('Acesso negado: Somente administradores.', 'danger')
            return redirect(url_for('index'))

        data_inicio_str = request.args.get('data_inicio')
        data_fim_str = request.args.get('data_fim')

        data_inicio = None
        data_fim = None
        query = Trip.query.filter_by(status='completed')

        if data_inicio_str:
            try:
                data_inicio = datetime.strptime(data_inicio_str, '%Y-%m-%d').date()
                query = query.filter(Trip.data_viagem >= data_inicio)
            except ValueError:
                flash('Formato de Data de Início inválido. Use AAAA-MM-DD.', 'danger')
        
        if data_fim_str:
            try:
                data_fim = datetime.strptime(data_fim_str, '%Y-%m-%d').date()
                query = query.filter(Trip.data_viagem <= data_fim)
            except ValueError:
                flash('Formato de Data de Fim inválido. Use AAAA-MM-DD.', 'danger')

        viagens_completas = query.order_by(Trip.data_viagem.desc(), Trip.start_time.desc()).all()

        return render_template('admin_historico_viagens.html', 
                               viagens_completas=viagens_completas,
                               data_inicio_str=data_inicio_str,
                               data_fim_str=data_fim_str)

    @app.route('/admin/excluir_viagem/<int:trip_id>', methods=['POST'])
    @login_required
    def excluir_viagem(trip_id):
        if current_user.role != 'admin':
            flash('Acesso negado: Somente administradores.', 'danger')
            return redirect(url_for('index')) 

        viagem = Trip.query.get_or_404(trip_id) 
        # Consider using db.session.get(Trip, trip_id) and checking if None for SQLAlchemy 2.0+ style
        # if not viagem: abort(404)
        try:
            db.session.delete(viagem)
            db.session.commit()
            flash('Viagem excluída com sucesso.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao excluir viagem: {str(e)}', 'danger')
            app.logger.error(f"Erro ao excluir viagem {trip_id}: {e}")
            
        return redirect(url_for('admin_historico_viagens'))

    # A rota /change_password e sua função change_password() foram removidas daqui.

    return app

# --- Execução Principal ---
if __name__ == '__main__':
    app_instance = create_app()
    init_database(app_instance) # Inicializa o BD com a instância da app
    app_instance.run(host='0.0.0.0', port=8080, debug=True)
