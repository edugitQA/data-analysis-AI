# backend/app/security.py

import os
import hashlib
import secrets
from typing import Optional
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import text
import re

# Configuração de segurança
security = HTTPBearer()

class SecurityManager:
    def __init__(self):
        self.api_key = os.getenv("API_SECRET_KEY", "default-secret-key")
        self.max_file_size = 50 * 1024 * 1024  # 50MB
        self.allowed_file_types = {'.csv', '.xlsx', '.xls', '.json', '.parquet'}
        self.max_query_length = 1000
        
    def validate_file_upload(self, filename: str, file_size: int) -> bool:
        """Valida upload de arquivo"""
        if file_size > self.max_file_size:
            raise HTTPException(
                status_code=413,
                detail=f"Arquivo muito grande. Tamanho máximo: {self.max_file_size // (1024*1024)}MB"
            )
        
        file_ext = os.path.splitext(filename.lower())[1]
        if file_ext not in self.allowed_file_types:
            raise HTTPException(
                status_code=400,
                detail=f"Tipo de arquivo não permitido. Tipos aceitos: {', '.join(self.allowed_file_types)}"
            )
        
        return True
    
    def validate_db_path(self, db_path: str) -> bool:
        """Valida caminho do banco de dados"""
        # Prevenir path traversal
        if '..' in db_path or db_path.startswith('/'):
            raise HTTPException(
                status_code=400,
                detail="Caminho de banco de dados inválido"
            )
        
        # Verificar se é arquivo SQLite
        if not db_path.lower().endswith('.db') and not db_path.lower().endswith('.sqlite'):
            raise HTTPException(
                status_code=400,
                detail="Apenas arquivos SQLite (.db, .sqlite) são permitidos"
            )
        
        return True
    
    def sanitize_sql_query(self, query: str) -> str:
        """Sanitiza consultas SQL para prevenir SQL injection"""
        # Lista de palavras-chave perigosas
        dangerous_keywords = [
            'DROP', 'DELETE', 'INSERT', 'UPDATE', 'ALTER', 'CREATE',
            'TRUNCATE', 'EXEC', 'EXECUTE', 'UNION', 'SCRIPT'
        ]
        
        query_upper = query.upper()
        for keyword in dangerous_keywords:
            if keyword in query_upper:
                raise HTTPException(
                    status_code=400,
                    detail=f"Operação SQL não permitida: {keyword}"
                )
        
        return query
    
    def validate_question(self, question: str) -> bool:
        """Valida pergunta do usuário"""
        if len(question) > self.max_query_length:
            raise HTTPException(
                status_code=400,
                detail=f"Pergunta muito longa. Máximo: {self.max_query_length} caracteres"
            )
        
        # Verificar caracteres suspeitos
        suspicious_patterns = [
            r'<script.*?>',
            r'javascript:',
            r'on\w+\s*=',
            r'eval\s*\(',
            r'exec\s*\('
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, question, re.IGNORECASE):
                raise HTTPException(
                    status_code=400,
                    detail="Pergunta contém conteúdo suspeito"
                )
        
        return True
    
    def generate_session_token(self) -> str:
        """Gera token seguro para sessão"""
        return secrets.token_urlsafe(32)
    
    def hash_sensitive_data(self, data: str) -> str:
        """Hash de dados sensíveis"""
        return hashlib.sha256(data.encode()).hexdigest()

# Instância global do gerenciador de segurança
security_manager = SecurityManager()

def get_security_manager() -> SecurityManager:
    """Dependency para obter o gerenciador de segurança"""
    return security_manager

def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)) -> bool:
    """Verifica chave de API (opcional para endpoints protegidos)"""
    if credentials.credentials != security_manager.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Chave de API inválida",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return True

