# backend/app/query_engine.py

import os
import pandas as pd
from llama_index.experimental.query_engine import PandasQueryEngine
from llama_index.llms.openai import OpenAI
from llama_index.core import Settings
from fastapi import HTTPException

def query_dataframe(df: pd.DataFrame, question: str):
    """
    Executa uma consulta em linguagem natural sobre um DataFrame Pandas 
    usando LlamaIndex e OpenAI.

    Args:
        df (pd.DataFrame): O DataFrame a ser consultado.
        question (str): A pergunta do usuário em linguagem natural.

    Returns:
        tuple: Contendo a resposta (str) e o código gerado (str, pode ser None).
               Retorna (None, None) se o LLM não estiver configurado.
    
    Raises:
        HTTPException: Se ocorrer um erro durante a consulta.
    """
    # Obter a chave da API e inicializar o LLM dentro da função
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("AVISO: Chave da API OpenAI não encontrada nas variáveis de ambiente.")
        raise HTTPException(status_code=500, detail="LLM não configurado. Verifique a chave da API OpenAI.")

    try:
        llm = OpenAI(model="gpt-4o", api_key=api_key)
        # Settings.llm = llm # Configuração global (opcional)
    except Exception as e:
        print(f"Erro ao inicializar OpenAI LLM: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao inicializar LLM: {e}")

    if df is None or df.empty:
        raise HTTPException(status_code=400, detail="Nenhum dado carregado para consulta.")

    try:
        # Usar Settings.llm ou passar llm diretamente
        query_engine = PandasQueryEngine(df=df, llm=llm, verbose=True)
        response = query_engine.query(question)
        
        # A resposta geralmente contém a resposta em linguagem natural.
        # O código gerado (Pandas) pode estar nos metadados, dependendo da versão/config.
        # Vamos assumir que response.response é a resposta textual
        # e response.metadata['pandas_instruction_str'] contém o código (verificar documentação LlamaIndex)
        answer = str(response.response) if response.response else "Não foi possível obter uma resposta."
        
        generated_code = None
        if response.metadata and 'pandas_instruction_str' in response.metadata:
             generated_code = response.metadata['pandas_instruction_str']
        elif response.metadata and 'code' in response.metadata: # Tentativa alternativa
             generated_code = response.metadata['code']

        return answer, generated_code

    except Exception as e:
        print(f"Erro ao executar a consulta com LlamaIndex: {e}")
        # Tentar fornecer uma mensagem de erro mais específica se possível
        error_detail = f"Erro ao processar a consulta: {e}"
        if "AuthenticationError" in str(e):
             error_detail = "Erro de autenticação com a API OpenAI. Verifique sua chave."
        elif "RateLimitError" in str(e):
             error_detail = "Limite de taxa da API OpenAI atingido. Tente novamente mais tarde."
        
        raise HTTPException(status_code=500, detail=error_detail)

