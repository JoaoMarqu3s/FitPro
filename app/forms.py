# fitpro_academia/app/forms.py

from flask_wtf import FlaskForm
from wtforms import (StringField, SubmitField, DateField, TextAreaField, 
                     SelectField, PasswordField, BooleanField)
from wtforms.validators import DataRequired, Email, Length, ValidationError
from datetime import datetime
from .models import Membro
# A importação da biblioteca fica comentada até ser necessária
# from validate_docbr import CPF


# app/forms.py

class CadastroAlunoForm(FlaskForm):
    nome = StringField('Nome Completo', validators=[DataRequired(), Length(min=3, max=150)])
    cpf = StringField('CPF', validators=[DataRequired(), Length(min=11, max=14)])
    pin = StringField('PIN de 5 Dígitos', validators=[DataRequired(), Length(min=5, max=5)])
    data_nascimento = DateField('Data de Nascimento', format='%Y-%m-%d', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    telefone = StringField('Telefone', validators=[DataRequired(), Length(min=10, max=20)])
    submit = SubmitField('Cadastrar Aluno')
    
    # Guarda o aluno original que está sendo editado
    def __init__(self, aluno_original=None, *args, **kwargs):
        super(CadastroAlunoForm, self).__init__(*args, **kwargs)
        self.aluno_original = aluno_original

    def validate_cpf(self, cpf):
        # Lógica de validação matemática (ainda comentada)
        # ...

        # Se estamos editando e o CPF não mudou, não há o que validar
        if self.aluno_original and self.aluno_original.cpf == cpf.data:
            return
            
        # Se o CPF mudou (ou se é um novo aluno), verifica se ele já existe
        aluno_existente = Membro.query.filter_by(cpf=cpf.data).first()
        if aluno_existente:
            raise ValidationError('Este CPF já está cadastrado. Por favor, utilize outro.')

    def validate_email(self, email):
        # Se estamos editando e o email não mudou, não há o que validar
        if self.aluno_original and self.aluno_original.email == email.data:
            return
        
        # Se o email mudou (ou se é um novo aluno), verifica se ele já existe
        aluno_existente = Membro.query.filter_by(email=email.data).first()
        if aluno_existente:
            raise ValidationError('Este e-mail já está cadastrado. Por favor, utilize outro.')


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