# backend/app/data_loader.py

import pandas as pd
import numpy as np
from fastapi import UploadFile, HTTPException
import io
import logging
from typing import Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def load_dataframe_from_file(file: UploadFile) -> pd.DataFrame:
    """Carrega e pré-processa um DataFrame a partir de um arquivo."""
    try:
        content = await file.read()
        df = None
        
        if file.filename.endswith('.csv'):
            # Tentar diferentes encodings e delimitadores
            for encoding in ['utf-8', 'latin1', 'iso-8859-1']:
                for delimiter in [',', ';', '\t']:
                    try:
                        df = pd.read_csv(
                            io.BytesIO(content),
                            encoding=encoding,
                            sep=delimiter,
                            na_values=['', 'nan', 'NaN', 'null', 'None', 'NA'],  # Lista expandida de valores nulos
                            keep_default_na=True
                        )
                        if len(df.columns) > 1:
                            break
                    except Exception as e:
                        logger.warning(f"Tentativa falhou com encoding {encoding} e delimiter {delimiter}: {e}")
                        continue
                if df is not None and len(df.columns) > 1:
                    break
        
        elif file.filename.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(io.BytesIO(content), na_values=['', 'nan', 'NaN', 'null', 'None', 'NA'])
        elif file.filename.endswith('.json'):
            df = pd.read_json(io.BytesIO(content))
        else:
            raise ValueError(f"Formato de arquivo não suportado: {file.filename}")

        if df is None or df.empty:
            raise ValueError("Não foi possível carregar dados do arquivo")

        # Processar e limpar dados
        df = process_dataframe(df)
        
        logger.info(f"DataFrame carregado com sucesso. Shape: {df.shape}")
        logger.info(f"Colunas: {df.columns.tolist()}")
        logger.info(f"Tipos de dados: {df.dtypes.to_dict()}")
        
        return df

    except Exception as e:
        logger.error(f"Erro ao carregar arquivo {file.filename}: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Erro ao processar arquivo: {str(e)}")

def process_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Processa e limpa o DataFrame."""
    # Remover linhas totalmente vazias
    df = df.dropna(how='all')
    
    # Limpar nomes das colunas
    df.columns = [clean_column_name(col) for col in df.columns]
    
    # Para cada coluna
    for col in df.columns:
        # Se a coluna tem mais de 50% de valores nulos, preencher com um valor padrão
        null_ratio = df[col].isnull().mean()
        if null_ratio > 0.5:
            logger.warning(f"Coluna {col} tem {null_ratio*100:.1f}% de valores nulos")
            
        # Tentar converter para numérico se possível
        if df[col].dtype == 'object':
            try:
                numeric_conversion = pd.to_numeric(df[col], errors='coerce')
                if numeric_conversion.notnull().sum() > df[col].notnull().sum() * 0.5:
                    df[col] = numeric_conversion
            except:
                pass
        
        # Preencher valores nulos
        if df[col].dtype in ['int64', 'float64']:
            df[col] = df[col].fillna(0)
        else:
            df[col] = df[col].fillna("N/A")
    
    return df

def clean_column_name(col: str) -> str:
    """Limpa e padroniza nomes de colunas."""
    import re
    col = str(col).strip().lower()
    col = re.sub(r'[^a-zA-Z0-9_\s]', '', col)
    col = re.sub(r'\s+', '_', col)
    return col

