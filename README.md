<h1>📘 Documentação de Configuração do Projeto GymFlow</h1>
  <p>
    Este guia descreve os passos necessários para configurar e rodar o ambiente de desenvolvimento 
    do sistema de gestão de academias <strong>FitPro</strong> em um novo computador.
  </p>
  
  <h2>1. Pré-requisitos</h2>
  <p>Antes de começar, garanta que você tenha os seguintes softwares instalados na sua máquina:</p>
  <ul>
    <li><strong>Python</strong>: Versão 3.10 ou superior. Você pode baixar em <a href="https://www.python.org" target="_blank">python.org</a>. Durante a instalação no Windows, marque a opção "Add Python to PATH".</li>
    <li><strong>Git</strong>: O sistema de controle de versão para baixar o código. Você pode baixar em <a href="https://git-scm.com" target="_blank">git-scm.com</a>.</li>
  </ul>

  <h2>2. Tecnologias e Bibliotecas Principais</h2>
  <p>Este projeto foi construído com as seguintes tecnologias:</p>
  
  <h3>Backend:</h3>
  <ul>
    <li><strong>Framework</strong>: Flask</li>
    <li><strong>Banco de Dados</strong>: SQLAlchemy (ORM) com SQLite (para desenvolvimento) e PostgreSQL (para produção).</li>
    <li><strong>Migrações de Banco</strong>: Flask-Migrate</li>
    <li><strong>Autenticação</strong>: Flask-Login</li>
    <li><strong>Formulários</strong>: Flask-WTF</li>
  </ul>

  <h3>Frontend:</h3>
  <ul>
    <li><strong>Templates</strong>: Jinja2</li>
    <li><strong>Estilização</strong>: Tailwind CSS (via CDN)</li>
    <li><strong>Interatividade</strong>: JavaScript (para o quiosque de QR Code)</li>
  </ul>

  <h3>Geração de QR Code:</h3>
  <ul>
    <li><code>qrcode[pil]</code></li>
  </ul>

  <h3>Servidores de Produção:</h3>
  <ul>
    <li><strong>gunicorn</strong> (para Linux)</li>
    <li><strong>waitress</strong> (para Windows)</li>
  </ul>

  <h2>3. Passos para Configuração do Ambiente</h2>
  <p>Siga os passos abaixo na ordem correta.</p>
  
  <h3>Passo 1: Obter o Código-Fonte</h3>
  <p>Clone o repositório do projeto a partir do GitHub. Abra um terminal e execute o seguinte comando (substitua pela URL do seu repositório):</p>
  <pre><code>git clone https://github.com/seu-usuario/seu-repositorio.git</code></pre>
  <p>Depois, navegue para a pasta do projeto:</p>
  <pre><code>cd nome-da-pasta-do-projeto</code></pre>

  <h3>Passo 2: Criar e Ativar o Ambiente Virtual</h3>
  <p>Um ambiente virtual (<code>venv</code>) isola as dependências do seu projeto, evitando conflitos.</p>
  <p><strong>Criar o ambiente:</strong></p>
  <pre><code>python -m venv venv</code></pre>
  <p><strong>Ativar o ambiente:</strong></p>
  <p>No Windows:</p>
  <pre><code>.\venv\Scripts\activate</code></pre>
  <p>No macOS/Linux:</p>
  <pre><code>source venv/bin/activate</code></pre>
  <p>Se funcionou, você verá <code>(venv)</code> no início do seu prompt de comando.</p>

  <h3>Passo 3: Instalar Todas as Dependências</h3>
  <p>O arquivo <code>requirements.txt</code> contém a lista de todas as bibliotecas Python que o projeto precisa. Com o ambiente virtual ativado, instale tudo com um único comando:</p>
  <pre><code>pip install -r requirements.txt</code></pre>

  <h3>Passo 4: Configurar as Variáveis de Ambiente</h3>
  <p>O arquivo <code>.flaskenv</code> configura automaticamente os comandos do Flask. Verifique se ele existe na raiz do seu projeto com o seguinte conteúdo:</p>
  <pre><code>FLASK_APP=run.py
FLASK_DEBUG=1</code></pre>

  <h3>Passo 5: Criar e Popular o Banco de Dados</h3>
  <p>Agora que o código e as bibliotecas estão prontos, precisamos criar o banco de dados local (<code>app.db</code>).</p>
  <p><strong>Crie a estrutura de tabelas (isso executa todas as migrações):</strong></p>
  <pre><code>flask db upgrade</code></pre>
  <p><strong>Popule o banco com dados iniciais (usuários admin/staff e os planos):</strong></p>
  <p>Inicie o shell do Flask:</p>
  <pre><code>flask shell</code></pre>
  <p>Dentro do shell, cole o script abaixo e pressione Enter:</p>
  <pre><code>from app import db
from app.models import User, Plano

print("Criando usuários e planos iniciais...")
User.query.delete()
Plano.query.delete()

admin = User(username='admin', email='admin@fitpro.com', role='admin')
admin.set_password('1234')
staff = User(username='staff', email='staff@fitpro.com', role='staff')
staff.set_password('1234')

plano_mensal = Plano(nome='Plano Mensal', descricao='Acesso por 30 dias.', preco=89.90, duracao_dias=30, max_parcelas=1)
plano_trimestral = Plano(nome='Plano Trimestral', descricao='Acesso por 90 dias.', preco=239.90, duracao_dias=90, max_parcelas=3)
plano_anual = Plano(nome='Plano Anual', descricao='Acesso por 365 dias.', preco=799.90, duracao_dias=365, max_parcelas=12)

db.session.add_all([admin, staff, plano_mensal, plano_trimestral, plano_anual])
db.session.commit()
print("Dados iniciais criados com sucesso!")
exit()</code></pre>

  <h2>4. Como Rodar a Aplicação</h2>
  <p>Com tudo configurado, para rodar o servidor de desenvolvimento, basta executar:</p>
  <pre><code>flask run</code></pre>
  <p>A aplicação estará disponível no seu navegador no endereço: <a href="http://127.0.0.1:5000" target="_blank">http://127.0.0.1:5000</a>.</p>
