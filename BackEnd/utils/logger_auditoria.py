"""
Sistema de logging e auditoria para rastreamento de eventos.
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum


class TipoAcao(Enum):
    """Enumeração dos tipos de ação possíveis no sistema."""
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    CADASTRO = "CADASTRO"
    DOACAO = "DOACAO"
    DISTRIBUICAO = "DISTRIBUICAO"
    ALTERACAO_PERFIL = "ALTERACAO_PERFIL"
    AJUSTE_PESO = "AJUSTE_PESO"
    GERACAO_RELATORIO = "GERACAO_RELATORIO"
    EXCLUSAO = "EXCLUSAO"
    EXPIRACAO_CREDITO = "EXPIRACAO_CREDITO"


class StatusLog(Enum):
    """Status de uma operação no log."""
    SUCESSO = "SUCESSO"
    FALHA = "FALHA"
    PENDENTE = "PENDENTE"
    ALERTA = "ALERTA"


class LoggerAuditoria:
    """
    Singleton responsável por registrar e gerenciar logs de auditoria.
    Mantém histórico de todas as operações críticas do sistema.
    """
    
    _instancia: Optional['LoggerAuditoria'] = None
    
    def __new__(cls):
        if cls._instancia is None:
            cls._instancia = super().__new__(cls)
            cls._instancia._logs: List[Dict[str, Any]] = []
        return cls._instancia
    
    def registrar(
        self,
        tipo_acao: TipoAcao,
        status: StatusLog,
        usuario_id: Optional[int] = None,
        ip_acesso: Optional[str] = None,
        detalhes: Optional[str] = None,
        dados_adicionais: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Registra uma nova entrada no log de auditoria.
        
        Args:
            tipo_acao: Tipo da ação realizada
            status: Status da operação
            usuario_id: ID do usuário que executou a ação
            ip_acesso: Endereço IP de origem
            detalhes: Descrição detalhada da ação
            dados_adicionais: Dados extras relevantes
            
        Returns:
            ID do log criado
        """
        log_id = len(self._logs) + 1
        
        log_entry = {
            'id_log': log_id,
            'data_hora': datetime.now(),
            'tipo_acao': tipo_acao,
            'status': status,
            'usuario_id': usuario_id,
            'ip_acesso': ip_acesso,
            'detalhes': detalhes,
            'dados_adicionais': dados_adicionais or {}
        }
        
        self._logs.append(log_entry)
        return log_id
    
    def obter_logs(
        self,
        usuario_id: Optional[int] = None,
        tipo_acao: Optional[TipoAcao] = None,
        status: Optional[StatusLog] = None,
        data_inicio: Optional[datetime] = None,
        data_fim: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Obtém logs filtrados por critérios específicos.
        
        Args:
            usuario_id: Filtrar por ID do usuário
            tipo_acao: Filtrar por tipo de ação
            status: Filtrar por status
            data_inicio: Data inicial do período
            data_fim: Data final do período
            
        Returns:
            Lista de logs que atendem aos critérios
        """
        logs_filtrados = self._logs.copy()
        
        if usuario_id is not None:
            logs_filtrados = [log for log in logs_filtrados if log['usuario_id'] == usuario_id]
        
        if tipo_acao is not None:
            logs_filtrados = [log for log in logs_filtrados if log['tipo_acao'] == tipo_acao]
        
        if status is not None:
            logs_filtrados = [log for log in logs_filtrados if log['status'] == status]
        
        if data_inicio is not None:
            logs_filtrados = [log for log in logs_filtrados if log['data_hora'] >= data_inicio]
        
        if data_fim is not None:
            logs_filtrados = [log for log in logs_filtrados if log['data_hora'] <= data_fim]
        
        return logs_filtrados
    
    def obter_estatisticas(self) -> Dict[str, Any]:
        """
        Retorna estatísticas gerais dos logs.
        
        Returns:
            Dicionário com estatísticas
        """
        total_logs = len(self._logs)
        
        por_tipo = {}
        por_status = {}
        
        for log in self._logs:
            tipo = log['tipo_acao'].value
            status = log['status'].value
            
            por_tipo[tipo] = por_tipo.get(tipo, 0) + 1
            por_status[status] = por_status.get(status, 0) + 1
        
        return {
            'total_logs': total_logs,
            'por_tipo_acao': por_tipo,
            'por_status': por_status
        }
    
    def limpar_logs(self) -> None:
        """Limpa todos os logs (use com cuidado)."""
        self._logs.clear()
    
    def __repr__(self) -> str:
        return f"<LoggerAuditoria(total_logs={len(self._logs)})>"