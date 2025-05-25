# data-analysis-AI

Projeto fullstack para análise de dados de tabelas e bancos de dados usando LLM (IA generativa).

## Funcionalidades
- Upload de arquivos de dados (CSV, Excel, JSON, Parquet)
- Conexão com bancos de dados SQLite
- Execução de perguntas em linguagem natural sobre os dados (DataFrame ou banco de dados)
- Geração de relatórios em PDF com base nas interações
- Interface web moderna (React + Vite + TypeScript)

## Estrutura do Projeto
```
backend/
  app/
    main.py
    data_loader.py
    db_connector.py
    query_engine.py
    pdf_generator.py
  requirements.txt
  .env
frontend/
  package.json
  src/
    App.tsx
    components/
    hooks/
    lib/
    ui/
```

## Como executar

### 1. Backend (FastAPI)

1. Instale as dependências:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```
2. Configure o arquivo `.env` com sua chave da OpenAI:
   ```env
   OPENAI_API_KEY=sk-...
   ```
3. Inicie o servidor:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```
4. Acesse a documentação automática em: http://localhost:8000/docs

### 2. Frontend (Vite + React)

1. Instale as dependências (resolvendo conflitos):
   ```bash
   cd frontend
   npm install --legacy-peer-deps
   ```
2. Inicie o servidor de desenvolvimento:
   ```bash
   npm run dev
   ```
3. Acesse: http://localhost:5173

## Observações
- O backend faz gerenciamento de sessões em memória (não recomendado para produção).
- O arquivo `.env` **NÃO deve ser versionado**. Use `.env.example` para compartilhar variáveis necessárias.
- Se houver conflitos de dependências no frontend, use `--legacy-peer-deps`.
- Para produção, utilize um sistema de sessões persistente (ex: Redis) e proteja suas chaves de API.

---

Desenvolvido por [Seu Nome].
