# fitpro_academia/app/__init__.py

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from config import Config

# 1. Inicializa as extensões globalmente
db = SQLAlchemy()
migrate = Migrate()
login = LoginManager() # <-- ESTA LINHA ESTAVA FALTANDO
login.login_view = 'main.login' # <-- E ESTA TAMBÉM (informa qual é a rota de login)

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