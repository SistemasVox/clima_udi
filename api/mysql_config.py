# mysql_config.example.py
# -*- coding: utf-8 -*-
"""
Exemplo de arquivo de configuração MySQL
Copie para mysql_config.py e ajuste os valores
"""

# ============================================================================
# CONFIGURAÇÃO MYSQL
# ============================================================================

# Conexão local
MYSQL_LOCAL = {
    'host': 'localhost',
    'port': 3306,
    'user': 'xxxxxxxxxxxxxxxxxxxx',
    'password': 'xxxxxxxxxxxxxxxxxxxx',
    'database': 'clima_tempo',
    'charset': 'utf8mb4',
    'use_unicode': True,
    'autocommit': False
}

# Conexão remota (exemplo)
MYSQL_REMOTO = {
    'host': 'xxxxxxxxxxxxxxxxxxxx',  # IP do servidor remoto
    'port': 3306,
    'user': 'xxxxxxxxxxxxxxxxxxxx',
    'password': 'xxxxxxxxxxxxxxxxxxxx',
    'database': 'xxxxxxxxxxxxxxxxxxxx',
    'charset': 'utf8mb4',
    'use_unicode': True,
    'autocommit': False
}

# Conexão nuvem (exemplo - AWS RDS, Google Cloud SQL, etc)
MYSQL_NUVEM = {
    'host': 'clima-db.xxxxxx.us-east-1.rds.amazonaws.com',
    'port': 3306,
    'user': 'admin',
    'password': 'senha_super_segura',
    'database': 'clima_producao',
    'charset': 'utf8mb4',
    'use_unicode': True,
    'ssl_ca': '/path/to/ca-cert.pem',  # Certificado SSL se necessário
    'ssl_disabled': False
}

# ============================================================================
# CONFIGURAÇÃO ATIVA (escolha uma)
# ============================================================================

# Descomente a configuração que deseja usar:

# MYSQL_CONFIG = MYSQL_LOCAL
MYSQL_CONFIG = MYSQL_REMOTO
# MYSQL_CONFIG = MYSQL_NUVEM

# ============================================================================
# INSTRUÇÕES DE USO
# ============================================================================

"""
1. CRIAR BANCO DE DADOS NO MYSQL:

   mysql -u root -p
   
   CREATE DATABASE clima_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   
   CREATE USER 'usuario_clima'@'localhost' IDENTIFIED BY 'senha_segura';
   
   GRANT ALL PRIVILEGES ON clima_db.* TO 'usuario_clima'@'localhost';
   
   FLUSH PRIVILEGES;
   
   EXIT;

2. TESTAR CONEXÃO:

   mysql -u usuario_clima -p clima_db

3. SINCRONIZAR DADOS:

   # Primeira vez (sincronizar tudo)
   python mysql_sync.py --full
   
   # Sincronização incremental (apenas novos dados)
   python mysql_sync.py

4. VERIFICAR DADOS:

   mysql -u usuario_clima -p clima_db
   
   SELECT COUNT(*) FROM medicoes;
   
   SELECT * FROM medicoes ORDER BY id DESC LIMIT 5;

5. CONFIGURAR ACESSO REMOTO (se necessário):

   # No servidor MySQL, editar:
   sudo nano /etc/mysql/mysql.conf.d/mysqld.cnf
   
   # Alterar bind-address:
   bind-address = 0.0.0.0
   
   # Reiniciar MySQL:
   sudo systemctl restart mysql
   
   # Permitir usuário remoto:
   mysql -u root -p
   
   CREATE USER 'usuario_clima'@'%' IDENTIFIED BY 'senha_segura';
   GRANT ALL PRIVILEGES ON clima_db.* TO 'usuario_clima'@'%';
   FLUSH PRIVILEGES;

6. SEGURANÇA - IMPORTANTE:

   - Use senhas fortes e únicas
   - Configure firewall para permitir apenas IPs confiáveis
   - Use SSL/TLS para conexões remotas
   - Faça backup regular do banco de dados
   - Nunca commite senhas no Git (.gitignore este arquivo)

7. BACKUP AUTOMATIZADO:

   # Criar script de backup diário
   0 3 * * * mysqldump -u usuario_clima -p'senha' clima_db > /backup/clima_$(date +\\%Y\\%m\\%d).sql

8. MONITORAMENTO:

   # Ver tamanho do banco
   SELECT 
       table_schema AS 'Database',
       ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS 'Size (MB)'
   FROM information_schema.TABLES
   WHERE table_schema = 'clima_db'
   GROUP BY table_schema;
   
   # Ver quantidade de registros
   SELECT COUNT(*) FROM medicoes;
   
   # Ver registros de hoje
   SELECT * FROM medicoes WHERE dt_medicao = CURDATE();
"""
