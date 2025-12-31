#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
config.py - Configurações centralizadas do Sistema Sentinela
Versão de produção para execução via cron
"""

import os
import sys
from datetime import datetime, time
from pathlib import Path


class Config:
    """Configurações centralizadas do sistema de monitoramento climático."""
    
    # =============================================
    # PATHS ABSOLUTOS (resistentes a cron)
    # =============================================
    BASE_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
    DB_PATH = BASE_DIR / "clima_uberlandia.db"
    MODEL_PATH = BASE_DIR / "chuva_model.pkl"
    LOG_DIR = BASE_DIR / "logs"
    LOCK_FILE = BASE_DIR / ".sentinela.lock"
    
    # Criar diretório de logs se não existir
    LOG_DIR.mkdir(exist_ok=True)
    
    # =============================================
    # API INMET (URL CORRETA - 2025)
    # =============================================
    API_URL = "https://apiprevmet3.inmet.gov.br/estacao/proxima/3170206"
    STATION_ID = "A507"
    TIMEOUT = 10
    MAX_RETRIES = 12
    RETRY_DELAYS = [5, 7.5, 10, 12, 15, 20, 25, 30, 40, 50, 60, 90]
    USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    
    # =============================================
    # CONFIGURAÇÕES DE RESILIÊNCIA
    # =============================================
    MAX_LOCK_AGE = 300  # segundos (5 minutos) - máximo que um lock pode existir
    MAX_DB_SIZE = 100 * 1024 * 1024  # 100MB máximo para o banco
    MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB máximo por arquivo de log
    MAX_LOG_FILES = 5  # máximo de arquivos de log a manter
    
    # =============================================
    # CONFIGURAÇÕES DE EXECUÇÃO CRON
    # =============================================
    CRON_INTERVAL = 300  # 5 minutos em segundos
    EXECUTION_TIMEOUT = 280  # timeout da execução (deve ser menor que o intervalo)
    MIN_DB_ENTRIES = 10  # mínimo de entradas para considerar dados válidos
    
    # =============================================
    # LIMITES PARA DETECÇÃO DE ALERTAS
    # =============================================
    # Deltas mínimos para considerar variação significativa
    LIMITE_TEMP = 0.5           # °C
    LIMITE_UMIDADE = 5          # %
    LIMITE_PRESSAO = 2.0        # hPa
    
    # Temperaturas críticas
    TEMP_BAIXA = 18.0           # °C - Considerado frio
    TEMP_ALTA = 32.0            # °C - Considerado quente
    
    # Frente Fria
    HISTORICO_FRENTE_FRIA = 72  # leituras (6 horas)
    FRENTE_FRIA_LIMITE = -3.0   # °C de queda
    
    # Tempestade
    TEMPESTADE_VENTO_LIMITE = 10.0   # m/s
    TEMPESTADE_CHUVA_LIMITE = 20.0   # mm
    
    # Chuva acumulada
    CHUVA_ACUMULADA_ALERTA = 50.0    # mm em 24h
    
    # =============================================
    # LIMIARES DE RADIAÇÃO SOLAR (kJ/m²)
    # Baseado em índice UV e padrões internacionais
    # =============================================
    RAD_LIMITS = {
        "NOITE": 50,           # < 50 kJ/m² = noite
        "BAIXA": 1000,         # 50-1000 = baixa
        "MODERADA": 2000,      # 1000-2000 = moderada
        "ALTA": 2500,          # 2000-2500 = alta
        "MUITO ALTA": 3000,    # 2500-3000 = muito alta
        "EXTREMA": 3000        # >= 3000 = extrema
    }
    
    # Janelas de tempo
    RADIACAO_DIA_CLARO = 1000      # kJ/m² - Dia claro
    RADIACAO_DIA_NUBLADO = 500     # kJ/m² - Dia nublado
    HISTORICO_RAD_POR_SOL = 36     # leituras (3 horas)
    
    # =============================================
    # CLASSIFICAÇÃO DE INTENSIDADE DE CHUVA (mm)
    # =============================================
    CHUVA_LIMITS = {
        "GAROA": 2.5,          # < 2.5 mm
        "FRACA": 10,           # 2.5-10 mm
        "MODERADA": 30,        # 10-30 mm
        "FORTE": 50,           # 30-50 mm
        "MUITO_FORTE": 50      # >= 50 mm
    }
    
    # =============================================
    # ESCALA BEAUFORT - VELOCIDADE DO VENTO (m/s)
    # =============================================
    VENTO_CALMO = 0.3              # < 0.3 m/s = Calmo
    VENTO_ARAGEM = 1.5             # 0.3-1.5 = Aragem
    VENTO_BRISA_LEVE = 3.3         # 1.5-3.3 = Brisa Leve
    VENTO_BRISA_MODERADA = 5.4     # 3.3-5.4 = Brisa Moderada
    VENTO_BRISA_FRESCA = 7.9       # 5.4-7.9 = Brisa Fresca
    VENTO_MODERADO = 10.7          # 7.9-10.7 = Vento Moderado
    VENTO_FORTE = 13.8             # 10.7-13.8 = Vento Forte
    # > 13.8 = VENTANIA/TEMPESTADE
    
    # =============================================
    # CLASSIFICAÇÃO DE CONFORTO TÉRMICO
    # Baseado em experiência local (Uberlândia) e padrões ASHRAE
    # Ajustado para clima tropical brasileiro
    # =============================================
    CONFORTO_FRIO = 19.0              # < 19°C = Frio (precisa agasalho)
    CONFORTO_FRESCO = 21.0            # 19-21°C = Fresco (ótima troca de calor)
    CONFORTO_IDEAL = 24.0             # 21-24°C = Confortável (perfeito)
    CONFORTO_MORNO = 27.0             # 24-27°C = Morno (começando esquentar)
    CONFORTO_QUENTE = 30.0            # 27-30°C = Quente (desconfortável)
    CONFORTO_MUITO_QUENTE = 33.0      # 30-33°C = Muito quente (suor, fadiga)
    # > 33°C = Calor extremo (risco à saúde)
    
    # =============================================
    # LIMIARES PARA FORMATAÇÃO DE MENSAGENS
    # =============================================
    # Sensação térmica
    DIFERENCA_SENSACAO_MIN = 0.5      # °C - Diferença mínima para mostrar sensação térmica
    
    # Heat Index
    HEAT_INDEX_ALERTA_MIN = 30.0      # °C - Mínimo para alertar sobre índice de calor
    HEAT_INDEX_DIFERENCA_MIN = 2.0    # °C - Diferença mínima entre HI e temperatura real
    
    # VPD (Vapor Pressure Deficit)
    VPD_CRITICO = 2.0                 # kPa - Ar muito seco (alerta)
    
    # Probabilidades da IA (Random Forest)
    IA_PROB_ALTA = 0.85               # 85% - Probabilidade alta de chuva
    IA_PROB_MODERADA = 0.70           # 70% - Probabilidade moderada de chuva
    
    # Zonas perigosas de radiação
    ZONAS_PERIGOSAS = ["MUITO ALTA", "EXTREMA"]
    
    # Avisos de proteção solar
    PROTECAO_SOLAR_FPS = "50+"
    PROTECAO_SOLAR_HORARIO = "10h-16h"
    
    # =============================================
    # CONFIGURAÇÕES DE NOTIFICAÇÃO
    # =============================================
    WHATSAPP_NUMBERS = os.environ.get('WHATSAPP_NUMBERS', 'xxxxxxxxxxxxxxxxxxxx')
    
    @staticmethod
    def setup_environment():
        """Configura ambiente para execução via cron."""
        # Define encoding padrão
        if sys.platform != "win32":
            import locale
            locale.setlocale(locale.LC_ALL, 'C')
        
        # Adiciona diretório atual ao PYTHONPATH
        sys.path.insert(0, str(Config.BASE_DIR))
    
    @staticmethod
    def get_log_file():
        """Retorna path do arquivo de log do dia."""
        today = datetime.now().strftime("%Y-%m-%d")
        return Config.LOG_DIR / f"sentinela_{today}.log"
    
    @staticmethod
    def cleanup_old_logs():
        """Remove logs antigos mantendo apenas os últimos N arquivos."""
        try:
            log_files = sorted(Config.LOG_DIR.glob("sentinela_*.log"))
            if len(log_files) > Config.MAX_LOG_FILES:
                for old_log in log_files[:-Config.MAX_LOG_FILES]:
                    try:
                        old_log.unlink()
                    except:
                        pass
        except Exception:
            pass
    
    # =============================================
    # MÉTODOS DE CLASSIFICAÇÃO
    # =============================================
    
    @staticmethod
    def get_rad_zone(radiacao):
        """Retorna a zona de radiação UV baseada no valor em kJ/m²."""
        if radiacao < Config.RAD_LIMITS["NOITE"]:
            return "NOITE"
        elif radiacao < Config.RAD_LIMITS["BAIXA"]:
            return "BAIXA"
        elif radiacao < Config.RAD_LIMITS["MODERADA"]:
            return "MODERADA"
        elif radiacao < Config.RAD_LIMITS["ALTA"]:
            return "ALTA"
        elif radiacao < Config.RAD_LIMITS["MUITO ALTA"]:
            return "MUITO ALTA"
        else:
            return "EXTREMA"
    
    @staticmethod
    def get_chuva_intensity(chuva_mm):
        """Retorna intensidade da chuva baseada em mm."""
        if chuva_mm < Config.CHUVA_LIMITS["GAROA"]:
            return "GAROA"
        elif chuva_mm < Config.CHUVA_LIMITS["FRACA"]:
            return "FRACA"
        elif chuva_mm < Config.CHUVA_LIMITS["MODERADA"]:
            return "MODERADA"
        elif chuva_mm < Config.CHUVA_LIMITS["FORTE"]:
            return "FORTE"
        else:
            return "MUITO_FORTE"
    
    @staticmethod
    def get_beaufort_scale(vento_vel):
        """Retorna classificação Beaufort do vento."""
        if vento_vel < Config.VENTO_CALMO:
            return "Calmo"
        elif vento_vel < Config.VENTO_ARAGEM:
            return "Aragem"
        elif vento_vel < Config.VENTO_BRISA_LEVE:
            return "Brisa Leve"
        elif vento_vel < Config.VENTO_BRISA_MODERADA:
            return "Brisa Moderada"
        elif vento_vel < Config.VENTO_BRISA_FRESCA:
            return "Brisa Fresca"
        elif vento_vel < Config.VENTO_MODERADO:
            return "Vento Moderado"
        elif vento_vel < Config.VENTO_FORTE:
            return "Vento Forte"
        else:
            return "VENTANIA"
    
    @staticmethod
    def get_conforto_termico(temperatura):
        """
        Classifica o conforto térmico baseado na temperatura.
        
        Retorna tupla: (categoria, emoji, descricao)
        """
        if temperatura < Config.CONFORTO_FRIO:
            return ("FRIO", "🥶", "Frio (precisa agasalho)")
        elif temperatura < Config.CONFORTO_FRESCO:
            return ("FRESCO", "🌡️", "Fresco (ótima troca de calor)")
        elif temperatura < Config.CONFORTO_IDEAL:
            return ("IDEAL", "✅", "Confortável (perfeito)")
        elif temperatura < Config.CONFORTO_MORNO:
            return ("MORNO", "🌤️", "Morno (começando a esquentar)")
        elif temperatura < Config.CONFORTO_QUENTE:
            return ("QUENTE", "🔥", "Quente (desconfortável)")
        elif temperatura < Config.CONFORTO_MUITO_QUENTE:
            return ("MUITO_QUENTE", "🥵", "Muito quente (suor, fadiga)")
        else:
            return ("EXTREMO", "🔴", "Calor extremo (risco à saúde)")
    
    @staticmethod
    def is_janela_por_sol():
        """Verifica se estamos em janela de pôr do sol (16h-20h)."""
        now = datetime.now().time()
        return time(16, 0) <= now <= time(20, 0)
    
    @staticmethod
    def is_janela_meio_dia():
        """Verifica se estamos próximos ao meio-dia (11h-13h)."""
        now = datetime.now().time()
        return time(11, 0) <= now <= time(13, 0)
    
    @staticmethod
    def is_hora_relatorio():
        """Verifica se é hora de enviar relatório (06:00 ou 18:00)."""
        now = datetime.now().time()
        return now.hour in [6, 18] and now.minute < 10
    
    @staticmethod
    def get_tipo_relatorio():
        """Retorna tipo de relatório baseado na hora."""
        hora = datetime.now().hour
        if hora == 6:
            return "BOM DIA"
        elif hora == 18:
            return "BOA NOITE"
        return None


# Configura ambiente automaticamente
Config.setup_environment()