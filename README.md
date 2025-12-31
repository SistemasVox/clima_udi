# Sentinela — Sistema de Monitoramento Climático (clima_udi)

Visão geral
----------
Sentinela é um orquestrador Python para monitoramento de dados meteorológicos (INMET/local), análise de zonas (temperatura, umidade, vento, chuva, radiação, pressão) e envio de notificações via WhatsApp. Projetado para execução periódica via cron (intervalo padrão: 5 minutos).

Principais componentes
----------------------
- sentinela/
  - main.py             — Orquestrador principal
  - config.py           — Configurações centrais
  - database.py         — Acesso ao banco de dados (sqlite / sincronização)
  - state_manager.py    — Controle de estados e anti-spam
  - zona_*.py           — Regras por zona (temperatura, chuva, etc.)
  - message_composer.py — Montagem de mensagens/relatórios
  - send_whatsapp.py    — Wrapper para envio via WhatsApp
  - states.json         — Estado runtime (normalmente ignorado no git)
- api/
  - api_clima.py
  - mysql_config.py
- sincro_db/
  - clima_uberlandia.db — banco sqlite (NÃO comitar no repositório)

Pré-requisitos
--------------
- Python 3.10+ (testado em 3.11)
- pip
- Virtualenv / venv recomendado
- Acesso à internet para API INMET (Config.API_URL)
- Credenciais / configuração do envio WhatsApp (ver `send_whatsapp.py`)

Instalação (exemplo)
--------------------
1. Na máquina/servidor:
   ```
   cd /var/www/clima
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
   Se não existir `requirements.txt`, instale manualmente as libs necessárias (requests, mysql-connector-python, etc.)

2. Ajuste configurações:
   - Edite `sentinela/config.py` se necessário (STATION_ID, WHATSAPP_NUMBERS etc.)
   - Prefira variáveis de ambiente para credenciais sensíveis (ex.: DB, tokens).

Execução (manual)
-----------------
1. Entrar no diretório da aplicação:
   ```
   cd /var/www/clima/sentinela
   source ../venv/bin/activate   # ajuste conforme seu venv
   python3 main.py
   ```

2. Saída de logs por padrão vai para STDOUT — o cron sugerido (abaixo) redireciona para arquivo.

Configuração em cron (exemplo)
------------------------------
Executa a cada 5 minutos (ajuste paths conforme seu ambiente):
```
*/5 * * * * cd /var/www/clima/sentinela && /usr/bin/python3 main.py >> /var/www/clima/sentinela/main.log 2>&1
```

Boas práticas / Segurança
-------------------------
- NÃO versionar bancos de dados, arquivos com credenciais ou estados runtime.
- Armazenar credenciais em variáveis de ambiente ou um cofre (Vault).
- Se já comitou arquivos sensíveis, remova-os do histórico (BFG ou git filter-repo) e rotacione credenciais.
- Verifique que `api/venv`, `sentinela/__pycache__`, `*.db`, `*.log` e `states.json` estejam ignorados pelo git.

Ajudas / Troubleshooting
------------------------
- Sem leituras: verifique conectividade com a API e permissões ao DB.
- Erros ao enviar WhatsApp: rode `send_whatsapp.py` com `-m` para debug.
- Logs: `sentinela/main.log` contém saída agregada quando executado via cron.

Contribuição
-----------
1. Abra issue descrevendo o problema/feature.
2. Crie branch com prefixo `feature/` ou `fix/`.
3. Faça PR com descrição e testes.

Licença
-------
Coloque aqui a licença do projeto (ex.: MIT) ou remova seção se quiser manter privado.

Contato
-------
Repo mantido por: SistemasVox