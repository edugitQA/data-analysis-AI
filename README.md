# data-analysis-AI

Projeto fullstack para análise de dados de tabelas e bancos de dados usando LLM (IA generativa) com foco em segurança e interface moderna.

## Funcionalidades

### Análise de Dados
- Upload de arquivos de dados (CSV, Excel, JSON, Parquet)
- Conexão segura com bancos de dados SQLite
- Execução de perguntas em linguagem natural sobre os dados
- Respostas formatadas com emojis e layout amigável
- Geração de relatórios em PDF com base nas interações

### Segurança
- Proteção contra SQL injection
- Sanitização de inputs e queries
- Validação de nomes de tabelas e campos
- Limitação de operações permitidas (apenas SELECT)
- Timeout e reciclagem de conexões
- Logging detalhado de operações

### Interface
- Frontend moderno com React + Vite + TypeScript
- Componentes UI reutilizáveis com Tailwind
- Design responsivo e acessível
- Previews de dados tabulares
- Feedback visual de operações

## Estrutura do Projeto
```
backend/
  app/
    ai_agents.py         # Gerenciamento de agentes IA
    data_loader.py       # Carregamento de dados
    database_security.py # Segurança do banco
    enhanced_query_engine.py # Motor de consultas avançado
    main.py             # API principal
    pdf_generator.py    # Geração de PDFs
    query_engine.py     # Motor de consultas base
    security.py         # Funcionalidades de segurança
  requirements.txt
  .env.example
frontend/
  src/
    components/         # Componentes React
      ui/              # Componentes UI base
    hooks/             # Hooks customizados
    lib/               # Utilitários
```

## Como executar

### 1. Backend (FastAPI)

1. Instale as dependências:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```
2. Configure o arquivo `.env` baseado no `.env.example`:
   ```env
   OPENAI_API_KEY=sk-...
   MAX_ROWS_PREVIEW=100
   LOG_LEVEL=INFO
   ```
3. Inicie o servidor:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```
4. Acesse a documentação automática em: http://localhost:8000/docs

### 2. Frontend (Vite + React)

1. Instale as dependências:
   ```bash
   cd frontend
   pnpm install
   ```
2. Inicie o servidor de desenvolvimento:
   ```bash
   pnpm run dev
   ```
3. Acesse: http://localhost:5173

## Segurança

O projeto implementa várias camadas de segurança:

- **Sanitização de Inputs**: Validação rigorosa de todos os inputs do usuário
- **Proteção SQL**: 
  - Bloqueio de operações perigosas (DROP, DELETE, etc)
  - Limitação a queries SELECT
  - Validação de nomes de tabelas e campos
- **Conexões**: 
  - Timeout de 30 segundos
  - Reciclagem de conexões a cada hora
  - Pool de conexões com health check
- **Logging**: Registro detalhado de todas as operações e erros

## Observações
- Utilize sempre o `.env.example` como base para criar seu `.env`
- O sistema de logging registra operações em `ai_responses.log`
- Preferência por pnpm no frontend para melhor gestão de dependências
- Para produção, recomenda-se:
  - Sistema de sessões persistente (ex: Redis)
  - Proteção adicional das chaves de API
  - Configuração de CORS apropriada
  - Rate limiting nas APIs
  - Monitoramento dos logs

---

Desenvolvido por Eduardo Alves.
