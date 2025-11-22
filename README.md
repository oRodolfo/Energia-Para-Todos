# ⚡ Energia Para Todos  

### Projeto Interdisciplinar – Sistemas de Informação  
**2º Ano | 4º Período**

Plataforma solidária que conecta pessoas e empresas com excedente de energia solar a famílias e comunidades em situação de vulnerabilidade, democratizando o acesso à energia limpa e sustentável.

---

## 🌍 Sobre o Projeto  

O Energia Para Todos é uma iniciativa tecnológica e social que transforma créditos de energia solar excedentes em impacto real, conectando doadores a beneficiários por meio de uma plataforma web integrada.

A proposta surgiu da necessidade de inclusão energética, aproveitando recursos já existentes e promovendo sustentabilidade ambiental e social.

O projeto está alinhado ao Objetivo de Desenvolvimento Sustentável (ODS) 7 – Energia Limpa e Acessível, com foco em:

- Acesso universal e acessível à energia;
- Uso eficiente e sustentável de energias renováveis;
- Ampliação de infraestrutura tecnológica para comunidades vulneráveis
---

## 💡 Principais Funcionalidades  

- Cadastro e autenticação de doadores, beneficiários e administradores.
- Registro e gerenciamento de créditos de energia (kWh).
- Fila de espera automática com critérios de priorização social (renda, consumo, tempo de fila).
- Distribuição proporcional de créditos de forma automatizada.
- Painéis de transparência (públicos e individuais) com indicadores sociais e energéticos.
- Relatórios de impacto (energia doada, famílias atendidas, economia gerada).
- Auditoria completa de transações, garantindo rastreabilidade e segurança.
- Simulação de impacto para o doador ("X kWh ajuda Y famílias por Z meses"). 

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
- crud.html → Interface de testes para operações básicas no banco.
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
