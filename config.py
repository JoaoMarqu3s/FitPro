# fitpro_academia/config.py

import os

# Pega o caminho absoluto do diretório onde este arquivo está.
# Isso garante que o caminho para o banco de dados funcione em qualquer computador.
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    """Configurações base para a aplicação."""
    # Chave secreta para proteger contra ataques CSRF (Cross-Site Request Forgery)
    # Em produção, use um valor muito mais complexo e guarde-o de forma segura.
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'voce-nunca-vai-adivinhar'

    # Configuração do banco de dados SQLAlchemy
    # Define o local do arquivo do banco de dados SQLite.
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')

    # Desativa um recurso do SQLAlchemy que não usaremos, para economizar recursos.
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- NOVA CONFIGURAÇÃO DE DESCONTO ---
    # Desconto em porcentagem para pagamentos à vista (PIX/Débito)
    DESCONTO_A_VISTA = 10.0 

    MAIL_SERVER = 'smtp.googlemail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')


    
    