#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import uvicorn  # Adicionado para corrigir o NameError
from fastapi import FastAPI, Response, HTTPException
import aiomysql
import logging
from contextlib import asynccontextmanager
from mysql_config import MYSQL_CONFIG

# Configuração de Logs para monitoramento via Systemd
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("API-CLIMA")

# --- CACHE EM MEMÓRIA (SINGLETON) ---
class WeatherCache:
    """Evita consultas pesadas ao MySQL se os dados não mudaram."""
    data = None        
    version_key = None 

# Pool de conexões global
db_pool = None

# --- GERENCIADOR DE CICLO DE VIDA (LIFESPAN) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia a conexão com o banco na subida e descida da API."""
    global db_pool
    # Ajusta o dicionário de configuração para compatibilidade com aiomysql
    config = MYSQL_CONFIG.copy()
    if 'database' in config:
        config['db'] = config.pop('database') 
    
    # Remove parâmetros do mysql-connector incompatíveis com aiomysql
    chaves_remover = ['use_unicode', 'autocommit', 'charset', 'ssl_disabled', 'ssl_ca']
    for chave in chaves_remover:
        config.pop(chave, None)

    try:
        db_pool = await aiomysql.create_pool(
            **config,
            minsize=1,
            maxsize=15, 
            autocommit=True
        )
        logger.info(f"✓ Pool MySQL ativo em: {config.get('host')}")
        yield
    finally:
        if db_pool:
            db_pool.close()
            await db_pool.wait_closed()
            logger.info("✓ Conexões MySQL encerradas")

app = FastAPI(title="SVOX Clima API", lifespan=lifespan)

async def fetch_latest_data_logic():
    """Busca o último registro usando Smart Cache para poupar o MySQL."""
    async with db_pool.acquire() as conn:
        async with conn.cursor() as cur:
            # Verifica versão via índices (Rápido)
            await cur.execute("SELECT MAX(id), COUNT(*) FROM medicoes")
            metadata = await cur.fetchone()
            
            # Se o banco não mudou, retorna o cache da RAM
            if WeatherCache.version_key == metadata and WeatherCache.data:
                return WeatherCache.data

            # Se mudou, busca a linha completa
            async with conn.cursor(aiomysql.DictCursor) as dict_cur:
                await dict_cur.execute("SELECT * FROM medicoes ORDER BY id DESC LIMIT 1")
                row = await dict_cur.fetchone()
                
                if not row:
                    raise HTTPException(status_code=404, detail="Sem dados")
                
                WeatherCache.data = row
                WeatherCache.version_key = metadata
                return row

# --- ENDPOINTS ---

@app.api_route("/clima/ultimo", methods=["GET", "HEAD"])
async def get_ultimo_json():
    """Retorna o registro mais recente em JSON."""
    return await fetch_latest_data_logic()

@app.api_route("/clima/txt", methods=["GET", "HEAD"])
async def get_ultimo_txt():
    """Retorna dados brutos para o OpenWRT (DATA|HORA|TEMP|UMID|PRES|VENTO|CHUVA|RAD)."""
    data = await fetch_latest_data_logic()
    
    # Ordem dos campos para o comando 'cut' do OpenWRT
    fields = [
        data['dt_medicao'], data['hr_medicao'], data['tem_ins'], 
        data['umd_ins'], data['pre_ins'], data['ven_vel'], 
        data['chuva'], data['rad_glo']
    ]
    txt_payload = "|".join(str(v) for v in fields)
    
    return Response(content=txt_payload, media_type="text/plain")

@app.get("/clima/historico")
async def get_historico(limite: int = 50):
    """Retorna histórico JSON (máx 500 registros)."""
    if limite > 500: limite = 500
    
    async with db_pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as dict_cur:
            await dict_cur.execute("SELECT * FROM medicoes ORDER BY id DESC LIMIT %s", (limite,))
            rows = await dict_cur.fetchall()
            return {"count": len(rows), "data": rows}

@app.get("/status")
async def health():
    return {"status": "online", "db": "connected" if db_pool else "error"}

if __name__ == "__main__":
    # Escuta em 127.0.0.1 para segurança (Nginx faz o proxy)
    uvicorn.run(app, host="127.0.0.1", port=8000)