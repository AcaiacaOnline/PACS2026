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
    
    async def safe_create_index(collection, *args, **kwargs):
        """Cria índice de forma segura, ignorando erros de duplicata"""
        try:
            await collection.create_index(*args, **kwargs)
            return True
        except Exception as e:
            if "duplicate" in str(e).lower() or "11000" in str(e):
                print(f"    ⚠️ Índice já existe ou há duplicatas em {collection.name}")
            else:
                print(f"    ❌ Erro: {e}")
            return False
    
    # ==================== USERS ====================
    print("  → Índices de users...")
    await safe_create_index(db.users, "user_id", unique=True)
    await safe_create_index(db.users, "email", unique=True)
    await safe_create_index(db.users, "cpf", unique=True, sparse=True)
    await safe_create_index(db.users, "is_active")
    await safe_create_index(db.users, "is_admin")
    await safe_create_index(db.users, "secretaria")
    
    # ==================== PACs ====================
    print("  → Índices de PACs...")
    await safe_create_index(db.pacs, "pac_id", unique=True)
    await safe_create_index(db.pacs, "ano")
    await safe_create_index(db.pacs, "secretaria")
    await safe_create_index(db.pacs, "status")
    await safe_create_index(db.pacs, [("ano", -1), ("secretaria", 1)])
    await safe_create_index(db.pacs, "created_by")
    
    await safe_create_index(db.pac_items, "item_id", unique=True)
    await safe_create_index(db.pac_items, "pac_id")
    await safe_create_index(db.pac_items, "status")
    await safe_create_index(db.pac_items, [("pac_id", 1), ("status", 1)])
    
    # ==================== PAC Geral ====================
    print("  → Índices de PAC Geral...")
    await safe_create_index(db.pacs_geral, "pac_id", unique=True)
    await safe_create_index(db.pacs_geral, "ano")
    await safe_create_index(db.pacs_geral, "status")
    await safe_create_index(db.pacs_geral, [("ano", -1), ("status", 1)])
    
    await safe_create_index(db.pac_geral_items, "item_id", unique=True)
    await safe_create_index(db.pac_geral_items, "pac_id")
    await safe_create_index(db.pac_geral_items, "classificacao_item")
    await safe_create_index(db.pac_geral_items, [("pac_id", 1), ("classificacao_item", 1)])
    
    # ==================== PAC Obras ====================
    print("  → Índices de PAC Obras...")
    await safe_create_index(db.pacs_geral_obras, "pac_id", unique=True)
    await safe_create_index(db.pacs_geral_obras, "ano")
    await safe_create_index(db.pacs_geral_obras, "status")
    await safe_create_index(db.pacs_geral_obras, [("ano", -1), ("status", 1)])
    
    await safe_create_index(db.pac_geral_obras_items, "item_id", unique=True)
    await safe_create_index(db.pac_geral_obras_items, "pac_id")
    await safe_create_index(db.pac_geral_obras_items, "classificacao_obras")
    
    # ==================== Processos ====================
    print("  → Índices de Processos...")
    await safe_create_index(db.processos, "processo_id", unique=True)
    await safe_create_index(db.processos, "numero_processo")
    await safe_create_index(db.processos, "ano")
    await safe_create_index(db.processos, "status")
    await safe_create_index(db.processos, "modalidade_contratacao")
    await safe_create_index(db.processos, "secretaria")
    await safe_create_index(db.processos, "created_by")
    await safe_create_index(db.processos, [("ano", -1), ("status", 1)])
    await safe_create_index(db.processos, [("ano", -1), ("modalidade_contratacao", 1)])
    await safe_create_index(db.processos, [("ano", -1), ("secretaria", 1)])
    # Índice de texto para busca
    try:
        await db.processos.create_index([
            ("numero_processo", "text"),
            ("objeto", "text"),
            ("fornecedor", "text")
        ])
    except Exception as e:
        print(f"    ⚠️ Índice de texto em processos: {e}")
    
    # ==================== MROSC ====================
    print("  → Índices de MROSC...")
    await safe_create_index(db.mrosc_projetos, "projeto_id", unique=True)
    await safe_create_index(db.mrosc_projetos, "status")
    await safe_create_index(db.mrosc_projetos, "created_by")
    await safe_create_index(db.mrosc_projetos, "cnpj_osc")
    await safe_create_index(db.mrosc_projetos, [("status", 1), ("created_at", -1)])
    
    await safe_create_index(db.mrosc_rh, "rh_id", unique=True)
    await safe_create_index(db.mrosc_rh, "projeto_id")
    
    await safe_create_index(db.mrosc_despesas, "despesa_id", unique=True)
    await safe_create_index(db.mrosc_despesas, "projeto_id")
    await safe_create_index(db.mrosc_despesas, "natureza")
    
    await safe_create_index(db.mrosc_documentos, "documento_id", unique=True)
    await safe_create_index(db.mrosc_documentos, "projeto_id")
    await safe_create_index(db.mrosc_documentos, "tipo")
    
    # ==================== Assinaturas ====================
    print("  → Índices de Assinaturas...")
    await safe_create_index(db.document_signatures, "signature_id", unique=True)
    await safe_create_index(db.document_signatures, "validation_code", unique=True)
    await safe_create_index(db.document_signatures, "document_type")
    await safe_create_index(db.document_signatures, "created_at")
    await safe_create_index(db.document_signatures, "signers.email")
    await safe_create_index(db.document_signatures, [("document_type", 1), ("created_at", -1)])
    
    # ==================== Sessions ====================
    print("  → Índices de Sessions...")
    await safe_create_index(db.user_sessions, "session_id", unique=True)
    await safe_create_index(db.user_sessions, "user_id")
    try:
        await db.user_sessions.create_index("expires_at", expireAfterSeconds=0)  # TTL index
    except Exception as e:
        print(f"    ⚠️ TTL index em sessions: {e}")
    
    # ==================== Analytics ====================
    print("  → Índices de Analytics...")
    await safe_create_index(db.analytics_events, "event_id", unique=True)
    await safe_create_index(db.analytics_events, "event_type")
    await safe_create_index(db.analytics_events, "timestamp")
    await safe_create_index(db.analytics_events, "user_id")
    await safe_create_index(db.analytics_events, [("event_type", 1), ("timestamp", -1)])
    
    # ==================== System Config ====================
    print("  → Índices de Configuração...")
    await safe_create_index(db.system_config, "config_id", unique=True)
    
    client.close()
    print("✅ Processo de criação de índices finalizado!")


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
