# backend/app/query_engine.py

import os
import pandas as pd
import numpy as np
from llama_index.llms.openai import OpenAI
from llama_index.core import Settings
from fastapi import HTTPException
import logging
from typing import Tuple, List, Dict, Any

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ai_responses.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def get_enhanced_llm():
    """Configuração do LLM com parâmetros otimizados"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="LLM não configurado. Verifique a chave da API OpenAI.")
    
    try:
        return OpenAI(
            model="gpt-3.5-turbo",
            api_key=api_key,
            temperature=0.1,
            max_tokens=2000,
            system_prompt="""Você é um assistente especializado em análise de dados que fornece respostas estruturadas e visualmente organizadas.

Para cada resposta, siga este formato:

📊 DADOS ENCONTRADOS:
- Liste cada item relevante em uma nova linha
- Use emojis contextuais para cada tipo de dado:
  💰 para valores monetários
  📈 para métricas/quantidades
  📅 para datas
  🏷️ para categorias/nomes
  📍 para localizações

💡 ANÁLISE:
- Forneça insights sobre os dados encontrados
- Destaque tendências ou padrões importantes
- Use linguagem clara e direta

Lembre-se:
- Mantenha a formatação consistente
- Apresente os números de forma legível
- Evite metadata técnica nas respostas
- Forneça contexto quando relevante
- Use quebras de linha para melhor legibilidade"""
        )
    except Exception as e:
        logger.error(f"Erro ao inicializar OpenAI com configuração principal: {e}")
        try:
            return OpenAI(
                model="gpt-3.5-turbo",
                api_key=api_key,
                temperature=0.3
            )
        except Exception as e:
            logger.error(f"Erro ao inicializar OpenAI com configuração de fallback: {e}")
            raise HTTPException(status_code=500, detail=f"Erro ao inicializar LLM: {e}")

def generate_sql_equivalent(df_operation: str) -> str:
    """Gera consulta SQL equivalente à operação Pandas."""
    if "df[" in df_operation and "'quantidade_vendida'" in df_operation:
        # Extrair condições do código Pandas
        conditions = []
        if ">=" in df_operation:
            conditions.append("quantidade_vendida >= 400")
        if "<=" in df_operation:
            conditions.append("quantidade_vendida <= 500")
            
        selected_columns = ""
        if "['nome_do_produto']" in df_operation:
            selected_columns = "nome_do_produto"
        
        # Construir consulta SQL
        sql = f"""SELECT {selected_columns or '*'}
FROM produtos
WHERE {' AND '.join(conditions)}"""
        
        return sql
    return None

def format_response(response_text: str) -> str:
    """
    Formata a resposta estruturando os dados em um formato limpo e visual.
    """
    if not response_text:
        return "⚠️ Não foi possível obter uma resposta."

    # Limpar a resposta de qualquer metadata do pandas
    cleaned_text = response_text
    if "Name: " in cleaned_text:
        cleaned_text = cleaned_text.split("Name: ")[0]
    if "dtype: " in cleaned_text:
        cleaned_text = cleaned_text.split("dtype: ")[0]
        
    # Extrair e estruturar dados
    structured_data = []
    current_item = {}
    
    # Dividir por linhas e processar cada uma
    lines = cleaned_text.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Remover metadados e índices
        if line.split()[0].isdigit():
            line = ' '.join(line.split()[1:])
        if line.startswith('id_'):
            line = line.replace('id_', '')
            
        # Identificar tipo de informação e adicionar emoji apropriado
        formatted_line = line
        if "nome_do_produto" in line.lower() or "produto" in line.lower():
            if current_item:
                structured_data.append(current_item)
            current_item = {"tipo": "produto", "dados": [f"🏷️ {line}"]}
        elif any(term in line.lower() for term in ['quantidade', 'qtd', 'total']):
            if "dados" not in current_item:
                current_item = {"tipo": "produto", "dados": []}
            current_item["dados"].append(f"📈 {line}")
        elif any(term in line.lower() for term in ['/202', 'data']):
            current_item["dados"].append(f"📅 {line}")
        elif any(term in line.lower() for term in ['valor', 'preço', 'receita', 'r$']):
            current_item["dados"].append(f"💰 {line}")
        else:
            if "dados" not in current_item:
                current_item = {"tipo": "info", "dados": []}
            current_item["dados"].append(f"📊 {line}")
    
    if current_item:
        structured_data.append(current_item)
        
    # Construir resposta formatada
    formatted_lines = ["📊 RESULTADOS DA CONSULTA:"]
    
    for item in structured_data:
        if item["tipo"] == "produto":
            formatted_lines.extend(["\n🎯 ITEM:"] + [f"  {dado}" for dado in item["dados"]])
        else:
            formatted_lines.extend(item["dados"])
            
    formatted_text = "\n".join(formatted_lines)
    
    return "\n".join(formatted_lines)

def query_dataframe(df: pd.DataFrame, question: str):
    """Executa uma consulta em linguagem natural sobre um DataFrame Pandas."""
    if df is None or df.empty:
        raise HTTPException(status_code=400, detail="Nenhum dado carregado para consulta.")

    try:
        # Log do estado dos dados
        logger.info(f"Dados recebidos - Shape: {df.shape}")
        logger.info(f"Colunas: {df.columns.tolist()}")
        logger.info(f"Tipos de dados: {df.dtypes.to_dict()}")
        logger.info(f"Valores nulos por coluna: {df.isnull().sum().to_dict()}")

        llm = get_enhanced_llm()
        
        # Preparar contexto detalhado dos dados
        data_context = {
            "columns": list(df.columns),
            "types": df.dtypes.to_dict(),
            "sample_size": len(df),
            "null_counts": df.isnull().sum().to_dict(),
            "numeric_columns": df.select_dtypes(include=[np.number]).columns.tolist(),
            "categorical_columns": df.select_dtypes(include=['object']).columns.tolist()
        }
        
        # Usar PandasQueryEngine com contexto aprimorado
        from llama_index.experimental.query_engine import PandasQueryEngine
        query_engine = PandasQueryEngine(
            df=df,
            llm=llm,
            verbose=True,
            metadata=data_context
        )
        
        # Executar consulta
        response = query_engine.query(question)
        
        # Processar resposta
        answer = str(response.response) if response.response else "⚠️ Não foi possível obter uma resposta."
        
        # Extrair e formatar o código gerado
        generated_code = None
        sql_equivalent = None
        
        if response.metadata:
            if 'pandas_instruction_str' in response.metadata:
                generated_code = response.metadata['pandas_instruction_str']
                sql_equivalent = generate_sql_equivalent(generated_code)
            elif 'code' in response.metadata:
                generated_code = response.metadata['code']
                sql_equivalent = generate_sql_equivalent(generated_code)
        
        # Log detalhado da resposta bruta
        logger.info("=== RESPOSTA BRUTA DA IA ===")
        logger.info(f"Pergunta: {question}")
        logger.info(f"Resposta: {answer}")
        
        # Formatar a resposta principal
        formatted_answer = format_response(answer)
        
        # Adicionar bordas decorativas mais leves
        border_top = "╭" + "─" * 58 + "╮"
        border_bottom = "╰" + "─" * 58 + "╯"
        
        # Formatar cada linha com borda lateral
        formatted_lines = []
        for line in formatted_answer.split("\n"):
            if line.strip():
                formatted_lines.append(f"│ {line.ljust(57)}│")
            else:
                formatted_lines.append(f"│{''.ljust(58)}│")
                
        # Montar resposta final
        formatted_answer = f"{border_top}\n" + "\n".join(formatted_lines) + f"\n{border_bottom}"
        
        # Log da resposta formatada
        logger.info("=== RESPOSTA FORMATADA ===")
        logger.info("\n" + formatted_answer)

        # Log da resposta
        logger.info(f"Pergunta processada: {question}")
        logger.info(f"Código gerado: {generated_code}")
        logger.info(f"SQL equivalente: {sql_equivalent}")
        
        return formatted_answer, generated_code, sql_equivalent

    except Exception as e:
        logger.error(f"Erro ao processar consulta: {e}")
        error_msg = str(e)
        if "AuthenticationError" in error_msg:
            error_msg = "Erro de autenticação com a API OpenAI. Verifique sua chave."
        elif "RateLimitError" in error_msg:
            error_msg = "Limite de taxa da API OpenAI atingido. Tente novamente mais tarde."
        elif "invalid_request_error" in error_msg:
            error_msg = "Erro na requisição à API. Verifique as configurações do modelo."
        
        raise HTTPException(status_code=500, detail=error_msg)

