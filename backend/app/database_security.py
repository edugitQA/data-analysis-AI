# backend/app/database_security.py

import os
import sqlite3
from typing import Optional, List, Dict, Any
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SecureDatabaseConnector:
    """Conector seguro para bancos de dados com proteções contra SQL injection"""
    
    def __init__(self):
        self.max_rows_preview = 100
        self.allowed_operations = ['SELECT']
        self.blocked_keywords = [
            'DROP', 'DELETE', 'INSERT', 'UPDATE', 'ALTER', 'CREATE',
            'TRUNCATE', 'EXEC', 'EXECUTE', 'GRANT', 'REVOKE'
        ]
    
    def create_secure_sqlite_connection(self, db_path: str):
        """Cria conexão segura com SQLite"""
        try:
            # Validar caminho
            if not os.path.exists(db_path):
                raise HTTPException(
                    status_code=404,
                    detail="Arquivo de banco de dados não encontrado"
                )
            
            # Criar engine com configurações de segurança
            engine = create_engine(
                f"sqlite:///{db_path}",
                connect_args={
                    "check_same_thread": False,
                    "timeout": 30,  # Timeout de 30 segundos
                },
                pool_pre_ping=True,
                pool_recycle=3600,  # Reciclar conexões a cada hora
                echo=False  # Não logar SQL em produção
            )
            
            # Testar conexão
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            logger.info(f"Conexão segura estabelecida com {db_path}")
            return engine
            
        except SQLAlchemyError as e:
            logger.error(f"Erro ao conectar ao banco: {e}")
            raise HTTPException(
                status_code=500,
                detail="Erro ao conectar ao banco de dados"
            )
    
    def validate_sql_query(self, query: str) -> str:
        """Valida e sanitiza consulta SQL"""
        query = query.strip()
        
        # Verificar se é uma consulta SELECT
        if not query.upper().startswith('SELECT'):
            raise HTTPException(
                status_code=400,
                detail="Apenas consultas SELECT são permitidas"
            )
        
        # Verificar palavras-chave bloqueadas
        query_upper = query.upper()
        for keyword in self.blocked_keywords:
            if keyword in query_upper:
                raise HTTPException(
                    status_code=400,
                    detail=f"Operação SQL não permitida: {keyword}"
                )
        
        # Limitar número de resultados
        if 'LIMIT' not in query_upper:
            query += f" LIMIT {self.max_rows_preview}"
        
        return query
    
    def execute_safe_query(self, engine, query: str) -> List[Dict[str, Any]]:
        """Executa consulta de forma segura"""
        try:
            # Validar consulta
            safe_query = self.validate_sql_query(query)
            
            # Executar com timeout
            with engine.connect() as conn:
                result = conn.execute(text(safe_query))
                
                # Converter para lista de dicionários
                columns = result.keys()
                rows = []
                for row in result.fetchall():
                    row_dict = {}
                    for i, value in enumerate(row):
                        # Tratar valores None e tipos especiais
                        if value is None:
                            row_dict[columns[i]] = None
                        elif isinstance(value, (int, float, str, bool)):
                            row_dict[columns[i]] = value
                        else:
                            row_dict[columns[i]] = str(value)
                    rows.append(row_dict)
                
                logger.info(f"Consulta executada com sucesso: {len(rows)} linhas retornadas")
                return rows
                
        except SQLAlchemyError as e:
            logger.error(f"Erro na execução da consulta: {e}")
            raise HTTPException(
                status_code=500,
                detail="Erro ao executar consulta no banco de dados"
            )
    
    def get_table_schema(self, engine, table_name: str) -> Dict[str, Any]:
        """Obtém schema de uma tabela de forma segura"""
        try:
            inspector = inspect(engine)
            
            # Verificar se a tabela existe
            if table_name not in inspector.get_table_names():
                raise HTTPException(
                    status_code=404,
                    detail=f"Tabela '{table_name}' não encontrada"
                )
            
            # Obter informações da tabela
            columns = inspector.get_columns(table_name)
            indexes = inspector.get_indexes(table_name)
            
            schema_info = {
                "table_name": table_name,
                "columns": [
                    {
                        "name": col["name"],
                        "type": str(col["type"]),
                        "nullable": col.get("nullable", True),
                        "default": col.get("default")
                    }
                    for col in columns
                ],
                "indexes": [
                    {
                        "name": idx["name"],
                        "columns": idx["column_names"],
                        "unique": idx.get("unique", False)
                    }
                    for idx in indexes
                ]
            }
            
            return schema_info
            
        except SQLAlchemyError as e:
            logger.error(f"Erro ao obter schema da tabela {table_name}: {e}")
            raise HTTPException(
                status_code=500,
                detail="Erro ao obter informações da tabela"
            )
    
    def get_table_preview(self, engine, table_name: str, limit: int = 5) -> Dict[str, Any]:
        """Obtém preview seguro de uma tabela"""
        try:
            # Sanitizar nome da tabela
            if not table_name.replace('_', '').replace('-', '').isalnum():
                raise HTTPException(
                    status_code=400,
                    detail="Nome de tabela inválido"
                )
            
            # Executar consulta segura
            query = f'SELECT * FROM "{table_name}" LIMIT {min(limit, self.max_rows_preview)}'
            rows = self.execute_safe_query(engine, query)
            
            # Obter schema
            schema = self.get_table_schema(engine, table_name)
            
            return {
                "table_name": table_name,
                "schema": schema,
                "preview_data": rows,
                "row_count": len(rows)
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter preview da tabela {table_name}: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao obter preview da tabela {table_name}"
            )

# Instância global do conector seguro
secure_db_connector = SecureDatabaseConnector()

def get_secure_db_connector() -> SecureDatabaseConnector:
    """Dependency para obter o conector seguro"""
    return secure_db_connector

