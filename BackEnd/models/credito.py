#criando a classe credito que representa os créditos de energia solar doados.
from datetime import datetime, timedelta
from typing import Optional
from enum import Enum

#definindo os status possiveis do credito 
class StatusCredito(Enum):
    DISPONIVEL = "DISPONIVEL"
    PARCIALMENTE_UTILIZADO = "PARCIALMENTE_UTILIZADO"
    ESGOTADO = "ESGOTADO"
    EXPIRADO = "EXPIRADO"
    BLOQUEADO = "BLOQUEADO"

""" 
Representa um lote de créditos de energia doados.
Permite consumo parcial e controle de expiração.
"""
class Credito:
    def __init__(
        self,
        id_credito: int,
        id_doador: int,
        quantidade_inicial_kwh: float,
        data_expiracao: Optional[datetime] = None,
        meses_validade: int = 12
    ):
        if quantidade_inicial_kwh <= 0:
            raise ValueError("Quantidade deve ser positiva")
        
        self._id_credito = id_credito
        self._id_doador = id_doador
        self._quantidade_inicial_kwh = quantidade_inicial_kwh
        self._quantidade_disponivel_kwh = quantidade_inicial_kwh
        self._data_criacao = datetime.now()
        
        # Define data de expiração
        if data_expiracao:
            self._data_expiracao = data_expiracao
        else:
            self._data_expiracao = self._data_criacao + timedelta(days=meses_validade * 30)
        
        self._status = StatusCredito.DISPONIVEL
        self._historico_consumo: list = []
    
    #Retorna o identificador do credito
    @property
    def id_credito(self) -> int:
        return self._id_credito
    
    #Retorna quem o identificado de quem doou o credito
    @property
    def id_doador(self) -> int:
        return self._id_doador
    
    #Retorna quanto que tem de KWH nos momentos iniciais (sem gastar nada)
    @property
    def quantidade_inicial_kwh(self) -> float:
        return self._quantidade_inicial_kwh
    
    #Retorna a quantidade de credito disponivel ainda
    @property
    def quantidade_disponivel_kwh(self) -> float:
        return self._quantidade_disponivel_kwh
    
    #Retorna quanto já foi consumido do crédito
    @property
    def quantidade_consumida_kwh(self) -> float:
        return self._quantidade_inicial_kwh - self._quantidade_disponivel_kwh
    
    #Retorna percentual consumido (0-100%).
    @property
    def percentual_consumido(self) -> float:
        return (self.quantidade_consumida_kwh / self._quantidade_inicial_kwh) * 100
    
    #Data/hora em que o crédito foi criado
    @property
    def data_criacao(self) -> datetime:
        return self._data_criacao
    
    #Data/hora em que o crédito expira
    @property
    def data_expiracao(self) -> datetime:
        return self._data_expiracao
    
    #Retorna o status do credito entre disponivel, parcialmente utilizado, esgotado, expirado ou bloqueado
    @property
    def status(self) -> StatusCredito:
        return self._status
    
    #Retorna cópia do histórico de consumo
    @property
    def historico_consumo(self) -> list:
        return self._historico_consumo.copy()
    
    #Verificando se o credito ja expirou ou nao
    def esta_expirado(self) -> bool:
        return datetime.now() > self._data_expiracao
    
    #calculando quantos dias falta para a expiração do credito
    def dias_ate_expiracao(self) -> int:
        delta = self._data_expiracao - datetime.now()
        return delta.days
    
    #fazendo o registro do consumo de credito do beneficiario e tbm toda a parte de atualiização do processo de qtd de credito disponivel
    def consumir(self, quantidade_kwh: float, id_beneficiario: int) -> float:
        """
        Args:
            quantidade_kwh: Quantidade a consumir
            id_beneficiario: ID do beneficiário que está consumindo
            
        Returns:
            Quantidade efetivamente consumida
            
        Raises:
            ValueError: Se crédito estiver expirado ou bloqueado
        """
        # Verificações
        if self.esta_expirado():
            self._status = StatusCredito.EXPIRADO
            raise ValueError("Crédito expirado")
        
        if self._status == StatusCredito.BLOQUEADO:
            raise ValueError("Crédito bloqueado")
        
        if self._status == StatusCredito.ESGOTADO:
            raise ValueError("Crédito já esgotado")
        
        # Calcula quanto pode consumir
        quantidade_a_consumir = min(quantidade_kwh, self._quantidade_disponivel_kwh)
        
        if quantidade_a_consumir <= 0:
            return 0.0
        
        # Realiza consumo
        self._quantidade_disponivel_kwh -= quantidade_a_consumir
        
        # Registra no histórico
        self._historico_consumo.append({
            'data': datetime.now(),
            'quantidade_kwh': quantidade_a_consumir,
            'id_beneficiario': id_beneficiario,
            'saldo_apos': self._quantidade_disponivel_kwh
        })
        
        # Atualiza status
        if self._quantidade_disponivel_kwh <= 0:
            self._status = StatusCredito.ESGOTADO
        elif self._quantidade_disponivel_kwh < self._quantidade_inicial_kwh:
            self._status = StatusCredito.PARCIALMENTE_UTILIZADO
        
        return quantidade_a_consumir
    
    #Bloqueia o crédito impedindo seu uso
    def bloquear(self) -> None:
        self._status = StatusCredito.BLOQUEADO
    
    #Desbloqueia o crédito
    def desbloquear(self) -> None:
        if self._status == StatusCredito.BLOQUEADO:
            if self._quantidade_disponivel_kwh > 0:
                self._status = StatusCredito.PARCIALMENTE_UTILIZADO if self.quantidade_consumida_kwh > 0 else StatusCredito.DISPONIVEL
    
    #verifica se ja expirou o credito do usuario ou nao e atualiza seu status
    def verificar_e_atualizar_status(self) -> StatusCredito:
        if self.esta_expirado() and self._status != StatusCredito.ESGOTADO:
            self._status = StatusCredito.EXPIRADO
        
        return self._status
    
    def __repr__(self) -> str:
        return (f"<Credito(id={self._id_credito}, doador_id={self._id_doador}, "
            f"disponivel={self._quantidade_disponivel_kwh:.2f}/{self._quantidade_inicial_kwh:.2f} kWh, "
            f"status={self._status.value})>")