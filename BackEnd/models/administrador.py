#criando a classe administrador que sera feita a gerencia configurações e operações do sistema.
from datetime import datetime
from typing import Dict, Any, Optional
from models.base import PerfilUsuario, TipoUsuario
from mixins.audit_mixin import AuditMixin

"""
Classe que representa um administrador do sistema.
Possui permissões especificas para ajustar configurações e aprovar beneficiários.
"""
class Administrador(AuditMixin, PerfilUsuario):
    def __init__(
        self,
        id_administrador: int,
        id_usuario: int,
        nome: str,
        email: str,
        telefone: str,
        cep: str,
        data_cadastro: Optional[datetime] = None
    ):
        PerfilUsuario.__init__(
            self,
            id_usuario=id_usuario,
            nome=nome,
            email=email,
            telefone=telefone,
            cep=cep,
            tipo_usuario=TipoUsuario.ADMINISTRADOR
        )
        AuditMixin.__init__(self)
        
        self._id_administrador = id_administrador
        self._data_cadastro_admin = data_cadastro or datetime.now()
        self._total_acoes_realizadas = 0
        
        # Configurações padrão dos pesos de priorização de 0 a 1, quanto maior mais prioridade (podem ser ajustadas)
        self._pesos_priorizacao: Dict[str, float] = {
            'renda': 0.5,
            'consumo': 0.2,
            'moradores': 0.2,
            'tempo_fila': 0.1
        }
    
    #Retorna o identificador do administrador
    @property
    def id_administrador(self) -> int:
        return self._id_administrador
    
    #Retorna cópia dos pesos atuais
    @property
    def pesos_priorizacao(self) -> Dict[str, float]:
        return self._pesos_priorizacao.copy()
    
    #Ajustando os pesos caso for necessario
    def ajustar_pesos_priorizacao(
        self,
        peso_renda: Optional[float] = None,
        peso_consumo: Optional[float] = None,
        peso_moradores: Optional[float] = None,
        peso_tempo_fila: Optional[float] = None
    ) -> None:
        """
        Ajusta os pesos usados no cálculo de prioridade.
        
        Args:
            peso_renda: Novo peso para renda
            peso_consumo: Novo peso para consumo
            peso_moradores: Novo peso para número de moradores
            peso_tempo_fila: Novo peso para tempo em fila
            
        Raises:
            ValueError: Se a soma dos pesos não for 1.0
        """
        pesos_antigos = self._pesos_priorizacao.copy()
        
        if peso_renda is not None:
            self._pesos_priorizacao['renda'] = peso_renda
        if peso_consumo is not None:
            self._pesos_priorizacao['consumo'] = peso_consumo
        if peso_moradores is not None:
            self._pesos_priorizacao['moradores'] = peso_moradores
        if peso_tempo_fila is not None:
            self._pesos_priorizacao['tempo_fila'] = peso_tempo_fila
        
        # Validar que soma = 1.0
        soma = sum(self._pesos_priorizacao.values())
        if abs(soma - 1.0) > 0.01:  # tolerância para arredondamento
            self._pesos_priorizacao = pesos_antigos
            raise ValueError(f"Soma dos pesos deve ser 1.0 (atual: {soma:.2f})")
        
        self.registrar_alteracao(
            campo='pesos_priorizacao',
            valor_antigo=str(pesos_antigos),
            valor_novo=str(self._pesos_priorizacao),
            usuario_id=self._id_usuario
        )
        
        self._total_acoes_realizadas += 1
    
    #Registrando qualquer ação feita pelo admistrador
    def registrar_acao_administrativa(self, descricao: str) -> None:
        self.registrar_alteracao(
            campo='acao_administrativa',
            valor_antigo=None,
            valor_novo=descricao,
            usuario_id=self._id_usuario
        )
        self._total_acoes_realizadas += 1
    
    #Retornando o resumo completo sobre o administrador
    def obter_resumo(self) -> Dict[str, Any]:
        resumo = {
            'id_administrador': self._id_administrador,
            'id_usuario': self._id_usuario,
            'nome': self._nome,
            'email': self._email,
            'total_acoes_realizadas': self._total_acoes_realizadas,
            'pesos_priorizacao_atuais': self._pesos_priorizacao
        }
        
        resumo.update(self.obter_info_auditoria())
        
        return resumo
    
    #Validadando se nao falta nenhuma informação no cadastro do admistrador
    def validar_perfil(self) -> bool:
        validacoes = [
            self._nome and len(self._nome.strip()) >= 3,
            self._email and '@' in self._email
        ]
        
        return all(validacoes)
    
    #Print de como sera mostrado as informações do administrador
    def __repr__(self) -> str:
        return (f"<Administrador(id={self._id_administrador}, nome='{self._nome}', ")