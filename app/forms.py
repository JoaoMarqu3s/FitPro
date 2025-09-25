# fitpro_academia/app/forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, DateField
from wtforms.validators import DataRequired, Email, Length
from datetime import datetime
from wtforms import PasswordField, BooleanField
from wtforms import TextAreaField, SelectField
from wtforms.validators import DataRequired, Email, Length, ValidationError # Adicione ValidationError
from .models import Membro # Adicione esta linha

class CadastroAlunoForm(FlaskForm):
    nome = StringField('Nome Completo', validators=[DataRequired(), Length(min=3, max=150)])
    cpf = StringField('CPF', validators=[DataRequired(), Length(min=11, max=14)])
    data_nascimento = DateField('Data de Nascimento', format='%Y-%m-%d', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    telefone = StringField('Telefone', validators=[DataRequired(), Length(min=10, max=20)])
    # Adicionaremos endereço e outros campos depois para simplificar
    submit = SubmitField('Cadastrar Aluno')

      # --- NOVA FUNÇÃO DE VALIDAÇÃO PARA CPF ---
    def validate_cpf(self, cpf):
        aluno = Membro.query.filter_by(cpf=cpf.data).first()
        if aluno:
            raise ValidationError('Este CPF já está cadastrado. Por favor, utilize outro.')

    # --- NOVA FUNÇÃO DE VALIDAÇÃO PARA EMAIL ---
    def validate_email(self, email):
        aluno = Membro.query.filter_by(email=email.data).first()
        if aluno:
            raise ValidationError('Este e-mail já está cadastrado. Por favor, utilize outro.')


    # Adicione estas importações no topo do arquivo
from wtforms.fields import SelectField
from .models import Membro, Plano

# ... (mantenha a classe CadastroAlunoForm aqui) ...

class NovaMatriculaForm(FlaskForm):
    membro = SelectField('Aluno', coerce=int, validators=[DataRequired()])
    plano = SelectField('Plano', coerce=int, validators=[DataRequired()])
    data_inicio = DateField('Data de Início', format='%Y-%m-%d', validators=[DataRequired()], default=datetime.today)
    
    # --- NOVOS CAMPOS ADICIONADOS ---
    metodo_pagamento = SelectField('Método de Pagamento', choices=[
        ('Cartão de Crédito', 'Cartão de Crédito'),
        ('PIX', 'PIX'),
        ('Débito', 'Débito'),
        ('Dinheiro', 'Dinheiro')
    ], validators=[DataRequired()])
    
    # As opções deste campo serão preenchidas dinamicamente na rota/javascript
    numero_parcelas = SelectField('Número de Parcelas', coerce=int, default=1)
    
    submit = SubmitField('Criar Matrícula')


class CheckinForm(FlaskForm):
    busca = StringField('Buscar Aluno por Nome ou CPF', validators=[DataRequired()])
    submit = SubmitField('Registrar Entrada')

class InstrutorForm(FlaskForm):
    nome = StringField('Nome Completo', validators=[DataRequired(), Length(min=3, max=150)])
    cpf = StringField('CPF', validators=[DataRequired(), Length(min=11, max=14)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    telefone = StringField('Telefone', validators=[DataRequired(), Length(min=10, max=20)])
    especialidade = StringField('Especialidade', validators=[DataRequired(), Length(max=100)])
    submit = SubmitField('Cadastrar Instrutor')

class LoginForm(FlaskForm):
    username = StringField('Usuário', validators=[DataRequired()])
    password = PasswordField('Senha', validators=[DataRequired()])
    remember_me = BooleanField('Lembrar-me')
    submit = SubmitField('Entrar')

class TreinoForm(FlaskForm):
    nome = StringField('Nome do Treino', validators=[DataRequired(), Length(max=150)], render_kw={"placeholder": "Ex: Treino A - Peito e Tríceps"})
    descricao = TextAreaField('Descrição (Exercícios, Séries, Repetições)', validators=[DataRequired()], render_kw={"rows": 10})
    instrutor = SelectField('Instrutor Responsável', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Salvar Treino')


class AssociarTreinoForm(FlaskForm):
    membro = SelectField('Selecione o Aluno', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Associar Aluno')
