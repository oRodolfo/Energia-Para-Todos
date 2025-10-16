"""
Serviço DistribuidorCreditos - realiza distribuição automática proporcional.
"""
from typing import List, Dict, Any, Tuple
from datetime import datetime

from models.credito import Credito, StatusCredito
from models.beneficiario import Beneficiario
from models.transacao import Transacao, TipoMovimento, StatusTransacao
from models.fila_espera import FilaEspera
from utils.logger_auditoria import LoggerAuditoria, TipoAcao, StatusLog

class DistribuidorCreditos:
    """
    Serviço responsável pela distribuição automática e proporcional de créditos.
    Implementa lógica de alocação baseada em prioridades e disponibilidade.
    """
    
    def __init__(self):
        self._creditos_disponiveis: List[Credito] = []
        self._transacoes: List[Transacao] = []
        self._proximo_id_transacao = 1
        self._logger = LoggerAuditoria()
    
    def adicionar_credito(self, credito: Credito) -> None:
        """
        Adiciona crédito ao pool de distribuição.
        
        Args:
            credito: Crédito a adicionar
        """
        if credito.status == StatusCredito.DISPONIVEL or credito.status == StatusCredito.PARCIALMENTE_UTILIZADO:
            self._creditos_disponiveis.append(credito)
            
            self._logger.registrar(
                tipo_acao=TipoAcao.DOACAO,
                status=StatusLog.SUCESSO,
                detalhes=f"Crédito {credito.id_credito} adicionado: {credito.quantidade_disponivel_kwh} kWh",
                dados_adicionais={'id_credito': credito.id_credito, 'id_doador': credito.id_doador}
            )
    
    def remover_creditos_expirados(self) -> List[int]:
        """
        Remove créditos expirados do pool.
        
        Returns:
            Lista de IDs dos créditos removidos
        """
        removidos = []
        for credito in self._creditos_disponiveis[:]:
            if credito.esta_expirado():
                credito.verificar_e_atualizar_status()
                self._creditos_disponiveis.remove(credito)
                removidos.append(credito.id_credito)
                
                self._logger.registrar(
                    tipo_acao=TipoAcao.EXPIRACAO_CREDITO,
                    status=StatusLog.ALERTA,
                    detalhes=f"Crédito {credito.id_credito} expirado e removido",
                    dados_adicionais={'id_credito': credito.id_credito}
                )
        
        return removidos
    
    def obter_total_disponivel(self) -> float:
        """
        Calcula total de kWh disponível para distribuição.
        
        Returns:
            Total de kWh disponível
        """
        return sum(credito.quantidade_disponivel_kwh for credito in self._creditos_disponiveis)
    
    def distribuir_proporcional(
        self,
        fila: FilaEspera,
        num_beneficiarios: int = None
    ) -> Dict[str, Any]:
        """
        Distribui créditos proporcionalmente aos beneficiários prioritários.
        
        Args:
            fila: Fila de espera com beneficiários
            num_beneficiarios: Número de beneficiários a atender (None = todos possíveis)
            
        Returns:
            Dicionário com resultado da distribuição
        """
        # Remove créditos expirados primeiro
        self.remover_creditos_expirados()
        
        # Obtém total disponível
        total_disponivel = self.obter_total_disponivel()
        
        if total_disponivel <= 0:
            return {
                'sucesso': False,
                'mensagem': 'Sem créditos disponíveis para distribuição',
                'total_distribuido': 0,
                'beneficiarios_atendidos': 0
            }
        
        # Obtém beneficiários prioritários
        if num_beneficiarios:
            beneficiarios = fila.obter_primeiros(num_beneficiarios)
        else:
            # Calcula quantos podem ser atendidos com o disponível
            beneficiarios = fila.obter_primeiros(100)  # Limite razoável
        
        if not beneficiarios:
            return {
                'sucesso': False,
                'mensagem': 'Fila de espera vazia',
                'total_distribuido': 0,
                'beneficiarios_atendidos': 0
            }
        
        # Marca como em distribuição
        ids_em_dist = [b.id_beneficiario for b in beneficiarios]
        fila.marcar_em_distribuicao(ids_em_dist)
        
        # Calcula pesos para distribuição proporcional baseado nas prioridades
        prioridades = [b.calcular_prioridade(**fila.pesos_priorizacao) for b in beneficiarios]
        soma_prioridades = sum(prioridades)
        
        # Calcula quanto cada um deve receber proporcionalmente
        alocacoes = []
        for beneficiario, prioridade in zip(beneficiarios, prioridades):
            peso = prioridade / soma_prioridades if soma_prioridades > 0 else 1.0 / len(beneficiarios)
            kwh_alocado = total_disponivel * peso
            alocacoes.append((beneficiario, kwh_alocado))
        
        # Realiza distribuição efetiva
        resultado = self._executar_distribuicao(alocacoes)
        
        # Marca beneficiários como atendidos
        ids_atendidos = [b.id_beneficiario for b in resultado['beneficiarios_atendidos']]
        fila.marcar_atendidos(ids_atendidos)
        
        # Log da operação
        self._logger.registrar(
            tipo_acao=TipoAcao.DISTRIBUICAO,
            status=StatusLog.SUCESSO,
            detalhes=f"Distribuição realizada: {resultado['total_distribuido']:.2f} kWh para {len(ids_atendidos)} beneficiários",
            dados_adicionais=resultado
        )
        
        return resultado
    
    def _executar_distribuicao(
        self,
        alocacoes: List[Tuple[Beneficiario, float]]
    ) -> Dict[str, Any]:
        """
        Executa a distribuição física dos créditos.
        
        Args:
            alocacoes: Lista de tuplas (beneficiário, quantidade_kwh)
            
        Returns:
            Resultado da distribuição
        """
        total_distribuido = 0.0
        beneficiarios_atendidos = []
        transacoes_criadas = []
        
        for beneficiario, quantidade_alvo in alocacoes:
            quantidade_restante = quantidade_alvo
            
            # Tenta consumir de múltiplos créditos se necessário
            for credito in self._creditos_disponiveis:
                if quantidade_restante <= 0:
                    break
                
                if credito.quantidade_disponivel_kwh <= 0:
                    continue
                
                try:
                    # Consome do crédito
                    quantidade_consumida = credito.consumir(
                        quantidade_restante,
                        beneficiario.id_beneficiario
                    )
                    
                    if quantidade_consumida > 0:
                        # Cria transação
                        transacao = Transacao(
                            id_transacao=self._proximo_id_transacao,
                            id_beneficiario=beneficiario.id_beneficiario,
                            id_credito=credito.id_credito,
                            quantidade_kwh=quantidade_consumida,
                            tipo_movimento=TipoMovimento.DISTRIBUICAO,
                            observacao=f"Distribuição proporcional automática"
                        )
                        
                        self._transacoes.append(transacao)
                        transacoes_criadas.append(transacao)
                        self._proximo_id_transacao += 1
                        
                        # Atualiza beneficiário
                        beneficiario.receber_creditos(quantidade_consumida)
                        
                        total_distribuido += quantidade_consumida
                        quantidade_restante -= quantidade_consumida
                
                except Exception as e:
                    # Log erro mas continua
                    self._logger.registrar(
                        tipo_acao=TipoAcao.DISTRIBUICAO,
                        status=StatusLog.ERRO,
                        detalhes=f"Erro ao consumir crédito {credito.id_credito}: {str(e)}"
                    )
            
            # Se recebeu alguma coisa, marca como atendido
            if quantidade_restante < quantidade_alvo:
                beneficiarios_atendidos.append(beneficiario)
        
        # Remove créditos esgotados
        self._creditos_disponiveis = [
            c for c in self._creditos_disponiveis 
            if c.status != StatusCredito.ESGOTADO
        ]
        
        return {
            'sucesso': True,
            'total_distribuido': round(total_distribuido, 2),
            'beneficiarios_atendidos': beneficiarios_atendidos,
            'num_beneficiarios': len(beneficiarios_atendidos),
            'num_transacoes': len(transacoes_criadas),
            'creditos_restantes': len(self._creditos_disponiveis)
        }
    
    def obter_historico_transacoes(
        self,
        id_beneficiario: int = None,
        limite: int = None
    ) -> List[Dict[str, Any]]:
        """
        Obtém histórico de transações.
        
        Args:
            id_beneficiario: Filtrar por beneficiário específico
            limite: Limitar número de resultados
            
        Returns:
            Lista de transações
        """
        transacoes = self._transacoes
        
        if id_beneficiario:
            transacoes = [t for t in transacoes if t.id_beneficiario == id_beneficiario]
        
        transacoes = sorted(transacoes, key=lambda t: t.data_transacao, reverse=True)
        
        if limite:
            transacoes = transacoes[:limite]
        
        return [t.obter_detalhes() for t in transacoes]
    
    def obter_estatisticas(self) -> Dict[str, Any]:
        """
        Retorna estatísticas do distribuidor.
        
        Returns:
            Dicionário com métricas
        """
        total_disponivel = self.obter_total_disponivel()
        total_transacoes = len(self._transacoes)
        total_distribuido = sum(t.quantidade_kwh for t in self._transacoes 
                               if t.status == StatusTransacao.CONCLUIDA)
        
        return {
            'creditos_no_pool': len(self._creditos_disponiveis),
            'kwh_disponivel': round(total_disponivel, 2),
            'total_transacoes': total_transacoes,
            'kwh_total_distribuido': round(total_distribuido, 2),
            'beneficiarios_unicos_atendidos': len(set(t.id_beneficiario for t in self._transacoes))
        }
    
    def __repr__(self) -> str:
        return (f"<DistribuidorCreditos(creditos={len(self._creditos_disponiveis)}, "
                f"kwh_disponivel={self.obter_total_disponivel():.2f})>")