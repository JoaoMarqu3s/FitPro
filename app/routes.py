# fitpro_academia/app/routes.py
from flask import Blueprint, render_template, flash, redirect, url_for, request, current_app, jsonify, send_file
from flask_login import current_user, login_user, logout_user, login_required
from sqlalchemy import func, or_
from datetime import date, timedelta, datetime
import qrcode
import io

from . import db
from .models import Membro, Plano, Matricula, Frequencia, Instrutor, Pagamento, User, Treino
from .forms import (CadastroAlunoForm, NovaMatriculaForm, CheckinForm, 
                    InstrutorForm, LoginForm, TreinoForm, AssociarTreinoForm)



bp = Blueprint('main', __name__)


# --- Rotas de Autenticação ---

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.lista_alunos'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Usuário ou senha inválidos', 'danger')
            return redirect(url_for('main.login'))
        login_user(user, remember=form.remember_me.data)
        return redirect(url_for('main.lista_alunos'))
    return render_template('login.html', form=form)

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login'))


# --- Rota Principal ---

@bp.route('/')
@login_required
def index():
    return redirect(url_for('main.lista_alunos'))


# --- Rotas de Gestão de Alunos (Membros) ---
@bp.route('/aluno/<int:aluno_id>/qrcode')
@login_required
def gerar_qrcode(aluno_id):
    # O dado que queremos embutir no QR Code. Usaremos uma URL simples para o futuro quiosque.
    # Poderia ser apenas o ID, mas uma URL é mais flexível.
    data = url_for('main.api_checkin', aluno_id=aluno_id)

    # Gera o QR Code em memória
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    # Salva a imagem em um buffer de bytes na memória
    buf = io.BytesIO()
    img.save(buf)
    buf.seek(0)

    # Retorna o buffer como uma imagem PNG
    return send_file(buf, mimetype='image/png')

@bp.route('/quiosque')
@login_required # Apenas usuários logados podem abrir o quiosque
def quiosque():
    return render_template('quiosque.html')


# app/routes.py

@bp.route('/api/checkin/<int:aluno_id>', methods=['POST'])
def api_checkin(aluno_id):
    aluno = Membro.query.get(aluno_id)
    if not aluno:
        return jsonify({'status': 'error', 'message': 'Aluno não encontrado.'}), 404

    # --- LÓGICA DE CHECK-IN MODIFICADA ---
    status_checkin = "Liberado"
    message = f'Bem-vindo(a), {aluno.nome}!'

    matricula_valida = Matricula.query.filter(
        Matricula.membro_id == aluno.id,
        Matricula.status == 'Ativa',
        Matricula.data_fim >= date.today()
    ).first()

    if not matricula_valida:
        status_checkin = "Bloqueado - Matrícula Inválida"
        message = f'Acesso Negado para {aluno.nome}. Matrícula irregular.'

    # SEMPRE cria o registro de frequência
    novo_checkin = Frequencia(membro_id=aluno.id, tipo='Entrada', status=status_checkin)
    db.session.add(novo_checkin)
    db.session.commit()

    # A resposta de sucesso (200) é sempre enviada, mas o conteúdo muda
    return jsonify({
        'status': status_checkin, # 'Liberado' ou 'Bloqueado...'
        'message': message,
        'aluno_nome': aluno.nome,
        'hora_checkin': datetime.now().strftime('%H:%M')
    })

@bp.route('/aluno/<int:aluno_id>/sucesso')
@login_required
def cadastro_sucesso(aluno_id):
    aluno = Membro.query.get_or_404(aluno_id)
    return render_template('cadastro_sucesso.html', aluno=aluno)


@bp.route('/alunos')
@login_required
def lista_alunos():
    # 1. Pega o número da página da URL (ex: /alunos?page=2). O padrão é 1.
    page = request.args.get('page', 1, type=int)
    termo_busca = request.args.get('busca', '')

    if termo_busca:
        query = Membro.query.filter(
            or_(Membro.nome.ilike(f'%{termo_busca}%'), Membro.cpf == termo_busca)
        )
    else:
        query = Membro.query

    # 2. Em vez de .all(), usamos .paginate().
    #    Ele pega a página atual e quantos itens por página queremos (ex: 10).
    alunos_paginados = query.order_by(Membro.nome).paginate(page=page, per_page=10)

    # 3. Passamos o objeto de paginação inteiro para o template.
    #    Ele contém não só os alunos da página, mas também informações sobre as outras páginas.
    return render_template('lista_alunos.html', alunos_paginados=alunos_paginados, termo_busca=termo_busca)

@bp.route('/aluno/novo', methods=['GET', 'POST'])
@login_required
def novo_aluno():
    form = CadastroAlunoForm()
    if form.validate_on_submit():
        novo_membro = Membro(
            nome=form.nome.data,
            cpf=form.cpf.data,
            data_nascimento=form.data_nascimento.data,
            email=form.email.data,
            telefone=form.telefone.data
        )
        db.session.add(novo_membro)
        db.session.commit()
        flash('Aluno cadastrado com sucesso!', 'success')
        return redirect(url_for('main.cadastro_sucesso', aluno_id=novo_membro.id))
    return render_template('novo_aluno.html', form=form)

@bp.route('/aluno/<int:aluno_id>')
@login_required
def aluno_detalhe(aluno_id):
    aluno = Membro.query.get_or_404(aluno_id)
    return render_template('aluno_detalhe.html', aluno=aluno)

@bp.route('/aluno/<int:aluno_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_aluno(aluno_id):
    aluno = Membro.query.get_or_404(aluno_id)
    form = CadastroAlunoForm(obj=aluno)
    if form.validate_on_submit():
        aluno.nome = form.nome.data
        aluno.cpf = form.cpf.data
        aluno.data_nascimento = form.data_nascimento.data
        aluno.email = form.email.data
        aluno.telefone = form.telefone.data
        db.session.commit()
        flash('Dados do aluno atualizados com sucesso!', 'success')
        return redirect(url_for('main.lista_alunos'))
    return render_template('editar_aluno.html', form=form, aluno=aluno)

@bp.route('/aluno/<int:aluno_id>/excluir', methods=['POST'])
@login_required
def excluir_aluno(aluno_id):
    aluno = Membro.query.get_or_404(aluno_id)
    db.session.delete(aluno)
    db.session.commit()
    flash('Aluno excluído com sucesso!', 'success')
    return redirect(url_for('main.lista_alunos'))


# --- Rotas de Gestão de Matrículas e Frequência ---

@bp.route('/matriculas')
@login_required
def matriculas():
    form_matricula = NovaMatriculaForm()
    
    # Prepara os dados dos planos para o JavaScript
    planos = Plano.query.order_by('nome').all()
    # Cria um dicionário: { 'id_do_plano': {'preco': 99.90, 'max_parcelas': 3}, ... }
    planos_data = {
        p.id: {'preco': float(p.preco), 'max_parcelas': p.max_parcelas} for p in planos
    }
    
    form_matricula.membro.choices = [(m.id, m.nome) for m in Membro.query.order_by('nome').all()]
    form_matricula.plano.choices = [(p.id, f"{p.nome} (R$ {p.preco})") for p in planos]
    
    matriculas_ativas = Matricula.query.filter(
        Matricula.status == 'Ativa',
        Matricula.data_fim >= date.today()
    ).order_by(Matricula.data_fim).all()
    
    # Pega a porcentagem do desconto da configuração
    desconto_config = current_app.config.get('DESCONTO_A_VISTA', 0.0)

    return render_template('matricula.html', 
                           form_matricula=form_matricula, 
                           matriculas=matriculas_ativas,
                           planos_data=planos_data, # <-- Envia os dados para o template
                           desconto_percentual=desconto_config) # <-- Envia o desconto

@bp.route('/matricula/<int:matricula_id>/cancelar', methods=['POST'])
@login_required
def cancelar_matricula(matricula_id):
    matricula = Matricula.query.get_or_404(matricula_id)
    matricula.status = 'Cancelada'
    db.session.commit()
    flash(f'A matrícula do plano {matricula.plano.nome} foi cancelada.', 'success')
    return redirect(request.referrer or url_for('main.matriculas'))

@bp.route('/matricular', methods=['POST'])
@login_required
def matricular():
    form = NovaMatriculaForm()
    form.membro.choices = [(m.id, m.nome) for m in Membro.query.order_by('nome').all()]
    form.plano.choices = [(p.id, f"{p.nome} (R$ {p.preco})") for p in Plano.query.order_by('nome').all()]

    plano_id = request.form.get('plano')
    if plano_id:
        try:
            plano = Plano.query.get(int(plano_id))
            if plano:
                form.numero_parcelas.choices = [(i, f'{i}x') for i in range(1, plano.max_parcelas + 1)]
        except (ValueError, TypeError):
            pass # Ignora se o plano_id não for um número válido

    if form.validate_on_submit():
        plano_selecionado = Plano.query.get(form.plano.data)
        metodo_pagamento = form.metodo_pagamento.data

        preco_final = float(plano_selecionado.preco)
        if metodo_pagamento in ['PIX', 'Débito', 'Dinheiro']:
            desconto_percentual = current_app.config.get('DESCONTO_A_VISTA', 0.0)
            valor_desconto = (preco_final * desconto_percentual) / 100
            preco_final -= valor_desconto
            flash(f'Desconto de {desconto_percentual}% (R$ {valor_desconto:.2f}) aplicado para pagamento à vista!', 'info')

        data_inicio = form.data_inicio.data
        # A CORREÇÃO ESTÁ NA LINHA ABAIXO (duracao_dias)
        data_fim = data_inicio + timedelta(days=plano_selecionado.duracao_dias)

        nova_matricula = Matricula(
            membro_id=form.membro.data,
            plano_id=form.plano.data,
            data_inicio=data_inicio,
            data_fim=data_fim,
            status='Ativa'
        )

        novo_pagamento = Pagamento(
            valor=preco_final,
            metodo_pagamento=metodo_pagamento,
            numero_parcelas=form.numero_parcelas.data if metodo_pagamento == 'Cartão de Crédito' else 1,
            matricula=nova_matricula
        )

        db.session.add(nova_matricula)
        db.session.add(novo_pagamento)
        db.session.commit()
        flash('Matrícula e pagamento registrados com sucesso!', 'success')
        return redirect(url_for('main.matriculas'))
    else:
        # Pega o primeiro erro de cada campo para exibir um flash mais específico
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Erro no campo '{getattr(form, field).label.text}': {error}", 'danger')
                break # Mostra apenas o primeiro erro por campo

    return redirect(url_for('main.matriculas'))


# --- Rotas de Gestão de Treinos ---

@bp.route('/treinos', methods=['GET', 'POST'])
@login_required
def treinos():
    form = TreinoForm()
    form.instrutor.choices = [(i.id, i.nome) for i in Instrutor.query.order_by('nome').all()]
    if form.validate_on_submit():
        novo_treino = Treino(
            nome=form.nome.data,
            descricao=form.descricao.data,
            instrutor_id=form.instrutor.data
        )
        db.session.add(novo_treino)
        db.session.commit()
        flash('Novo modelo de treino salvo com sucesso!', 'success')
        return redirect(url_for('main.treinos'))
    lista_treinos = Treino.query.order_by(Treino.nome).all()
    return render_template('treinos.html', form=form, treinos=lista_treinos)

@bp.route('/treino/<int:treino_id>')
@login_required
def treino_detalhe(treino_id):
    treino = Treino.query.get_or_404(treino_id)
    form = AssociarTreinoForm()
    alunos_associados_ids = {membro.id for membro in treino.membros}
    alunos_disponiveis = Membro.query.filter(Membro.id.notin_(alunos_associados_ids)).order_by(Membro.nome).all()
    form.membro.choices = [(a.id, a.nome) for a in alunos_disponiveis]
    return render_template('treino_detalhe.html', treino=treino, form=form)

@bp.route('/treino/<int:treino_id>/associar', methods=['POST'])
@login_required
def associar_aluno_treino(treino_id):
    treino = Treino.query.get_or_404(treino_id)
    form = AssociarTreinoForm()
    alunos_associados_ids = {membro.id for membro in treino.membros}
    alunos_disponiveis = Membro.query.filter(Membro.id.notin_(alunos_associados_ids)).order_by(Membro.nome).all()
    form.membro.choices = [(a.id, a.nome) for a in alunos_disponiveis]
    if form.validate_on_submit():
        aluno = Membro.query.get_or_404(form.membro.data)
        treino.membros.append(aluno)
        db.session.commit()
        flash(f'{aluno.nome} foi associado ao treino "{treino.nome}" com sucesso!', 'success')
    else:
        flash('Ocorreu um erro ao associar o aluno.', 'danger')
    return redirect(url_for('main.treino_detalhe', treino_id=treino.id))

@bp.route('/treino/<int:treino_id>/desassociar/<int:membro_id>', methods=['POST'])
@login_required
def desassociar_aluno_treino(treino_id, membro_id):
    treino = Treino.query.get_or_404(treino_id)
    membro = Membro.query.get_or_404(membro_id)
    if membro in treino.membros:
        treino.membros.remove(membro)
        db.session.commit()
        flash(f'"{membro.nome}" foi desassociado do treino com sucesso.', 'success')
    else:
        flash(f'"{membro.nome}" já não estava neste treino.', 'warning')
    return redirect(url_for('main.treino_detalhe', treino_id=treino.id))


# --- Rotas de Admin (Instrutores e Relatórios) ---

@bp.route('/instrutores', methods=['GET', 'POST'])
@login_required
def instrutores():
    form = InstrutorForm()
    if form.validate_on_submit():
        novo_instrutor = Instrutor(
            nome=form.nome.data,
            cpf=form.cpf.data,
            email=form.email.data,
            telefone=form.telefone.data,
            especialidade=form.especialidade.data
        )
        db.session.add(novo_instrutor)
        db.session.commit()
        flash('Instrutor cadastrado com sucesso!', 'success')
        return redirect(url_for('main.instrutores'))
    lista_instrutores = Instrutor.query.order_by(Instrutor.nome).all()
    return render_template('instrutores.html', form=form, instrutores=lista_instrutores)

@bp.route('/planilhas')
@login_required
def planilhas():
    hoje = date.today()
    alunos_presentes_hoje = db.session.query(func.count(func.distinct(Frequencia.membro_id))).filter(func.date(Frequencia.data_hora) == hoje).scalar()
    novos_cadastros_hoje = db.session.query(func.count(Membro.id)).filter(func.date(Membro.data_cadastro) == hoje).scalar()
    receita_hoje = db.session.query(func.sum(Pagamento.valor)).filter(func.date(Pagamento.data_pagamento) == hoje).scalar() or 0.0
    relatorio_diario = {
        'data': hoje,
        'alunos_presentes': alunos_presentes_hoje,
        'novos_cadastros': novos_cadastros_hoje,
        'receita': f"{receita_hoje:.2f}"
    }
    return render_template('planilhas.html', relatorio_diario=relatorio_diario)

@bp.route('/matricula/<int:matricula_id>/excluir', methods=['POST'])
@login_required
def excluir_matricula(matricula_id):
    matricula = Matricula.query.get_or_404(matricula_id)
    
    # 1. Guarda as informações ANTES de deletar
    aluno_id = matricula.membro_id
    plano_nome = matricula.plano.nome
    
    # 2. Deleta o objeto do banco de dados
    db.session.delete(matricula)
    db.session.commit()
    
    # 3. Usa as informações guardadas para criar a mensagem
    flash(f'A matrícula do plano "{plano_nome}" foi removida do histórico permanentemente.', 'success')
    
    # 4. Redireciona de volta para a página de detalhes do aluno
    return redirect(url_for('main.aluno_detalhe', aluno_id=aluno_id))

# Cole esta função completa dentro do seu arquivo app/routes.py
@bp.route('/frequencia', methods=['GET', 'POST'])
@login_required
def frequencia():
    form = CheckinForm()
    # A lógica do POST (check-in) continua exatamente a mesma
    if form.validate_on_submit():
        # ... (código do check-in sem alterações) ...
        termo_busca = form.busca.data
        aluno = Membro.query.filter(or_(Membro.cpf == termo_busca, Membro.nome.ilike(f'%{termo_busca}%'))).first()
        if not aluno:
            flash('Aluno não encontrado.', 'danger')
        else:
            status_checkin = "Liberado"
            matricula_valida = Matricula.query.filter(
                Matricula.membro_id == aluno.id,
                Matricula.status == 'Ativa',
                Matricula.data_fim >= date.today()
            ).first()
            if not matricula_valida:
                status_checkin = "Bloqueado - Matrícula Inválida"
                flash(f'Atenção: Acesso registrado para {aluno.nome}, mas a matrícula está irregular.', 'warning')
            else:
                flash(f'Entrada registrada para {aluno.nome}!', 'success')
            novo_checkin = Frequencia(membro_id=aluno.id, tipo='Entrada', status=status_checkin)
            db.session.add(novo_checkin)
            db.session.commit()
        return redirect(url_for('main.frequencia'))

    # --- LÓGICA DE PAGINAÇÃO E FILTRAGEM ATUALIZADA ---
    page = request.args.get('page', 1, type=int) # Pega o número da página
    filtro_ativo = request.args.get('filtro', 'todos')

    query_base = Frequencia.query.filter(func.date(Frequencia.data_hora) == date.today())

    if filtro_ativo == 'Liberado':
        query_base = query_base.filter_by(status='Liberado')
    elif filtro_ativo == 'Bloqueado':
        query_base = query_base.filter(Frequencia.status.like('Bloqueado%'))

    # Usa .paginate() em vez de .all()
    registros_paginados = query_base.order_by(Frequencia.data_hora.desc()).paginate(page=page, per_page=10)

    return render_template('frequencia.html', 
                           form=form, 
                           registros_paginados=registros_paginados, # Envia o objeto paginado
                           filtro_ativo=filtro_ativo)