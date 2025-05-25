# backend/app/data_loader.py

import pandas as pd
from fastapi import UploadFile, HTTPException
import io

async def load_dataframe_from_file(file: UploadFile) -> pd.DataFrame:
    """
    Lê o conteúdo de um UploadFile (CSV, Excel, JSON, Parquet) 
    e o carrega em um DataFrame Pandas.
    """
    filename = file.filename
    if not filename:
        raise ValueError("Nome do arquivo não pode ser vazio.")

    file_extension = filename.split('.')[-1].lower()
    content = await file.read() # Ler o conteúdo do arquivo em memória
    file_stream = io.BytesIO(content)

    try:
        if file_extension == 'csv':
            # Tentar detectar separador comum, pode precisar de ajuste
            try:
                df = pd.read_csv(file_stream, sep=None, engine='python') # engine='python' para detectar sep=None
            except Exception as e:
                 # Fallback para vírgula se a detecção falhar
                 file_stream.seek(0) # Resetar stream
                 df = pd.read_csv(file_stream, sep=',')
        elif file_extension in ['xlsx', 'xls']:
            df = pd.read_excel(file_stream, engine='openpyxl')
        elif file_extension == 'json':
            # Assume formato JSON orient='records', pode precisar de ajuste
            df = pd.read_json(file_stream, orient='records')
        elif file_extension == 'parquet':
            df = pd.read_parquet(file_stream, engine='pyarrow')
        else:
            raise ValueError(f"Formato de arquivo não suportado: {file_extension}. Formatos suportados: CSV, Excel, JSON, Parquet.")
        
        if df.empty:
            raise ValueError("O arquivo carregado está vazio ou não pôde ser lido corretamente.")
            
        return df
    except ValueError as ve:
        raise ve # Re-lançar ValueErrors específicos
    except Exception as e:
        # Capturar outros erros de leitura do Pandas ou I/O
        print(f"Erro ao ler o arquivo {filename} com pandas: {e}")
        raise ValueError(f"Erro ao processar o arquivo {filename}. Verifique o formato e o conteúdo. Detalhe: {e}")
    finally:
        file_stream.close()

