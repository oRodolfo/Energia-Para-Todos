"""
Sistema Energia Para Todos - Programa Principal
Demonstração completa do sistema de doação e distribuição de créditos de energia solar.
"""
from datetime import datetime, timedelta

# Importações dos modelos
from models.doador import Doador, ClassificacaoDoador
from models.beneficiario import Beneficiario, StatusBeneficiario
from models.administrador import Administrador
from models.credito import Credito
from models.fila_espera import FilaEspera

# Importações dos serviços
from services.distribuidor_creditos import DistribuidorCreditos
from services.gerador_relatorio import GeradorRelatorios
from services.painel_transparencia import PainelTransparencia

# Importações utilitários
from utils.logger_auditoria import LoggerAuditoria, TipoAcao, StatusLog


def imprimir_secao(titulo: str) -> None:
    """Imprime cabeçalho de seção."""
    print("\n" + "=" * 80)
    print(f"  {titulo}")
    print("=" * 80)


def imprimir_dict(dados: dict, indent: int = 0) -> None:
    """Imprime dicionário formatado."""
    espacos = "  " * indent
    for chave, valor in dados.items():
        if isinstance(valor, dict):
            print(f"{espacos}{chave}:")
            imprimir_dict(valor, indent + 1)
        elif isinstance(valor, list) and valor and isinstance(valor[0], dict):
            print(f"{espacos}{chave}:")
            for item in valor:
                imprimir_dict(item, indent + 1)
                print()
        else:
            print(f"{espacos}{chave}: {valor}")


def main():
    """Função principal que demonstra todo o sistema."""
    
    imprimir_secao("SISTEMA ENERGIA PARA TODOS - DEMONSTRAÇÃO COMPLETA")
    print("Sistema de intermediação de créditos de energia solar")
    print("Conectando doadores a beneficiários com distribuição automática e transparente")
    
    # 1. INICIALIZAÇÃO DOS SERVIÇOS
    imprimir_secao("1. INICIALIZAÇÃO DOS SERVIÇOS")
    
    distribuidor = DistribuidorCreditos()
    gerador_relatorios = GeradorRelatorios()
    painel_transparencia = PainelTransparencia()
    logger = LoggerAuditoria()
    
    print("Distribuidor de Créditos inicializado")
    print("Gerador de Relatórios inicializado")
    print("Painel de Transparência inicializado")
    print("Sistema de Auditoria inicializado")
    
    # 2. CRIAÇÃO DO ADMINISTRADOR
    imprimir_secao("2. CRIAÇÃO DO ADMINISTRADOR")
    
    admin = Administrador(
        id_administrador=1,
        id_usuario=1,
        nome="Maria Silva Administradora",
        email="admin@energiaparatodos.org",
        telefone="11987654321",
        cep= "01310100",
    )
    print(f"Administrador criado: {admin}")
    
    # 3. CADASTRO DE DOADORES
    imprimir_secao("3. CADASTRO DE DOADORES")
    doadores = [
        Doador(
            id_doador=1,
            id_usuario=10,
            nome="João Energia Solar Ltda",
            email="joao@solarenergia.com",
            telefone="11912345678",
            cep= "01310200",
            classificacao=ClassificacaoDoador.PESSOA_JURIDICA
        ),
        Doador(
            id_doador=2,
            id_usuario=11,
            nome="Ana Paula Sustentável",
            email="ana@email.com",
            telefone="11923456789",
            cep= "01310300",
            classificacao=ClassificacaoDoador.PESSOA_FISICA
        )
    ]
    
    for doador in doadores:
        gerador_relatorios.registrar_doador(doador)
        painel_transparencia.atualizar_metricas_doacao(0, novo_doador=True)
        print(f"✓ {doador}")
    
    logger.registrar(
        tipo_acao=TipoAcao.CADASTRO,
        status=StatusLog.SUCESSO,
        detalhes=f"{len(doadores)} doadores cadastrados"
    )
    
    # 4. CADASTRO DE BENEFICIÁRIOS
    imprimir_secao("4. CADASTRO DE BENEFICIÁRIOS")
    beneficiarios = [
        Beneficiario(
            id_beneficiario=1,
            id_usuario=20,
            nome="Maria das Graças",
            email="maria.gracas@email.com",
            telefone="11945678901",
            cep= "08220100",
            renda_familiar=800.0,
            consumo_medio_kwh=120.0,
            num_moradores=4,
            data_aprovacao=datetime.now()
        ),
        Beneficiario(
            id_beneficiario=2,
            id_usuario=21,
            nome="José Santos",
            email="jose.santos@email.com",
            telefone="11956789012",
            cep= "08220200",
            renda_familiar=1200.0,
            consumo_medio_kwh=150.0,
            num_moradores=3,
            data_aprovacao=datetime.now()
        ),
        Beneficiario(
            id_beneficiario=3,
            id_usuario=22,
            nome="Francisca Oliveira",
            email="francisca@email.com",
            telefone="11967890123",
            cep= "08220300",
            renda_familiar=600.0,
            consumo_medio_kwh=100.0,
            num_moradores=5,
            data_aprovacao=datetime.now()
        ),
        Beneficiario(
            id_beneficiario=4,
            id_usuario=23,
            nome="Carlos Mendes",
            email="carlos.mendes@email.com",
            telefone="11978901234",
            cep= "08220400",
            renda_familiar=1500.0,
            consumo_medio_kwh=180.0,
            num_moradores=2,
            data_aprovacao=datetime.now()
        ),
        Beneficiario(
            id_beneficiario=5,
            id_usuario=24,
            nome="Antônia Silva",
            email="antonia.silva@email.com",
            telefone="11989012345",
            cep= "08220500",
            renda_familiar=500.0,
            consumo_medio_kwh=90.0,
            num_moradores=6,
            data_aprovacao=datetime.now()
        )
    ]
    
    for beneficiario in beneficiarios:
        gerador_relatorios.registrar_beneficiario(beneficiario)
        painel_transparencia.registrar_beneficiario()
        print(f"✓ {beneficiario}")
        print(f"  Renda: R$ {beneficiario.renda_familiar:.2f} | "
              f"Consumo: {beneficiario.consumo_medio_kwh} kWh | "
              f"Moradores: {beneficiario.num_moradores}")
    
    # 5. CRIAÇÃO E CONFIGURAÇÃO DA FILA DE ESPERA
    imprimir_secao("5. CRIAÇÃO DA FILA DE ESPERA")
    
    fila = FilaEspera(id_temporada=1, nome_temporada="Temporada 2025-1")
    print(f"Fila criada: {fila}")
    
    # Adiciona beneficiários à fila
    print("\nAdicionando beneficiários à fila...")
    for beneficiario in beneficiarios:
        fila.adicionar_beneficiario(beneficiario)
    
    print(f"✓ {fila.tamanho} beneficiários na fila")
    
    # Exibe fila ordenada por prioridade
    print("\n FILA ORDENADA POR PRIORIDADE:")
    print("-" * 80)
    print(f"{'Pos':<5} {'Nome':<30} {'Prioridade':<12} {'Renda':<10} {'Moradores':<10}")
    print("-" * 80)
    
    for item in fila.listar_fila():
        print(f"{item['posicao']:<5} {item['nome']:<30} {item['prioridade']:<12} "
              f"R$ {item['renda_familiar']:<8.2f} {item['num_moradores']:<10}")
    
    # Demonstra ajuste de pesos pelo administrador
    print("\nAdministrador ajustando pesos de priorização...")
    admin.ajustar_pesos_priorizacao(
        peso_renda=0.4,
        peso_consumo=0.2,
        peso_moradores=0.3,
        peso_tempo_fila=0.1
    )
    
    fila.configurar_pesos(**admin.pesos_priorizacao)
    print("Pesos ajustados:")
    imprimir_dict(admin.pesos_priorizacao, indent=1)
    
    admin.registrar_acao_administrativa("Ajuste de pesos de priorização da fila")

    # 6. REGISTRO DE DOAÇÕES (CRÉDITOS)
    imprimir_secao("6. REGISTRO DE DOAÇÕES DE CRÉDITOS")
    
    creditos = []
    # Doação 1 - Empresa médio porte
    credito1 = Credito(
        id_credito=1,
        id_doador=doadores[0].id_doador,
        quantidade_inicial_kwh=500.0,
        meses_validade=12
    )
    creditos.append(credito1)
    doadores[0].registrar_doacao(credito1.id_credito, 500.0)
    distribuidor.adicionar_credito(credito1)
    painel_transparencia.atualizar_metricas_doacao(500.0, novo_doador=False)
    print(f"✓ {credito1}")
    
    # Doação 2 - Pessoa física
    credito2 = Credito(
        id_credito=2,
        id_doador=doadores[1].id_doador,
        quantidade_inicial_kwh=200.0,
        meses_validade=12
    )
    creditos.append(credito2)
    doadores[1].registrar_doacao(credito2.id_credito, 200.0)
    distribuidor.adicionar_credito(credito2)
    painel_transparencia.atualizar_metricas_doacao(200.0, novo_doador=False)
    print(f"{credito2}")
    
    print(f"\n Total disponível para distribuição: {distribuidor.obter_total_disponivel():.2f} kWh")
    
    # 7. DISTRIBUIÇÃO AUTOMÁTICA PROPORCIONAL
    imprimir_secao("7. DISTRIBUIÇÃO AUTOMÁTICA PROPORCIONAL")
    
    print("Iniciando distribuição proporcional aos beneficiários prioritários...\n")
    
    resultado_distribuicao = distribuidor.distribuir_proporcional(fila, num_beneficiarios=5)
    
    print("RESULTADO DA DISTRIBUIÇÃO:")
    print("-" * 80)
    imprimir_dict(resultado_distribuicao)
    
    # Registra transações no gerador de relatórios
    for transacao in distribuidor._transacoes:
        gerador_relatorios.registrar_transacao(transacao)
        painel_transparencia.atualizar_metricas_distribuicao(
            transacao.quantidade_kwh,
            transacao
        )
    
    # Atualiza contador de beneficiários atendidos
    for _ in resultado_distribuicao['beneficiarios_atendidos']:
        painel_transparencia.marcar_beneficiario_atendido()
    
    # 8. VERIFICAÇÃO PÓS-DISTRIBUIÇÃO
    imprimir_secao("8. VERIFICAÇÃO PÓS-DISTRIBUIÇÃO")
    
    print("SALDO DOS BENEFICIÁRIOS APÓS DISTRIBUIÇÃO:")
    print("-" * 80)
    print(f"{'Nome':<30} {'Recebido (kWh)':<18} {'Saldo (kWh)':<15} {'Transações':<12}")
    print("-" * 80)
    
    for beneficiario in beneficiarios:
        print(f"{beneficiario.nome:<30} {beneficiario.total_recebido_kwh:<18.2f} "
              f"{beneficiario.saldo_creditos_kwh:<15.2f} {beneficiario.total_transacoes:<12}")
    
    print(f"\n kWh restante no pool: {distribuidor.obter_total_disponivel():.2f}")
    
    # 9. REALOCAÇÃO NA FILA
    imprimir_secao("9. REALOCAÇÃO NA FILA")
    
    print("Verificando necessidade contínua dos beneficiários atendidos...\n")
    
    fila.realocar_atendidos()
    
    print("FILA APÓS REALOCAÇÃO:")
    print("-" * 80)
    stats = fila.obter_estatisticas()
    imprimir_dict(stats)

    # 10. RELATÓRIO DE IMPACTO GERAL
    imprimir_secao("10. RELATÓRIO DE IMPACTO GERAL")
    
    relatorio_geral = gerador_relatorios.gerar_relatorio_impacto_geral(preco_kwh=0.85)
    imprimir_dict(relatorio_geral)
    
    # 11. RELATÓRIO INDIVIDUAL DE DOADOR
    imprimir_secao("11. RELATÓRIO INDIVIDUAL DE DOADOR")
    
    print("Gerando relatório do doador 'GreenPower Industrias S.A.'...\n")
    relatorio_doador = gerador_relatorios.gerar_relatorio_doador(
        id_doador=doadores[0].id_doador,
        preco_kwh=0.85
    )
    imprimir_dict(relatorio_doador)
    
    # 12. RELATÓRIO INDIVIDUAL DE BENEFICIÁRIO
    imprimir_secao("12. RELATÓRIO INDIVIDUAL DE BENEFICIÁRIO")
    
    print("Gerando relatório da beneficiária 'Antônia Silva'...\n")
    relatorio_beneficiario = gerador_relatorios.gerar_relatorio_beneficiario(
        id_beneficiario=beneficiarios[4].id_beneficiario
    )
    imprimir_dict(relatorio_beneficiario)
    
    # 13. RANKINGS
    imprimir_secao("13. RANKINGS")
    
    print("TOP 3 DOADORES (por kWh doados):")
    print("-" * 80)
    ranking_doadores = gerador_relatorios.gerar_ranking_doadores('kwh', 3)
    for item in ranking_doadores:
        print(f"{item['posicao']}º - {item['nome']} ({item['classificacao']}): "
              f"{item['total_kwh_doados']} kWh em {item['total_doacoes']} doações")
    
    print("\n TOP 3 BENEFICIÁRIOS (por kWh recebidos):")
    print("-" * 80)
    ranking_beneficiarios = gerador_relatorios.gerar_ranking_beneficiarios('kwh', 3)
    for item in ranking_beneficiarios:
        print(f"{item['posicao']}º - {item['nome']} (Renda: R$ {item['renda_familiar']:.2f}): "
              f"{item['total_kwh_recebido']} kWh em {item['total_transacoes']} transações")
    
    # 14. PAINEL DE TRANSPARÊNCIA PÚBLICA
    imprimir_secao("14. PAINEL DE TRANSPARÊNCIA PÚBLICA")
    
    visao_publica = painel_transparencia.obter_visao_geral(preco_kwh=0.85)
    imprimir_dict(visao_publica)
    
    # 15. SIMULAÇÃO DE IMPACTO DE NOVA DOAÇÃO
    imprimir_secao("15. SIMULAÇÃO DE IMPACTO DE NOVA DOAÇÃO")
    
    print("Simulando impacto de uma doação de 300 kWh...\n")
    simulacao = painel_transparencia.simular_impacto_doacao(
        quantidade_kwh=300.0,
        preco_kwh=0.85,
        consumo_medio_familia=120.0
    )
    imprimir_dict(simulacao)
    
    # 16. CERTIFICADO DE DOADOR
    imprimir_secao("16. CERTIFICADO DE DOADOR")

    alvo_nome = "GreenPower Industrias S.A."  # o que você quer certificar

    # tenta achar pelo nome; se não achar, cai no doador com maior kWh doado
    doador_alvo = next((d for d in doadores if d.nome == alvo_nome), None)
    if not doador_alvo and doadores:
        doador_alvo = max(doadores, key=lambda d: d.total_kwh_doados)

    if doador_alvo:
        certificado = painel_transparencia.obter_certificado_doador(
            nome_doador=doador_alvo.nome,
            kwh_doados=doador_alvo.total_kwh_doados,
            preco_kwh=0.85
        )

        print("CERTIFICADO DE IMPACTO SOCIAL")
        print("-" * 80)
        print(certificado['mensagem'])
        print("-" * 80)
        print(f"Data de emissão: {certificado['data_emissao']}")
    else:
        print("Nenhum doador disponível para emissão de certificado.")
    

    # 17. FEEDBACKS ANÔNIMOS
    imprimir_secao("17. FEEDBACKS DE BENEFICIÁRIOS (ANÔNIMOS)")
    
    feedbacks = painel_transparencia.obter_feedbacks_anonimos(limite=3)
    for idx, feedback in enumerate(feedbacks, 1):
        print(f"{idx}. \"{feedback}\"")
    
    # 18. LOG DE AUDITORIA
    imprimir_secao("18. LOG DE AUDITORIA")
    
    print("REGISTROS DE AUDITORIA DO SISTEMA:")
    print("-" * 80)
    
    logs = logger.obter_logs()
    for log in logs[-10:]:  # Últimos 10 logs
        print(f"[{log['data_hora'].strftime('%d/%m/%Y %H:%M:%S')}] "
              f"{log['tipo_acao'].value} - {log['status'].value}")
        if log['detalhes']:
            print(f"  └─ {log['detalhes']}")
    
    print(f"\nTotal de logs registrados: {len(logs)}")
    
    # Estatísticas de logs
    stats_logs = logger.obter_estatisticas()
    print("\nESTATÍSTICAS DE AUDITORIA:")
    imprimir_dict(stats_logs)
    
    # 19. HISTÓRICO DE ALTERAÇÕES (AUDIT MIXIN)
    imprimir_secao("19. HISTÓRICO DE ALTERAÇÕES (DEMONSTRAÇÃO AUDIT MIXIN)")
    
    print("Histórico de alterações do Administrador:")
    print("-" * 80)
    historico_admin = admin.historico_alteracoes
    for alteracao in historico_admin[-5:]:  # Últimas 5 alterações
        print(f"[{alteracao['timestamp'].strftime('%d/%m/%Y %H:%M:%S')}] "
              f"Campo: {alteracao['campo']}")
        print(f"  └─ De: {alteracao['valor_antigo']} → Para: {alteracao['valor_novo']}")
        if alteracao['observacao']:
            print(f"  └─ Obs: {alteracao['observacao']}")
    
    print(f"\nHistórico de alterações do Doador '{doadores[0].nome}':")
    print("-" * 80)
    historico_doador = doadores[0].historico_alteracoes
    for alteracao in historico_doador[-3:]:
        print(f"[{alteracao['timestamp'].strftime('%d/%m/%Y %H:%M:%S')}] "
              f"Campo: {alteracao['campo']}")
        print(f"  └─ Valor: {alteracao['valor_novo']}")
        if alteracao['observacao']:
            print(f"  └─ {alteracao['observacao']}")

    # 20. ESTATÍSTICAS FINAIS
    imprimir_secao("20. ESTATÍSTICAS FINAIS DO SISTEMA")
    
    print("RESUMO EXECUTIVO:")
    print("-" * 80)
    print(f"Doadores cadastrados: {len(doadores)}")
    print(f"Beneficiários cadastrados: {len(beneficiarios)}")
    print(f"Créditos registrados: {len(creditos)}")
    print(f"Total kWh doados: {sum(d.total_kwh_doados for d in doadores):.2f}")
    print(f"Total kWh distribuídos: {sum(b.total_recebido_kwh for b in beneficiarios):.2f}")
    print(f"Transações realizadas: {len(distribuidor._transacoes)}")
    print(f"Beneficiários atendidos: {len([b for b in beneficiarios if b.total_recebido_kwh > 0])}")
    print(f"Taxa de distribuição: {(sum(b.total_recebido_kwh for b in beneficiarios) / sum(d.total_kwh_doados for d in doadores) * 100):.2f}%")
    print(f"Economia social gerada: R$ {sum(b.total_recebido_kwh for b in beneficiarios) * 0.85:.2f}")
    
    stats_dist = distribuidor.obter_estatisticas()
    print(f"\nPool de Créditos:")
    print(f"  Créditos ativos: {stats_dist['creditos_no_pool']}")
    print(f"  kWh disponível: {stats_dist['kwh_disponivel']:.2f}")
    
    print(f"\nFila de Espera:")
    stats_fila = fila.obter_estatisticas()
    print(f"  Aguardando: {stats_fila['aguardando']}")
    print(f"  Prioridade média: {stats_fila['prioridade_media']:.2f}")
    
    # FINALIZAÇÃO
    imprimir_secao("DEMONSTRAÇÃO CONCLUÍDA COM SUCESSO")
    
    print(" Todos os componentes do sistema foram testados:")
    print("   • Cadastro de usuários (Doadores, Beneficiários, Administrador)")
    print("   • Herança múltipla (PerfilUsuario + AuditMixin)")
    print("   • Polimorfismo (calcular_prioridade)")
    print("   • Encapsulamento (properties e métodos privados)")
    print("   • Classes abstratas (ABC)")
    print("   • Mixins (AuditMixin)")
    print("   • Fila de espera com priorização dinâmica")
    print("   • Distribuição proporcional automática")
    print("   • Geração de relatórios e análises")
    print("   • Painel de transparência pública")
    print("   • Sistema completo de auditoria")
    
    print("\n Sistema 'Energia Para Todos' operacional!")
    print("=" * 80)


if __name__ == "__main__":
    main()