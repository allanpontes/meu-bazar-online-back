from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.produtos.modelos import Produto
from app.usuarios.modelos import Usuario

router = APIRouter()

@router.get("/resumo")
def obter_metricas_dashboard(db: Session = Depends(get_db)):
    # 1. Volumetria de Clientes/Usuários cadastrados
    total_usuarios = db.query(Usuario).count()
    
    # 2. Volumetria de Estoque total
    total_produtos = db.query(Produto).count()
    
    # 3. Faturamento Total (Soma o preço de tudo o que foi marcado como 'Vendido')
    faturamento = db.query(func.sum(Produto.preco)).filter(Produto.status == "Vendido").scalar() or 0.0
    
    # 4. Contagem por Status para o gráfico do Dashboard
    disponiveis = db.query(Produto).filter(Produto.status == "Disponivel").count()
    reservados = db.query(Produto).filter(Produto.status == "Reservado").count()
    vendidos = db.query(Produto).filter(Produto.status == "Vendido").count()
    
    return {
        "clientes_registrados": total_usuarios,
        "total_itens_historico": total_produtos,
        "faturamento_total_reais": round(faturamento, 2),
        "grafico_status": {
            "disponiveis": disponiveis,
            "reservados": reservados,
            "vendidos": vendidos
        }
    }
