# fitpro_academia/run.py

from app import create_app, db
from app.models import Membro, Matricula

# Cria a instância da aplicação
app = create_app()

# --- INÍCIO DO NOVO COMANDO CUSTOMIZADO ---
@app.cli.command("limpar-matriculas")
def limpar_matriculas_orfans():
    """Encontra e remove matrículas órfãs do banco de dados."""
    print("--- Iniciando script de limpeza de matrículas órfãs ---")
    try:
        # Pega todos os IDs de Membros válidos
        ids_de_membros_validos = {membro.id for membro in Membro.query.all()}
        print(f"Alunos válidos encontrados: {len(ids_de_membros_validos)}")
        
        # Pega todas as matrículas
        todas_as_matriculas = Matricula.query.all()
        print(f"Verificando {len(todas_as_matriculas)} matrículas...")
        
        # Encontra as órfãs usando list comprehension
        matriculas_para_deletar = [m for m in todas_as_matriculas if m.membro_id not in ids_de_membros_validos]
        
        if not matriculas_para_deletar:
            print("\nBOA NOTÍCIA: Nenhuma matrícula órfã foi encontrada!")
        else:
            print(f"\nEncontradas {len(matriculas_para_deletar)} matrículas órfãs para deletar.")
            for m in matriculas_para_deletar:
                db.session.delete(m)
            
            db.session.commit()
            print("Limpeza concluída com sucesso!")
    except Exception as e:
        print(f"Ocorreu um erro: {e}")
        db.session.rollback()
    
    print("--- Script finalizado ---")
# --- FIM DO NOVO COMANDO CUSTOMIZADO ---


if __name__ == '__main__':
    app.run(debug=True)