-- Usuários
SELECT id_usuario, nome, email FROM usuario ORDER BY id_usuario DESC LIMIT 10;

-- Doadores
SELECT id_doador, id_usuario, data_cadastro FROM doador ORDER BY id_doador DESC LIMIT 10;

-- Credenciais (ver login e último acesso)
SELECT login, data_ultimo_login FROM credencial_usuario ORDER BY id_credencial DESC LIMIT 10;

-- Logs de auditoria
SELECT id_log, data_hora, detalhes FROM log_auditoria ORDER BY id_log DESC LIMIT 20;