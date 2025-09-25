# fitpro_academia/app/models.py

from . import db
from datetime import date, datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

# Tabela de associação para a relação Muitos-para-Muitos entre Membro e Treino
treinos_membros = db.Table('treinos_membros',
    db.Column('membro_id', db.Integer, db.ForeignKey('membro.id'), primary_key=True),
    db.Column('treino_id', db.Integer, db.ForeignKey('treino.id'), primary_key=True)
)

class Membro(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    cpf = db.Column(db.String(14), unique=True, nullable=False)
    data_nascimento = db.Column(db.Date, nullable=False)
    endereco = db.Column(db.String(250))
    telefone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    data_cadastro = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Relacionamentos
    matriculas = db.relationship('Matricula', back_populates='membro', lazy=True, cascade="all, delete-orphan")
    frequencias = db.relationship('Frequencia', back_populates='membro', lazy=True, cascade="all, delete-orphan")
    treinos = db.relationship('Treino', secondary=treinos_membros, back_populates='membros', lazy='dynamic')

    def __repr__(self):
        return f"<Membro '{self.nome}'>"

class Plano(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text)
    preco = db.Column(db.Numeric(10, 2), nullable=False)
    duracao_dias = db.Column(db.Integer, nullable=False)
    max_parcelas = db.Column(db.Integer, nullable=False, default=1)

    # Relacionamento
    matriculas = db.relationship('Matricula', back_populates='plano', lazy=True)

    def __repr__(self):
        return f"<Plano '{self.nome}'>"

class Matricula(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data_inicio = db.Column(db.Date, nullable=False)
    data_fim = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(50), nullable=False, default='Ativa') # Usado para status manuais como 'Cancelada'

    # Chaves Estrangeiras
    membro_id = db.Column(db.Integer, db.ForeignKey('membro.id'), nullable=False)
    plano_id = db.Column(db.Integer, db.ForeignKey('plano.id'), nullable=False)

    # Relacionamentos
    membro = db.relationship('Membro', back_populates='matriculas')
    plano = db.relationship('Plano', back_populates='matriculas')
    pagamentos = db.relationship('Pagamento', back_populates='matricula', lazy=True, cascade="all, delete-orphan")

    @property
    def status_dinamico(self):
        hoje = date.today()
        
        if self.status != 'Ativa':
            return self.status

        if self.data_fim < hoje:
            return "Vencida"
        
        dias_restantes = (self.data_fim - hoje).days
        
        if dias_restantes <= 7:
            if dias_restantes == 0:
                return "Vence hoje"
            if dias_restantes == 1:
                return "Vence amanhã"
            return f"Vence em {dias_restantes} dias"
        
        return "Ativa"

    def __repr__(self):
        return f"<Matricula id={self.id} do Membro id={self.membro_id}>"

class Pagamento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data_pagamento = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    valor = db.Column(db.Numeric(10, 2), nullable=False)
    metodo_pagamento = db.Column(db.String(50))
    numero_parcelas = db.Column(db.Integer, default=1)
    status = db.Column(db.String(50), nullable=False, default='Aprovado')

    # Chave Estrangeira
    matricula_id = db.Column(db.Integer, db.ForeignKey('matricula.id'), nullable=False)

    # Relacionamento
    matricula = db.relationship('Matricula', back_populates='pagamentos')

    def __repr__(self):
        return f"<Pagamento de R${self.valor} para Matrícula id={self.matricula_id}>"

class Instrutor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    cpf = db.Column(db.String(14), unique=True, nullable=False)
    telefone = db.Column(db.String(20))
    email = db.Column(db.String(150), unique=True, nullable=False)
    especialidade = db.Column(db.String(100))

    # Relacionamento
    treinos_criados = db.relationship('Treino', back_populates='instrutor', lazy=True)

    def __repr__(self):
        return f"<Instrutor '{self.nome}'>"

class Treino(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    descricao = db.Column(db.Text)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)

    # Chave Estrangeira
    instrutor_id = db.Column(db.Integer, db.ForeignKey('instrutor.id'), nullable=False)

    # Relacionamentos
    instrutor = db.relationship('Instrutor', back_populates='treinos_criados')
    membros = db.relationship('Membro', secondary=treinos_membros, back_populates='treinos', lazy='dynamic')

    def __repr__(self):
        return f"<Treino '{self.nome}'>"

class Frequencia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data_hora = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    tipo = db.Column(db.String(10), nullable=False) # 'Entrada' ou 'Saída'

    # --- NOVO CAMPO ADICIONADO ---
    status = db.Column(db.String(50), nullable=False, default='Indefinido') # Ex: Liberado, Bloqueado - Vencida

    # Chave Estrangeira
    membro_id = db.Column(db.Integer, db.ForeignKey('membro.id'), nullable=False)

    # Relacionamento
    membro = db.relationship('Membro', back_populates='frequencias')

    def __repr__(self):
        return f"<Frequencia de {self.tipo} do Membro id={self.membro_id}>"

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    role = db.Column(db.String(20), nullable=False, default='staff')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'