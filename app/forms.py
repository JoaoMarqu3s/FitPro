# fitpro_academia/app/forms.py

from flask_wtf import FlaskForm
from wtforms import (StringField, SubmitField, DateField, TextAreaField, 
                     SelectField, PasswordField, BooleanField)
from wtforms import (StringField, SubmitField, DateField, TextAreaField, 
                     SelectField, SelectMultipleField, PasswordField, 
                     BooleanField, widgets)
from wtforms.validators import DataRequired, Email, Length, ValidationError
from datetime import datetime
from .models import Membro
from .models import Instrutor
# A importação da biblioteca fica comentada até ser necessária
# from validate_docbr import CPF


# app/forms.py

# app/forms.py

class CadastroAlunoForm(FlaskForm):
    nome = StringField('Nome Completo', validators=[DataRequired(), Length(min=3, max=150)])
    cpf = StringField('CPF', validators=[DataRequired(), Length(min=11, max=14)])
    pin = StringField('PIN de 5 Dígitos', validators=[DataRequired(), Length(min=5, max=5)])
    data_nascimento = DateField('Data de Nascimento', format='%Y-%m-%d', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    telefone = StringField('Telefone', validators=[DataRequired(), Length(min=10, max=20)])
    submit = SubmitField('Cadastrar Aluno')
    
    def __init__(self, aluno_original=None, *args, **kwargs):
        super(CadastroAlunoForm, self).__init__(*args, **kwargs)
        self.aluno_original = aluno_original

    def validate_cpf(self, cpf):
        if self.aluno_original and self.aluno_original.cpf == cpf.data:
            return
        if Membro.query.filter_by(cpf=cpf.data).first():
            raise ValidationError('Este CPF já está cadastrado.')

    def validate_email(self, email):
        if self.aluno_original and self.aluno_original.email == email.data:
            return
        if Membro.query.filter_by(email=email.data).first():
            raise ValidationError('Este e-mail já está cadastrado.')


class NovaMatriculaForm(FlaskForm):
    membro = SelectField('Aluno', coerce=int, validators=[DataRequired()])
    plano = SelectField('Plano', coerce=int, validators=[DataRequired()])
    data_inicio = DateField('Data de Início', format='%Y-%m-%d', validators=[DataRequired()], default=datetime.today)
    metodo_pagamento = SelectField('Método de Pagamento', choices=[
        ('Cartão de Crédito', 'Cartão de Crédito'),
        ('PIX', 'PIX'),
        ('Débito', 'Débito'),
        ('Dinheiro', 'Dinheiro')
    ], validators=[DataRequired()])
    numero_parcelas = SelectField('Número de Parcelas', coerce=int, default=1)
    submit = SubmitField('Criar Matrícula')


class CheckinForm(FlaskForm):
    busca = StringField('Registrar Entrada do Aluno por Nome ou CPF', validators=[DataRequired()])
    submit = SubmitField('Registrar Entrada')


class InstrutorForm(FlaskForm):
    nome = StringField('Nome Completo', validators=[DataRequired(), Length(min=3, max=150)])
    cpf = StringField('CPF', validators=[DataRequired(), Length(min=11, max=14)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    telefone = StringField('Telefone', validators=[DataRequired(), Length(min=10, max=20)])
    especialidade = StringField('Especialidade', validators=[DataRequired(), Length(max=100)])
    submit = SubmitField('Cadastrar Instrutor')

    def __init__(self, instrutor_original=None, *args, **kwargs):
        super(InstrutorForm, self).__init__(*args, **kwargs)
        self.instrutor_original = instrutor_original

    def validate_cpf(self, cpf):
        if self.instrutor_original and self.instrutor_original.cpf == cpf.data:
            return
        if Instrutor.query.filter_by(cpf=cpf.data).first():
            raise ValidationError('Este CPF já está cadastrado.')

    def validate_email(self, email):
        if self.instrutor_original and self.instrutor_original.email == email.data:
            return
        if Instrutor.query.filter_by(email=email.data).first():
            raise ValidationError('Este e-mail já está cadastrado.')


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


class AvisoForm(FlaskForm):
    conteudo = TextAreaField('Conteúdo do Aviso', validators=[DataRequired()], render_kw={"rows": 5})
    submit = SubmitField('Publicar Aviso')

class AnamneseForm(FlaskForm):
    objetivo = TextAreaField('Qual é o seu principal objetivo com os treinos? (Ex: perder peso, ganhar massa muscular, etc.)', 
                             validators=[DataRequired()], render_kw={"rows": 3})

    historico_lesoes = TextAreaField('Você tem alguma lesão, dor crônica ou condição médica que devamos saber? (Ex: dor no joelho, cirurgia na coluna, etc.)', 
                                     render_kw={"rows": 3})

    usa_medicamentos = TextAreaField('Você faz uso de algum medicamento contínuo? Se sim, qual?', 
                                     render_kw={"rows": 3})

    dias_disponiveis = SelectMultipleField(
        'Quais dias da semana você geralmente pretende treinar?',
        choices=[
            ('Segunda-feira', 'Segunda-feira'),
            ('Terça-feira', 'Terça-feira'),
            ('Quarta-feira', 'Quarta-feira'),
            ('Quinta-feira', 'Quinta-feira'),
            ('Sexta-feira', 'Sexta-feira'),
            ('Sábado', 'Sábado'),
            ('Domingo', 'Domingo')
        ],
        widget=widgets.ListWidget(prefix_label=False), 
        option_widget=widgets.CheckboxInput()
    )

    submit = SubmitField('Enviar Respostas')