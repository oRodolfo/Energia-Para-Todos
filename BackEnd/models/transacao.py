#criando a classe transacao que registra distribuição de créditos para beneficiários
from datetime import datetime
from typing import Optional
from enum import Enum

#identificando qual é o tipo de movimentação que o credito esta
class TipoMovimento(Enum):
    DISTRIBUICAO = "DISTRIBUICAO"
    ESTORNO = "ESTORNO"
    AJUSTE = "AJUSTE"
    EXPIRACAO = "EXPIRACAO"

#identificando em qual status a transação esta
class StatusTransacao(Enum):
    CONCLUIDA = "CONCLUIDA"
    PENDENTE = "PENDENTE"
    CANCELADA = "CANCELADA"
    ERRO = "ERRO"

"""
Representa uma transação de distribuição de créditos.
Rastreia transferência de kWh de créditos para beneficiários.
"""
class Transacao:
    def __init__(
        self,
        id_transacao: int,
        id_beneficiario: int,
        id_credito: int,
        quantidade_kwh: float,
        tipo_movimento: TipoMovimento = TipoMovimento.DISTRIBUICAO,
        observacao: Optional[str] = None
    ):
        if quantidade_kwh <= 0:
            raise ValueError("Quantidade deve ser positiva")
        
        self._id_transacao = id_transacao
        self._id_beneficiario = id_beneficiario
        self._id_credito = id_credito
        self._quantidade_kwh = quantidade_kwh
        self._tipo_movimento = tipo_movimento
        self._data_transacao = datetime.now()
        self._status = StatusTransacao.CONCLUIDA
        self._observacao = observacao
    
    #Retorna o identificador da transação atual 
    @property
    def id_transacao(self) -> int:
        return self._id_transacao
    
    #Retorna o identificador do beneficiario que esta sendo relacionado na transação
    @property
    def id_beneficiario(self) -> int:
        return self._id_beneficiario
    
    #Retorna o identificador do credito que esta relacionado ao beneficiario e a transacao
    @property
    def id_credito(self) -> int:
        return self._id_credito
    
    #Retorna qual é a quantidade de KWH da transação
    @property
    def quantidade_kwh(self) -> float:
        return self._quantidade_kwh
    
    #Retorna o tipo de movimento que esta a transação entre: distribuicao, estorno, ajuste ou expiracao
    @property
    def tipo_movimento(self) -> TipoMovimento:
        return self._tipo_movimento
    
    #Retorna quando que foi feita a transacao (data)
    @property
    def data_transacao(self) -> datetime:
        return self._data_transacao
    
    #Retorna o status atual da transacao entre: concluida, pendente, cancelada ou se deu erro
    @property
    def status(self) -> StatusTransacao:
        return self._status
    
    #Retorna a descrição do que é a transação, por exemplo, foi cancelada por motivo de x,y,z 
    @property
    def observacao(self) -> Optional[str]:
        return self._observacao
    
    #Marca transação como pendente
    def marcar_como_pendente(self) -> None:
        self._status = StatusTransacao.PENDENTE
    
    #Marca transação como concluída
    def marcar_como_concluida(self) -> None:
        self._status = StatusTransacao.CONCLUIDA
    
    #Marca transação como erro e identifica o motivo do erro
    def marcar_como_erro(self, motivo: str) -> None:
        self._status = StatusTransacao.ERRO
        self._observacao = f"ERRO: {motivo}"
    
    #Cancela a transação e identifica o motivo do cancelamento
    def cancelar(self, motivo: str) -> None:
        self._status = StatusTransacao.CANCELADA
        self._observacao = f"CANCELADA: {motivo}"
    
    #retorna o resumo da transação 
    def obter_detalhes(self) -> dict:
        return {
            'id_transacao': self._id_transacao,
            'id_beneficiario': self._id_beneficiario,
            'id_credito': self._id_credito,
            'quantidade_kwh': self._quantidade_kwh,
            'tipo_movimento': self._tipo_movimento.value,
            'status': self._status.value,
            'data_transacao': self._data_transacao.strftime('%d/%m/%Y %H:%M:%S'),
            'observacao': self._observacao
        }