# backend/app/enhanced_query_engine.py

import os
from typing import Dict, List, Any, Optional, Tuple, Union
import pandas as pd
from sqlalchemy import Engine
import logging
from datetime import datetime

from app.ai_agents import MultiAgentOrchestrator, get_multi_agent_orchestrator
from app.query_engine import query_dataframe, create_sql_query_engine, query_database_engine
from app.database_security import SecureDatabaseConnector, get_secure_db_connector

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedQueryEngine:
    """Motor de consulta aprimorado com sistema multi-agente e IA avançada"""
    
    def __init__(self):
        self.orchestrator = get_multi_agent_orchestrator()
        self.db_connector = get_secure_db_connector()
        self.query_cache: Dict[str, Any] = {}
        self.performance_metrics: List[Dict[str, Any]] = []
        
    def process_intelligent_query(self, 
                                question: str, 
                                session_data: Dict[str, Any],
                                use_multi_agent: bool = True) -> Dict[str, Any]:
        """
        Processa uma consulta usando IA avançada e sistema multi-agente
        
        Args:
            question: Pergunta do usuário
            session_data: Dados da sessão (DataFrame ou conexão DB)
            use_multi_agent: Se deve usar o sistema multi-agente
            
        Returns:
            Resultado da consulta com metadados
        """
        start_time = datetime.now()
        
        try:
            # Determinar tipo de dados
            data_type = session_data.get("type", "unknown")
            
            if use_multi_agent:
                # Usar sistema multi-agente para análise inteligente
                agent_result = self.orchestrator.process_user_query(
                    question=question,
                    data_type=data_type,
                    session_context=self._extract_session_context(session_data)
                )
                
                if agent_result["success"]:
                    # Executar código/SQL gerado pelos agentes
                    execution_result = self._execute_agent_result(agent_result, session_data)
                    
                    # Combinar resultados
                    final_result = {
                        "answer": execution_result.get("answer", ""),
                        "generated_code": execution_result.get("generated_code", ""),
                        "agent_analysis": agent_result,
                        "execution_time": (datetime.now() - start_time).total_seconds(),
                        "method": "multi_agent",
                        "success": True
                    }
                else:
                    # Fallback para método tradicional
                    logger.warning("Sistema multi-agente falhou, usando método tradicional")
                    final_result = self._fallback_to_traditional_query(question, session_data, start_time)
            else:
                # Usar método tradicional diretamente
                final_result = self._fallback_to_traditional_query(question, session_data, start_time)
            
            # Registrar métricas de performance
            self._record_performance_metrics(question, final_result, start_time)
            
            return final_result
            
        except Exception as e:
            logger.error(f"Erro no processamento inteligente da consulta: {e}")
            return {
                "answer": f"Erro ao processar consulta: {str(e)}",
                "generated_code": "",
                "success": False,
                "error": str(e),
                "execution_time": (datetime.now() - start_time).total_seconds()
            }
    
    def _extract_session_context(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extrai contexto relevante da sessão para os agentes"""
        context = {
            "data_type": session_data.get("type", "unknown"),
            "has_history": len(session_data.get("history", [])) > 0
        }
        
        if session_data["type"] == "dataframe":
            df = session_data.get("dataframe")
            if df is not None:
                context.update({
                    "columns": list(df.columns),
                    "shape": df.shape,
                    "dtypes": df.dtypes.to_dict(),
                    "sample_data": df.head(3).to_dict()
                })
        elif session_data["type"] == "database":
            context.update({
                "tables": session_data.get("tables", []),
                "db_path": session_data.get("db_path", "")
            })
        
        return context
    
    def _execute_agent_result(self, agent_result: Dict[str, Any], session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Executa o resultado processado pelos agentes"""
        try:
            if session_data["type"] == "dataframe":
                df = session_data.get("dataframe")
                if df is None:
                    raise ValueError("DataFrame não encontrado na sessão")
                
                # Usar a análise do agente para refinar a consulta
                analysis = agent_result.get("analysis", {})
                refined_question = self._refine_question_based_on_analysis(
                    agent_result["original_question"],
                    analysis
                )
                
                # Executar consulta refinada
                answer, code = query_dataframe(df, refined_question)
                
            elif session_data["type"] == "database":
                # Obter engine SQL
                engine = session_data.get("engine_instance")
                if engine is None:
                    raise ValueError("Engine SQL não encontrada na sessão")
                
                # Usar SQL gerado pelos agentes se disponível
                if "generated_sql" in agent_result:
                    sql = agent_result["generated_sql"]
                else:
                    # Fallback para geração tradicional
                    sql_engine = create_sql_query_engine(engine, session_data.get("tables", []))
                    answer, sql = query_database_engine(sql_engine, agent_result["original_question"])
                
                # Executar SQL com validações
                answer = self._execute_validated_sql(engine, sql)
                code = sql
                
            else:
                raise ValueError(f"Tipo de dados não suportado: {session_data['type']}")
            
            return {
                "answer": answer,
                "generated_code": code,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Erro na execução do resultado dos agentes: {e}")
            return {
                "answer": str(e),
                "generated_code": "",
                "success": False,
                "error": str(e)
            }
    
    def _refine_question_based_on_analysis(self, original_question: str, analysis: Dict[str, Any]) -> str:
        """Refina a pergunta com base na análise dos agentes"""
        refined = original_question
        
        # Adicionar contexto baseado nos indicadores
        context = analysis.get("context_indicators", {})
        if context.get("temporal"):
            refined += " (considerando o aspecto temporal dos dados)"
        if context.get("comparative"):
            refined += " (realizando comparações apropriadas)"
        if context.get("categorical"):
            refined += " (agrupando por categorias relevantes)"
        if context.get("numeric"):
            refined += " (focando em métricas numéricas)"
            
        # Ajustar com base na complexidade
        complexity = analysis.get("complexity", "simple")
        if complexity == "complex":
            refined += " (forneça uma análise detalhada e abrangente)"
        elif complexity == "medium":
            refined += " (forneça uma análise equilibrada)"
            
        return refined
    
    def _fallback_to_traditional_query(self, question: str, session_data: Dict[str, Any], start_time: datetime) -> Dict[str, Any]:
        """Fallback para o método tradicional de consulta"""
        try:
            if session_data["type"] == "dataframe":
                df = session_data["dataframe"]
                answer, generated_code = query_dataframe(df, question)
                
                return {
                    "answer": answer,
                    "generated_code": generated_code,
                    "execution_time": (datetime.now() - start_time).total_seconds(),
                    "method": "traditional_pandas",
                    "success": True
                }
                
            elif session_data["type"] == "database":
                # Usar query engine SQL tradicional
                engine = session_data.get("engine_instance")
                tables = session_data.get("tables", [])
                
                if engine and tables:
                    sql_query_engine = create_sql_query_engine(engine, tables)
                    answer, generated_code = query_database_engine(sql_query_engine, question)
                    
                    return {
                        "answer": answer,
                        "generated_code": generated_code,
                        "execution_time": (datetime.now() - start_time).total_seconds(),
                        "method": "traditional_sql",
                        "success": True
                    }
            
            return {
                "answer": "Tipo de dados não suportado para consulta",
                "generated_code": "",
                "success": False,
                "execution_time": (datetime.now() - start_time).total_seconds()
            }
            
        except Exception as e:
            logger.error(f"Erro no método tradicional: {e}")
            return {
                "answer": f"Erro no processamento tradicional: {str(e)}",
                "generated_code": "",
                "success": False,
                "execution_time": (datetime.now() - start_time).total_seconds()
            }
    
    def _record_performance_metrics(self, question: str, result: Dict[str, Any], start_time: datetime):
        """Registra métricas de performance"""
        metrics = {
            "timestamp": start_time,
            "question_length": len(question),
            "execution_time": result.get("execution_time", 0),
            "method": result.get("method", "unknown"),
            "success": result.get("success", False),
            "has_agent_analysis": "agent_analysis" in result
        }
        
        self.performance_metrics.append(metrics)
        
        # Manter apenas as últimas 100 métricas
        if len(self.performance_metrics) > 100:
            self.performance_metrics = self.performance_metrics[-100:]
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Retorna resumo das métricas de performance"""
        if not self.performance_metrics:
            return {"message": "Nenhuma métrica disponível"}
        
        total_queries = len(self.performance_metrics)
        successful_queries = sum(1 for m in self.performance_metrics if m["success"])
        avg_execution_time = sum(m["execution_time"] for m in self.performance_metrics) / total_queries
        
        method_counts = {}
        for metric in self.performance_metrics:
            method = metric["method"]
            method_counts[method] = method_counts.get(method, 0) + 1
        
        return {
            "total_queries": total_queries,
            "success_rate": successful_queries / total_queries,
            "average_execution_time": avg_execution_time,
            "method_distribution": method_counts,
            "multi_agent_usage": sum(1 for m in self.performance_metrics if m["has_agent_analysis"]) / total_queries
        }
    
    def optimize_query_strategy(self, question: str, session_context: Dict[str, Any]) -> str:
        """Otimiza a estratégia de consulta baseada no histórico e contexto"""
        # Análise simples para determinar melhor estratégia
        question_lower = question.lower()
        
        # Consultas complexas se beneficiam do sistema multi-agente
        complexity_indicators = [
            "comparar", "correlação", "tendência", "análise", "insights",
            "padrões", "distribuição", "múltiplas", "várias"
        ]
        
        if any(indicator in question_lower for indicator in complexity_indicators):
            return "multi_agent"
        
        # Consultas simples podem usar método tradicional
        simple_indicators = ["média", "total", "count", "máximo", "mínimo"]
        if any(indicator in question_lower for indicator in simple_indicators):
            return "traditional"
        
        # Default para multi-agente para melhor experiência
        return "multi_agent"

# Instância global do motor aprimorado
enhanced_query_engine = EnhancedQueryEngine()

def get_enhanced_query_engine() -> EnhancedQueryEngine:
    """Dependency para obter o motor de consulta aprimorado"""
    return enhanced_query_engine

