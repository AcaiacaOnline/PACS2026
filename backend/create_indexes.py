"""
MongoDB Index Configuration
Planejamento Acaiaca - Otimização de Performance

Este módulo cria índices otimizados para melhorar a performance das queries.
Execute uma vez após a instalação ou quando adicionar novas coleções.
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'planejamento_acaiaca')


async def create_indexes():
    """Cria todos os índices necessários para otimização"""
    
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    print("🔧 Criando índices do MongoDB...")
    
    # ==================== USERS ====================
    print("  → Índices de users...")
    await db.users.create_index("user_id", unique=True)
    try:
        await db.users.create_index("email", unique=True)
    except Exception as e:
        print(f"    ⚠️ Índice email já existe ou há duplicatas: {e}")
    try:
        await db.users.create_index("cpf", unique=True, sparse=True)
    except Exception as e:
        print(f"    ⚠️ Índice cpf: {e}")
    await db.users.create_index("is_active")
    await db.users.create_index("is_admin")
    await db.users.create_index("secretaria")
    
    # ==================== PACs ====================
    print("  → Índices de PACs...")
    await db.pacs.create_index("pac_id", unique=True)
    await db.pacs.create_index("ano")
    await db.pacs.create_index("secretaria")
    await db.pacs.create_index("status")
    await db.pacs.create_index([("ano", -1), ("secretaria", 1)])
    await db.pacs.create_index("created_by")
    
    await db.pac_items.create_index("item_id", unique=True)
    await db.pac_items.create_index("pac_id")
    await db.pac_items.create_index("status")
    await db.pac_items.create_index([("pac_id", 1), ("status", 1)])
    
    # ==================== PAC Geral ====================
    print("  → Índices de PAC Geral...")
    await db.pacs_geral.create_index("pac_id", unique=True)
    await db.pacs_geral.create_index("ano")
    await db.pacs_geral.create_index("status")
    await db.pacs_geral.create_index([("ano", -1), ("status", 1)])
    
    await db.pac_geral_items.create_index("item_id", unique=True)
    await db.pac_geral_items.create_index("pac_id")
    await db.pac_geral_items.create_index("classificacao_item")
    await db.pac_geral_items.create_index([("pac_id", 1), ("classificacao_item", 1)])
    
    # ==================== PAC Obras ====================
    print("  → Índices de PAC Obras...")
    await db.pacs_geral_obras.create_index("pac_id", unique=True)
    await db.pacs_geral_obras.create_index("ano")
    await db.pacs_geral_obras.create_index("status")
    await db.pacs_geral_obras.create_index([("ano", -1), ("status", 1)])
    
    await db.pac_geral_obras_items.create_index("item_id", unique=True)
    await db.pac_geral_obras_items.create_index("pac_id")
    await db.pac_geral_obras_items.create_index("classificacao_obras")
    
    # ==================== Processos ====================
    print("  → Índices de Processos...")
    await db.processos.create_index("processo_id", unique=True)
    await db.processos.create_index("numero_processo")
    await db.processos.create_index("ano")
    await db.processos.create_index("status")
    await db.processos.create_index("modalidade_contratacao")
    await db.processos.create_index("secretaria")
    await db.processos.create_index("created_by")
    await db.processos.create_index([("ano", -1), ("status", 1)])
    await db.processos.create_index([("ano", -1), ("modalidade_contratacao", 1)])
    await db.processos.create_index([("ano", -1), ("secretaria", 1)])
    # Índice de texto para busca
    await db.processos.create_index([
        ("numero_processo", "text"),
        ("objeto", "text"),
        ("fornecedor", "text")
    ])
    
    # ==================== MROSC ====================
    print("  → Índices de MROSC...")
    await db.mrosc_projetos.create_index("projeto_id", unique=True)
    await db.mrosc_projetos.create_index("status")
    await db.mrosc_projetos.create_index("created_by")
    await db.mrosc_projetos.create_index("cnpj_osc")
    await db.mrosc_projetos.create_index([("status", 1), ("created_at", -1)])
    
    await db.mrosc_rh.create_index("rh_id", unique=True)
    await db.mrosc_rh.create_index("projeto_id")
    
    await db.mrosc_despesas.create_index("despesa_id", unique=True)
    await db.mrosc_despesas.create_index("projeto_id")
    await db.mrosc_despesas.create_index("natureza")
    
    await db.mrosc_documentos.create_index("documento_id", unique=True)
    await db.mrosc_documentos.create_index("projeto_id")
    await db.mrosc_documentos.create_index("tipo")
    
    # ==================== Assinaturas ====================
    print("  → Índices de Assinaturas...")
    await db.document_signatures.create_index("signature_id", unique=True)
    await db.document_signatures.create_index("validation_code", unique=True)
    await db.document_signatures.create_index("document_type")
    await db.document_signatures.create_index("created_at")
    await db.document_signatures.create_index("signers.email")
    await db.document_signatures.create_index([("document_type", 1), ("created_at", -1)])
    
    # ==================== Sessions ====================
    print("  → Índices de Sessions...")
    await db.user_sessions.create_index("session_id", unique=True)
    await db.user_sessions.create_index("user_id")
    await db.user_sessions.create_index("expires_at", expireAfterSeconds=0)  # TTL index
    
    # ==================== Analytics ====================
    print("  → Índices de Analytics...")
    await db.analytics_events.create_index("event_id", unique=True)
    await db.analytics_events.create_index("event_type")
    await db.analytics_events.create_index("timestamp")
    await db.analytics_events.create_index("user_id")
    await db.analytics_events.create_index([("event_type", 1), ("timestamp", -1)])
    
    # ==================== System Config ====================
    print("  → Índices de Configuração...")
    await db.system_config.create_index("config_id", unique=True)
    
    client.close()
    print("✅ Todos os índices foram criados com sucesso!")


async def drop_all_indexes():
    """Remove todos os índices (exceto _id)"""
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    collections = await db.list_collection_names()
    for collection_name in collections:
        collection = db[collection_name]
        await collection.drop_indexes()
        print(f"  → Índices removidos de {collection_name}")
    
    client.close()
    print("✅ Todos os índices foram removidos!")


async def show_indexes():
    """Lista todos os índices existentes"""
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    collections = await db.list_collection_names()
    for collection_name in collections:
        collection = db[collection_name]
        indexes = await collection.index_information()
        print(f"\n📋 {collection_name}:")
        for name, info in indexes.items():
            print(f"   - {name}: {info.get('key')}")
    
    client.close()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "drop":
            asyncio.run(drop_all_indexes())
        elif sys.argv[1] == "show":
            asyncio.run(show_indexes())
        else:
            print("Uso: python create_indexes.py [drop|show]")
    else:
        asyncio.run(create_indexes())
