"""
Classificação Orçamentária Routes - Refactored Module
Budget classification codes according to Law 14.133/2021
"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/classificacao", tags=["Classificação Orçamentária"])

# Budget classification codes according to Law 14.133/2021
CLASSIFICACAO_CODIGOS = {
    "339030": {
        "nome": "Material de Consumo",
        "subitens": [
            "Material de Consumo - Combustíveis e Lubrificantes Automotivos",
            "Combustíveis e Lubrificantes de Aviação",
            "Gás Engarrafado",
            "Explosivos e Munições",
            "Alimentos para Animais",
            "Gêneros de Alimentação",
            "Animais para Pesquisa e Abate",
            "Material Farmacológico",
            "Material Odontológico",
            "Material Químico",
            "Material de Coudelaria / Zootécnico",
            "Material de Caça e Pesca",
            "Material Educativo e Esportivo",
            "Material para Festividades e Homenagens",
            "Material de Expediente",
            "Material de Processamento de Dados",
            "Material de Acondicionamento e Embalagem",
            "Material de Cama, Mesa e Banho",
            "Material de Copa e Cozinha",
            "Material de Limpeza e Higienização",
            "Uniformes, Tecidos e Aviamentos",
            "Material para Manutenção de Bens Imóveis",
            "Material para Manutenção de Bens Móveis",
            "Material Elétrico e Eletrônico",
            "Material de Proteção e Segurança",
            "Material para Áudio, Vídeo e Foto",
            "Sementes, Mudas e Insumos",
            "Material Hospitalar",
            "Material para Manutenção de Veículos",
            "Ferramentas",
            "Material de Sinalização Visual"
        ]
    },
    "339036": {
        "nome": "Outros Serviços de Terceiros (Pessoa Física)",
        "subitens": [
            "Diárias a Colaboradores Eventuais",
            "Serviços Técnicos Profissionais",
            "Estagiários",
            "Locação de Imóveis",
            "Locação de Bens Móveis",
            "Manutenção e Conservação de Equipamentos",
            "Manutenção e Conservação de Veículos",
            "Manutenção e Conservação de Imóveis",
            "Serviços de Limpeza e Conservação",
            "Serviços Médicos e Odontológicos",
            "Serviços de Apoio Administrativo/Técnico",
            "Confecção de Uniformes/Bandeiras",
            "Fretes e Transportes de Encomendas",
            "Jetons"
        ]
    },
    "339039": {
        "nome": "Outros Serviços de Terceiros (Pessoa Jurídica)",
        "subitens": [
            "Assinaturas de Periódicos",
            "Condomínios",
            "Serviços Técnicos Profissionais",
            "Manutenção de Software",
            "Locação de Imóveis",
            "Locação de Máquinas e Equipamentos",
            "Manutenção e Conservação de Imóveis",
            "Manutenção e Conservação de Máquinas",
            "Manutenção e Conservação de Veículos",
            "Exposições, Congressos e Festividades",
            "Serviços de Energia Elétrica",
            "Serviços de Água e Esgoto",
            "Serviços de Telecomunicações",
            "Serviços Gráficos",
            "Seguros em Geral",
            "Confecção de Uniformes e Bandeiras",
            "Vale-Transporte",
            "Vigilância Ostensiva",
            "Limpeza e Conservação",
            "Serviços Bancários",
            "Serviços de Cópias e Reprodução",
            "Publicidade e Propaganda"
        ]
    },
    "449052": {
        "nome": "Equipamentos e Material Permanente",
        "subitens": [
            "Aparelhos de Medição e Orientação",
            "Aparelhos e Equipamentos de Comunicação",
            "Equipamentos Médico-Hospitalares",
            "Aparelhos e Utensílios Domésticos",
            "Coleções e Materiais Bibliográficos",
            "Mobiliário em Geral",
            "Equipamentos de Processamento de Dados",
            "Máquinas e Utensílios de Escritório",
            "Máquinas, Ferramentas e Utensílios de Oficina",
            "Equipamentos Hidráulicos e Elétricos",
            "Máquinas Agrícolas e Rodoviárias",
            "Veículos de Tração Mecânica",
            "Veículos Diversos",
            "Acessórios para Automóveis"
        ]
    }
}

@router.get("/codigos")
async def get_classificacao_codigos():
    """
    Returns all budget classification codes according to Law 14.133/2021
    """
    return CLASSIFICACAO_CODIGOS
