-- =======================================================================
-- SCRIPT COMPLETO DO BANCO DE DADOS "energia_db"
-- Projeto: Energia para Todos
-- =======================================================================

-- ✅ HABILITAR EXTENSÃO PARA CRIPTOGRAFIA
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- =======================================================================
-- TABELAS DE APOIO
-- =======================================================================

CREATE TABLE IF NOT EXISTS TIPO_USUARIO (
    ID_TIPO SERIAL PRIMARY KEY,
    DESCRICAO_TIPO VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS STATUS (
    ID_STATUS SERIAL PRIMARY KEY,
    DESCRICAO_STATUS VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS CLASSIFICACAO_DOADOR (
    ID_CLASSIFICACAO SERIAL PRIMARY KEY,
    DESCRICAO_CLASSIFICACAO VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS STATUS_BENEFICIARIO (
    ID_STATUS_BENEFICIARIO SERIAL PRIMARY KEY,
    DESCRICAO_STATUS_BENEFICIARIO VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS STATUS_CREDITO (
    ID_STATUS_CREDITO SERIAL PRIMARY KEY,
    DESCRICAO_STATUS VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS TIPO_MOVIMENTO (
    ID_TIPO_MOVIMENTACAO SERIAL PRIMARY KEY,
    DESCRICAO_TIPO VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS STATUS_TRANSACAO (
    ID_STATUS_TRANSACAO SERIAL PRIMARY KEY,
    DESCRICAO_STATUS VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS TIPO_ACAO (
    ID_TIPO_ACAO SERIAL PRIMARY KEY,
    DESCRICAO_TIPO_ACAO VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS TIPO_DISPOSITIVO (
    ID_TIPO_DISPOSITIVO SERIAL PRIMARY KEY,
    DESCRICAO_TIPO_DISPOSITIVO VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS STATUS_LOG (
    ID_STATUS_LOG SERIAL PRIMARY KEY,
    DESCRICAO_STATUS_LOG VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS STATUS_FILA (
    ID_STATUS_FILA SERIAL PRIMARY KEY,
    DESCRICAO_STATUS_FILA VARCHAR(50) NOT NULL UNIQUE
);

-- ✅ TABELA TELEFONE
CREATE TABLE IF NOT EXISTS TELEFONE (
    ID_TELEFONE SERIAL PRIMARY KEY,
    NUMERO VARCHAR(20) NOT NULL
);

-- ✅ TABELA CREDENCIAL_USUARIO
CREATE TABLE IF NOT EXISTS CREDENCIAL_USUARIO (
    ID_CREDENCIAL SERIAL PRIMARY KEY,
    LOGIN VARCHAR(120) UNIQUE NOT NULL,
    SENHA_HASH TEXT NOT NULL,
    SENHA_SALT TEXT NOT NULL,
    DATA_ULTIMO_LOGIN TIMESTAMP
);

-- =======================================================================
-- TABELAS PRINCIPAIS
-- =======================================================================

CREATE TABLE IF NOT EXISTS USUARIO (
    ID_USUARIO SERIAL PRIMARY KEY,
    NOME VARCHAR(120) NOT NULL,
    EMAIL VARCHAR(120) UNIQUE NOT NULL,
    CEP VARCHAR(20),
    ID_TELEFONE INTEGER REFERENCES TELEFONE(ID_TELEFONE),
    ID_TIPO INTEGER REFERENCES TIPO_USUARIO(ID_TIPO),
    ID_STATUS INTEGER REFERENCES STATUS(ID_STATUS),
    ID_CREDENCIAL INTEGER REFERENCES CREDENCIAL_USUARIO(ID_CREDENCIAL)
);

CREATE TABLE IF NOT EXISTS DOADOR (
    ID_DOADOR SERIAL PRIMARY KEY,
    DATA_CADASTRO DATE DEFAULT CURRENT_DATE,
    ID_USUARIO INTEGER REFERENCES USUARIO(ID_USUARIO),
    ID_CLASSIFICACAO INTEGER REFERENCES CLASSIFICACAO_DOADOR(ID_CLASSIFICACAO)
);

CREATE TABLE IF NOT EXISTS RENDA_BENEFICIARIO (
    ID_RENDA SERIAL PRIMARY KEY,
    VALOR_RENDA DECIMAL(10,2),
    PERIODO VARCHAR(20) DEFAULT 'MENSAL'
);

CREATE TABLE IF NOT EXISTS CONSUMO_BENEFICIARIO (
    ID_CONSUMO SERIAL PRIMARY KEY,
    MEDIA_KWH DECIMAL(10,2),
    PERIODO VARCHAR(20) DEFAULT 'MENSAL'
);

CREATE TABLE IF NOT EXISTS BENEFICIARIO (
    ID_BENEFICIARIO SERIAL PRIMARY KEY,
    NUM_MORADORES INTEGER,
    ID_USUARIO INTEGER REFERENCES USUARIO(ID_USUARIO),
    ID_RENDA INTEGER REFERENCES RENDA_BENEFICIARIO(ID_RENDA),
    ID_CONSUMO INTEGER REFERENCES CONSUMO_BENEFICIARIO(ID_CONSUMO),
    ID_STATUS_BENEFICIARIO INTEGER REFERENCES STATUS_BENEFICIARIO(ID_STATUS_BENEFICIARIO)
);

CREATE TABLE IF NOT EXISTS CREDITO (
    ID_CREDITO SERIAL PRIMARY KEY,
    QUANTIDADE_DISPONIVEL_KWH DECIMAL(10,2) NOT NULL,
    DATA_EXPIRACAO DATE,
    ID_DOADOR INTEGER REFERENCES DOADOR(ID_DOADOR),
    ID_STATUS_CREDITO INTEGER REFERENCES STATUS_CREDITO(ID_STATUS_CREDITO)
);

CREATE TABLE IF NOT EXISTS TRANSACAO (
    ID_TRANSACAO SERIAL PRIMARY KEY,
    QUANTIDADE_KWH DECIMAL(10,2),
    DATA_TRANSACAO DATE DEFAULT CURRENT_DATE,
    ID_BENEFICIARIO INTEGER REFERENCES BENEFICIARIO(ID_BENEFICIARIO),
    ID_STATUS_TRANSACAO INTEGER REFERENCES STATUS_TRANSACAO(ID_STATUS_TRANSACAO),
    ID_TIPO_MOVIMENTACAO INTEGER REFERENCES TIPO_MOVIMENTO(ID_TIPO_MOVIMENTACAO)
);

CREATE TABLE IF NOT EXISTS HISTORICO_CREDITO (
    ID_HISTORICO SERIAL PRIMARY KEY,
    QUANTIDADE_KWH DECIMAL(10,2),
    DATA_MOVIMENTO DATE DEFAULT CURRENT_DATE,
    ID_CREDITO INTEGER REFERENCES CREDITO(ID_CREDITO)
);

CREATE TABLE IF NOT EXISTS LOG_AUDITORIA (
    ID_LOG SERIAL PRIMARY KEY,
    IP_ACESSO VARCHAR(50),
    DATA_HORA TIMESTAMP DEFAULT NOW(),
    DETALHES TEXT,
    ID_USUARIO INTEGER REFERENCES USUARIO(ID_USUARIO),
    ID_TIPO_ACAO INTEGER REFERENCES TIPO_ACAO(ID_TIPO_ACAO),
    ID_TIPO_DISPOSITIVO INTEGER REFERENCES TIPO_DISPOSITIVO(ID_TIPO_DISPOSITIVO),
    ID_STATUS_LOG INTEGER REFERENCES STATUS_LOG(ID_STATUS_LOG)
);

CREATE TABLE IF NOT EXISTS fila_espera (
    id_fila SERIAL PRIMARY KEY,
    id_beneficiario INTEGER REFERENCES beneficiario(id_beneficiario),
    data_entrada TIMESTAMP DEFAULT NOW(),
    prioridade INTEGER DEFAULT 0,
    id_status_fila INTEGER REFERENCES status_fila(id_status_fila)
);

-- =======================================================================
-- INSERTS INICIAIS
-- =======================================================================

INSERT INTO TIPO_USUARIO (DESCRICAO_TIPO) VALUES 
('DOADOR'), ('BENEFICIARIO'), ('ADMINISTRADOR')
ON CONFLICT (DESCRICAO_TIPO) DO NOTHING;

INSERT INTO STATUS (DESCRICAO_STATUS) VALUES 
('ATIVO'), ('INATIVO'), ('PENDENTE'), ('BLOQUEADO')
ON CONFLICT (DESCRICAO_STATUS) DO NOTHING;

INSERT INTO CLASSIFICACAO_DOADOR (DESCRICAO_CLASSIFICACAO) VALUES 
('PESSOA_FISICA'), ('PESSOA_JURIDICA')
ON CONFLICT (DESCRICAO_CLASSIFICACAO) DO NOTHING;

INSERT INTO STATUS_BENEFICIARIO (DESCRICAO_STATUS_BENEFICIARIO) VALUES 
('AGUARDANDO_APROVACAO'), ('APROVADO'), ('EM_ATENDIMENTO'), ('SUSPENSO'), ('INATIVO')
ON CONFLICT (DESCRICAO_STATUS_BENEFICIARIO) DO NOTHING;

INSERT INTO STATUS_CREDITO (DESCRICAO_STATUS) VALUES 
('DISPONIVEL'), ('PARCIALMENTE_UTILIZADO'), ('ESGOTADO'), ('EXPIRADO'), ('BLOQUEADO')
ON CONFLICT (DESCRICAO_STATUS) DO NOTHING;

INSERT INTO TIPO_MOVIMENTO (DESCRICAO_TIPO) VALUES 
('DISTRIBUICAO'), ('ESTORNO'), ('AJUSTE'), ('EXPIRACAO')
ON CONFLICT (DESCRICAO_TIPO) DO NOTHING;

INSERT INTO STATUS_TRANSACAO (DESCRICAO_STATUS) VALUES 
('CONCLUIDA'), ('PENDENTE'), ('CANCELADA'), ('ERRO')
ON CONFLICT (DESCRICAO_STATUS) DO NOTHING;

INSERT INTO TIPO_ACAO (DESCRICAO_TIPO_ACAO) VALUES 
('LOGIN'), ('LOGOUT'), ('CADASTRO'), ('DOACAO'), ('DISTRIBUICAO')
ON CONFLICT (DESCRICAO_TIPO_ACAO) DO NOTHING;

INSERT INTO TIPO_DISPOSITIVO (DESCRICAO_TIPO_DISPOSITIVO) VALUES 
('WEB'), ('MOBILE')
ON CONFLICT (DESCRICAO_TIPO_DISPOSITIVO) DO NOTHING;

INSERT INTO STATUS_LOG (DESCRICAO_STATUS_LOG) VALUES 
('SUCESSO'), ('FALHA'), ('PENDENTE'), ('ALERTA')
ON CONFLICT (DESCRICAO_STATUS_LOG) DO NOTHING;

INSERT INTO STATUS_FILA (DESCRICAO_STATUS_FILA) VALUES 
('AGUARDANDO'), ('EM_DISTRIBUICAO'), ('ATENDIDO'), ('REMOVIDO')
ON CONFLICT (DESCRICAO_STATUS_FILA) DO NOTHING;

-- ============================================
-- ADICIONAR CAMPOS DE PESSOA JURÍDICA
-- ============================================

-- Adiciona campos de PJ ao doador
ALTER TABLE doador
  ADD COLUMN IF NOT EXISTS razao_social VARCHAR(120),
  ADD COLUMN IF NOT EXISTS cnpj VARCHAR(14);

ALTER TABLE doador ALTER COLUMN cnpj TYPE VARCHAR(18);

-- Índice/único para CNPJ (opcional, mas recomendado)
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uk_doador_cnpj'
  ) THEN
    ALTER TABLE doador ADD CONSTRAINT uk_doador_cnpj UNIQUE (cnpj);
  END IF;
END$$;

-- =======================================================================
-- ✅ FIM DO SCRIPT
-- =======================================================================

-- ============================================
-- CORREÇÃO DA LÓGICA DA FILA DINÂMICA
-- Execute este script para garantir que a fila funcione corretamente
-- ============================================

-- 1. CRIAR FUNÇÃO PARA RECALCULAR POSIÇÕES DA FILA
-- Esta função recalcula as posições de TODOS os beneficiários na fila
CREATE OR REPLACE FUNCTION recalcular_posicoes_fila()
RETURNS void AS $$
BEGIN
    -- A posição é calculada dinamicamente na query, não precisa armazenar
    -- Apenas garantimos que beneficiários atendidos não apareçam mais como AGUARDANDO
    
    -- Remove da fila beneficiários que já foram atendidos
    UPDATE fila_espera f
    SET id_status_fila = (
        SELECT id_status_fila FROM status_fila WHERE descricao_status_fila = 'ATENDIDO'
    )
    WHERE f.id_beneficiario IN (
        SELECT DISTINCT t.id_beneficiario
        FROM transacao t
        JOIN status_transacao st ON t.id_status_transacao = st.id_status_transacao
        WHERE st.descricao_status = 'CONCLUIDA'
    )
    AND f.id_status_fila = (
        SELECT id_status_fila FROM status_fila WHERE descricao_status_fila = 'AGUARDANDO'
    );
    
END;
$$ LANGUAGE plpgsql;

-- 2. VIEW ATUALIZADA PARA FILA COM POSIÇÕES DINÂMICAS
CREATE OR REPLACE VIEW v_fila_priorizada AS
SELECT 
    f.id_fila,
    f.id_beneficiario,
    b.id_usuario,
    u.nome,
    u.email,
    f.prioridade,
    f.data_entrada,
    f.renda_familiar,
    f.consumo_medio_kwh,
    f.num_moradores,
    f.tempo_espera_dias,
    EXTRACT(DAY FROM NOW() - f.data_entrada) AS dias_na_fila,
    -- POSIÇÃO CALCULADA DINAMICAMENTE
    (
        SELECT COUNT(*) + 1 
        FROM fila_espera f2 
        JOIN status_fila sf2 ON f2.id_status_fila = sf2.id_status_fila
        WHERE sf2.descricao_status_fila = 'AGUARDANDO'
          AND (
              f2.prioridade > f.prioridade 
              OR (f2.prioridade = f.prioridade AND f2.data_entrada < f.data_entrada)
          )
    ) AS posicao_fila,
    sf.descricao_status_fila
FROM fila_espera f
JOIN beneficiario b ON f.id_beneficiario = b.id_beneficiario
JOIN usuario u ON b.id_usuario = u.id_usuario
JOIN status_fila sf ON f.id_status_fila = sf.id_status_fila
WHERE sf.descricao_status_fila = 'AGUARDANDO'
ORDER BY f.prioridade DESC, f.data_entrada ASC;

-- 3. TRIGGER PARA RECALCULAR FILA AUTOMATICAMENTE
-- Sempre que uma transação é concluída, atualiza a fila
CREATE OR REPLACE FUNCTION trigger_atualizar_fila()
RETURNS TRIGGER AS $$
BEGIN
    -- Marca beneficiário como ATENDIDO se ele recebeu créditos
    IF NEW.id_status_transacao = (
        SELECT id_status_transacao FROM status_transacao WHERE descricao_status = 'CONCLUIDA'
    ) THEN
        -- Atualiza APENAS UMA entrada da fila (a mais antiga AGUARDANDO) para evitar
        -- violação de única (um beneficiário não pode ter duas linhas com o mesmo status).
        -- Fazemos a atualização por id_fila escolhido por subquery com LIMIT 1.
        UPDATE fila_espera
        SET id_status_fila = (
            SELECT id_status_fila FROM status_fila WHERE descricao_status_fila = 'ATENDIDO'
        )
        WHERE id_fila = (
            SELECT id_fila FROM fila_espera f2
            WHERE f2.id_beneficiario = NEW.id_beneficiario
              AND f2.id_status_fila = (
                  SELECT id_status_fila FROM status_fila WHERE descricao_status_fila = 'AGUARDANDO'
              )
            ORDER BY f2.data_entrada ASC
            LIMIT 1
        )
        AND id_status_fila = (
              SELECT id_status_fila FROM status_fila WHERE descricao_status_fila = 'AGUARDANDO'
        );
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Remove trigger antigo se existir
DROP TRIGGER IF EXISTS trg_atualizar_fila ON transacao;

-- Cria novo trigger
CREATE TRIGGER trg_atualizar_fila
    AFTER INSERT OR UPDATE ON transacao
    FOR EACH ROW
    EXECUTE FUNCTION trigger_atualizar_fila();

-- 4. QUERY PARA VERIFICAR FILA ATUALIZADA
-- Use esta query para ver a fila atual com posições corretas
SELECT 
    posicao_fila AS "Posição",
    nome AS "Nome",
    email AS "Email",
    consumo_medio_kwh AS "kWh Solicitados",
    prioridade AS "Prioridade",
    TO_CHAR(data_entrada, 'DD/MM/YYYY HH24:MI') AS "Data Entrada",
    dias_na_fila AS "Dias na Fila"
FROM v_fila_priorizada
ORDER BY posicao_fila;

-- 5. LIMPAR DADOS INCONSISTENTES (EXECUTAR UMA VEZ)
-- Remove beneficiários da fila que já foram atendidos mas ainda aparecem como AGUARDANDO
DO $$
BEGIN
    -- Marca como ATENDIDO todos que receberam créditos
    UPDATE fila_espera f
    SET id_status_fila = (
        SELECT id_status_fila FROM status_fila WHERE descricao_status_fila = 'ATENDIDO'
    )
    WHERE f.id_beneficiario IN (
        SELECT DISTINCT t.id_beneficiario
        FROM transacao t
        JOIN status_transacao st ON t.id_status_transacao = st.id_status_transacao
        WHERE st.descricao_status = 'CONCLUIDA'
    )
    AND f.id_status_fila = (
        SELECT id_status_fila FROM status_fila WHERE descricao_status_fila = 'AGUARDANDO'
    );
    
    RAISE NOTICE 'Fila recalculada com sucesso!';
END $$;

-- 6. TESTE: VERIFICAR TOTAL DE BENEFICIÁRIOS NA FILA
SELECT 
    COUNT(*) AS "Total na Fila",
    COUNT(CASE WHEN descricao_status_fila = 'AGUARDANDO' THEN 1 END) AS "Aguardando",
    COUNT(CASE WHEN descricao_status_fila = 'ATENDIDO' THEN 1 END) AS "Atendidos"
FROM fila_espera f
JOIN status_fila sf ON f.id_status_fila = sf.id_status_fila;

-- ============================================
-- QUERIES ÚTEIS PARA DIAGNÓSTICO
-- ============================================

-- Ver histórico completo de um beneficiário específico
-- Substitua {ID_BENEFICIARIO} pelo ID real
/*
SELECT 
    f.id_fila,
    f.consumo_medio_kwh AS "kWh Solicitados",
    TO_CHAR(f.data_entrada, 'DD/MM/YYYY HH24:MI') AS "Data",
    sf.descricao_status_fila AS "Status",
    CASE 
        WHEN sf.descricao_status_fila = 'AGUARDANDO' THEN
            (SELECT COUNT(*) + 1 
             FROM fila_espera f2 
             JOIN status_fila sf2 ON f2.id_status_fila = sf2.id_status_fila
             WHERE sf2.descricao_status_fila = 'AGUARDANDO'
               AND (f2.prioridade > f.prioridade 
                    OR (f2.prioridade = f.prioridade AND f2.data_entrada < f.data_entrada)))
        ELSE NULL
    END AS "Posição Atual"
FROM fila_espera f
JOIN status_fila sf ON f.id_status_fila = sf.id_status_fila
WHERE f.id_beneficiario = {ID_BENEFICIARIO}
ORDER BY f.data_entrada DESC;
*/

-- Ver todas as transações concluídas
SELECT 
    t.id_transacao,
    u.nome AS "Beneficiário",
    t.quantidade_kwh AS "kWh Recebidos",
    TO_CHAR(t.data_transacao, 'DD/MM/YYYY') AS "Data"
FROM transacao t
JOIN beneficiario b ON t.id_beneficiario = b.id_beneficiario
JOIN usuario u ON b.id_usuario = u.id_usuario
JOIN status_transacao st ON t.id_status_transacao = st.id_status_transacao
WHERE st.descricao_status = 'CONCLUIDA'
ORDER BY t.data_transacao DESC
LIMIT 20;

-- ============================================
-- SCRIPT DE DEBUG PARA BENEFICIÁRIO ID=14
-- Execute este script no PostgreSQL
-- ============================================

-- 1. VERIFICAR SE O BENEFICIÁRIO EXISTE
SELECT 
    b.id_beneficiario,
    b.id_usuario,
    b.num_moradores,
    b.id_renda,
    b.id_consumo,
    b.id_status_beneficiario,
    u.nome,
    u.email
FROM beneficiario b
JOIN usuario u ON b.id_usuario = u.id_usuario
WHERE b.id_beneficiario = 14;

-- 2. VERIFICAR DADOS DE RENDA
SELECT * FROM renda_beneficiario
WHERE id_renda IN (
    SELECT id_renda FROM beneficiario WHERE id_beneficiario = 14
);

-- 3. VERIFICAR DADOS DE CONSUMO
SELECT * FROM consumo_beneficiario
WHERE id_consumo IN (
    SELECT id_consumo FROM beneficiario WHERE id_beneficiario = 14
);

-- 4. VERIFICAR STATUS DO BENEFICIÁRIO
SELECT sb.* 
FROM status_beneficiario sb
WHERE sb.id_status_beneficiario IN (
    SELECT id_status_beneficiario FROM beneficiario WHERE id_beneficiario = 14
);

-- 5. QUERY COMPLETA (MESMA DO CÓDIGO)
SELECT b.id_beneficiario, 
       COALESCE(b.num_moradores, 0) AS num_moradores,
       COALESCE(rb.valor_renda, 0) AS valor_renda, 
       COALESCE(cb.media_kwh, 0) AS media_kwh,
       COALESCE(sb.descricao_status_beneficiario, 'AGUARDANDO_APROVACAO') AS descricao_status_beneficiario,
       u.nome, u.email
FROM beneficiario b
JOIN usuario u ON b.id_usuario = u.id_usuario
LEFT JOIN renda_beneficiario rb ON b.id_renda = rb.id_renda
LEFT JOIN consumo_beneficiario cb ON b.id_consumo = cb.id_consumo
LEFT JOIN status_beneficiario sb ON b.id_status_beneficiario = sb.id_status_beneficiario
WHERE b.id_beneficiario = 14;

-- 6. VERIFICAR FILA DE ESPERA
SELECT * FROM fila_espera
WHERE id_beneficiario = 14;

-- 7. VERIFICAR TRANSAÇÕES
SELECT * FROM transacao
WHERE id_beneficiario = 14;

-- ============================================
-- SE NÃO RETORNAR NADA, EXECUTE ESTA CORREÇÃO:
-- ============================================

-- Atualiza o beneficiário para garantir que tenha status
UPDATE beneficiario
SET id_status_beneficiario = (
    SELECT id_status_beneficiario 
    FROM status_beneficiario 
    WHERE descricao_status_beneficiario = 'APROVADO'
)
WHERE id_beneficiario = 14
  AND id_status_beneficiario IS NULL;

-- Verifica resultado
SELECT * FROM beneficiario WHERE id_beneficiario = 14;

-- ============================================
-- SISTEMA DE PERMISSÕES - ENERGIA PARA TODOS
-- Versão Atualizada (sem telefone)
-- ============================================

-- 1. Garantir que tipo ADMINISTRADOR existe
INSERT INTO tipo_usuario (descricao_tipo) 
VALUES ('ADMINISTRADOR')
ON CONFLICT (descricao_tipo) DO NOTHING;

-- 2. Criar usuário administrador padrão
DO $$
DECLARE
    v_id_credencial INTEGER;
    v_id_tipo INTEGER;
    v_id_status INTEGER;
    v_id_usuario INTEGER;
BEGIN
    -- Buscar IDs necessários
    SELECT id_tipo INTO v_id_tipo 
    FROM tipo_usuario 
    WHERE descricao_tipo = 'ADMINISTRADOR';

    SELECT id_status INTO v_id_status 
    FROM status 
    WHERE descricao_status = 'ATIVO';

    IF v_id_status IS NULL THEN
        RAISE EXCEPTION 'O status ATIVO não existe na tabela status.';
    END IF;

    -- Criar credencial (senha: admin123)
    INSERT INTO credencial_usuario (login, senha_hash, senha_salt)
    VALUES (
        'admin@energiaparatodos.com',
        crypt('admin123', gen_salt('bf')),
        gen_salt('bf')
    )
    RETURNING id_credencial INTO v_id_credencial;

    -- Criar usuário administrador (sem telefone)
    INSERT INTO usuario (nome, email, id_tipo, id_status, cep, id_credencial)
    VALUES (
        'Administrador Sistema',
        'admin@energiaparatodos.com',
        v_id_tipo,
        v_id_status,
        '00000-000',
        v_id_credencial
    )
    RETURNING id_usuario INTO v_id_usuario;

    RAISE NOTICE '✅ Usuário administrador criado com sucesso!';
    RAISE NOTICE '📧 Email: admin@energiaparatodos.com';
    RAISE NOTICE '🔑 Senha: admin123';
    RAISE NOTICE '🆔 ID: %', v_id_usuario;
END $$;

-- 3. Criar tabela de configurações do sistema
CREATE TABLE IF NOT EXISTS configuracao_sistema (
    id_config SERIAL PRIMARY KEY,
    chave VARCHAR(100) UNIQUE NOT NULL,
    valor TEXT,
    descricao TEXT,
    data_atualizacao TIMESTAMP DEFAULT NOW()
);

-- Inserir configurações iniciais
INSERT INTO configuracao_sistema (chave, valor, descricao) VALUES
    ('taxa_conversao_co2', '0.356', 'kg de CO2 por kWh evitado'),
    ('dias_expiracao_credito', '365', 'Dias até crédito expirar'),
    ('limite_solicitacao_mes', '1', 'Número máximo de solicitações por mês')
ON CONFLICT (chave) DO NOTHING;

-- 4. View para métricas do administrador
CREATE OR REPLACE VIEW v_metricas_admin AS
SELECT
    -- Usuários
    (SELECT COUNT(*) FROM usuario) AS total_usuarios,
    (SELECT COUNT(*) FROM usuario u JOIN tipo_usuario tu ON u.id_tipo = tu.id_tipo WHERE tu.descricao_tipo = 'DOADOR') AS total_doadores,
    (SELECT COUNT(*) FROM usuario u JOIN tipo_usuario tu ON u.id_tipo = tu.id_tipo WHERE tu.descricao_tipo = 'BENEFICIARIO') AS total_beneficiarios,

    -- Créditos
    (SELECT COALESCE(SUM(quantidade_disponivel_kwh), 0) FROM credito) AS creditos_disponiveis,
    (SELECT COALESCE(SUM(t.quantidade_kwh), 0) FROM transacao t 
        JOIN status_transacao st ON t.id_status_transacao = st.id_status_transacao 
        WHERE st.descricao_status = 'CONCLUIDA') AS creditos_distribuidos,

    -- Filas
    (SELECT COUNT(*) FROM fila_espera f 
        JOIN status_fila sf ON f.id_status_fila = sf.id_status_fila 
        WHERE sf.descricao_status_fila = 'AGUARDANDO') AS beneficiarios_na_fila,

    -- Atividade
    (SELECT COUNT(*) FROM log_auditoria WHERE data_hora >= NOW() - INTERVAL '24 hours') AS atividades_24h,
    (SELECT COUNT(*) FROM log_auditoria WHERE data_hora >= NOW() - INTERVAL '7 days') AS atividades_7d;

-- Adiciona coluna se não existir
ALTER TABLE transacao 
ADD COLUMN IF NOT EXISTS id_credito INTEGER REFERENCES credito(id_credito);

-- Cria índice para performance
CREATE INDEX IF NOT EXISTS idx_transacao_credito ON transacao(id_credito);