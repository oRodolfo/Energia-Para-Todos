"""
Serviço PainelTransparencia - fornece visão pública agregada do sistema.
"""
from typing import Dict, Any, List
from datetime import datetime
from collections import defaultdict

from models.transacao import Transacao, StatusTransacao


class PainelTransparencia:
    """
    Serviço que fornece informações públicas agregadas sobre o sistema.
    Não expõe dados pessoais, apenas estatísticas gerais.
    """
    
    def __init__(self):
        self._total_kwh_doados = 0.0
        self._total_kwh_distribuidos = 0.0
        self._total_doacoes = 0
        self._total_doadores = 0
        self._total_beneficiarios_cadastrados = 0
        self._total_beneficiarios_atendidos = 0
        self._transacoes: List[Transacao] = []
        self._data_inicio_operacao = datetime.now()
    
    def atualizar_metricas_doacao(
        self,
        kwh_doados: float,
        novo_doador: bool = False
    ) -> None:
        """
        Atualiza métricas de doação.
        
        Args:
            kwh_doados: Quantidade de kWh doada
            novo_doador: Se é um novo doador sendo cadastrado
        """
        self._total_kwh_doados += kwh_doados
        self._total_doacoes += 1
        
        if novo_doador:
            self._total_doadores += 1
    
    def atualizar_metricas_distribuicao(
        self,
        kwh_distribuidos: float,
        transacao: Transacao
    ) -> None:
        """
        Atualiza métricas de distribuição.
        
        Args:
            kwh_distribuidos: Quantidade distribuída
            transacao: Transação realizada
        """
        self._total_kwh_distribuidos += kwh_distribuidos
        self._transacoes.append(transacao)
    
    def registrar_beneficiario(self, ja_foi_atendido: bool = False) -> None:
        """
        Registra novo beneficiário.
        
        Args:
            ja_foi_atendido: Se já recebeu créditos
        """
        self._total_beneficiarios_cadastrados += 1
        
        if ja_foi_atendido:
            self._total_beneficiarios_atendidos += 1
    
    def marcar_beneficiario_atendido(self) -> None:
        """Incrementa contador de beneficiários atendidos."""
        self._total_beneficiarios_atendidos += 1
    
    def obter_visao_geral(self, preco_kwh: float = 0.80) -> Dict[str, Any]:
        """
        Retorna visão geral pública do sistema.
        
        Args:
            preco_kwh: Preço médio do kWh
            
        Returns:
            Dicionário com estatísticas gerais
        """
        # Calcula economia estimada
        economia_total = self._total_kwh_distribuidos * preco_kwh
        economia_por_familia = (economia_total / self._total_beneficiarios_atendidos 
                               if self._total_beneficiarios_atendidos > 0 else 0)
        
        # Dias em operação
        dias_operacao = (datetime.now() - self._data_inicio_operacao).days
        if dias_operacao == 0:
            dias_operacao = 1
        
        # Taxa de distribuição
        taxa_distribuicao = ((self._total_kwh_distribuidos / self._total_kwh_doados * 100) 
                            if self._total_kwh_doados > 0 else 0)
        
        return {
            'resumo_doacoes': {
                'total_doadores_ativos': self._total_doadores,
                'total_kwh_doados': round(self._total_kwh_doados, 2),
                'numero_doacoes_realizadas': self._total_doacoes,
                'media_kwh_por_doacao': round(self._total_kwh_doados / self._total_doacoes, 2) if self._total_doacoes > 0 else 0
            },
            'resumo_distribuicao': {
                'total_kwh_distribuidos': round(self._total_kwh_distribuidos, 2),
                'taxa_distribuicao_percentual': round(taxa_distribuicao, 2),
                'kwh_aguardando_distribuicao': round(self._total_kwh_doados - self._total_kwh_distribuidos, 2)
            },
            'impacto_social': {
                'familias_cadastradas': self._total_beneficiarios_cadastrados,
                'familias_atendidas': self._total_beneficiarios_atendidos,
                'economia_estimada_total_reais': round(economia_total, 2),
                'economia_media_por_familia_reais': round(economia_por_familia, 2)
            },
            'metricas_tempo': {
                'dias_em_operacao': dias_operacao,
                'media_kwh_por_dia': round(self._total_kwh_distribuidos / dias_operacao, 2),
                'media_familias_atendidas_por_mes': round((self._total_beneficiarios_atendidos / dias_operacao) * 30, 2)
            }
        }
    
    def obter_estatisticas_mensais(self) -> List[Dict[str, Any]]:
        """
        Retorna estatísticas agregadas por mês.
        
        Returns:
            Lista de estatísticas mensais
        """
        por_mes = defaultdict(lambda: {'kwh': 0.0, 'transacoes': 0, 'beneficiarios': set()})
        
        for transacao in self._transacoes:
            if transacao.status == StatusTransacao.CONCLUIDA:
                mes_ano = transacao.data_transacao.strftime('%m/%Y')
                por_mes[mes_ano]['kwh'] += transacao.quantidade_kwh
                por_mes[mes_ano]['transacoes'] += 1
                por_mes[mes_ano]['beneficiarios'].add(transacao.id_beneficiario)
        
        resultado = []
        for mes_ano, dados in sorted(por_mes.items()):
            resultado.append({
                'periodo': mes_ano,
                'kwh_distribuidos': round(dados['kwh'], 2),
                'numero_transacoes': dados['transacoes'],
                'familias_atendidas': len(dados['beneficiarios'])
            })
        
        return resultado
    
    def simular_impacto_doacao(
        self,
        quantidade_kwh: float,
        preco_kwh: float = 0.80,
        consumo_medio_familia: float = 150.0
    ) -> Dict[str, Any]:
        """
        Simula o impacto de uma possível doação.
        
        Args:
            quantidade_kwh: Quantidade que seria doada
            preco_kwh: Preço médio do kWh
            consumo_medio_familia: Consumo médio mensal de uma família
            
        Returns:
            Simulação do impacto
        """
        # Estima quantas famílias podem ser atendidas
        familias_atendidas = int(quantidade_kwh / consumo_medio_familia)
        
        # Estima meses de cobertura
        meses_cobertura = quantidade_kwh / consumo_medio_familia
        
        # Economia estimada
        economia_estimada = quantidade_kwh * preco_kwh
        
        return {
            'quantidade_doacao_kwh': quantidade_kwh,
            'impacto_estimado': {
                'familias_beneficiadas': familias_atendidas,
                'meses_energia_fornecida': round(meses_cobertura, 1),
                'economia_gerada_reais': round(economia_estimada, 2),
                'reducao_emissoes_co2_kg': round(quantidade_kwh * 0.0817, 2)  # Fator médio Brasil
            },
            'contexto': {
                'equivalente_residencias_mes': familias_atendidas,
                'percentual_aumento_impacto': round((quantidade_kwh / self._total_kwh_distribuidos * 100), 2) if self._total_kwh_distribuidos > 0 else 0
            }
        }
    
    def obter_feedbacks_anonimos(self, limite: int = 5) -> List[str]:
        """
        Retorna feedbacks anônimos de beneficiários (simulado).
        
        Args:
            limite: Número máximo de feedbacks
            
        Returns:
            Lista de feedbacks anônimos
        """
        # Em implementação real, isso viria de um banco de dados
        # Aqui retornamos exemplos baseados nas métricas
        feedbacks = []
        
        if self._total_beneficiarios_atendidos > 0:
            feedbacks.extend([
                f"Esta iniciativa reduziu minha conta de energia em aproximadamente 60%",
                f"Graças aos créditos, consigo manter geladeira e iluminação sem preocupação",
                f"Estou na lista há {(datetime.now() - self._data_inicio_operacao).days} dias e já fui atendido",
                f"A transparência do sistema me dá confiança na distribuição justa",
                f"Como doador, é gratificante ver o impacto real nas famílias"
            ])
        
        return feedbacks[:limite]
    
    def obter_certificado_doador(
        self,
        nome_doador: str,
        kwh_doados: float,
        preco_kwh: float = 0.80
    ) -> Dict[str, Any]:
        """
        Gera dados para certificado de doador.
        
        Args:
            nome_doador: Nome do doador
            kwh_doados: kWh doados
            preco_kwh: Preço médio
            
        Returns:
            Dados do certificado
        """
        economia_gerada = kwh_doados * preco_kwh
        co2_evitado = kwh_doados * 0.0817
        
        return {
            'doador': nome_doador,
            'data_emissao': datetime.now().strftime('%d/%m/%Y'),
            'contribuicao': {
                'kwh_doados': round(kwh_doados, 2),
                'economia_social_reais': round(economia_gerada, 2),
                'co2_evitado_kg': round(co2_evitado, 2)
            },
            'mensagem': (
                f"Certificamos que {nome_doador} contribuiu com {kwh_doados:.2f} kWh "
                f"de energia solar, gerando impacto social estimado de R$ {economia_gerada:.2f} "
                f"e evitando a emissão de {co2_evitado:.2f} kg de CO₂."
            )
        }
    
    def __repr__(self) -> str:
        return (f"<PainelTransparencia(doadores={self._total_doadores}, "
                f"familias_atendidas={self._total_beneficiarios_atendidos}, "
                f"kwh_distribuidos={self._total_kwh_distribuidos:.2f})>")