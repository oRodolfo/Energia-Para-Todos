# ⚡ Energia Para Todos  

### Projeto Interdisciplinar – Sistemas de Informação  
**2º Ano | 4º Período**

Plataforma social e tecnológica que conecta doadores de créditos de energia solar a famílias e comunidades em situação de vulnerabilidade, democratizando o acesso à energia limpa, sustentável e acessível.

---

## 🌍 Sobre o Projeto  

Energia Para Todos nasceu como uma iniciativa acadêmica alinhada ao ODS 7 – Energia Limpa e Acessível, buscando reduzir desigualdades energéticas e promover impacto social por meio da redistribuição de créditos solares.

O sistema possibilita:

  - Cadastro e autenticação de usuários (Doadores, Beneficiários e Administradores)

  - Doação e distribuição automática de créditos de energia

  - Gestão de fila com critérios sociais

  - Painéis dinâmicos, relatórios e indicadores

  - Transparência total por meio de logs e auditoria

A solução entrega uma plataforma robusta, modular e escalável, sustentada por boas práticas de Engenharia de Software. 

---

##  🎯 Objetivo do Projeto

 - Criar uma plataforma web funcional e responsiva que permite:

 - Doadores registrarem créditos excedentes de energia solar.

 - Beneficiários solicitarem créditos com base em critérios socioeconômicos.

 - Administração monitorar operações, usuários e distribuição energética em tempo real.

---

## 💡 Principais Funcionalidades  

👤 Usuários e Perfis
- Cadastro e login unificado (com abas dinâmicas)
- Perfis distintos: Doador, Beneficiário e Administrador
- Recuperação de senha
- Controle de sessão e autenticação

🤝 Doadores
- Registro de créditos de energia (kWh)
- Acompanhamento de impacto social gerado
- Histórico completo de doações
- Simulador de impacto energético (kWh → famílias atendidas)

🏠 Beneficiários
- Entrada dinâmica na fila (priorização automática)
- Solicitação de créditos
- Dashboard com:
  - Posição na fila
  - Consumo médio
  - Histórico de solicitações
- Previsão de atendimento

🛠️ Administrador
- Painel completo via crud.html
- Gestão de:
  - Usuários
  - Créditos
  - Fila
  - Transações
- Métricas consolidadas via view v_metricas_admin
- Configuração dos pesos de priorização social
- Acesso ao painel de transparência e aos logs de auditoria

⚙️ Lógica de Negócio

- Distribuição proporcional e automática de créditos
- Critérios de priorização:
    - Renda
- Auditoria completa de todas as ações
- Expiração automática e reaproveitamento de créditos
- Gatilhos e funções SQL para manter fila e status atualizados automaticamente
---

## 🚀 Tecnologias Utilizadas  

### **Front-End:**  
- HTML5
- CSS3 modularizado (base, layout, componentes)
- JavaScript (fetch API e DOM dinâmico) 

### **Back-End:**  
- Python 3 (POO, modularização e serviços)
- PostgreSQL (estrutura relacional completa e segura)
- Rotas REST com server.py e routes.py 

### **Boas práticas:**  
- Arquitetura em camadas (MVC/DDD)
- Auditoria completa (LoggerAuditoria + AuditMixin)
- Logs de transação e histórico de fila
- Criptografia pgcrypto no banco
- Herança, composição e mixins reutilizáveis
- CRUDs transacionais e uso de FOR UPDATE SKIP LOCKED

### **Banco De Dados:**
Estrutura completa implementada em PostgreSQL, com:
- Tabelas normalizadas e relacionamento completo (FKs, índices, ON DELETE CASCADE).
- Funções automáticas (recalcular_posicoes_fila, trigger_atualizar_fila).
- View v_fila_priorizada para visualização de fila em tempo real.
- Extensão pgcrypto para criptografia de senhas.
O modelo garante integridade, rastreabilidade e escalabilidade, sustentando todas as operações do sistema

### **Interface WEB:**
- login.html → Autenticação e cadastro (abas dinâmicas).
- selecionar-perfil.html → Escolha de perfil (Doador ou Beneficiário).
- completar-cadastro.html → Formulário dinâmico conforme o tipo de perfil.
- dashboard-doador.html → Visualização de créditos e impacto social.
- dashboard-beneficiario.html → Fila de atendimento e histórico de solicitações.
- crud.html → Dashboard interativo do Administrador do sistema.
Todos os front-ends comunicam-se com o backend via fetch() → routes.py, retornando dados JSON.
---

## ⚙️ Como usar

1.  Clone o repositório:

    ``` bash
    git clone https://github.com/oRodolfo/Energia-Para-Todos.git
    cd Energia-Para-Todos
    ```

2.  Configure o banco PostgreSQL:

   ``` bash
   psql -U postgres -f script_banco.sql
   ```

3.  Execute o servidor local:

   ``` bash
   python Conexao/server.py
   ```

4. Abra no navegador:

   ``` bash
   http://localhost:8000
   ```

5.  Para acessar a área de login/cadastro, use o arquivo `login.html` ou
    clique em **Login** no menu.

------------------------------------------------------------------------
## 📂 Estrutura do Projeto
```
ProjetoPiEnergia/
ProjetoPiEnergia/
├── BackEnd/
│   ├── mixins/
│   │   └── audit_mixin.py
│   ├── models/
│   │   ├── administrador.py
│   │   ├── base.py
│   │   ├── beneficiario.py
│   │   ├── credito.py
│   │   ├── doador.py
│   │   ├── fila_espera.py
│   │   └── transacao.py
│   ├── services/
│   │   ├── distribuidor_creditos.py
│   │   ├── gerador_relatorio.py
│   │   └── painel_transparencia.py
│   ├── utils/
│   │   ├── database.py
│   │   └── logger_auditoria.py
│   ├── script_banco.sql
│   └── extensao_sprint1.sql
│
├── Conexao/
│   ├── routes.py
│   └── server.py
│
└── FrontEnd/
    ├── index.html
    ├── login.html
    ├── selecionar-perfil.html
    ├── completar-cadastro.html
    ├── dashboard-doador.html
    ├── dashboard-beneficiario.html
    ├── crud.html
    └── assets/
        ├── css/
        ├── js/
        └── images/
```
---

## 🧩 Destaques Técnicos do Back-End
- Entidades Principais
  - PerfilUsuario (classe base)
  - Administrador
  - Doador
  - Beneficiario
  - Credito
  - Transacao
  - FilaEspera + ItemFila
- Serviços
  - DistribuidorCreditos – lógica central de distribuição
  - GeradorRelatorio – métricas e estatísticas
  - PainelTransparencia – indicadores públicos
- Auditoria e Segurança
  - Logs estruturados
  - Criptografia de senhas
  - Histórico de alterações (via Mixin)
  - Validações duplas (front/back)
   
---

## 🛠️ Segurança e Boas Práticas
- Criptografia bcrypt (pgcrypto)
- Sanitização / validação dupla
- Proteção contra XSS
- Princípios SOLID
- Arquitetura por camadas
- Baixo acoplamento e alta coesão
- Auditoria completa das operações críticas

---
🧩 Arquitetura do Sistema

O projeto segue uma arquitetura modular e orientada a camadas, separando responsabilidades de forma clara:

| **Camada** | **Descrição** |
|-------------|----------------|
| **Models** | Entidades principais do domínio (Usuário, Doador, Beneficiário, Crédito, Fila, Transação). |
| **Services** | Regras de negócio (Distribuição de créditos, Relatórios, Painel de transparência). |
| **Mixins** | Comportamentos reutilizáveis, como auditoria e trilhas de alteração. |
| **Utils** | Conexão com banco, logs e enums auxiliares. |
| **Conexão (Routes/Server)** | Camada intermediária de rotas REST e controle de sessão. |
| **FrontEnd** | Interface HTML/CSS/JS, formulários dinâmicos e dashboards interativos. |

Essa separação garante alta coesão e baixo acoplamento, facilitando manutenção, testes e expansão futura (como dashboards dinâmicos).

---
✨ Contribuidores

| RA      | Nome                                   |
|----------|----------------------------------------|
| 116319   | Arthur Peixoto Lacerda                 |
| 116657   | Enzo Zaia Soares                       |
| 117017   | Guilherme Henrique Cavarsan da Silva   |
| 117607   | Octávio Thim Dias                      |
| 117179   | Rodolfo Henrique Ribeiro Zanchetta     |


































------------------------------------------------------------------------

💡 **Energia limpa transforma vidas.**
