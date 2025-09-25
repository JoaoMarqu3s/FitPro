from app import create_app
from waitress import serve

# Cria a instância da aplicação a partir da nossa factory
app = create_app()

if __name__ == '__main__':
    # Esta linha inicia o servidor de produção Waitress.
    # É o comando ideal para rodar a aplicação em um ambiente Windows real.
    # Ele vai rodar em http://localhost:8080 (ou no IP da sua rede)
    print("Iniciando servidor de produção Waitress em http://0.0.0.0:8080")
    serve(app, host='0.0.0.0', port=8080)