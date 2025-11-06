#criando a classe beneficiario que representa um beneficiário de créditos de energia.
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum
from models.base import PerfilUsuario, TipoUsuario
from mixins.audit_mixin import AuditMixin

#Status específico do beneficiário.
class StatusBeneficiario(Enum):
    AGUARDANDO_APROVACAO = "AGUARDANDO_APROVACAO"
    APROVADO = "APROVADO"
    EM_ATENDIMENTO = "EM_ATENDIMENTO"
    SUSPENSO = "SUSPENSO"
    INATIVO = "INATIVO"

"""
Criando a classe doador onde ira herda os atributos e metodos da classe base (dados)
E tambem herda os atributos e metodos da classe aduditoria onde registra todo e qualquer processo feito pelo beneficiario
"""
class Beneficiario(AuditMixin, PerfilUsuario):
    def __init__(
        self,
        id_beneficiario: int,
        id_usuario: int,
        nome: str,
        email: str,
        telefone: str,
        cep: str,
        renda_familiar: float,
        consumo_medio_kwh: float,
        num_moradores: int = 1,
        data_aprovacao: Optional[datetime] = None
    ):
        AuditMixin.__init__(self)
        PerfilUsuario.__init__(
            self,
            id_usuario=id_usuario,
            nome=nome,
            email=email,
            telefone=telefone,
            cep=cep,
            tipo_usuario=TipoUsuario.BENEFICIARIO
        )
        
        self._id_beneficiario = id_beneficiario
        self._renda_familiar = renda_familiar
        self._consumo_medio_kwh = consumo_medio_kwh
        self._num_moradores = num_moradores
        self._data_aprovacao = data_aprovacao
        self._status_beneficiario = (StatusBeneficiario.APROVADO 
                                    if data_aprovacao 
                                    else StatusBeneficiario.AGUARDANDO_APROVACAO)
        
        self._saldo_creditos_kwh = 0.0
        self._total_recebido_kwh = 0.0
        self._total_transacoes = 0
        self._data_entrada_fila: Optional[datetime] = None
        self._ultima_data_atendimento: Optional[datetime] = None
    
    #Retonando o identificador do beneficiario
    @property
    def id_beneficiario(self) -> int:
        return self._id_beneficiario
    
    #Retornando a renda familiar identificada pelo beneficiario
    @property
    def renda_familiar(self) -> float:
        return self._renda_familiar
    
    #atualizando a renda familiar e validando se realmente é valida (pois a renda nao pode ser menor que 0)
    @renda_familiar.setter
    def renda_familiar(self, valor: float) -> None:
        if valor < 0:
            raise ValueError("Renda não pode ser negativa")
        valor_antigo = self._renda_familiar
        self._renda_familiar = valor
        self.registrar_alteracao('renda_familiar', valor_antigo, valor)
    
    #Retornando o consumo medio do beneficiario
    @property
    def consumo_medio_kwh(self) -> float:
        return self._consumo_medio_kwh
    
    #Atualizando o consumo medio do beneficiario e validando se realmente é real o consumo (pois o consumo não pode ser menor que 0)
    @consumo_medio_kwh.setter
    def consumo_medio_kwh(self, valor: float) -> None:
        if valor < 0:
            raise ValueError("Consumo não pode ser negativo")
        valor_antigo = self._consumo_medio_kwh
        self._consumo_medio_kwh = valor
        self.registrar_alteracao('consumo_medio_kwh', valor_antigo, valor)
    
    #Retornando a quantidade de moradores da casa
    @property
    def num_moradores(self) -> int:
        return self._num_moradores
    
    #atualizando a quantidade de moradores da casa e fazendo a validação se realmente ainda tem gente morando na casa
    @num_moradores.setter
    def num_moradores(self, valor: int) -> None:
        if valor < 1:
            raise ValueError("Número de moradores deve ser pelo menos 1")
        valor_antigo = self._num_moradores
        self._num_moradores = valor
        self.registrar_alteracao('num_moradores', valor_antigo, valor)
    
    #Retornando o status do beneficiario se esta entre aguardando aprovação, aprovado, em atendimento, suspenso ou inativo
    @property
    def status_beneficiario(self) -> StatusBeneficiario:
        return self._status_beneficiario
    
    #Retornando quanto que o beneficiario tem de credito de energia disponivel
    @property
    def saldo_creditos_kwh(self) -> float:
        return self._saldo_creditos_kwh
    
    #Retonando quanto que o beneficiario ja recebeu ao total de credito de energia
    @property
    def total_recebido_kwh(self) -> float:
        return self._total_recebido_kwh
    
    #Retorna a quantidade de vezes que o beneficiario foi contemplado com os creditos de energia
    @property
    def total_transacoes(self) -> int:
        return self._total_transacoes
    
    #Retorna a data em que o beneciario entra na fila, informação importante para os pesos de priorizacao
    @property
    def data_entrada_fila(self) -> Optional[datetime]:
        return self._data_entrada_fila
    
    #Retorna quando foi a ultima vez que recebeu os creditos de energiia
    @property
    def ultima_data_atendimento(self) -> Optional[datetime]:
        return self._ultima_data_atendimento
    
    #Verificando se o beneficiario esta aprovado para receber os creditos
    def aprovar(self) -> None:
        self._status_beneficiario = StatusBeneficiario.APROVADO
        self._data_aprovacao = datetime.now()
        self.registrar_alteracao(
            campo='status_beneficiario',
            valor_antigo=StatusBeneficiario.AGUARDANDO_APROVACAO.value,
            valor_novo=StatusBeneficiario.APROVADO.value
        )
    
    #Definindo quando que o beneficiario entrou na fila de espera
    def entrar_fila(self) -> None:
        self._data_entrada_fila = datetime.now()
    
    #Registrando quando o beneficiario recebe os creditos
    def receber_creditos(self, quantidade_kwh: float) -> None:
        if quantidade_kwh <= 0:
            raise ValueError("Quantidade deve ser positiva")
        
        self._saldo_creditos_kwh += quantidade_kwh
        self._total_recebido_kwh += quantidade_kwh
        self._total_transacoes += 1
        self._ultima_data_atendimento = datetime.now()
        self._status_beneficiario = StatusBeneficiario.EM_ATENDIMENTO
        
        self.registrar_alteracao(
            campo='recebimento_creditos',
            valor_antigo=self._saldo_creditos_kwh - quantidade_kwh,
            valor_novo=self._saldo_creditos_kwh,
            observacao=f'Recebido {quantidade_kwh} kWh'
        )
    
    #Registrando quanto que o beneficiario consome de energia 
    def consumir_creditos(self, quantidade_kwh: float) -> None:
        if quantidade_kwh > self._saldo_creditos_kwh:
            raise ValueError("Saldo insuficiente")
        
        self._saldo_creditos_kwh -= quantidade_kwh
    
    #Fazendo o calculo das prioridades a ser dada para o beneficiario conforme identificado pelo admin pelos pesos de prioridade
    def calcular_prioridade(
       self,
        renda: float = 0.5,
        consumo: float = 0.2,
        moradores: float = 0.2,
        tempo_fila: float = 0.1,
        **kwargs
    ) -> float:
        """
        Calcula pontuação de prioridade do beneficiário.
        Aceita tanto 'renda/consumo/moradores/tempo_fila' quanto
        'peso_renda/peso_consumo/peso_moradores/peso_tempo_fila'.
        """

        # Aceita aliases (retrocompatibilidade)
        renda = kwargs.get("peso_renda", renda)
        consumo = kwargs.get("peso_consumo", consumo)
        moradores = kwargs.get("peso_moradores", moradores)
        tempo_fila = kwargs.get("peso_tempo_fila", tempo_fila)

        # --- suas normalizações originais (exemplo que você já tinha) ---
        # renda menor => maior prioridade (máx 10k)
        score_renda = max(0, (10000 - self._renda_familiar) / 10000) * 100
        # consumo menor => maior prioridade (máx 500 kWh)
        score_consumo = max(0, (500 - self._consumo_medio_kwh) / 500) * 100
        # mais moradores => maior prioridade (máx 10)
        score_moradores = min(self._num_moradores / 10, 1.0) * 100
        # tempo em fila
        score_tempo = 0.0
        if self._data_entrada_fila:
            dias_em_fila = (datetime.now() - self._data_entrada_fila).days
            score_tempo = min(dias_em_fila / 365, 1.0) * 100

        prioridade = (
            score_renda * renda
            + score_consumo * consumo
            + score_moradores * moradores
            + score_tempo * tempo_fila
        )
        return round(prioridade, 2)
    
    #Verificando se o beneficiario ainda esta precisando de creditos de energia
    def verificar_necessidade_continua(self) -> bool:
        # Considera que precisa se:
        # Saldo atual < consumo médio mensal
        # Ou se não foi atendido nos últimos 60 dias
        if self._saldo_creditos_kwh < self._consumo_medio_kwh:
            return True
        
        if self._ultima_data_atendimento:
            dias_desde_ultimo = (datetime.now() - self._ultima_data_atendimento).days
            return dias_desde_ultimo > 60
        
        return True
    
    #Retorna o resumo sobre o beneficiario com seus dados e com todas as informações de registro (auditoria)
    def obter_resumo(self) -> Dict[str, Any]:
        resumo = {
            'id_beneficiario': self._id_beneficiario,
            'id_usuario': self._id_usuario,
            'nome': self._nome,
            'email': self._email,
            'status': self._status_beneficiario.value,
            'renda_familiar': self._renda_familiar,
            'consumo_medio_kwh': self._consumo_medio_kwh,
            'num_moradores': self._num_moradores,
            'saldo_creditos_kwh': self._saldo_creditos_kwh,
            'total_recebido_kwh': self._total_recebido_kwh,
            'total_transacoes': self._total_transacoes
        }
        
        # Adiciona informações de auditoria
        resumo.update(self.obter_info_auditoria())
        return resumo
    
    #validando se nao precisa de mais nenhuma informação no cadastro do beneficiario
    def validar_perfil(self) -> bool:
        validacoes = [
            self._nome and len(self._nome.strip()) >= 3,
            self._email and '@' in self._email,
            self._renda_familiar >= 0,
            self._consumo_medio_kwh > 0,
            self._num_moradores >= 1,
            self._status_beneficiario != StatusBeneficiario.SUSPENSO
        ]
        
        return all(validacoes)
    
    #Print de como sera mostrado as informações do doador
    def __repr__(self) -> str:
        return (f"<Beneficiario(id={self._id_beneficiario}, nome='{self._nome}', "
                f"renda={self._renda_familiar:.2f}, "
                f"saldo={self._saldo_creditos_kwh:.2f} kWh)>")