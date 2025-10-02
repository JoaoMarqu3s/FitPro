# fitpro_academia/app/routes.py
from flask import Blueprint, render_template, flash, redirect, url_for, request, current_app, jsonify, send_file
from flask_login import current_user, login_user, logout_user, login_required
from sqlalchemy import func, or_
from datetime import date, timedelta, datetime
import qrcode
import io
import calendar
import pandas as pd
from flask_mail import Message
from app import mail
import random

from . import db
from .models import Membro, Aviso, Plano, Matricula, Frequencia, Instrutor, Pagamento, User, Treino
from .forms import (CadastroAlunoForm, NovaMatriculaForm, CheckinForm, 
                    InstrutorForm, AvisoForm, LoginForm, TreinoForm, AssociarTreinoForm)



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

@bp.route('/') # Esta agora é a rota do dashboard
@login_required
def index():
    # Card 1: Total de Check-ins (entradas) hoje
    hoje_utc = datetime.utcnow()
    hoje_local = hoje_utc - timedelta(hours=3)
    inicio_dia_utc = (hoje_local.replace(hour=0, minute=0, second=0, microsecond=0)) + timedelta(hours=3)
    fim_dia_utc = (hoje_local.replace(hour=23, minute=59, second=59, microsecond=999999)) + timedelta(hours=3)
    total_checkins_hoje = Frequencia.query.filter(Frequencia.tipo == 'Entrada', Frequencia.data_hora.between(inicio_dia_utc, fim_dia_utc)).count()

    # Card 2: Receita confirmada hoje
    receita_hoje = db.session.query(func.sum(Pagamento.valor)).filter(
        Pagamento.status == 'Confirmado',
        Pagamento.data_pagamento.between(inicio_dia_utc, fim_dia_utc)
    ).scalar() or 0.0

    # Card 3: Matrículas vencendo em 7 dias
    proximos_7_dias = hoje_local.date() + timedelta(days=7)
    vencendo_em_breve = Matricula.query.filter(
        Matricula.status == 'Ativa',
        Matricula.data_fim.between(hoje_local.date(), proximos_7_dias)
    ).count()

    # Card 4: Pagamentos pendentes
    pagamentos_pendentes = Pagamento.query.filter(Pagamento.status == 'Pendente').count()

    # Pega o aviso mais recente para o mural
    aviso_ativo = Aviso.query.order_by(Aviso.data_criacao.desc()).first()

    return render_template('dashboard.html',
                           total_checkins_hoje=total_checkins_hoje,
                           receita_hoje=f"{receita_hoje:.2f}",
                           vencendo_em_breve=vencendo_em_breve,
                           pagamentos_pendentes=pagamentos_pendentes,
                           aviso_ativo=aviso_ativo)


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
def quiosque():
    return render_template('quiosque.html')


# app/routes.py

@bp.route('/api/checkin/<int:aluno_id>', methods=['POST'])
def api_checkin(aluno_id):
    aluno = Membro.query.get(aluno_id)
    if not aluno:
        return jsonify({'status': 'error', 'message': 'Aluno não encontrado.'}), 404

    # --- Lógica de Check-in (igual à da outra rota) ---
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

    # --- PARTE CRÍTICA QUE PROVAVELMENTE ESTAVA FALTANDO ---
    # 1. Cria o novo registro de frequência
    novo_checkin = Frequencia(membro_id=aluno.id, tipo='Entrada', status=status_checkin)
    
    # 2. Adiciona à sessão do banco de dados
    db.session.add(novo_checkin)
    
    # 3. Salva permanentemente no banco de dados
    db.session.commit()
    # --- FIM DA PARTE CRÍTICA ---
    
    # A resposta de sucesso (200) é sempre enviada, mas o conteúdo muda
    return jsonify({
        'status': status_checkin,
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
    page = request.args.get('page', 1, type=int)
    termo_busca = request.args.get('busca', '')
    # Novo: Pega o parâmetro de ordenação da URL. O padrão é 'nome'.
    ordem = request.args.get('ordem', 'nome')
    
    query = Membro.query
    if termo_busca:
        query = query.filter(
            or_(Membro.nome.ilike(f'%{termo_busca}%'), Membro.cpf == termo_busca)
        )
    
    # --- LÓGICA DE ORDENAÇÃO ATUALIZADA ---
    if ordem == 'antigos':
        query = query.order_by(Membro.data_cadastro.asc()) # .asc() = ascendente (do mais antigo para o mais novo)
    elif ordem == 'recentes':
        query = query.order_by(Membro.data_cadastro.desc()) # .desc() = descendente (do mais novo para o mais antigo)
    else: # Padrão
        query = query.order_by(Membro.nome.asc())

    alunos_paginados = query.paginate(page=page, per_page=10)
    
    return render_template('lista_alunos.html', 
                           alunos_paginados=alunos_paginados, 
                           termo_busca=termo_busca,
                           ordem_ativa=ordem) # Envia a ordenação ativa para o template

@bp.route('/aluno/novo', methods=['GET', 'POST'])
@login_required
def novo_aluno():
    form = CadastroAlunoForm()
    if form.validate_on_submit():
        novo_membro = Membro(
            nome=form.nome.data,
            cpf=form.cpf.data,
            pin=form.pin.data, 
            data_nascimento=form.data_nascimento.data,
            email=form.email.data,
            telefone=form.telefone.data
        )
        db.session.add(novo_membro)
        db.session.commit()
        flash('Aluno cadastrado com sucesso!', 'success')
        return redirect(url_for('main.cadastro_sucesso', aluno_id=novo_membro.id))

    # --- LÓGICA PARA GERAR SUGESTÕES DE PIN ---
    sugestoes_pin = []
    # Pega todos os PINs que já estão em uso
    pins_existentes = {m.pin for m in Membro.query.with_entities(Membro.pin).all()}
    while len(sugestoes_pin) < 3:
        # Gera um número aleatório de 5 dígitos (com zeros à esquerda se necessário)
        novo_pin = str(random.randint(0, 99999)).zfill(5)
        if novo_pin not in pins_existentes and novo_pin not in sugestoes_pin:
            sugestoes_pin.append(novo_pin)

    return render_template('novo_aluno.html', form=form, sugestoes_pin=sugestoes_pin)

@bp.route('/aluno/<int:aluno_id>')
@login_required
def aluno_detalhe(aluno_id):
    aluno = Membro.query.get_or_404(aluno_id)
    return render_template('aluno_detalhe.html', aluno=aluno)

@bp.route('/aluno/<int:aluno_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_aluno(aluno_id):
    aluno = Membro.query.get_or_404(aluno_id)
    # Passamos o 'aluno' original para o formulário
    form = CadastroAlunoForm(aluno_original=aluno)

    # Quando o formulário é enviado, o WTForms popula o 'form' com os novos dados
    if form.validate_on_submit():
        aluno.nome = form.nome.data
        aluno.cpf = form.cpf.data
        aluno.data_nascimento = form.data_nascimento.data
        aluno.email = form.email.data
        aluno.telefone = form.telefone.data
        db.session.commit()
        flash('Dados do aluno atualizados com sucesso!', 'success')
        return redirect(url_for('main.lista_alunos'))
    
    # Na primeira vez que a página carrega (GET), popula o formulário com os dados existentes
    elif request.method == 'GET':
        form.process(obj=aluno)

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
# app/routes.py

# app/routes.py

@bp.route('/matriculas')
@login_required
def matriculas():
    form_matricula = NovaMatriculaForm()
    
    # --- LINHAS QUE FALTAVAM (ADICIONADAS DE VOLTA) ---
    planos = Plano.query.order_by('nome').all()
    planos_data = {
        p.id: {'preco': float(p.preco), 'max_parcelas': p.max_parcelas} for p in planos
    }
    desconto_config = current_app.config.get('DESCONTO_A_VISTA', 0.0)
    # --- FIM DAS LINHAS ADICIONADAS ---
    
    # Popula as opções dos menus dropdown
    form_matricula.membro.choices = [(m.id, m.nome) for m in Membro.query.order_by('nome').all()]
    form_matricula.plano.choices = [(p.id, f"{p.nome} (R$ {p.preco})") for p in planos]
    
    # Lógica de filtros e paginação (continua a mesma)
    page = request.args.get('page', 1, type=int)
    filtro_ativo = request.args.get('filtro', 'ativas')
    
    hoje = date.today()
    query_base = Matricula.query.filter(Matricula.status == 'Ativa')
    titulo_pagina = "Matrículas Efetuadas"

    if filtro_ativo == '7dias':
        titulo_pagina = "Vencendo nos Próximos 7 Dias"
        proximos_7_dias = hoje + timedelta(days=7)
        query_base = query_base.filter(Matricula.data_fim.between(hoje, proximos_7_dias))
    elif filtro_ativo == 'proximo_mes':
        titulo_pagina = "Vencendo no Próximo Mês"
        primeiro_dia_mes_atual = hoje.replace(day=1)
        proximo_mes = primeiro_dia_mes_atual + timedelta(days=32)
        primeiro_dia_proximo_mes = proximo_mes.replace(day=1)
        mes_seguinte_ao_proximo = primeiro_dia_proximo_mes + timedelta(days=32)
        ultimo_dia_proximo_mes = mes_seguinte_ao_proximo.replace(day=1) - timedelta(days=1)
        query_base = query_base.filter(Matricula.data_fim.between(primeiro_dia_proximo_mes, ultimo_dia_proximo_mes))
    elif filtro_ativo == 'vencidas':
        titulo_pagina = "Matrículas Vencidas"
        query_base = query_base.filter(Matricula.data_fim < hoje)
    else: # Filtro padrão 'ativas'
        query_base = query_base.filter(Matricula.data_fim >= hoje)
        
    matriculas_paginadas = query_base.order_by(Matricula.data_fim).paginate(page=page, per_page=4)

    # Adiciona as variáveis que faltavam ao render_template
    return render_template('matricula.html', 
                           form_matricula=form_matricula, 
                           matriculas_paginadas=matriculas_paginadas,
                           filtro_ativo=filtro_ativo,
                           titulo_pagina=titulo_pagina,
                           planos_data=planos_data,
                           desconto_percentual=desconto_config)

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
            matricula=nova_matricula,
            status='Pendente'
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

# app/routes.py

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

    # --- LÓGICA DE BUSCA E PAGINAÇÃO ADICIONADA ---
    page = request.args.get('page', 1, type=int)
    termo_busca = request.args.get('busca', '')

    query = Treino.query
    if termo_busca:
        query = query.filter(Treino.nome.ilike(f'%{termo_busca}%'))

    treinos_paginados = query.order_by(Treino.nome).paginate(page=page, per_page=5) # Alterado para 5 por página
    
    return render_template('treinos.html', 
                           form=form, 
                           treinos_paginados=treinos_paginados,
                           termo_busca=termo_busca)

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

    # --- LÓGICA DE BUSCA E PAGINAÇÃO ADICIONADA ---
    page = request.args.get('page', 1, type=int)
    termo_busca = request.args.get('busca', '')

    query = Instrutor.query
    if termo_busca:
        query = query.filter(
            or_(
                Instrutor.nome.ilike(f'%{termo_busca}%'),
                Instrutor.cpf == termo_busca,
                Instrutor.especialidade.ilike(f'%{termo_busca}%')
            )
        )

    # Paginação de 3 em 3
    instrutores_paginados = query.order_by(Instrutor.nome).paginate(page=page, per_page=3)
    
    return render_template('instrutores.html', 
                           form=form, 
                           instrutores_paginados=instrutores_paginados,
                           termo_busca=termo_busca)

# --- FUNÇÃO AUXILIAR PARA GERAR DADOS DO RELATÓRIO ---
def _gerar_dados_relatorio(periodo):
    """Função interna para calcular os dados de um relatório para um dado período."""
    hoje_local = (datetime.utcnow() - timedelta(hours=3)).date()
    
    if periodo == 'diario':
        titulo_relatorio = "Relatório Diário - " + hoje_local.strftime('%d/%m/%Y')
        inicio_periodo_data = fim_periodo_data = hoje_local
    elif periodo == 'semanal':
        inicio_periodo_data = hoje_local - timedelta(days=hoje_local.weekday())
        fim_periodo_data = inicio_periodo_data + timedelta(days=6)
        titulo_relatorio = f"Relatório Semanal ({inicio_periodo_data.strftime('%d/%m')} - {fim_periodo_data.strftime('%d/%m')})"
    elif periodo == 'mensal':
        inicio_periodo_data = hoje_local.replace(day=1)
        _, ultimo_dia_numero = calendar.monthrange(hoje_local.year, hoje_local.month)
        fim_periodo_data = hoje_local.replace(day=ultimo_dia_numero)
        titulo_relatorio = f"Relatório Mensal - {hoje_local.strftime('%B de %Y')}"
    elif periodo == 'semestral':
        fim_periodo_data = hoje_local
        mes_inicio = hoje_local.month - 5
        ano_inicio = hoje_local.year
        if mes_inicio <= 0:
            mes_inicio += 12
            ano_inicio -= 1
        inicio_periodo_data = hoje_local.replace(year=ano_inicio, month=mes_inicio, day=1)
        titulo_relatorio = f"Relatório Semestral ({inicio_periodo_data.strftime('%m/%Y')} a {fim_periodo_data.strftime('%m/%Y')})"
    elif periodo == 'anual':
        inicio_periodo_data = hoje_local.replace(month=1, day=1)
        fim_periodo_data = hoje_local.replace(month=12, day=31)
        titulo_relatorio = f"Relatório Anual - {hoje_local.year}"
    else: # Fallback
        periodo = 'diario'
        titulo_relatorio = "Relatório Diário - " + hoje_local.strftime('%d/%m/%Y')
        inicio_periodo_data = fim_periodo_data = hoje_local

    inicio_periodo_dt_local = datetime.combine(inicio_periodo_data, datetime.min.time())
    fim_periodo_dt_local = datetime.combine(fim_periodo_data, datetime.max.time())
    inicio_periodo_utc = inicio_periodo_dt_local + timedelta(hours=3)
    fim_periodo_utc = fim_periodo_dt_local + timedelta(hours=3)

    alunos_presentes = db.session.query(func.count(func.distinct(Frequencia.membro_id))).filter(
        Frequencia.data_hora.between(inicio_periodo_utc, fim_periodo_utc)
    ).scalar()
    novos_cadastros = db.session.query(func.count(Membro.id)).filter(
        Membro.data_cadastro.between(inicio_periodo_utc, fim_periodo_utc)
    ).scalar()
    receita = db.session.query(func.sum(Pagamento.valor)).filter(
    Pagamento.status.in_(['Confirmado', 'Arquivado']),
    Pagamento.data_pagamento.between(inicio_periodo_utc, fim_periodo_utc)
    ).scalar() or 0.0

    relatorio = {
        'Alunos Únicos Presentes': alunos_presentes,
        'Novos Cadastros': novos_cadastros,
        'Receita no Período (R$)': f"{receita:.2f}"
    }
    
    return titulo_relatorio, relatorio, periodo

# --- ROTA DE PLANILHAS ATUALIZADA ---
@bp.route('/planilhas')
@login_required
def planilhas():
    periodo_ativo = request.args.get('periodo', 'diario')
    titulo_relatorio, relatorio_dados, _ = _gerar_dados_relatorio(periodo_ativo)

    return render_template('planilhas.html', 
                           relatorio=relatorio_dados,
                           titulo_relatorio=titulo_relatorio,
                           periodo_ativo=periodo_ativo)

# --- NOVA ROTA PARA EXPORTAÇÃO ---
@bp.route('/planilhas/exportar')
@login_required
def exportar_planilhas():
    periodo_ativo = request.args.get('periodo', 'diario')
    titulo_relatorio, relatorio_dados, _ = _gerar_dados_relatorio(periodo_ativo)

    # Cria um DataFrame do pandas com os dados
    df = pd.DataFrame(list(relatorio_dados.items()), columns=['Métrica', 'Valor'])

    # Cria um buffer de bytes na memória para salvar o arquivo Excel
    output = io.BytesIO()
    
    # Escreve o DataFrame no buffer em formato Excel
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Relatorio')
        
    output.seek(0) # Volta para o início do buffer

    # Envia o arquivo para o navegador para download
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'relatorio_{periodo_ativo}.xlsx'
    )

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


@bp.route('/frequencia', methods=['GET', 'POST'])
@login_required
def frequencia():
    form = CheckinForm()
    if form.validate_on_submit():
        # ... (a lógica do POST para o formulário de check-in continua a mesma) ...
        termo_busca = form.busca.data
        aluno = Membro.query.filter(or_(Membro.cpf == termo_busca, Membro.nome.ilike(f'%{termo_busca}%'))).first()
        if not aluno:
            flash('Aluno não encontrado.', 'danger')
        else:
            status_checkin = "Liberado"
            matricula_valida = Matricula.query.filter(
                Matricula.membro_id == aluno.id,
                Matricula.status == 'Ativa',
                Matricula.data_fim >= date.today() # A verificação da data aqui pode continuar simples
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
    
    # --- LÓGICA DE FILTRAGEM DE HORÁRIO CORRIGIDA ---
    page = request.args.get('page', 1, type=int)
    filtro_ativo = request.args.get('filtro', 'todos')
    
    # Define o "hoje" local (UTC-3)
    hoje_utc = datetime.utcnow()
    hoje_local = hoje_utc - timedelta(hours=3)
    
    # Define o início e o fim do dia de hoje no horário local
    inicio_dia_local = hoje_local.replace(hour=0, minute=0, second=0, microsecond=0)
    fim_dia_local = hoje_local.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    # Converte esse intervalo de volta para UTC para fazer a consulta no banco
    inicio_dia_utc = inicio_dia_local + timedelta(hours=3)
    fim_dia_utc = fim_dia_local + timedelta(hours=3)

    # A consulta agora busca registros dentro deste intervalo de tempo preciso
    query_base = Frequencia.query.filter(Frequencia.data_hora.between(inicio_dia_utc, fim_dia_utc))

    if filtro_ativo == 'Liberado':
        query_base = query_base.filter_by(status='Liberado')
    elif filtro_ativo == 'Bloqueado':
        query_base = query_base.filter(Frequencia.status.like('Bloqueado%'))

    registros_paginados = query_base.order_by(Frequencia.data_hora.desc()).paginate(page=page, per_page=5)

    return render_template('frequencia.html', 
                           form=form, 
                           registros_paginados=registros_paginados,
                           filtro_ativo=filtro_ativo)


@bp.route('/financeiro')
@login_required
def financeiro():
    page = request.args.get('page', 1, type=int)
    filtro_status = request.args.get('status', 'todos')
    filtro_periodo = request.args.get('periodo', 'todos')
    ordem = request.args.get('ordem', 'recentes') # Novo: Pega o parâmetro de ordenação

    query = Pagamento.query.filter(Pagamento.status != 'Arquivado')

    # Filtro de STATUS (sem alteração)
    if filtro_status != 'todos':
        query = query.filter(Pagamento.status == filtro_status)

    # --- LÓGICA DE FILTRO DE PERÍODO ATUALIZADA ---
    hoje_utc = datetime.utcnow()
    hoje_local = hoje_utc - timedelta(hours=3)

    if filtro_periodo == 'este_mes':
        inicio_mes = hoje_local.replace(day=1)
        _, ultimo_dia = calendar.monthrange(inicio_mes.year, inicio_mes.month)
        fim_mes = hoje_local.replace(day=ultimo_dia)
        inicio_utc = datetime.combine(inicio_mes, datetime.min.time()) + timedelta(hours=3)
        fim_utc = datetime.combine(fim_mes, datetime.max.time()) + timedelta(hours=3)
        query = query.filter(Pagamento.data_pagamento.between(inicio_utc, fim_utc))
    elif filtro_periodo == 'ultimos_3_meses':
        fim_utc = hoje_utc
        # Aproximação de 3 meses (90 dias)
        inicio_utc = hoje_utc - timedelta(days=90)
        query = query.filter(Pagamento.data_pagamento.between(inicio_utc, fim_utc))
    elif filtro_periodo == 'ultimos_6_meses':
        fim_utc = hoje_utc
        # Aproximação de 6 meses (180 dias)
        inicio_utc = hoje_utc - timedelta(days=180)
        query = query.filter(Pagamento.data_pagamento.between(inicio_utc, fim_utc))
    elif filtro_periodo == 'este_ano':
        inicio_ano = hoje_local.replace(month=1, day=1)
        inicio_utc = datetime.combine(inicio_ano, datetime.min.time()) + timedelta(hours=3)
        fim_utc = datetime.utcnow() # Até o momento atual
        query = query.filter(Pagamento.data_pagamento.between(inicio_utc, fim_utc))
    # 'todos' não precisa de filtro de data

    # --- LÓGICA DE ORDENAÇÃO ADICIONADA ---
    if ordem == 'antigos':
        query = query.order_by(Pagamento.data_pagamento.asc())
    else: # Padrão é 'recentes'
        query = query.order_by(Pagamento.data_pagamento.desc())

    pagamentos_paginados = query.paginate(page=page, per_page=15)
    
    return render_template('financeiro.html', 
                           pagamentos_paginados=pagamentos_paginados,
                           filtro_status_ativo=filtro_status,
                           filtro_periodo_ativo=filtro_periodo,
                           ordem_ativa=ordem) # Envia a ordenação para o template

# --- NOVA ROTA PARA EXCLUIR PAGAMENTOS ---
@bp.route('/pagamento/<int:pagamento_id>/excluir', methods=['POST'])
@login_required
def excluir_pagamento(pagamento_id):
    pagamento = Pagamento.query.get_or_404(pagamento_id)
    if current_user.role != 'admin':
        flash('Acesso não autorizado.', 'danger')
        return redirect(url_for('main.financeiro'))
        
    # --- LÓGICA ALTERADA: EM VEZ DE DELETAR, ARQUIVAMOS ---
    pagamento.status = 'Arquivado'
    db.session.commit()
    flash('Registro de pagamento arquivado e oculto da lista.', 'success')
    return redirect(request.referrer or url_for('main.financeiro'))

@bp.route('/pagamento/<int:pagamento_id>/confirmar', methods=['POST'])
@login_required
def confirmar_pagamento(pagamento_id):
    pagamento = Pagamento.query.get_or_404(pagamento_id)
    pagamento.status = 'Confirmado'
    
    # --- LINHA ADICIONADA PARA CORRIGIR O BUG ---
    # Garante que a matrícula associada seja marcada como 'Ativa'
    pagamento.matricula.status = 'Ativa'
    
    db.session.commit()
    flash('Pagamento confirmado e matrícula ativada com sucesso!', 'success')
    return redirect(url_for('main.financeiro'))

@bp.route('/pagamento/<int:pagamento_id>/cancelar', methods=['POST'])
@login_required
def cancelar_pagamento(pagamento_id):
    pagamento = Pagamento.query.get_or_404(pagamento_id)
    pagamento.status = 'Cancelado'
    # Também cancelamos a matrícula associada
    pagamento.matricula.status = 'Cancelada'
    db.session.commit()
    flash('Pagamento e matrícula cancelados.', 'warning')
    return redirect(url_for('main.financeiro'))


@bp.route('/instrutor/<int:instrutor_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_instrutor(instrutor_id):
    instrutor = Instrutor.query.get_or_404(instrutor_id)
    # Reutilizamos o mesmo formulário, passando o instrutor original para a validação
    form = InstrutorForm(obj=instrutor)
    
    if form.validate_on_submit():
        instrutor.nome = form.nome.data
        instrutor.cpf = form.cpf.data
        instrutor.email = form.email.data
        instrutor.telefone = form.telefone.data
        instrutor.especialidade = form.especialidade.data
        db.session.commit()
        flash('Dados do instrutor atualizados com sucesso!', 'success')
        return redirect(url_for('main.instrutores'))
        
    return render_template('editar_instrutor.html', form=form, instrutor=instrutor)


@bp.route('/instrutor/<int:instrutor_id>/excluir', methods=['POST'])
@login_required
def excluir_instrutor(instrutor_id):
    instrutor = Instrutor.query.get_or_404(instrutor_id)
    # Adicionar verificação se o instrutor tem treinos associados antes de excluir (melhoria futura)
    db.session.delete(instrutor)
    db.session.commit()
    flash('Instrutor excluído com sucesso!', 'success')
    return redirect(url_for('main.instrutores'))

@bp.route('/treino/<int:treino_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_treino(treino_id):
    treino = Treino.query.get_or_404(treino_id)
    form = TreinoForm(obj=treino)
    form.instrutor.choices = [(i.id, i.nome) for i in Instrutor.query.order_by('nome').all()]

    if form.validate_on_submit():
        treino.nome = form.nome.data
        treino.descricao = form.descricao.data
        treino.instrutor_id = form.instrutor.data
        db.session.commit()
        flash('Modelo de treino atualizado com sucesso!', 'success')
        return redirect(url_for('main.treinos'))
        
    return render_template('editar_treino.html', form=form, treino=treino)


@bp.route('/treino/<int:treino_id>/excluir', methods=['POST'])
@login_required
def excluir_treino(treino_id):
    treino = Treino.query.get_or_404(treino_id)
    
    # Prática segura: antes de deletar o treino, remove todas as associações com membros
    treino.membros = []
    
    db.session.delete(treino)
    db.session.commit()
    flash('Modelo de treino excluído com sucesso!', 'success')
    return redirect(url_for('main.treinos'))

# app/routes.py

@bp.route('/avisos', methods=['GET', 'POST'])
@login_required
def gerenciar_avisos():
    # Apenas admins podem gerenciar avisos
    if current_user.role != 'admin':
        flash('Acesso não autorizado.', 'danger')
        return redirect(url_for('main.dashboard'))

    form = AvisoForm()
    if form.validate_on_submit():
        novo_aviso = Aviso(conteudo=form.conteudo.data)
        db.session.add(novo_aviso)
        db.session.commit()
        flash('Aviso publicado com sucesso!', 'success')
        return redirect(url_for('main.gerenciar_avisos'))

    avisos = Aviso.query.order_by(Aviso.data_criacao.desc()).all()
    return render_template('avisos.html', form=form, avisos=avisos)

@bp.route('/aviso/<int:aviso_id>/excluir', methods=['POST'])
@login_required
def excluir_aviso(aviso_id):
    if current_user.role != 'admin':
        return redirect(url_for('main.dashboard'))

    aviso = Aviso.query.get_or_404(aviso_id)
    db.session.delete(aviso)
    db.session.commit()
    flash('Aviso excluído com sucesso.', 'success')
    return redirect(url_for('main.gerenciar_avisos'))

@bp.route('/aluno/<int:aluno_id>/enviar-qrcode', methods=['POST'])
@login_required
def enviar_qrcode(aluno_id):
    aluno = Membro.query.get_or_404(aluno_id)

    # Gera a imagem do QR Code em memória (mesma lógica da outra rota)
    qr_data = url_for('main.api_checkin', aluno_id=aluno.id, _external=True)
    qr_img = qrcode.make(qr_data)
    buf = io.BytesIO()
    qr_img.save(buf)
    buf.seek(0)

    # Cria e envia o e-mail
    try:
        msg = Message(
            subject='Seu Acesso GymFlow',
            sender=('GymFlow', current_app.config['MAIL_USERNAME']),
            recipients=[aluno.email]
        )
        msg.body = f'Olá, {aluno.nome}! Use o QR Code em anexo para fazer seu check-in na academia.'
        # Anexa a imagem do QR Code gerada em memória
        msg.attach('qrcode.png', 'image/png', buf.read())

        mail.send(msg)
        flash(f'QR Code enviado com sucesso para o e-mail {aluno.email}!', 'success')
    except Exception as e:
        flash(f'Erro ao enviar e-mail: {e}', 'danger')

    return redirect(url_for('main.aluno_detalhe', aluno_id=aluno.id))