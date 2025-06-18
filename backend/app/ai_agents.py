# backend/app/ai_agents.py

import os
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgentType(Enum):
    """Tipos de agentes disponíveis no sistema"""
    QUERY_ANALYZER = "query_analyzer"
    SQL_GENERATOR = "sql_generator"
    DATA_INTERPRETER = "data_interpreter"
    RESULT_SYNTHESIZER = "result_synthesizer"
    VALIDATION_AGENT = "validation_agent"

@dataclass
class AgentMessage:
    """Estrutura de mensagem entre agentes"""
    sender: str
    receiver: str
    content: Dict[str, Any]
    timestamp: datetime
    message_type: str

class BaseAgent:
    """Classe base para todos os agentes"""
    
    def __init__(self, agent_id: str, agent_type: AgentType):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.message_history: List[AgentMessage] = []
        
    def process_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Processa uma mensagem recebida"""
        self.message_history.append(message)
        return self._handle_message(message)
    
    def _handle_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Implementação específica do processamento de mensagem"""
        raise NotImplementedError
    
    def create_message(self, receiver: str, content: Dict[str, Any], message_type: str) -> AgentMessage:
        """Cria uma nova mensagem"""
        return AgentMessage(
            sender=self.agent_id,
            receiver=receiver,
            content=content,
            timestamp=datetime.now(),
            message_type=message_type
        )

class QueryAnalyzerAgent(BaseAgent):
    """Agente responsável por analisar e classificar consultas do usuário"""
    
    def __init__(self):
        super().__init__("query_analyzer", AgentType.QUERY_ANALYZER)
        self.intent_patterns = {
            "aggregation": {
                "keywords": ["média", "total", "soma", "count", "máximo", "mínimo", "average", "sum", "max", "min"],
                "importance": 0.8
            },
            "filtering": {
                "keywords": ["onde", "filter", "com", "que", "when", "where", "igual", "maior", "menor", "entre"],
                "importance": 0.7
            },
            "comparison": {
                "keywords": ["comparar", "diferença", "versus", "vs", "compare", "difference", "em relação"],
                "importance": 0.9
            },
            "trend": {
                "keywords": ["tendência", "evolução", "ao longo", "trend", "over time", "temporal", "período"],
                "importance": 0.85
            },
            "distribution": {
                "keywords": ["distribuição", "frequência", "histogram", "distribution", "frequency", "percentual"],
                "importance": 0.75
            },
            "correlation": {
                "keywords": ["correlação", "relação", "correlation", "relationship", "dependência", "influência"],
                "importance": 0.9
            }
        }

    def _handle_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Analisa a consulta do usuário e determina o tipo de análise necessária"""
        try:
            user_question = message.content.get("question", "")
            data_type = message.content.get("data_type", "")
            
            # Análise da intenção da consulta
            analysis_result = self._analyze_query_intent(user_question, data_type)
            
            # Determinar próximo agente
            next_agent = self._determine_next_agent(analysis_result)
            
            response_content = {
                "original_question": user_question,
                "analysis": analysis_result,
                "next_agent": next_agent,
                "confidence": analysis_result.get("confidence", 0.8)
            }
            
            return self.create_message(
                receiver=next_agent,
                content=response_content,
                message_type="query_analysis"
            )
            
        except Exception as e:
            logger.error(f"Erro no QueryAnalyzerAgent: {e}")
            return None
    
    def _analyze_query_intent(self, question: str, data_type: str) -> Dict[str, Any]:
        """Analisa a intenção da consulta com pesos e confiança ajustada"""
        question_lower = question.lower()
        detected_intents = []
        confidence_scores = []
        
        # Análise por padrões e keywords com pesos
        for intent, config in self.intent_patterns.items():
            matched_keywords = [k for k in config["keywords"] if k in question_lower]
            if matched_keywords:
                score = len(matched_keywords) * config["importance"]
                detected_intents.append(intent)
                confidence_scores.append(score)

        # Determinar complexidade com mais nuances
        complexity = self._determine_complexity(question_lower, detected_intents)
        
        # Calcular confiança global
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.5
        context_boost = 0.1 if complexity != "complex" else 0
        data_type_boost = 0.1 if data_type in ["database", "dataframe"] else 0
        
        final_confidence = min(0.95, avg_confidence + context_boost + data_type_boost)

        return {
            "intents": detected_intents,
            "complexity": complexity,
            "data_type": data_type,
            "requires_sql": data_type == "database",
            "requires_pandas": data_type == "dataframe",
            "confidence": final_confidence,
            "context_indicators": self._extract_context_indicators(question_lower)
        }

    def _determine_complexity(self, question: str, intents: List[str]) -> str:
        """Determina a complexidade da consulta com mais critérios"""
        if len(intents) <= 1 and len(question.split()) < 10:
            return "simple"
            
        if any(word in question for word in [
            "múltiplas", "várias", "complex", "advanced", "relacionar", 
            "combinar", "agrupar", "categorizar", "analisar"
        ]) or len(intents) >= 3:
            return "complex"
            
        return "medium"

    def _extract_context_indicators(self, question: str) -> Dict[str, Any]:
        """Extrai indicadores de contexto da pergunta"""
        return {
            "temporal": any(word in question for word in ["quando", "data", "período", "mês", "ano"]),
            "comparative": any(word in question for word in ["mais", "menos", "maior", "menor", "igual"]),
            "categorical": any(word in question for word in ["tipo", "categoria", "classe", "grupo"]),
            "numeric": any(word in question for word in ["quantidade", "valor", "número", "total"])
        }

class SQLGeneratorAgent(BaseAgent):
    """Agente responsável por gerar consultas SQL"""
    
    def __init__(self):
        super().__init__("sql_generator", AgentType.SQL_GENERATOR)
        
    def _handle_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Gera consulta SQL baseada na análise da pergunta"""
        try:
            analysis = message.content.get("analysis", {})
            question = message.content.get("original_question", "")
            
            # Gerar SQL baseado na análise
            sql_query = self._generate_sql_query(question, analysis)
            
            # Validar SQL
            validation_result = self._validate_sql_query(sql_query)
            
            response_content = {
                "original_question": question,
                "generated_sql": sql_query,
                "validation": validation_result,
                "analysis": analysis
            }
            
            return self.create_message(
                receiver="validation_agent",
                content=response_content,
                message_type="sql_generation"
            )
            
        except Exception as e:
            logger.error(f"Erro no SQLGeneratorAgent: {e}")
            return None
    
    def _generate_sql_query(self, question: str, analysis: Dict[str, Any]) -> str:
        """Gera consulta SQL baseada na pergunta e análise"""
        # Esta é uma implementação simplificada
        # Em um sistema real, usaria um LLM para gerar SQL
        
        intents = analysis.get("intents", [])
        
        if "aggregation" in intents:
            if any(word in question.lower() for word in ["média", "average"]):
                return "SELECT AVG(column_name) FROM table_name"
            elif any(word in question.lower() for word in ["total", "soma", "sum"]):
                return "SELECT SUM(column_name) FROM table_name"
            elif any(word in question.lower() for word in ["count", "quantidade"]):
                return "SELECT COUNT(*) FROM table_name"
        
        # SQL padrão para consultas simples
        return "SELECT * FROM table_name LIMIT 10"
    
    def _validate_sql_query(self, sql_query: str) -> Dict[str, Any]:
        """Valida a consulta SQL gerada"""
        # Validações básicas de segurança
        dangerous_keywords = ["DROP", "DELETE", "INSERT", "UPDATE", "ALTER", "CREATE"]
        
        sql_upper = sql_query.upper()
        for keyword in dangerous_keywords:
            if keyword in sql_upper:
                return {
                    "is_valid": False,
                    "error": f"Operação SQL perigosa detectada: {keyword}",
                    "severity": "high"
                }
        
        # Verificar se é uma consulta SELECT
        if not sql_upper.strip().startswith("SELECT"):
            return {
                "is_valid": False,
                "error": "Apenas consultas SELECT são permitidas",
                "severity": "medium"
            }
        
        return {
            "is_valid": True,
            "confidence": 0.9,
            "estimated_complexity": "medium"
        }

class DataInterpreterAgent(BaseAgent):
    """Agente responsável por interpretar dados e gerar código Pandas"""
    
    def __init__(self):
        super().__init__("data_interpreter", AgentType.DATA_INTERPRETER)
        
    def _handle_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Interpreta dados e gera código Pandas"""
        try:
            analysis = message.content.get("analysis", {})
            question = message.content.get("original_question", "")
            
            # Gerar código Pandas
            pandas_code = self._generate_pandas_code(question, analysis)
            
            response_content = {
                "original_question": question,
                "generated_code": pandas_code,
                "analysis": analysis,
                "code_type": "pandas"
            }
            
            return self.create_message(
                receiver="result_synthesizer",
                content=response_content,
                message_type="data_interpretation"
            )
            
        except Exception as e:
            logger.error(f"Erro no DataInterpreterAgent: {e}")
            return None
    
    def _generate_pandas_code(self, question: str, analysis: Dict[str, Any]) -> str:
        """Gera código Pandas baseado na pergunta"""
        intents = analysis.get("intents", [])
        
        if "aggregation" in intents:
            if any(word in question.lower() for word in ["média", "average"]):
                return "df.mean()"
            elif any(word in question.lower() for word in ["total", "soma", "sum"]):
                return "df.sum()"
            elif any(word in question.lower() for word in ["count", "quantidade"]):
                return "df.count()"
        
        if "distribution" in intents:
            return "df.describe()"
        
        # Código padrão
        return "df.head()"

class ResultSynthesizerAgent(BaseAgent):
    """Agente responsável por sintetizar resultados finais"""
    
    def __init__(self):
        super().__init__("result_synthesizer", AgentType.RESULT_SYNTHESIZER)
        
    def _handle_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Sintetiza resultado final para o usuário"""
        try:
            question = message.content.get("original_question", "")
            generated_code = message.content.get("generated_code", "")
            generated_sql = message.content.get("generated_sql", "")
            
            # Gerar resposta em linguagem natural
            natural_response = self._generate_natural_response(question, generated_code or generated_sql)
            
            response_content = {
                "original_question": question,
                "natural_response": natural_response,
                "generated_code": generated_code,
                "generated_sql": generated_sql,
                "final_result": True
            }
            
            return self.create_message(
                receiver="user",
                content=response_content,
                message_type="final_result"
            )
            
        except Exception as e:
            logger.error(f"Erro no ResultSynthesizerAgent: {e}")
            return None
    
    def _generate_natural_response(self, question: str, code: str) -> str:
        """Gera resposta em linguagem natural"""
        # Esta é uma implementação simplificada
        # Em um sistema real, usaria um LLM para gerar respostas mais naturais
        
        if "média" in question.lower() or "average" in question.lower():
            return f"Para calcular a média solicitada, utilizei o seguinte código: {code}"
        elif "total" in question.lower() or "soma" in question.lower():
            return f"Para obter o total solicitado, executei: {code}"
        elif "count" in question.lower() or "quantidade" in question.lower():
            return f"Para contar os registros, utilizei: {code}"
        
        return f"Baseado na sua pergunta, executei o seguinte código: {code}"

class ValidationAgent(BaseAgent):
    """Agente responsável por validar consultas e resultados"""
    
    def __init__(self):
        super().__init__("validation_agent", AgentType.VALIDATION_AGENT)
        
    def _handle_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Valida consultas SQL e código gerado"""
        try:
            sql_query = message.content.get("generated_sql", "")
            validation = message.content.get("validation", {})
            
            if validation.get("is_valid", False):
                # Se válido, encaminhar para execução
                return self.create_message(
                    receiver="result_synthesizer",
                    content=message.content,
                    message_type="validated_query"
                )
            else:
                # Se inválido, retornar erro
                error_content = {
                    "error": validation.get("error", "Consulta inválida"),
                    "original_question": message.content.get("original_question", ""),
                    "failed_validation": True
                }
                
                return self.create_message(
                    receiver="user",
                    content=error_content,
                    message_type="validation_error"
                )
                
        except Exception as e:
            logger.error(f"Erro no ValidationAgent: {e}")
            return None

class MultiAgentOrchestrator:
    """Orquestrador do sistema multi-agente"""
    
    def __init__(self):
        self.agents = {
            "query_analyzer": QueryAnalyzerAgent(),
            "sql_generator": SQLGeneratorAgent(),
            "data_interpreter": DataInterpreterAgent(),
            "result_synthesizer": ResultSynthesizerAgent(),
            "validation_agent": ValidationAgent()
        }
        self.message_queue: List[AgentMessage] = []
        self.execution_history: List[Dict[str, Any]] = []
        
    def process_user_query(self, question: str, data_type: str, session_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Processa uma consulta do usuário através do sistema multi-agente"""
        try:
            # Criar mensagem inicial
            initial_message = AgentMessage(
                sender="user",
                receiver="query_analyzer",
                content={
                    "question": question,
                    "data_type": data_type,
                    "session_context": session_context or {}
                },
                timestamp=datetime.now(),
                message_type="user_query"
            )
            
            # Processar através dos agentes
            current_message = initial_message
            max_iterations = 10  # Prevenir loops infinitos
            iteration = 0
            
            while current_message and iteration < max_iterations:
                iteration += 1
                
                # Obter agente receptor
                receiver_id = current_message.receiver
                if receiver_id == "user":
                    # Resultado final alcançado
                    break
                    
                if receiver_id not in self.agents:
                    logger.error(f"Agente não encontrado: {receiver_id}")
                    break
                
                # Processar mensagem
                agent = self.agents[receiver_id]
                response = agent.process_message(current_message)
                
                # Registrar na história
                self.execution_history.append({
                    "iteration": iteration,
                    "agent": receiver_id,
                    "input": current_message.content,
                    "output": response.content if response else None,
                    "timestamp": datetime.now()
                })
                
                current_message = response
            
            # Retornar resultado final
            if current_message and current_message.receiver == "user":
                return {
                    "success": True,
                    "result": current_message.content,
                    "execution_path": self.execution_history,
                    "iterations": iteration
                }
            else:
                return {
                    "success": False,
                    "error": "Falha no processamento multi-agente",
                    "execution_path": self.execution_history,
                    "iterations": iteration
                }
                
        except Exception as e:
            logger.error(f"Erro no MultiAgentOrchestrator: {e}")
            return {
                "success": False,
                "error": str(e),
                "execution_path": self.execution_history
            }
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Retorna status de todos os agentes"""
        status = {}
        for agent_id, agent in self.agents.items():
            status[agent_id] = {
                "type": agent.agent_type.value,
                "message_count": len(agent.message_history),
                "last_activity": agent.message_history[-1].timestamp if agent.message_history else None
            }
        return status

# Instância global do orquestrador
multi_agent_orchestrator = MultiAgentOrchestrator()

def get_multi_agent_orchestrator() -> MultiAgentOrchestrator:
    """Dependency para obter o orquestrador multi-agente"""
    return multi_agent_orchestrator

