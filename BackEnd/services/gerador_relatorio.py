"""
Serviço GeradorRelatorios - gera relatórios de impacto e análises.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict

from models.doador import Doador
from models.beneficiario import Beneficiario
from models.transacao import Transacao, StatusTransacao


class GeradorRelatorios:
    """
    Serviço para geração de relatórios de impacto social e estatísticas.
    """
    
    def __init__(self):
        self._doadores: List[Doador] = []
        self._beneficiarios: List[Beneficiario] = []
        self._transacoes: List[Transacao] = []
    
    def registrar_doador(self, doador: Doador) -> None:
        """Registra doador para relatórios."""
        if doador not in self._doadores:
            self._doadores.append(doador)
    
    def registrar_beneficiario(self, beneficiario: Beneficiario) -> None:
        """Registra beneficiário para relatórios."""
        if beneficiario not in self._beneficiarios:
            self._beneficiarios.append(beneficiario)
    
    def registrar_transacao(self, transacao: Transacao) -> None:
        """Registra transação para relatórios."""
        self._transacoes.append(transacao)
    
    def gerar_relatorio_impacto_geral(self, preco_kwh: float = 0.80) -> Dict[str, Any]:
        """
        Gera relatório de impacto geral do sistema.
        
        Args:
            preco_kwh: Preço médio do kWh para cálculo de economia
            
        Returns:
            Dicionário com métricas gerais
        """
        # Métricas de doações
        total_doadores = len(self._doadores)
        total_kwh_doados = sum(d.total_kwh_doados for d in self._doadores)
        
        # Métricas de distribuição
        transacoes_concluidas = [t for t in self._transacoes 
                                 if t.status == StatusTransacao.CONCLUIDA]
        total_kwh_distribuidos = sum(t.quantidade_kwh for t in transacoes_concluidas)
        
        # Métricas de beneficiários
        total_beneficiarios = len(self._beneficiarios)
        beneficiarios_atendidos = len(set(t.id_beneficiario for t in transacoes_concluidas))
        
        # Economia estimada
        economia_total = total_kwh_distribuidos * preco_kwh
        
        # Distribuição por classificação de doador
        por_classificacao = defaultdict(lambda: {'quantidade': 0, 'kwh': 0.0})
        for doador in self._doadores:
            classificacao = doador.classificacao.value
            por_classificacao[classificacao]['quantidade'] += 1
            por_classificacao[classificacao]['kwh'] += doador.total_kwh_doados
        
        return {
            'data_relatorio': datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
            'resumo_doacoes': {
                'total_doadores': total_doadores,
                'total_kwh_doados': round(total_kwh_doados, 2),
                'media_kwh_por_doador': round(total_kwh_doados / total_doadores, 2) if total_doadores > 0 else 0
            },
            'resumo_distribuicao': {
                'total_kwh_distribuidos': round(total_kwh_distribuidos, 2),
                'taxa_distribuicao_percentual': round((total_kwh_distribuidos / total_kwh_doados * 100), 2) if total_kwh_doados > 0 else 0,
                'total_transacoes': len(transacoes_concluidas)
            },
            'resumo_beneficiarios': {
                'total_cadastrados': total_beneficiarios,
                'total_atendidos': beneficiarios_atendidos,
                'taxa_atendimento_percentual': round((beneficiarios_atendidos / total_beneficiarios * 100), 2) if total_beneficiarios > 0 else 0
            },
            'impacto_social': {
                'economia_estimada_reais': round(economia_total, 2),
                'familias_beneficiadas': beneficiarios_atendidos,
                'media_economia_por_familia': round(economia_total / beneficiarios_atendidos, 2) if beneficiarios_atendidos > 0 else 0
            },
            'doadores_por_classificacao': dict(por_classificacao)
        }
    
    def gerar_relatorio_doador(self, id_doador: int, preco_kwh: float = 0.80) -> Optional[Dict[str, Any]]:
        """
        Gera relatório específico de um doador.
        
        Args:
            id_doador: ID do doador
            preco_kwh: Preço médio do kWh
            
        Returns:
            Dicionário com informações do doador ou None
        """
        doador = next((d for d in self._doadores if d.id_doador == id_doador), None)
        
        if not doador:
            return None
        
        # Calcula impacto social
        impacto = doador.calcular_impacto_social(preco_kwh)
        
        # Estatísticas temporais
        if doador.total_doacoes > 0:
            dias_ativo = (datetime.now() - doador.data_criacao).days
            media_doacoes_mes = (doador.total_doacoes / max(dias_ativo / 30, 1))
        else:
            media_doacoes_mes = 0
        
        return {
            'informacoes_doador': doador.obter_resumo(),
            'impacto_social': impacto,
            'metricas_temporais': {
                'dias_desde_cadastro': (datetime.now() - doador.data_criacao).days,
                'media_doacoes_por_mes': round(media_doacoes_mes, 2)
            }
        }
    
    def gerar_relatorio_beneficiario(self, id_beneficiario: int) -> Optional[Dict[str, Any]]:
        """
        Gera relatório específico de um beneficiário.
        
        Args:
            id_beneficiario: ID do beneficiário
            
        Returns:
            Dicionário com informações do beneficiário ou None
        """
        beneficiario = next((b for b in self._beneficiarios 
                           if b.id_beneficiario == id_beneficiario), None)
        
        if not beneficiario:
            return None
        
        # Transações do beneficiário
        transacoes_ben = [t for t in self._transacoes 
                         if t.id_beneficiario == id_beneficiario 
                         and t.status == StatusTransacao.CONCLUIDA]
        
        # Calcula estatísticas
        if transacoes_ben:
            ultima_transacao = max(transacoes_ben, key=lambda t: t.data_transacao)
            dias_desde_ultimo = (datetime.now() - ultima_transacao.data_transacao).days
            primeira_transacao = min(transacoes_ben, key=lambda t: t.data_transacao)
        else:
            dias_desde_ultimo = None
            primeira_transacao = None
        
        return {
            'informacoes_beneficiario': beneficiario.obter_resumo(),
            'historico_recebimentos': {
                'total_transacoes': len(transacoes_ben),
                'total_kwh_recebido': beneficiario.total_recebido_kwh,
                'saldo_atual_kwh': beneficiario.saldo_creditos_kwh,
                'dias_desde_ultimo_recebimento': dias_desde_ultimo,
                'data_primeira_transacao': primeira_transacao.data_transacao.strftime('%d/%m/%Y') if primeira_transacao else None
            },
            'necessidade_atual': {
                'continua_necessitando': beneficiario.verificar_necessidade_continua(),
                'consumo_medio_mensal': beneficiario.consumo_medio_kwh,
                'meses_cobertos_saldo_atual': round(beneficiario.saldo_creditos_kwh / beneficiario.consumo_medio_kwh, 2) if beneficiario.consumo_medio_kwh > 0 else 0
            }
        }
    
    def gerar_relatorio_periodo(
        self,
        data_inicio: datetime,
        data_fim: datetime,
        preco_kwh: float = 0.80
    ) -> Dict[str, Any]:
        """
        Gera relatório de um período específico.
        
        Args:
            data_inicio: Data inicial do período
            data_fim: Data final do período
            preco_kwh: Preço médio do kWh
            
        Returns:
            Relatório do período
        """
        # Filtra transações do período
        transacoes_periodo = [
            t for t in self._transacoes
            if data_inicio <= t.data_transacao <= data_fim
            and t.status == StatusTransacao.CONCLUIDA
        ]
        
        if not transacoes_periodo:
            return {
                'periodo': f"{data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}",
                'mensagem': 'Nenhuma transação no período'
            }
        
        # Métricas
        total_kwh = sum(t.quantidade_kwh for t in transacoes_periodo)
        beneficiarios_unicos = len(set(t.id_beneficiario for t in transacoes_periodo))
        economia_periodo = total_kwh * preco_kwh
        
        # Distribuição diária
        por_dia = defaultdict(float)
        for t in transacoes_periodo:
            dia = t.data_transacao.date()
            por_dia[dia] += t.quantidade_kwh
        
        media_diaria = total_kwh / len(por_dia) if por_dia else 0
        
        return {
            'periodo': f"{data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}",
            'metricas': {
                'total_kwh_distribuidos': round(total_kwh, 2),
                'total_transacoes': len(transacoes_periodo),
                'beneficiarios_atendidos': beneficiarios_unicos,
                'economia_estimada_reais': round(economia_periodo, 2)
            },
            'medias': {
                'kwh_por_transacao': round(total_kwh / len(transacoes_periodo), 2),
                'kwh_por_beneficiario': round(total_kwh / beneficiarios_unicos, 2) if beneficiarios_unicos > 0 else 0,
                'kwh_por_dia': round(media_diaria, 2)
            },
            'dias_com_atividade': len(por_dia)
        }
    
    def gerar_relatorio_mensal(self, mes: int, ano: int, preco_kwh: float = 0.80) -> Dict[str, Any]:
        """
        Gera relatório mensal.
        
        Args:
            mes: Mês (1-12)
            ano: Ano
            preco_kwh: Preço médio do kWh
            
        Returns:
            Relatório do mês
        """
        # Define período
        data_inicio = datetime(ano, mes, 1)
        if mes == 12:
            data_fim = datetime(ano + 1, 1, 1) - timedelta(seconds=1)
        else:
            data_fim = datetime(ano, mes + 1, 1) - timedelta(seconds=1)
        
        relatorio_periodo = self.gerar_relatorio_periodo(data_inicio, data_fim, preco_kwh)
        relatorio_periodo['mes_referencia'] = f"{mes:02d}/{ano}"
        
        return relatorio_periodo
    
    def gerar_ranking_doadores(self, criterio: str = 'kwh', top: int = 10) -> List[Dict[str, Any]]:
        """
        Gera ranking de doadores.
        
        Args:
            criterio: 'kwh' ou 'quantidade' (número de doações)
            top: Número de doadores no ranking
            
        Returns:
            Lista ordenada de doadores
        """
        if criterio == 'kwh':
            doadores_ordenados = sorted(
                self._doadores,
                key=lambda d: d.total_kwh_doados,
                reverse=True
            )
        else:  # quantidade
            doadores_ordenados = sorted(
                self._doadores,
                key=lambda d: d.total_doacoes,
                reverse=True
            )
        
        ranking = []
        for posicao, doador in enumerate(doadores_ordenados[:top], start=1):
            ranking.append({
                'posicao': posicao,
                'id_doador': doador.id_doador,
                'nome': doador.nome,
                'classificacao': doador.classificacao.value,
                'total_kwh_doados': round(doador.total_kwh_doados, 2),
                'total_doacoes': doador.total_doacoes
            })
        
        return ranking
    
    def gerar_ranking_beneficiarios(self, criterio: str = 'kwh', top: int = 10) -> List[Dict[str, Any]]:
        """
        Gera ranking de beneficiários mais atendidos.
        
        Args:
            criterio: 'kwh' ou 'transacoes'
            top: Número de beneficiários no ranking
            
        Returns:
            Lista ordenada de beneficiários
        """
        if criterio == 'kwh':
            beneficiarios_ordenados = sorted(
                self._beneficiarios,
                key=lambda b: b.total_recebido_kwh,
                reverse=True
            )
        else:  # transacoes
            beneficiarios_ordenados = sorted(
                self._beneficiarios,
                key=lambda b: b.total_transacoes,
                reverse=True
            )
        
        ranking = []
        for posicao, beneficiario in enumerate(beneficiarios_ordenados[:top], start=1):
            ranking.append({
                'posicao': posicao,
                'id_beneficiario': beneficiario.id_beneficiario,
                'nome': beneficiario.nome,
                'renda_familiar': beneficiario.renda_familiar,
                'total_kwh_recebido': round(beneficiario.total_recebido_kwh, 2),
                'total_transacoes': beneficiario.total_transacoes,
                'saldo_atual': round(beneficiario.saldo_creditos_kwh, 2)
            })
        
        return ranking
    
    def exportar_relatorio_completo(self, preco_kwh: float = 0.80) -> Dict[str, Any]:
        """
        Gera relatório completo do sistema.
        
        Args:
            preco_kwh: Preço médio do kWh
            
        Returns:
            Relatório completo com todas as seções
        """
        return {
            'data_geracao': datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
            'impacto_geral': self.gerar_relatorio_impacto_geral(preco_kwh),
            'ranking_doadores_kwh': self.gerar_ranking_doadores('kwh', 5),
            'ranking_beneficiarios_kwh': self.gerar_ranking_beneficiarios('kwh', 5),
            'relatorio_mes_atual': self.gerar_relatorio_mensal(
                datetime.now().month,
                datetime.now().year,
                preco_kwh
            )
        }
    
    def __repr__(self) -> str:
        return (f"<GeradorRelatorios(doadores={len(self._doadores)}, "
                f"beneficiarios={len(self._beneficiarios)}, "
                f"transacoes={len(self._transacoes)})>")