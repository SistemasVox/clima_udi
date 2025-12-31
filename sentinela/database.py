#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
database.py - Gerenciador de conexão MySQL e queries
Sistema Sentinela v2.0
"""

import pymysql
from datetime import datetime, timedelta


class WeatherDatabase:
    """
    Gerenciador de conexão e queries ao MySQL
    """
    
    def __init__(self):
        self.connection = None
        self.host = 'xxxxxxxxxxxxxxxxxxxx'
        self.user = 'xxxxxxxxxxxxxxxxxxxx'
        self.password = 'xxxxxxxxxxxxxxxxxxxx'
        self.database = 'xxxxxxxxxxxxxxxxxxxx'
    
    def connect(self):
        """Conecta ao MySQL"""
        try:
            self.connection = pymysql.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
            return True
        except Exception as e:
            print(f"Erro ao conectar MySQL: {e}")
            return False
    
    def get_latest_reading(self):
        """
        Retorna a leitura mais recente
        
        Returns:
            dict: Dicionário com todos os campos da leitura
        """
        try:
            with self.connection.cursor() as cursor:
                query = """
                SELECT 
                    cd_estacao,
                    dt_medicao,
                    hr_medicao,
                    timestamp,
                    tem_ins,
                    tem_min,
                    tem_max,
                    tem_sen,
                    umd_ins,
                    umd_min,
                    umd_max,
                    pre_ins,
                    pre_min,
                    pre_max,
                    pto_ins,
                    pto_min,
                    pto_max,
                    ven_vel,
                    ven_dir,
                    ven_raj,
                    chuva,
                    rad_glo
                FROM medicoes
                ORDER BY timestamp DESC
                LIMIT 1
                """
                cursor.execute(query)
                result = cursor.fetchone()
                
                # Trata valores None e converte para float
                if result:
                    for key in result:
                        if result[key] is None and key not in ['cd_estacao', 'dt_medicao', 'hr_medicao', 'timestamp']:
                            result[key] = 0.0
                
                return result
        except Exception as e:
            print(f"Erro ao buscar leitura atual: {e}")
            return None
    
    def get_reading_hours_ago(self, hours):
        """
        Retorna leitura de N horas atrás usando dt_medicao + hr_medicao
        IMPORTANTE: INMET usa UTC-3, então compensa o fuso horário
        
        Args:
            hours (int): Número de horas atrás
            
        Returns:
            dict: Leitura ou None
        """
        try:
            with self.connection.cursor() as cursor:
                # Busca últimos N+5 registros para ter margem
                query = """
                SELECT 
                    tem_ins, umd_ins, pre_ins, ven_vel, ven_raj,
                    chuva, rad_glo, timestamp,
                    dt_medicao, hr_medicao,
                    STR_TO_DATE(
                        CONCAT(dt_medicao, ' ', LPAD(hr_medicao, 4, '0')),
                        '%%Y-%%m-%%d %%H%%i'
                    ) as medicao_real
                FROM medicoes
                ORDER BY dt_medicao DESC, hr_medicao DESC
                LIMIT %s
                """
                cursor.execute(query, (hours + 5,))
                registros = cursor.fetchall()
                
                if not registros:
                    return None
                
                # Pega o mais recente (primeiro)
                mais_recente = registros[0]
                hora_alvo = mais_recente['medicao_real']
                
                if not hora_alvo:
                    return None
                
                # Calcula horário N horas atrás
                from datetime import timedelta
                hora_busca = hora_alvo - timedelta(hours=hours)
                
                # Busca registro mais próximo dessa hora
                melhor_registro = None
                menor_diferenca = None
                
                for registro in registros:
                    if registro['medicao_real']:
                        diferenca = abs((registro['medicao_real'] - hora_busca).total_seconds())
                        if menor_diferenca is None or diferenca < menor_diferenca:
                            menor_diferenca = diferenca
                            melhor_registro = registro
                
                return melhor_registro
                
        except Exception as e:
            print(f"Erro ao buscar leitura de {hours}h atrás: {e}")
            return None
    
    def get_reading_n_records_ago(self, n):
        """
        Retorna leitura N posições antes da mais recente
        Usa dt_medicao + hr_medicao para ordenação correta
        
        Args:
            n (int): Número de registros atrás (1=1h atrás, 3=3h atrás)
            
        Returns:
            dict: Leitura ou None
        """
        try:
            with self.connection.cursor() as cursor:
                query = """
                SELECT 
                    tem_ins, umd_ins, pre_ins, ven_vel, ven_raj,
                    chuva, rad_glo, timestamp,
                    dt_medicao, hr_medicao,
                    STR_TO_DATE(
                        CONCAT(dt_medicao, ' ', LPAD(hr_medicao, 4, '0')),
                        '%%Y-%%m-%%d %%H%%i'
                    ) as medicao_real
                FROM medicoes
                ORDER BY dt_medicao DESC, hr_medicao DESC
                LIMIT 1 OFFSET %s
                """
                cursor.execute(query, (n,))
                return cursor.fetchone()
        except Exception as e:
            print(f"Erro ao buscar leitura {n} registros atrás: {e}")
            return None
    
    def get_reading_minutes_ago(self, minutes):
        """
        Retorna leitura de N minutos atrás
        
        Args:
            minutes (int): Número de minutos atrás
            
        Returns:
            dict: Leitura ou None
        """
        try:
            with self.connection.cursor() as cursor:
                query = """
                SELECT 
                    tem_ins, umd_ins, pre_ins, ven_vel, ven_raj,
                    chuva, rad_glo, timestamp
                FROM medicoes
                WHERE timestamp <= DATE_SUB(NOW(), INTERVAL %s MINUTE)
                ORDER BY timestamp DESC
                LIMIT 1
                """
                cursor.execute(query, (minutes,))
                return cursor.fetchone()
        except Exception as e:
            print(f"Erro ao buscar leitura de {minutes}min atrás: {e}")
            return None
    
    def get_last_day_period(self):
        """
        Retorna última transição noite→dia (radiação 0→>0)
        
        Returns:
            dict: timestamp do início do dia
        """
        try:
            with self.connection.cursor() as cursor:
                query = """
                SELECT timestamp
                FROM medicoes
                WHERE rad_glo > 0
                AND DATE(timestamp) = CURDATE()
                ORDER BY timestamp ASC
                LIMIT 1
                """
                cursor.execute(query)
                return cursor.fetchone()
        except Exception as e:
            print(f"Erro ao buscar início do dia: {e}")
            return None
    
    def get_last_night_period(self):
        """
        Retorna última transição dia→noite (radiação >0→0)
        
        Returns:
            dict: timestamp do início da noite
        """
        try:
            with self.connection.cursor() as cursor:
                query = """
                SELECT timestamp
                FROM medicoes
                WHERE rad_glo <= 0
                AND DATE(timestamp) = CURDATE()
                ORDER BY timestamp ASC
                LIMIT 1
                """
                cursor.execute(query)
                return cursor.fetchone()
        except Exception as e:
            print(f"Erro ao buscar início da noite: {e}")
            return None
    
    def get_day_summary(self):
        """
        Resumo do dia atual (desde radiação > 0)
        
        Returns:
            dict: Estatísticas do dia
        """
        try:
            with self.connection.cursor() as cursor:
                query = """
                SELECT 
                    MAX(tem_ins) as temp_max,
                    MIN(tem_ins) as temp_min,
                    MAX(rad_glo) as rad_max,
                    MIN(umd_ins) as umid_min,
                    SUM(chuva) as chuva_total,
                    MAX(ven_raj) as rajada_max,
                    MIN(timestamp) as inicio,
                    MAX(timestamp) as fim
                FROM medicoes
                WHERE DATE(timestamp) = CURDATE()
                AND rad_glo > 0
                """
                cursor.execute(query)
                result = cursor.fetchone()
                
                # Calcula duração
                if result and result['inicio'] and result['fim']:
                    duracao = result['fim'] - result['inicio']
                    horas = int(duracao.total_seconds() // 3600)
                    minutos = int((duracao.total_seconds() % 3600) // 60)
                    result['duracao_horas'] = horas
                    result['duracao_minutos'] = minutos
                
                return result
        except Exception as e:
            print(f"Erro ao gerar resumo do dia: {e}")
            return None
    
    def get_night_summary(self):
        """
        Resumo da última noite (desde radiação <= 0)
        
        Returns:
            dict: Estatísticas da noite
        """
        try:
            with self.connection.cursor() as cursor:
                # Busca última vez que radiação foi > 0
                query_inicio = """
                SELECT timestamp
                FROM medicoes
                WHERE rad_glo > 0
                ORDER BY timestamp DESC
                LIMIT 1
                """
                cursor.execute(query_inicio)
                inicio = cursor.fetchone()
                
                if not inicio:
                    return None
                
                # Estatísticas desde então
                query = """
                SELECT 
                    MAX(tem_ins) as temp_max,
                    MIN(tem_ins) as temp_min,
                    AVG(umd_ins) as umid_media,
                    SUM(chuva) as chuva_total,
                    MAX(ven_raj) as rajada_max,
                    MIN(timestamp) as inicio,
                    MAX(timestamp) as fim
                FROM medicoes
                WHERE timestamp > %s
                AND rad_glo <= 0
                """
                cursor.execute(query, (inicio['timestamp'],))
                result = cursor.fetchone()
                
                # Calcula duração
                if result and result['inicio'] and result['fim']:
                    duracao = result['fim'] - result['inicio']
                    horas = int(duracao.total_seconds() // 3600)
                    minutos = int((duracao.total_seconds() % 3600) // 60)
                    result['duracao_horas'] = horas
                    result['duracao_minutos'] = minutos
                
                return result
        except Exception as e:
            print(f"Erro ao gerar resumo da noite: {e}")
            return None
    
    def get_accumulated_rain_24h(self):
        """
        Retorna chuva acumulada nas últimas 24 horas
        
        Returns:
            float: Total de chuva em mm
        """
        try:
            with self.connection.cursor() as cursor:
                query = """
                SELECT SUM(chuva) as total
                FROM medicoes
                WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
                """
                cursor.execute(query)
                result = cursor.fetchone()
                return result['total'] if result and result['total'] else 0.0
        except Exception as e:
            print(f"Erro ao calcular chuva 24h: {e}")
            return 0.0
    
    def get_pressure_variation(self, hours=3):
        """
        Calcula variação de pressão nas últimas N horas
        Usa dt_medicao + hr_medicao para cálculo correto
        
        Args:
            hours (int): Janela de tempo (1 ou 3 horas)
            
        Returns:
            float: Delta de pressão (positivo = subindo, negativo = caindo)
        """
        try:
            leitura_atual = self.get_latest_reading()
            leitura_anterior = self.get_reading_hours_ago(hours)
            
            if leitura_atual and leitura_anterior:
                delta = leitura_atual['pre_ins'] - leitura_anterior['pre_ins']
                # Debug
                if leitura_anterior.get('medicao_real'):
                    print(f"  🔍 Variação pressão {hours}h: {delta:+.1f} hPa")
                return delta
            
            return 0.0
        except Exception as e:
            print(f"Erro ao calcular variação de pressão: {e}")
            return 0.0
    
    def get_temperature_variation(self, hours=3):
        """
        Calcula variação de temperatura nas últimas N horas
        Usa dt_medicao + hr_medicao para cálculo correto
        
        Args:
            hours (int): Janela de tempo (1 ou 3 horas)
            
        Returns:
            float: Delta de temperatura
        """
        try:
            leitura_atual = self.get_latest_reading()
            leitura_anterior = self.get_reading_hours_ago(hours)
            
            if leitura_atual and leitura_anterior:
                delta = leitura_atual['tem_ins'] - leitura_anterior['tem_ins']
                # Debug
                if leitura_anterior.get('medicao_real'):
                    print(f"  🔍 Variação temp {hours}h: {delta:+.1f}°C")
                return delta
            
            return 0.0
        except Exception as e:
            print(f"Erro ao calcular variação de temperatura: {e}")
            return 0.0
    
    def close(self):
        """Fecha conexão com MySQL"""
        if self.connection:
            self.connection.close()
            self.connection = None