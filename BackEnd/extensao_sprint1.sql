-- ============================================
-- QUERY 1: TODOS OS USUÁRIOS CADASTRADOS
-- ============================================
SELECT 
    u.id_usuario,
    u.nome,
    u.email,
    tu.descricao_tipo AS tipo_usuario,
    s.descricao_status AS status,
    cu.login,
    cu.data_ultimo_login,
    TO_CHAR(cu.data_ultimo_login, 'DD/MM/YYYY HH24:MI:SS') AS ultimo_acesso_formatado
FROM usuario u
LEFT JOIN tipo_usuario tu ON u.id_tipo = tu.id_tipo
LEFT JOIN status s ON u.id_status = s.id_status
LEFT JOIN credencial_usuario cu ON u.id_credencial = cu.id_credencial
ORDER BY u.id_usuario DESC;

-- ============================================
-- QUERY 2: TODOS OS DOADORES
-- ============================================
SELECT 
    d.id_doador,
    u.nome,
    u.email,
    cd.descricao_classificacao AS classificacao,
    d.razao_social,
    d.cnpj,
    TO_CHAR(d.data_cadastro, 'DD/MM/YYYY') AS data_cadastro,
    -- Total doado por este doador
    COALESCE(
        (SELECT SUM(quantidade_disponivel_kwh) 
         FROM credito 
         WHERE id_doador = d.id_doador), 0
    ) AS total_kwh_doados,
    -- Total distribuído
    COALESCE(
        (SELECT SUM(t.quantidade_kwh)
         FROM transacao t
         JOIN credito c ON t.id_credito = c.id_credito
         JOIN status_transacao st ON t.id_status_transacao = st.id_status_transacao
         WHERE c.id_doador = d.id_doador 
           AND st.descricao_status = 'CONCLUIDA'), 0
    ) AS total_kwh_distribuidos
FROM doador d
JOIN usuario u ON d.id_usuario = u.id_usuario
LEFT JOIN classificacao_doador cd ON d.id_classificacao = cd.id_classificacao
ORDER BY d.id_doador DESC;

-- ============================================
-- QUERY 3: TODOS OS BENEFICIÁRIOS
-- ============================================
SELECT 
    b.id_beneficiario,
    u.nome,
    u.email,
    b.num_moradores,
    COALESCE(rb.valor_renda, 0) AS renda_familiar,
    COALESCE(cb.media_kwh, 0) AS consumo_medio_kwh,
    sb.descricao_status_beneficiario AS status,
    -- Total recebido
    COALESCE(
        (SELECT SUM(t.quantidade_kwh)
         FROM transacao t
         JOIN status_transacao st ON t.id_status_transacao = st.id_status_transacao
         WHERE t.id_beneficiario = b.id_beneficiario 
           AND st.descricao_status = 'CONCLUIDA'), 0
    ) AS total_kwh_recebidos,
    -- Posição na fila (se aguardando)
    (
        SELECT COUNT(*) + 1 
        FROM fila_espera f2 
        JOIN status_fila sf2 ON f2.id_status_fila = sf2.id_status_fila
        JOIN fila_espera f3 ON f3.id_beneficiario = b.id_beneficiario
        WHERE sf2.descricao_status_fila = 'AGUARDANDO'
          AND (f2.prioridade > f3.prioridade 
               OR (f2.prioridade = f3.prioridade AND f2.data_entrada < f3.data_entrada))
    ) AS posicao_fila_atual
FROM beneficiario b
JOIN usuario u ON b.id_usuario = u.id_usuario
LEFT JOIN renda_beneficiario rb ON b.id_renda = rb.id_renda
LEFT JOIN consumo_beneficiario cb ON b.id_consumo = cb.id_consumo
LEFT JOIN status_beneficiario sb ON b.id_status_beneficiario = sb.id_status_beneficiario
ORDER BY b.id_beneficiario DESC;

-- ============================================
-- QUERY 4: SENHAS CRIPTOGRAFADAS
-- ============================================
SELECT 
    u.id_usuario,
    u.nome,
    u.email,
    cu.login,
    LEFT(cu.senha_hash, 20) || '...' AS senha_hash_preview,
    LENGTH(cu.senha_hash) AS tamanho_hash,
    LEFT(cu.senha_salt, 20) || '...' AS senha_salt_preview,
   CASE 
    WHEN cu.senha_hash LIKE '$2%' THEN 'BCRYPT_ATIVO'
    ELSE 'NAO_BCRYPT'
END AS status_criptografia
FROM usuario u
JOIN credencial_usuario cu ON u.id_credencial = cu.id_credencial
ORDER BY u.id_usuario DESC;

-- ============================================
-- QUERY 5: LOG DE AUDITORIA COMPLETO
-- ============================================
SELECT 
    l.id_log,
    u.nome AS usuario_nome,
    u.email AS usuario_email,
    ta.descricao_tipo_acao AS acao,
    TO_CHAR(l.data_hora, 'DD/MM/YYYY HH24:MI:SS') AS data_hora_formatada,
    l.ip_acesso,
    l.detalhes,
    td.descricao_tipo_dispositivo AS dispositivo,
    sl.descricao_status_log AS status
FROM log_auditoria l
LEFT JOIN usuario u ON l.id_usuario = u.id_usuario
LEFT JOIN tipo_acao ta ON l.id_tipo_acao = ta.id_tipo_acao
LEFT JOIN tipo_dispositivo td ON l.id_tipo_dispositivo = td.id_tipo_dispositivo
LEFT JOIN status_log sl ON l.id_status_log = sl.id_status_log
ORDER BY l.data_hora DESC
LIMIT 100;

-- ============================================
-- QUERY 6: HISTÓRICO DE DOAÇÕES
-- ============================================
SELECT 
    c.id_credito,
    u.nome AS doador_nome,
    c.quantidade_disponivel_kwh AS kwh_disponiveis,
    (
        SELECT COALESCE(SUM(t.quantidade_kwh), 0)
        FROM transacao t
        JOIN status_transacao st ON t.id_status_transacao = st.id_status_transacao
        WHERE t.id_credito = c.id_credito 
          AND st.descricao_status = 'CONCLUIDA'
    ) AS kwh_consumidos,
    sc.descricao_status AS status_credito,
    TO_CHAR(c.data_expiracao, 'DD/MM/YYYY') AS expira_em
FROM credito c
JOIN doador d ON c.id_doador = d.id_doador
JOIN usuario u ON d.id_usuario = u.id_usuario
JOIN status_credito sc ON c.id_status_credito = sc.id_status_credito
ORDER BY c.id_credito DESC
LIMIT 50;

-- ============================================
-- QUERY 7: HISTÓRICO DE SOLICITAÇÕES/RECEBIMENTOS
-- ============================================
SELECT 
    t.id_transacao,
    u_benef.nome AS beneficiario_nome,
    t.quantidade_kwh,
    TO_CHAR(t.data_transacao, 'DD/MM/YYYY') AS data_transacao,
    u_doador.nome AS doador_nome,
    st.descricao_status AS status_transacao,
    tm.descricao_tipo AS tipo_movimento
FROM transacao t
JOIN beneficiario b ON t.id_beneficiario = b.id_beneficiario
JOIN usuario u_benef ON b.id_usuario = u_benef.id_usuario
LEFT JOIN credito c ON t.id_credito = c.id_credito
LEFT JOIN doador d ON c.id_doador = d.id_doador
LEFT JOIN usuario u_doador ON d.id_usuario = u_doador.id_usuario
LEFT JOIN status_transacao st ON t.id_status_transacao = st.id_status_transacao
LEFT JOIN tipo_movimento tm ON t.id_tipo_movimentacao = tm.id_tipo_movimentacao
ORDER BY t.data_transacao DESC
LIMIT 50;

-- ============================================
-- QUERY 8: FILA ATUAL DE ESPERA
-- ============================================
SELECT 
    ROW_NUMBER() OVER (ORDER BY f.prioridade DESC, f.data_entrada ASC) AS posicao,
    u.nome,
    u.email,
    f.consumo_medio_kwh AS kwh_solicitados,
    f.prioridade,
    TO_CHAR(f.data_entrada, 'DD/MM/YYYY HH24:MI') AS data_entrada,
    EXTRACT(DAY FROM NOW() - f.data_entrada) || ' dias' AS tempo_na_fila,
    sf.descricao_status_fila AS status
FROM fila_espera f
JOIN beneficiario b ON f.id_beneficiario = b.id_beneficiario
JOIN usuario u ON b.id_usuario = u.id_usuario
JOIN status_fila sf ON f.id_status_fila = sf.id_status_fila
WHERE sf.descricao_status_fila = 'AGUARDANDO'
ORDER BY posicao;

-- ============================================
-- CORREÇÃO SIMPLIFICADA DO TRIGGER DE DISTRIBUIÇÃO
-- ============================================

-- 1. Remover constraint problemático
ALTER TABLE fila_espera DROP CONSTRAINT IF EXISTS fila_beneficiario_unico;

-- 2. Recriar função do trigger (CORRIGIDA)
CREATE OR REPLACE FUNCTION trigger_atualizar_fila()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.id_status_transacao = (
        SELECT id_status_transacao FROM status_transacao WHERE descricao_status = 'CONCLUIDA'
    ) THEN
        -- ✅ Atualiza APENAS UMA entrada (a mais antiga AGUARDANDO)
        UPDATE fila_espera
        SET id_status_fila = (
            SELECT id_status_fila FROM status_fila WHERE descricao_status_fila = 'ATENDIDO'
        )
        WHERE id_fila = (
            SELECT id_fila 
            FROM fila_espera f2
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

-- 3. Recriar trigger
DROP TRIGGER IF EXISTS trg_atualizar_fila ON transacao;
CREATE TRIGGER trg_atualizar_fila
    AFTER INSERT OR UPDATE ON transacao
    FOR EACH ROW
    EXECUTE FUNCTION trigger_atualizar_fila();

-- 4. Limpar duplicatas
DELETE FROM fila_espera
WHERE id_fila IN (
    SELECT f1.id_fila
    FROM fila_espera f1
    JOIN status_fila sf1 ON f1.id_status_fila = sf1.id_status_fila
    WHERE sf1.descricao_status_fila = 'ATENDIDO'
      AND EXISTS (
          SELECT 1
          FROM fila_espera f2
          JOIN status_fila sf2 ON f2.id_status_fila = sf2.id_status_fila
          WHERE sf2.descricao_status_fila = 'ATENDIDO'
            AND f2.id_beneficiario = f1.id_beneficiario
            AND f2.data_entrada > f1.data_entrada
      )
);

-- 5. Verificar estado da fila
SELECT 
    sf.descricao_status_fila AS "Status",
    COUNT(*) AS "Quantidade",
    COUNT(DISTINCT f.id_beneficiario) AS "Beneficiários Únicos"
FROM fila_espera f
JOIN status_fila sf ON f.id_status_fila = sf.id_status_fila
GROUP BY sf.descricao_status_fila
ORDER BY sf.descricao_status_fila;

--Total "inicial" doado (soma da quantidade inicial de todos os créditos)
SELECT
  COALESCE(SUM(
    c.quantidade_disponivel_kwh
    + COALESCE((
        SELECT SUM(t.quantidade_kwh)
        FROM transacao t
        JOIN status_transacao st ON t.id_status_transacao = st.id_status_transacao
        WHERE t.id_credito = c.id_credito
          AND st.descricao_status = 'CONCLUIDA'
      ), 0)
  ), 0) AS total_kwh_inicial_doado
FROM credito c;

--Total atualmente disponível (soma de quantidade_disponivel_kwh)
SELECT COALESCE(SUM(quantidade_disponivel_kwh), 0) AS total_kwh_disponivel
FROM credito;

--Total já distribuído (somatório de transações concluídas)
SELECT COALESCE(SUM(t.quantidade_kwh), 0) AS total_kwh_distribuido
FROM transacao t
JOIN status_transacao st ON t.id_status_transacao = st.id_status_transacao
WHERE st.descricao_status = 'CONCLUIDA';

--Resumo por doador (útil para ver origem das doações)
SELECT
  d.id_doador,
  u.nome AS doador,
  COALESCE(SUM(c.quantidade_disponivel_kwh
    + COALESCE((
        SELECT SUM(t.quantidade_kwh)
        FROM transacao t
        JOIN status_transacao st ON t.id_status_transacao = st.id_status_transacao
        WHERE t.id_credito = c.id_credito
          AND st.descricao_status = 'CONCLUIDA'
    ), 0)
  ), 0) AS total_kwh_inicial_doado,
  COALESCE(SUM(c.quantidade_disponivel_kwh), 0) AS total_kwh_disponivel,
  COALESCE((
    SELECT SUM(t2.quantidade_kwh)
    FROM transacao t2
    JOIN credito c2 ON t2.id_credito = c2.id_credito
    JOIN status_transacao st2 ON t2.id_status_transacao = st2.id_status_transacao
    WHERE c2.id_doador = d.id_doador
      AND st2.descricao_status = 'CONCLUIDA'
  ), 0) AS total_kwh_distribuido
FROM doador d
JOIN usuario u ON d.id_usuario = u.id_usuario
LEFT JOIN credito c ON c.id_doador = d.id_doador
GROUP BY d.id_doador, u.nome
ORDER BY total_kwh_inicial_doado DESC;

--Ver detalhes por crédito (linha a linha)
SELECT
  c.id_credito,
  c.quantidade_disponivel_kwh AS disponivel_kwh,
  COALESCE((
    SELECT SUM(t.quantidade_kwh)
    FROM transacao t
    JOIN status_transacao st ON t.id_status_transacao = st.id_status_transacao
    WHERE t.id_credito = c.id_credito
      AND st.descricao_status = 'CONCLUIDA'
  ), 0) AS consumido_kwh,
  (c.quantidade_disponivel_kwh + COALESCE((
    SELECT SUM(t.quantidade_kwh)
    FROM transacao t
    JOIN status_transacao st ON t.id_status_transacao = st.id_status_transacao
    WHERE t.id_credito = c.id_credito
      AND st.descricao_status = 'CONCLUIDA'
  ), 0)) AS quantidade_inicial_estimada,
  c.data_expiracao,
  c.id_doador
FROM credito c
ORDER BY c.id_credito DESC;

SELECT 
    u.id_usuario,
    u.email,
    cu.senha_hash
FROM usuario u
JOIN credencial_usuario cu ON u.id_credencial = cu.id_credencial;