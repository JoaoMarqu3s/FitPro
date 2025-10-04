<h1>📘 Documentação de Configuração do Projeto GymFlow</h1>
<p>
    Este guia descreve os passos necessários para configurar e rodar o ambiente de desenvolvimento 
    do sistema de gestão de academias <strong>GymFlow</strong> em um novo computador.
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
    <li><strong>Envio de E-mail</strong>: Flask-Mail</li>
</ul>

<h3>Frontend:</h3>
<ul>
    <li><strong>Templates</strong>: Jinja2</li>
    <li><strong>Estilização</strong>: Tailwind CSS (via CDN)</li>
    <li><strong>Interatividade</strong>: JavaScript</li>
</ul>

<h3>Funcionalidades Específicas:</h3>
<ul>
    <li><strong>Geração de QR Code</strong>: <code>qrcode[pil]</code></li>
    <li><strong>Leitura de QR Code (Quiosque)</strong>: <code>html5-qrcode</code> (biblioteca JavaScript)</li>
    <li><strong>Exportação para Excel</strong>: <code>pandas</code> e <code>openpyxl</code></li>
</ul>

<h3>Servidores de Produção:</h3>
<ul>
    <li><strong><code>gunicorn</code></strong> (para ambientes Linux, como o Render.com)</li>
    <li><strong><code>waitress</code></strong> (para ambientes Windows)</li>
</ul>

<h2>3. Passos para Configuração do Ambiente</h2>
<p>Siga os passos abaixo na ordem correta.</p>

<h3>Passo 1: Obter o Código-Fonte</h3>
<p>Clone o repositório do projeto a partir do GitHub e navegue para a pasta do projeto:</p>
<pre><code>git clone https://github.com/seu-usuario/seu-repositorio.git
cd nome-da-pasta-do-projeto</code></pre>

<h3>Passo 2: Criar e Ativar o Ambiente Virtual</h3>
<p>Um ambiente virtual (<code>venv</code>) isola as dependências do seu projeto, evitando conflitos.</p>
<p><strong>Criar o ambiente:</strong></p>
<pre><code>python -m venv venv</code></pre>
<p><strong>Ativar o ambiente (Windows):</strong></p>
<pre><code>.\venv\Scripts\activate</code></pre>
<p><em>(Você verá <code>(venv)</code> no início do seu prompt de comando).</em></p>

<h3>Passo 3: Instalar Todas as Dependências</h3>
<p>O arquivo <code>requirements.txt</code> contém a lista de todas as bibliotecas Python que o projeto precisa. Com o ambiente virtual ativado, instale tudo com um único comando:</p>
<pre><code>pip install -r requirements.txt</code></pre>

<h3>Passo 4: Configurar as Variáveis de Ambiente (MUITO IMPORTANTE)</h3>
<p>Crie um arquivo chamado <code>.flaskenv</code> na raiz do projeto. Este arquivo guarda configurações e senhas de forma segura.</p>
<ul>
    <li><strong>Nome do arquivo:</strong> <code>.flaskenv</code></li>
    <li><strong>Conteúdo do arquivo:</strong>
        <pre><code>FLASK_APP=run.py
FLASK_DEBUG=1

# --- Configurações de E-mail (Exemplo com Gmail) ---
MAIL_USERNAME=seu-email-de-envio@gmail.com
MAIL_PASSWORD=sua-senha-de-app-de-16-letras</code></pre>
    </li>
    <li><strong>Atenção:</strong> <code>MAIL_PASSWORD</code> <strong>não</strong> é a sua senha normal do Gmail. É uma <strong>"Senha de App"</strong> de 16 letras que você precisa gerar na página de segurança da sua Conta Google. A "Verificação em duas etapas" precisa estar ativada.</li>
</ul>

<h3>Passo 5: Criar e Popular o Banco de Dados</h3>
<p>Agora que o código e as bibliotecas estão prontos, precisamos criar o banco de dados local (<code>app.db</code>).</p>
<p><strong>1. Crie a estrutura de tabelas (executa as migrações):</strong></p>
<pre><code>flask db upgrade</code></pre>
<p><strong>2. Popule o banco com dados iniciais (usuários e planos):</strong></p>
<p>Inicie o shell do Flask:</p>
<pre><code>flask shell</code></pre>
<p>Dentro do shell, cole o script abaixo e pressione Enter:</p>
<pre><code>from app import db
from app.models import User, Plano
print("Criando usuários e planos iniciais...")
User.query.delete()
Plano.query.delete()
admin = User(username='admin', email='admin@gymflow.com', role='admin')
admin.set_password('senhaforte123')
staff = User(username='staff', email='staff@gymflow.com', role='staff')
staff.set_password('senhaforte123')
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