# fitpro_academia/app/__init__.py

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from config import Config
from datetime import datetime, timedelta
from flask_mail import Mail # Adicione esta importação

# 1. Inicializa as extensões globalmente
db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
login.login_view = 'main.login'
mail = Mail()

def create_app(config_class=Config):
    """
    Função 'Application Factory'. Cria e configura a instância da aplicação Flask.
    """
    app = Flask(__name__)
    app.config.from_object(config_class)

    # 2. Vincula as instâncias das extensões com a aplicação
    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    mail.init_app(app)

    # --- Início da Seção dos Filtros de Template ---
    
    # Filtro para formatar data e hora completa (ex: 24/09/2025 às 23:18)
    def format_datetime_local(utc_datetime):
        if utc_datetime is None:
            return ""
        # Subtrai 3 horas do tempo UTC para converter para o fuso de São Paulo (UTC-3)
        local_time = utc_datetime - timedelta(hours=3)
        return local_time.strftime('%d/%m/%Y às %H:%M')
    app.jinja_env.filters['localtime'] = format_datetime_local

    # Novo filtro apenas para a hora (ex: 23:18)
    def format_time_local(utc_datetime):
        if utc_datetime is None:
            return ""
        local_time = utc_datetime - timedelta(hours=3)
        return local_time.strftime('%H:%M')
    app.jinja_env.filters['localtime_timeonly'] = format_time_local
    
    # --- Fim da Seção dos Filtros ---

    # 3. Importa e registra os blueprints (nossas rotas)
    from . import routes, models
    app.register_blueprint(routes.bp)

    return app

# 4. Importa os modelos aqui para evitar importação circular
from .models import User

# Esta função é usada pelo Flask-Login para carregar um usuário
@login.user_loader
def load_user(id):
    return User.query.get(int(id))