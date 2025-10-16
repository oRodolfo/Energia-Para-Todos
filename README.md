# ⚡ Energia Para Todos  

### Projeto Interdisciplinar – Sistemas de Informação  
**2º Ano | 4º Período**

Plataforma solidária que conecta pessoas e empresas com **excedente de energia solar** a **famílias e comunidades em situação de vulnerabilidade**, democratizando o acesso à energia limpa e sustentável.

---

## 🌍 Sobre o Projeto  

O **Energia Para Todos** tem como objetivo **transformar excedentes de energia em impacto social real**, usando tecnologia para promover equidade energética.  
Com o sistema, doadores podem compartilhar créditos de energia, enquanto famílias beneficiadas têm suas contas reduzidas ou até zeradas.  

O projeto está alinhado aos **Objetivos de Desenvolvimento Sustentável (ODS)** da ONU, especialmente o **ODS 7 – Energia Limpa e Acessível**.

---

## 💡 Principais Funcionalidades  

- Página inicial com missão, impacto e funcionamento do projeto.  
- Área de login e cadastro para doadores, beneficiários e administradores.  
- Seção de galeria e depoimentos sobre transformação social.  
- Painel de transparência com dados agregados (energia distribuída, beneficiários atendidos).  
- Sistema de auditoria e relatórios no back-end.  
- Fila de priorização inteligente para distribuição de créditos.  

---

## 🚀 Tecnologias Utilizadas  

### **Front-End:**  
- HTML5  
- CSS3 (modularizado por seções e componentes)  
- JavaScript  

### **Back-End:**  
- Python (Programação Orientada a Objetos)  
- PostgreSQL (banco de dados relacional)  

### **Boas práticas:**  
- Padrões de arquitetura MVC simplificado  
- Auditoria e logging centralizado (`LoggerAuditoria`)  
- Estrutura modular e extensível  
- Enums e mixins para comportamento reutilizável  

---

## ⚙️ Como usar

1.  Clone o repositório:

    ``` bash
    git clone https://github.com/oRodolfo/energia-para-todos.git
    ```

2.  Abra o arquivo `index.html` no navegador.

3.  Para acessar a área de login/cadastro, use o arquivo `login.html` ou
    clique em **Login** no menu.

------------------------------------------------------------------------
## 📂 Estrutura do Projeto
```
ProjetoPiEnergia/
├── BackEnd/
│ ├── main.py                    # Executa o fluxo completo do sistema
│ │
│ ├── mixins/                    # Comportamentos reutilizáveis (ex: auditoria)
│ │ └── audit_mixin.py           # AuditMixin – histórico e rastreabilidade de alterações
│ │
│ ├── models/                    # Entidades e enums do domínio
│ │ ├── administrador.py         # Classe Administrador – gerencia pesos de priorização
│ │ ├── base.py                  # Classe base PerfilUsuario e enums de tipo/status
│ │ ├── beneficiario.py          # Classe Beneficiário – saldo, fila e prioridade
│ │ ├── credito.py               # Classe Crédito – controla doações em kWh
│ │ ├── doador.py                # Classe Doador – estatísticas e saldo de energia
│ │ ├── fila_espera.py           # FilaEspera e ItemFila – ordenação por critérios sociais
│ │ └── transacao.py             # Classe Transacao – movimentação de créditos
│ │
│ ├── services/                  # Regras de negócio e orquestração
│ │ ├── distribuidor_creditos.py # Distribuição automática de créditos
│ │ ├── gerador_relatorio.py     # Relatórios e rankings
│ │ └── painel_transparencia.py  # Métricas públicas e certificados
│ │
│ └── utils/
│ └── logger_auditoria.py        # Logger global + enums de ações (auditoria)
│
└── FrontEnd/
├── index.html                   # Página principal da plataforma
├── login.html                   # Tela de login e cadastro
│
├── assets/
│ ├── css/                       # Estilos modulares (base, layout, componentes)
│ │ ├── base.css
│ │ ├── components.css
│ │ ├── layout.css
│ │ ├── styles.css
│ │ ├── login-css/styles.css     # CSS específico da tela de login
│ │ └── sections/                # Estilos por seção da página
│ │ ├── _header.css
│ │ ├── _hero.css
│ │ ├── _contact.css
│ │ └── _footer.css
│ │
│ ├── images/                    # Imagens e ícones usados nas seções
│ └── js/                        # Scripts de interação e comportamento
│ ├── main.js                    # Interações gerais da página inicial
│ └── login.js                   # Lógica de autenticação e validação
```
---
🧩 Arquitetura do Sistema

O projeto segue uma arquitetura modular e orientada a camadas, separando responsabilidades de forma clara:

Camada	Função
Models	Representam as entidades centrais do domínio (usuários, créditos, transações, fila)
Mixins	Implementam comportamentos reutilizáveis (ex.: auditoria)
Services	Contêm as regras de negócio e orquestração de processos
Utils	Responsáveis por utilidades, logs e enums auxiliares
FrontEnd	Interface de interação com o usuário final (HTML, CSS, JS)

Essa separação garante alta coesão e baixo acoplamento, facilitando manutenção, testes e expansão futura (como dashboards dinâmicos).

---

📈 Roadmap Futuro

Autenticação real e banco conectado (PostgreSQL).

Painel de transparência dinâmico com dados em tempo real.

Testes unitários e integração contínua (CI/CD).

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
