# backend/main.py

import os
import uuid
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import pandas as pd
import io
import numpy as np

from app.data_loader import load_dataframe_from_file
from app.query_engine import query_dataframe
from app.db_connector import get_sqlite_engine, get_db_tables_and_preview, create_sql_query_engine, query_database_engine
# from app.pdf_generator import generate_report_pdf # Importar quando for criado

# Carregar variáveis de ambiente
load_dotenv()

# Adicionando prefixo /api para todos os endpoints do backend
app = FastAPI(title="API de Análise de Dados com IA", prefix="/api")

# Configuração do CORS
origins = [
    "https://5173-ig5pxrzl6nxv1q1c07urp-bc096365.manusvm.computer",
    "https://5180-ig5pxrzl6nxv1q1c07urp-bc096365.manusvm.computer",
    "http://localhost:5173",
    "http://localhost:5180"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Gerenciamento de Estado Simples (In-Memory) ---
# ATENÇÃO: Esta abordagem em memória não é adequada para produção.
# Sessões serão perdidas se o servidor reiniciar.
# Considere Redis, um banco de dados, ou outra solução persistente.
data_sessions = {}

class SessionManager:
    def __init__(self):
        self.sessions = {}

    def create_dataframe_session(self, df: pd.DataFrame, filename: str):
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            "type": "dataframe",
            "dataframe": df,
            "filename": filename,
            "history": [],
            "query_engine": None # Query engine será criado sob demanda
        }
        print(f"Sessão DataFrame {session_id} criada para {filename}")
        return session_id

    def create_db_session(self, engine, db_path: str, tables: list[str]):
        session_id = str(uuid.uuid4())
        # Não armazenamos a engine diretamente por segurança/serialização
        # Armazenamos o necessário para recriar a engine ou o query_engine
        self.sessions[session_id] = {
            "type": "database",
            "db_path": db_path, # Ou connection string
            "tables": tables,
            "engine_instance": engine, # Guardar a instância para reutilização na sessão
            "query_engine": None, # Será criado sob demanda
            "history": []
        }
        print(f"Sessão DB {session_id} criada para {db_path} (tabelas: {tables})")
        return session_id

    def get_session_data(self, session_id: str):
        if session_id not in self.sessions:
            print(f"Tentativa de acesso à sessão inexistente: {session_id}")
            raise HTTPException(status_code=404, detail="Sessão não encontrada ou expirada.")
        return self.sessions[session_id]

    def get_query_engine(self, session_id: str):
        session_data = self.get_session_data(session_id)
        
        if session_data.get("query_engine") is None:
            print(f"Criando query engine para sessão {session_id}...")
            if session_data["type"] == "dataframe":
                # Cria engine para DataFrame sob demanda
                # Note: PandasQueryEngine não precisa ser armazenado, pode ser criado a cada query
                # Mas para consistência, vamos seguir o padrão
                pass # Não há engine persistente para PandasQueryEngine
            elif session_data["type"] == "database":
                # Cria engine SQL sob demanda
                session_data["query_engine"] = create_sql_query_engine(
                    session_data["engine_instance"],
                    session_data["tables"]
                )
            else:
                 raise HTTPException(status_code=500, detail="Tipo de sessão desconhecido.")
        
        return session_data.get("query_engine") # Retorna None para dataframe

    def add_history(self, session_id: str, question: str, answer: str, code: str):
        session_data = self.get_session_data(session_id)
        session_data["history"].append({
            "id": str(uuid.uuid4()),
            "question": question,
            "answer": answer,
            "code": code
        })
        print(f"Histórico adicionado à sessão {session_id}: Q: {question[:50]}...")

session_manager = SessionManager()

# --- Modelos Pydantic ---
class QueryRequest(BaseModel):
    session_id: str
    question: str

class PdfRequest(BaseModel):
    session_id: str
    interaction_ids: list[str]

class DBConnectionRequest(BaseModel):
    db_path: str = Field(..., description="Caminho para o arquivo do banco de dados SQLite.")
    # Adicionar campos para outros tipos de BD (host, port, user, password, db_name) depois

# --- Endpoints ---

@app.post("/upload", summary="Upload de arquivo de dados (CSV, Excel, JSON, Parquet)")
async def upload_data_file(file: UploadFile = File(...) ):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nome do arquivo não fornecido.")
    print(f"Recebendo upload do arquivo: {file.filename}")
    try:
        df = await load_dataframe_from_file(file)
        session_id = session_manager.create_dataframe_session(df, file.filename)
        
        # Obter preview e tratar valores não finitos explicitamente
        preview_data_raw = df.head().to_dict(orient='records')
        
        # Limpar dados de preview para garantir compatibilidade com JSON
        preview_data_cleaned = []
        for row in preview_data_raw:
            cleaned_row = {}
            for key, value in row.items():
                if isinstance(value, float) and (np.isnan(value) or np.isinf(value)):
                    cleaned_row[key] = None
                else:
                    cleaned_row[key] = value
            preview_data_cleaned.append(cleaned_row)

        columns = list(df.columns)
        print(f"Arquivo {file.filename} carregado. Session ID: {session_id}")
        return {
            "message": "Arquivo carregado com sucesso!",
            "session_id": session_id,
            "filename": file.filename,
            "columns": columns,
            "preview": preview_data_cleaned, # Usar dados limpos
            "data_type": "dataframe"
        }
    except ValueError as e:
        print(f"Erro de valor durante o upload: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Erro inesperado no upload: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno ao processar o arquivo: {e}")

@app.post("/connect_db", summary="Conecta a um banco de dados SQLite")
async def connect_database(request: DBConnectionRequest):
    print(f"Tentando conectar ao BD SQLite em: {request.db_path}")
    # Simplificado para SQLite por enquanto
    # Validação básica do caminho (existe?)
    if not os.path.exists(request.db_path) or not os.path.isfile(request.db_path):
         raise HTTPException(status_code=400, detail=f"Arquivo do banco de dados não encontrado em: {request.db_path}")
    try:
        engine = get_sqlite_engine(request.db_path)
        table_names, previews = get_db_tables_and_preview(engine)
        
        if not table_names:
            raise HTTPException(status_code=400, detail="Nenhuma tabela encontrada no banco de dados.")
            
        # Iniciar sessão com todas as tabelas por padrão
        session_id = session_manager.create_db_session(engine, request.db_path, table_names)
        print(f"Conexão com BD {request.db_path} estabelecida. Session ID: {session_id}")
        return {
            "message": "Conexão com banco de dados estabelecida com sucesso!",
            "session_id": session_id,
            "db_path": request.db_path,
            "tables": table_names,
            "previews": previews, # Dicionário com preview de cada tabela
            "data_type": "database"
        }
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        print(f"Erro inesperado ao conectar ao BD: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno ao conectar ao banco de dados: {e}")

@app.post("/query", summary="Executa uma pergunta sobre os dados carregados (DataFrame ou DB)")
async def execute_query(request: QueryRequest):
    print(f"Recebida query para sessão {request.session_id}: {request.question[:50]}...")
    try:
        session_data = session_manager.get_session_data(request.session_id)
        answer = None
        generated_code = None

        if session_data["type"] == "dataframe":
            df = session_data["dataframe"]
            # PandasQueryEngine é criado a cada chamada aqui
            answer, generated_code = query_dataframe(df, request.question)
        elif session_data["type"] == "database":
            # Obtém ou cria o query engine SQL para a sessão
            sql_query_engine = session_manager.get_query_engine(request.session_id)
            if sql_query_engine is None: # Deve ter sido criado no get_query_engine
                 raise HTTPException(status_code=500, detail="Falha ao obter o motor de consulta SQL.")
            answer, generated_code = query_database_engine(sql_query_engine, request.question)
        else:
             raise HTTPException(status_code=400, detail="Tipo de sessão inválida para consulta.")

        # Adicionar ao histórico
        session_manager.add_history(request.session_id, request.question, answer, generated_code)
        print(f"Consulta para sessão {request.session_id} respondida.")
        return {"answer": answer, "generated_code": generated_code}

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        print(f"Erro inesperado durante a consulta na sessão {request.session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno ao processar a consulta: {e}")

# --- Endpoint de Geração de PDF (a implementar) ---

@app.post("/generate_pdf", summary="Gera um relatório PDF com interações selecionadas")
async def generate_pdf_report(request: PdfRequest):
    try:
        from app.pdf_generator import generate_report_pdf
        
        session_data = session_manager.get_session_data(request.session_id)
        history = session_data["history"]
        selected_interactions = [item for item in history if item["id"] in request.interaction_ids]
        
        if not selected_interactions:
             raise HTTPException(status_code=400, detail="Nenhuma interação válida selecionada para o relatório.")

        # Definir o nome do arquivo baseado na origem dos dados
        source_name = session_data.get("filename") or session_data.get("db_path", "Dados")
        pdf_content = generate_report_pdf(selected_interactions, source_name)
        
        return StreamingResponse(io.BytesIO(pdf_content),
                               media_type="application/pdf",
                               headers={"Content-Disposition": f"attachment; filename=relatorio_analise_{session_data['type']}.pdf"})
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        print(f"Erro ao gerar PDF para sessão {request.session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno ao gerar o relatório PDF: {e}")

@app.get("/", summary="Endpoint raiz")
async def read_root():
    return {"message": "Bem-vindo à API de Análise de Dados com IA"}

# Para executar localmente: uvicorn main:app --reload --host 0.0.0.0 --port 8000

