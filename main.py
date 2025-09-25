# main.py
from app import create_app

# A instância da aplicação é criada pela factory
app = create_app()

# O resto do código relacionado ao 'waitress' foi removido.
# O Gunicorn vai importar a variável 'app' diretamente deste arquivo.