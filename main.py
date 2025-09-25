# run.py

from app import create_app

# Cria a instância da aplicação
app = create_app()

if __name__ == '__main__':
    # Esta parte é um fallback, o principal é usar o comando 'flask run'
    app.run(debug=True)