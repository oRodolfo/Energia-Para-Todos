from datetime import datetime
from typing import Optional, Dict, Any, List

class AuditMixin:
    """
    Mixin responsável por registrar informações de auditoria:
    - data de criação e atualização
    - histórico de alterações
    """

    def __init__(self) -> None:
        self._criado_em = datetime.now()
        self._atualizado_em: Optional[datetime] = None
        self._historico_alteracoes: List[Dict[str, Any]] = []

    # === GETTERS ===
    @property
    def data_criacao(self) -> datetime:
        """Data e hora de criação do registro."""
        return self._criado_em

    @property
    def data_atualizacao(self) -> Optional[datetime]:
        """Data e hora da última atualização."""
        return self._atualizado_em

    @property
    def historico_alteracoes(self) -> List[Dict[str, Any]]:
        """Retorna a lista de alterações realizadas."""
        return self._historico_alteracoes
    
    # === MÉTODOS DE AUDITORIA ===
    def registrar_alteracao(
        self, campo: str, valor_antigo: Any, valor_novo: Any,
        observacao: str = "", usuario_id: Optional[int] = None
    ) -> None:
        """Adiciona uma entrada ao histórico de alterações."""
        self._historico_alteracoes.append({
            "timestamp": datetime.now(),
            "campo": campo,
            "valor_antigo": valor_antigo,
            "valor_novo": valor_novo,
            "observacao": observacao,
            "usuario_id": usuario_id,
        })
        self._atualizado_em = datetime.now()

    def obter_info_auditoria(self) -> Dict[str, Any]:
        """Retorna resumo da auditoria do objeto."""
        return {
            "data_criacao": self.data_criacao.strftime("%Y-%m-%d %H:%M:%S"),
            "data_atualizacao": (
                self.data_atualizacao.strftime("%Y-%m-%d %H:%M:%S")
                if self.data_atualizacao else None
            ),
            "alteracoes": len(self._historico_alteracoes),
        }
