# data-analysis-AI
Analisa dados de tabelas e banco de dados usando llm (IA)

# API de Análise de Dados com IA

Este projeto é um backend desenvolvido em FastAPI para análise de dados utilizando inteligência artificial. Ele permite:

- Upload de arquivos de dados (CSV, Excel, JSON, Parquet)
- Conexão com bancos de dados SQLite
- Execução de perguntas em linguagem natural sobre os dados (DataFrame ou banco de dados)
- Geração de relatórios em PDF com base nas interações

Principais tecnologias e bibliotecas:
- FastAPI
- SQLAlchemy
- Pandas
- LlamaIndex (integração com LLMs)
- OpenAI API
- fpdf2

O backend expõe endpoints REST para upload, consulta, conexão com banco de dados e geração de relatórios. O gerenciamento de sessões é feito em memória (não recomendado para produção).

## Como executar

1. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
2. Inicie o servidor:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```
3. Acesse a documentação automática em: http://localhost:8000/docs

## Observações
- É necessário definir a variável de ambiente `OPENAI_API_KEY` no arquivo `.env` para uso das funcionalidades de IA.
- Para produção, recomenda-se usar um sistema de gerenciamento de sessões persistente (ex: Redis).
