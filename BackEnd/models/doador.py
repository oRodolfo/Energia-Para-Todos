#criando a classe de doador que é responsavel por fornecer os creditos de energia
from datetime import datetime
from typing import Dict, Any, List
from enum import Enum
from models.base import PerfilUsuario, TipoUsuario
from mixins.audit_mixin import AuditMixin

#tipo de classificação que um doador pode ser entre pessoa fisica e pessoa juridica
class ClassificacaoDoador(Enum):
    PESSOA_FISICA = "PESSOA_FISICA"
    PESSOA_JURIDICA = "PESSOA_JURIDICA"

"""
Criando a classe doador onde ira herda os atributos e metodos da classe base (dados)
E tambem herda os atributos e metodos da classe aduditoria onde registra todo e qualquer processo feito pelo doadors
"""
class Doador(AuditMixin, PerfilUsuario):
    def __init__(
        self,
        id_doador: int,
        id_usuario: int,
        nome: str,
        email: str,
        telefone: str,
        cep: str,
        classificacao: ClassificacaoDoador = ClassificacaoDoador.PESSOA_FISICA,
        data_cadastro: datetime = None
    ):
        AuditMixin.__init__(self)
        PerfilUsuario.__init__(
            self,
            id_usuario=id_usuario,
            nome=nome,
            email=email,
            telefone=telefone,
            cep=cep,
            tipo_usuario=TipoUsuario.DOADOR
        )
        
        self._id_doador = id_doador
        self._classificacao = classificacao
        self._data_cadastro_doador = data_cadastro or datetime.now()
        self._total_kwh_doados = 0.0
        self._total_doacoes = 0
        self._creditos_ativos: List[int] = []  # IDs dos créditos ativos
    
    #Retornando o ID do doador
    @property
    def id_doador(self) -> int:
        return self._id_doador
    
    #Retornando a classificacao (se é pessoa fisica ou juridica) do doador
    @property
    def classificacao(self) -> ClassificacaoDoador:
        return self._classificacao
    
    #se caso o usuario quiser trocar de pessoa fisica para juridica, ja altera e registra no historico essa troca
    @classificacao.setter
    def classificacao(self, valor: ClassificacaoDoador) -> None:
        valor_antigo = self._classificacao
        self._classificacao = valor
        self.registrar_alteracao(
            campo='classificacao',
            valor_antigo=valor_antigo.value,
            valor_novo=valor.value
        )
    
    #Retornando o total de kWh doado de todas as doações do doador
    @property
    def total_kwh_doados(self) -> float:
        return self._total_kwh_doados
    
    #Retonando a quantidade total de doações feitas
    @property
    def total_doacoes(self) -> int:
        return self._total_doacoes
    
    #Retornando uma lista com todos os identificadores dos creditos que os beneficiarios pode utilizar ainda 
    @property
    def creditos_ativos(self) -> List[int]:
        return self._creditos_ativos.copy()
    
    #Registrando uma nova doação
    def registrar_doacao(self, id_credito: int, quantidade_kwh: float) -> None:
        self._creditos_ativos.append(id_credito)
        self._total_kwh_doados += quantidade_kwh
        self._total_doacoes += 1
        
        self.registrar_alteracao(
            campo='doacao',
            valor_antigo=None,
            valor_novo=f'{quantidade_kwh} kWh',
            observacao=f'Doação registrada - Crédito ID: {id_credito}'
        )
    
    #Removendo o credito da lista dos creditos do doador caso esse credito acabou ou expirou e o beneficiario nao utilizou
    def remover_credito(self, id_credito: int) -> None:
        if id_credito in self._creditos_ativos:
            self._creditos_ativos.remove(id_credito)
    
    #Fazendo o calculo de quanto que o doador ajudou com a doação dele (0.80 é o valor minimo de preço do kWh (quilowatt-hora) de energia elétrica)
    def calcular_impacto_social(self, preco_kwh: float = 0.80) -> Dict[str, Any]:
        economia_estimada = self._total_kwh_doados * preco_kwh
        
        return {
            'total_kwh_doados': self._total_kwh_doados,
            'total_doacoes': self._total_doacoes,
            'economia_estimada_reais': round(economia_estimada, 2),
            'creditos_ativos': len(self._creditos_ativos),
            'classificacao': self._classificacao.value
        }
    
    #Retornando o resumo completo do doador incluindo todos os registros feitos por ele mesmo
    def obter_resumo(self) -> Dict[str, Any]:
        resumo_base = {
            'id_doador': self._id_doador,
            'id_usuario': self._id_usuario,
            'nome': self._nome,
            'email': self._email,
            'classificacao': self._classificacao.value,
            'status': self._status.value,
            'total_kwh_doados': self._total_kwh_doados,
            'total_doacoes': self._total_doacoes,
            'creditos_ativos': len(self._creditos_ativos)
        }
        
        # Adiciona informações de auditoria (registro de cada processo feito)
        resumo_base.update(self.obter_info_auditoria())
        
        return resumo_base
    
    #Validadando se o perfil do doador esta completo ou se esta falando alguma informação
    def validar_perfil(self) -> bool:
        validacoes_base = [
            self._nome and len(self._nome.strip()) >= 3,
            self._email and '@' in self._email,
            self._classificacao is not None
        ]
        
        return all(validacoes_base)
    
    #Print de como sera mostrado as informações do doador
    def __repr__(self) -> str:
        return (f"<Doador(id={self._id_doador}, nome='{self._nome}', "
                f"classificacao={self._classificacao.value}, "
                f"total_kwh={self._total_kwh_doados:.2f})>")