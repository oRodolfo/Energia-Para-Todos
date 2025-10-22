-- Usuários
SELECT id_usuario, nome, email FROM usuario ORDER BY id_usuario DESC LIMIT 1000;

-- Doadores
SELECT id_doador, id_usuario, data_cadastro FROM doador ORDER BY id_doador DESC LIMIT 1000;

-- Credenciais (ver login e último acesso)
SELECT login, data_ultimo_login FROM credencial_usuario ORDER BY id_credencial DESC LIMIT 1000;

-- Logs de auditoria
SELECT id_log, data_hora, detalhes FROM log_auditoria ORDER BY id_log DESC LIMIT 2000;