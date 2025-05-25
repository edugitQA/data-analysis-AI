# backend/app/db_connector.py

import os
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import SQLAlchemyError
from llama_index.core import SQLDatabase
from llama_index.llms.openai import OpenAI
from llama_index.core.indices.struct_store import NLSQLTableQueryEngine
from fastapi import HTTPException
import pandas as pd
from typing import Optional, List

# Reutilizar LLM configurado (ou configurar aqui se necessário)
api_key = os.getenv("OPENAI_API_KEY")
llm = None
if api_key:
    try:
        llm = OpenAI(model="gpt-3.5-turbo", api_key=api_key)
    except Exception as e:
        print(f"Erro ao inicializar OpenAI LLM em db_connector: {e}")
else:
    print("AVISO: Chave da API OpenAI não encontrada em db_connector.")

def get_sqlite_engine(db_path: str):
    """Cria uma engine SQLAlchemy para um banco de dados SQLite."""
    try:
        # 'check_same_thread=False' é importante para FastAPI/SQLite
        engine = create_engine(f"sqlite:///{db_path}?check_same_thread=False")
        # Testar conexão
        with engine.connect() as connection:
            print(f"Conexão com SQLite DB em {db_path} bem-sucedida.")
        return engine
    except SQLAlchemyError as e:
        print(f"Erro ao conectar ao banco de dados SQLite em {db_path}: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao conectar ao banco de dados SQLite: {e}")
    except Exception as e:
        print(f"Erro inesperado ao criar engine SQLite: {e}")
        raise HTTPException(status_code=500, detail=f"Erro inesperado ao configurar conexão com banco de dados: {e}")

def get_db_tables_and_preview(engine):
    """Obtém nomes das tabelas e preview das primeiras linhas de cada uma."""
    try:
        inspector = inspect(engine)
        table_names = inspector.get_table_names()
        previews = {}
        with engine.connect() as connection:
            for table in table_names:
                # Usar text() para consultas SQL seguras
                query = text(f'SELECT * FROM "{table}" LIMIT 5')
                try:
                    preview_df = pd.read_sql_query(query, connection)
                    previews[table] = {
                        "columns": list(preview_df.columns),
                        "data": preview_df.to_dict(orient='records')
                    }
                except Exception as e:
                    print(f"Erro ao obter preview da tabela {table}: {e}")
                    previews[table] = {"error": f"Não foi possível obter preview: {e}"}
        return table_names, previews
    except SQLAlchemyError as e:
        print(f"Erro ao inspecionar o banco de dados: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao ler metadados do banco de dados: {e}")

def create_sql_query_engine(engine, tables: Optional[List[str]] = None):
    """Cria um query engine LlamaIndex para um banco de dados SQL."""
    if llm is None:
        raise HTTPException(status_code=500, detail="LLM não configurado para consulta SQL.")
    try:
        sql_database = SQLDatabase(engine, include_tables=tables)
        # NLSQLTableQueryEngine é adequado para perguntas sobre tabelas específicas
        query_engine = NLSQLTableQueryEngine(
            sql_database=sql_database,
            tables=tables, # Especificar tabelas melhora o desempenho/precisão
            llm=llm,
            verbose=True
        )
        return query_engine
    except Exception as e:
        print(f"Erro ao criar SQL query engine: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao inicializar o motor de consulta SQL: {e}")

def query_database_engine(query_engine: NLSQLTableQueryEngine, question: str):
    """
    Executa uma consulta em linguagem natural usando um NLSQLTableQueryEngine.
    """
    try:
        response = query_engine.query(question)
        answer = str(response.response) if response.response else "Não foi possível obter uma resposta."
        
        generated_sql = None
        if response.metadata and 'sql_query' in response.metadata:
            generated_sql = response.metadata['sql_query']
        elif response.metadata and 'code' in response.metadata: # Tentativa alternativa
             generated_sql = response.metadata['code']

        return answer, generated_sql
    except Exception as e:
        print(f"Erro ao executar a consulta SQL com LlamaIndex: {e}")
        error_detail = f"Erro ao processar a consulta SQL: {e}"
        if "AuthenticationError" in str(e):
             error_detail = "Erro de autenticação com a API OpenAI. Verifique sua chave."
        elif "RateLimitError" in str(e):
             error_detail = "Limite de taxa da API OpenAI atingido. Tente novamente mais tarde."
        raise HTTPException(status_code=500, detail=error_detail)

