#criando a classe FilaEspera que gerencia fila de beneficiários com priorização.

from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum
from models.beneficiario import Beneficiario

#identifica qual status do beneficiario da fila entre: aguardando, em distribuicao, atentido ou removido
class StatusFila(Enum):
    AGUARDANDO = "AGUARDANDO"
    EM_DISTRIBUICAO = "EM_DISTRIBUICAO"
    ATENDIDO = "ATENDIDO"
    REMOVIDO = "REMOVIDO"

#identifica as informações do beneficiario da fila (com seus dados e a data que entrou) 
class ItemFila:
    def __init__(
        self,
        beneficiario: Beneficiario,
        data_entrada: Optional[datetime] = None
    ):
        self.beneficiario = beneficiario
        self.data_entrada = data_entrada or datetime.now()
        self.posicao_atual = 0
        self.prioridade_calculada = 0.0
        self.status = StatusFila.AGUARDANDO
        self.historico_posicoes: List[Dict] = []
    
    def atualizar_posicao(self, nova_posicao: int) -> None:
        """Atualiza posição e registra no histórico."""
        self.historico_posicoes.append({
            'data': datetime.now(),
            'posicao_anterior': self.posicao_atual,
            'posicao_nova': nova_posicao
        })
        self.posicao_atual = nova_posicao
    
    def __repr__(self) -> str:
        return (f"<ItemFila(beneficiario={self.beneficiario.nome}, "
                f"posicao={self.posicao_atual}, prioridade={self.prioridade_calculada:.2f})>")

"""
Gerencia fila de espera de beneficiários com sistema de priorização.
Implementa ordenação dinâmica baseada em critérios configuráveis.
"""
class FilaEspera:
    def __init__(self, id_temporada: int, nome_temporada: str = "Padrão"):
        self._id_temporada = id_temporada
        self._nome_temporada = nome_temporada
        self._itens: List[ItemFila] = []
        self._pesos_priorizacao = {
            'renda': 0.5,
            'consumo': 0.2,
            'moradores': 0.2,
            'tempo_fila': 0.1
        }
    
    #Retorna quantidade de beneficiários na fila
    @property
    def tamanho(self) -> int:
        return len([item for item in self._itens if item.status == StatusFila.AGUARDANDO])
    
    #Retorna cópia dos pesos de priorização
    @property
    def pesos_priorizacao(self) -> Dict[str, float]:
        return self._pesos_priorizacao.copy()
    
    """
    Configura pesos de priorização e reordena a fila.
        
    Args:
        peso_renda: Peso da renda familiar
        peso_consumo: Peso do consumo médio
        peso_moradores: Peso do número de moradores
        peso_tempo_fila: Peso do tempo em fila
    """
    def configurar_pesos(
        self,
        renda: Optional[float] = None,
        consumo: Optional[float] = None,
        moradores: Optional[float] = None,
        tempo_fila: Optional[float] = None,
    ) -> None:
        """Atualiza pesos de priorização. A soma deve ser 1.0 (±0.01)."""
        novos = self._pesos_priorizacao.copy()
        if renda is not None:
            novos["renda"] = renda
        if consumo is not None:
            novos["consumo"] = consumo
        if moradores is not None:
            novos["moradores"] = moradores
        if tempo_fila is not None:
            novos["tempo_fila"] = tempo_fila

        soma = sum(novos.values())
        if abs(soma - 1.0) > 0.01:
            raise ValueError(f"Soma dos pesos deve ser 1.0 (atual: {soma:.2f})")

        self._pesos_priorizacao = novos
    
    #adicionando o beneficiario na fila
    def adicionar_beneficiario(self, beneficiario: Beneficiario) -> None:
        # Verifica se já está na fila
        if any(item.beneficiario.id_beneficiario == beneficiario.id_beneficiario 
               for item in self._itens):
            raise ValueError("Beneficiário já está na fila")
        
        # Marca entrada na fila no beneficiário
        beneficiario.entrar_fila()
        
        # Cria item e adiciona
        item = ItemFila(beneficiario)
        self._itens.append(item)
        
        # Reordena para posicionar corretamente
        self.reordenar_fila()
    
    #removendo da fila
    def remover_beneficiario(self, id_beneficiario: int) -> bool:
        for item in self._itens:
            if item.beneficiario.id_beneficiario == id_beneficiario:
                item.status = StatusFila.REMOVIDO
                self._itens.remove(item)
                self.reordenar_fila()
                return True
        return False
    
    """ 
    reordenando (reorganizando) a fila apos a inclusão do novo beneficiario e seguindo as regras de prioridade:
    Itens com MAIOR prioridade ficam no início.
    """
    def reordenar_fila(self) -> None:
        itens_ativos = [item for item in self._itens if item.status == StatusFila.AGUARDANDO]
        
        # Calcula prioridade de cada um
        for item in itens_ativos:
            item.prioridade_calculada = item.beneficiario.calcular_prioridade(
                peso_renda=self._pesos_priorizacao['renda'],
                peso_consumo=self._pesos_priorizacao['consumo'],
                peso_moradores=self._pesos_priorizacao['moradores'],
                peso_tempo_fila=self._pesos_priorizacao['tempo_fila']
            )
        
        # Ordena por prioridade (maior primeiro)
        itens_ativos.sort(key=lambda x: x.prioridade_calculada, reverse=True)
        
        # Atualiza posições
        for idx, item in enumerate(itens_ativos, start=1):
            item.atualizar_posicao(idx)
        
        # Substitui lista
        self._itens = itens_ativos + [item for item in self._itens if item.status != StatusFila.AGUARDANDO]
    
    #obtendo os primeiros beneficiarios para a fila
    def obter_primeiros(self, quantidade: int) -> List[Beneficiario]:
        itens_ativos = [item for item in self._itens if item.status == StatusFila.AGUARDANDO]
        return [item.beneficiario for item in itens_ativos[:quantidade]]
    
    #obtendo a posicao atual do beneficiario da fila atual
    def obter_posicao(self, id_beneficiario: int) -> Optional[int]:
        for item in self._itens:
            if (item.beneficiario.id_beneficiario == id_beneficiario and 
                item.status == StatusFila.AGUARDANDO):
                return item.posicao_atual
        return None
    
    #atualizando os status dos beneficiarios da fila ao mesmo tempo, quando o sistema começa a distribuir os créditos.
    def marcar_em_distribuicao(self, ids_beneficiarios: List[int]) -> None:
        for item in self._itens:
            if item.beneficiario.id_beneficiario in ids_beneficiarios:
                item.status = StatusFila.EM_DISTRIBUICAO
    
    #identificando quais beneficiarios ja foram atendidos e autenticando os mesmos
    def marcar_atendidos(self, ids_beneficiarios: List[int]) -> None:
        for item in self._itens:
            if item.beneficiario.id_beneficiario in ids_beneficiarios:
                item.status = StatusFila.ATENDIDO

    """
    Realocando beneficiários atendidos de volta para a fila se ainda precisam.
    Removendo da fila se não precisam mais.
    """
    def realocar_atendidos(self) -> None:
      
        for item in self._itens[:]:  # Cópia para modificar durante iteração
            if item.status == StatusFila.ATENDIDO:
                if item.beneficiario.verificar_necessidade_continua():
                    # Ainda precisa, volta para aguardando
                    item.status = StatusFila.AGUARDANDO
                else:
                    # Não precisa mais, remove
                    item.status = StatusFila.REMOVIDO
                    self._itens.remove(item)
        
        # Reordena após realocação
        self.reordenar_fila()
    
    #retornando as informações completa da fila
    def obter_estatisticas(self) -> Dict[str, Any]:
        total_itens = len(self._itens)
        aguardando = sum(1 for item in self._itens if item.status == StatusFila.AGUARDANDO)
        em_distribuicao = sum(1 for item in self._itens if item.status == StatusFila.EM_DISTRIBUICAO)
        atendidos = sum(1 for item in self._itens if item.status == StatusFila.ATENDIDO)
        
        if aguardando > 0:
            prioridades = [item.prioridade_calculada for item in self._itens 
                          if item.status == StatusFila.AGUARDANDO]
            prioridade_media = sum(prioridades) / len(prioridades)
            prioridade_max = max(prioridades)
            prioridade_min = min(prioridades)
        else:
            prioridade_media = prioridade_max = prioridade_min = 0.0
        
        return {
            'total_itens': total_itens,
            'aguardando': aguardando,
            'em_distribuicao': em_distribuicao,
            'atendidos': atendidos,
            'prioridade_media': round(prioridade_media, 2),
            'prioridade_maxima': round(prioridade_max, 2),
            'prioridade_minima': round(prioridade_min, 2),
            'pesos_atuais': self._pesos_priorizacao
        }
    
    #Lista beneficiários na fila com suas informações
    def listar_fila(self, limite: int = None) -> List[Dict[str, Any]]:
        itens_ativos = [item for item in self._itens if item.status == StatusFila.AGUARDANDO]
        
        if limite:
            itens_ativos = itens_ativos[:limite]
        
        resultado = []
        for item in itens_ativos:
            resultado.append({
                'posicao': item.posicao_atual,
                'id_beneficiario': item.beneficiario.id_beneficiario,
                'nome': item.beneficiario.nome,
                'prioridade': round(item.prioridade_calculada, 2),
                'renda_familiar': item.beneficiario.renda_familiar,
                'consumo_medio_kwh': item.beneficiario.consumo_medio_kwh,
                'num_moradores': item.beneficiario.num_moradores,
                'dias_em_fila': (datetime.now() - item.data_entrada).days
            })
        
        return resultado
    
    def __repr__(self) -> str:
        return (f"<FilaEspera(temporada='{self._nome_temporada}', "
                f"aguardando={self.tamanho}, total={len(self._itens)})>")