#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_collector.py - Orquestrador Principal do Sistema de Coleta Meteorológica
Versão: 3.0 - Autossuficiente
Data: 2025-12-30

Orquestrador completo que gerencia:
- Coleta de dados da API INMET
- Armazenamento no SQLite
- Sincronização com MySQL
- Recuperação automática de dados perdidos
- Tratamento de erros e retry logic

Para uso com cron: */5 * * * * /usr/bin/python3 /path/to/run_collector.py
"""

import sqlite3
import json
import time
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
import requests


# ============================================================================
# CONFIGURAÇÕES
# ============================================================================

class Config:
    """Configurações do sistema."""
    
    # Carregar de config.py se existir
    try:
        from config import Config as ExternalConfig
        BASE_DIR = ExternalConfig.BASE_DIR
        DB_PATH = ExternalConfig.DB_PATH
        API_URL = ExternalConfig.API_URL
        MAX_RETRIES = ExternalConfig.MAX_RETRIES
        RETRY_DELAYS = ExternalConfig.RETRY_DELAYS
        USER_AGENT = ExternalConfig.USER_AGENT
    except ImportError:
        # Configurações padrão
        BASE_DIR = Path(__file__).parent
        DB_PATH = BASE_DIR / "clima_uberlandia.db"
        API_URL = "https://apiprevmet3.inmet.gov.br/estacao/proxima/3170206"
        MAX_RETRIES = 12
        RETRY_DELAYS = [5, 7.5, 10, 12, 15, 20, 25, 30, 40, 50, 60, 90]
        USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"


# ============================================================================
# MÓDULO: GERENCIADOR DE BANCO DE DADOS SQLITE
# ============================================================================

class SQLiteManager:
    """Gerencia operações no banco SQLite."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
    
    def connect(self) -> bool:
        """Conecta e inicializa banco."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            self._create_schema()
            return True
        except sqlite3.Error as e:
            print(f"✗ Erro SQLite: {e}")
            return False
    
    def _create_schema(self):
        """Cria estrutura do banco se não existir."""
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS medicoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cd_estacao TEXT NOT NULL,
                dt_medicao DATE NOT NULL,
                hr_medicao TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                tem_ins REAL, tem_min REAL, tem_max REAL, tem_sen REAL,
                umd_ins REAL, umd_min REAL, umd_max REAL,
                pre_ins REAL, pre_min REAL, pre_max REAL,
                pto_ins REAL, pto_min REAL, pto_max REAL,
                ven_vel REAL, ven_dir INTEGER, ven_raj REAL,
                chuva REAL, rad_glo REAL,
                UNIQUE(cd_estacao, dt_medicao, hr_medicao)
            )
        """)
        
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_dt_hr ON medicoes(dt_medicao, hr_medicao)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON medicoes(timestamp)")
        self.conn.commit()
    
    def is_duplicate(self, dados: Dict[str, Any]) -> bool:
        """Verifica se dados já existem (compara valores meteorológicos)."""
        try:
            self.cursor.execute("""
                SELECT tem_ins, umd_ins, pre_ins, ven_vel, chuva, rad_glo
                FROM medicoes
                WHERE cd_estacao = ? AND dt_medicao = ? AND hr_medicao = ?
                ORDER BY id DESC LIMIT 1
            """, (dados.get('CD_ESTACAO'), dados.get('DT_MEDICAO'), dados.get('HR_MEDICAO')))
            
            result = self.cursor.fetchone()
            if not result:
                return False
            
            # Comparar valores principais
            valores_db = {'tem_ins': result[0], 'umd_ins': result[1], 'pre_ins': result[2],
                         'ven_vel': result[3], 'chuva': result[4], 'rad_glo': result[5]}
            
            valores_novos = {
                'tem_ins': self._to_float(dados.get('TEM_INS')),
                'umd_ins': self._to_float(dados.get('UMD_INS')),
                'pre_ins': self._to_float(dados.get('PRE_INS')),
                'ven_vel': self._to_float(dados.get('VEN_VEL')),
                'chuva': self._to_float(dados.get('CHUVA')),
                'rad_glo': self._to_float(dados.get('RAD_GLO'))
            }
            
            return all(valores_db[k] == valores_novos[k] for k in valores_db)
        except:
            return False
    
    def insert(self, dados: Dict[str, Any]) -> bool:
        """Insere nova medição."""
        try:
            if self.is_duplicate(dados):
                print("⊘ Dados duplicados detectados")
                return False
            
            self.cursor.execute("""
                INSERT OR IGNORE INTO medicoes (
                    cd_estacao, dt_medicao, hr_medicao,
                    tem_ins, tem_min, tem_max, tem_sen,
                    umd_ins, umd_min, umd_max,
                    pre_ins, pre_min, pre_max,
                    pto_ins, pto_min, pto_max,
                    ven_vel, ven_dir, ven_raj,
                    chuva, rad_glo
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                dados.get('CD_ESTACAO'), dados.get('DT_MEDICAO'), dados.get('HR_MEDICAO'),
                self._to_float(dados.get('TEM_INS')), self._to_float(dados.get('TEM_MIN')),
                self._to_float(dados.get('TEM_MAX')), self._to_float(dados.get('TEM_SEN')),
                self._to_float(dados.get('UMD_INS')), self._to_float(dados.get('UMD_MIN')),
                self._to_float(dados.get('UMD_MAX')), self._to_float(dados.get('PRE_INS')),
                self._to_float(dados.get('PRE_MIN')), self._to_float(dados.get('PRE_MAX')),
                self._to_float(dados.get('PTO_INS')), self._to_float(dados.get('PTO_MIN')),
                self._to_float(dados.get('PTO_MAX')), self._to_float(dados.get('VEN_VEL')),
                self._to_int(dados.get('VEN_DIR')), self._to_float(dados.get('VEN_RAJ')),
                self._to_float(dados.get('CHUVA')), self._to_float(dados.get('RAD_GLO'))
            ))
            
            self.conn.commit()
            return self.cursor.rowcount > 0
        except Exception as e:
            print(f"✗ Erro ao inserir: {e}")
            self.conn.rollback()
            return False
    
    def count(self) -> int:
        """Retorna total de registros."""
        try:
            self.cursor.execute("SELECT COUNT(*) FROM medicoes")
            return self.cursor.fetchone()[0]
        except:
            return 0
    
    def cleanup_old_data(self, days: int = 90):
        """Remove dados antigos."""
        try:
            cutoff = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            self.cursor.execute("DELETE FROM medicoes WHERE dt_medicao < ?", (cutoff,))
            deleted = self.cursor.rowcount
            self.conn.commit()
            if deleted > 0:
                self.cursor.execute("VACUUM")
                print(f"✓ Limpeza: {deleted} registros antigos removidos")
        except:
            pass
    
    def close(self):
        if self.conn:
            self.conn.close()
    
    @staticmethod
    def _to_float(value) -> Optional[float]:
        try:
            return float(value) if value is not None else None
        except:
            return None
    
    @staticmethod
    def _to_int(value) -> Optional[int]:
        try:
            return int(value) if value is not None else None
        except:
            return None


# ============================================================================
# MÓDULO: GERENCIADOR MYSQL
# ============================================================================

class MySQLManager:
    """Gerencia operações no MySQL."""
    
    def __init__(self):
        self.conn = None
        self.mysql = None
        self.config = None
    
    def connect(self) -> bool:
        """Conecta ao MySQL."""
        try:
            import mysql.connector
        except ImportError:
            print("⚠ mysql-connector-python não instalado, MySQL desabilitado")
            return False
        
        try:
            from mysql_config import MYSQL_CONFIG
        except ImportError:
            print("⚠ mysql_config.py não encontrado, MySQL desabilitado")
            return False
        
        try:
            self.mysql = mysql.connector
            self.config = MYSQL_CONFIG
            self.conn = self.mysql.connect(**MYSQL_CONFIG)
            self._ensure_schema()
            print(f"✓ Conectado ao MySQL: {MYSQL_CONFIG['host']}")
            return True
        except Exception as e:
            print(f"⚠ Não foi possível conectar ao MySQL: {e}")
            return False
    
    def _ensure_schema(self):
        """Garante que estrutura existe."""
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS medicoes (
                id INT AUTO_INCREMENT PRIMARY KEY,
                cd_estacao VARCHAR(10) NOT NULL,
                dt_medicao DATE NOT NULL,
                hr_medicao VARCHAR(4) NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                tem_ins FLOAT, tem_min FLOAT, tem_max FLOAT, tem_sen FLOAT,
                umd_ins FLOAT, umd_min FLOAT, umd_max FLOAT,
                pre_ins FLOAT, pre_min FLOAT, pre_max FLOAT,
                pto_ins FLOAT, pto_min FLOAT, pto_max FLOAT,
                ven_vel FLOAT, ven_dir INT, ven_raj FLOAT,
                chuva FLOAT, rad_glo FLOAT,
                UNIQUE KEY unique_medicao (cd_estacao, dt_medicao, hr_medicao),
                INDEX idx_dt_hr (dt_medicao, hr_medicao)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        self.conn.commit()
        cursor.close()
    
    def count(self) -> int:
        """Retorna total de registros."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM medicoes")
            result = cursor.fetchone()[0]
            cursor.close()
            return result
        except:
            return 0
    
    def sync_from_sqlite(self, sqlite_db: SQLiteManager, full: bool = False) -> int:
        """Sincroniza dados do SQLite para MySQL."""
        try:
            # Configurar row_factory antes de buscar dados
            sqlite_db.conn.row_factory = sqlite3.Row
            sqlite_cursor = sqlite_db.conn.cursor()
            
            if full:
                sqlite_cursor.execute("SELECT * FROM medicoes ORDER BY id")
            else:
                sqlite_cursor.execute("SELECT * FROM medicoes ORDER BY id DESC LIMIT 1")
            
            mysql_cursor = self.conn.cursor()
            synced = 0
            skipped = 0
            total = 0
            
            for row in sqlite_cursor:
                total += 1
                
                # Converter Row para dict
                record = {
                    'cd_estacao': row['cd_estacao'],
                    'dt_medicao': row['dt_medicao'],
                    'hr_medicao': row['hr_medicao'],
                    'tem_ins': row['tem_ins'],
                    'tem_min': row['tem_min'],
                    'tem_max': row['tem_max'],
                    'tem_sen': row['tem_sen'],
                    'umd_ins': row['umd_ins'],
                    'umd_min': row['umd_min'],
                    'umd_max': row['umd_max'],
                    'pre_ins': row['pre_ins'],
                    'pre_min': row['pre_min'],
                    'pre_max': row['pre_max'],
                    'pto_ins': row['pto_ins'],
                    'pto_min': row['pto_min'],
                    'pto_max': row['pto_max'],
                    'ven_vel': row['ven_vel'],
                    'ven_dir': row['ven_dir'],
                    'ven_raj': row['ven_raj'],
                    'chuva': row['chuva'],
                    'rad_glo': row['rad_glo']
                }
                
                try:
                    # Verificar se já existe ANTES de tentar inserir
                    mysql_cursor.execute("""
                        SELECT id FROM medicoes 
                        WHERE cd_estacao = %(cd_estacao)s 
                        AND dt_medicao = %(dt_medicao)s 
                        AND hr_medicao = %(hr_medicao)s
                    """, record)
                    
                    if mysql_cursor.fetchone() is not None:
                        # Registro já existe, pular
                        skipped += 1
                        continue
                    
                    # Registro não existe, inserir
                    mysql_cursor.execute("""
                        INSERT INTO medicoes (
                            cd_estacao, dt_medicao, hr_medicao,
                            tem_ins, tem_min, tem_max, tem_sen,
                            umd_ins, umd_min, umd_max,
                            pre_ins, pre_min, pre_max,
                            pto_ins, pto_min, pto_max,
                            ven_vel, ven_dir, ven_raj,
                            chuva, rad_glo
                        ) VALUES (
                            %(cd_estacao)s, %(dt_medicao)s, %(hr_medicao)s,
                            %(tem_ins)s, %(tem_min)s, %(tem_max)s, %(tem_sen)s,
                            %(umd_ins)s, %(umd_min)s, %(umd_max)s,
                            %(pre_ins)s, %(pre_min)s, %(pre_max)s,
                            %(pto_ins)s, %(pto_min)s, %(pto_max)s,
                            %(ven_vel)s, %(ven_dir)s, %(ven_raj)s,
                            %(chuva)s, %(rad_glo)s
                        )
                    """, record)
                    
                    synced += 1
                    
                    # Commit a cada 100 registros em modo full
                    if full and total % 100 == 0:
                        self.conn.commit()
                        print(f"  Progresso: {total} processados, {synced} novos, {skipped} já existentes")
                        
                except self.mysql.Error as e:
                    print(f"  ⚠ Erro ao inserir registro: {e}")
                    continue
            
            self.conn.commit()
            mysql_cursor.close()
            
            if full and skipped > 0:
                print(f"  Final: {synced} inseridos, {skipped} já existiam")
            
            return synced
            
        except Exception as e:
            print(f"⚠ Erro na sincronização MySQL: {e}")
            import traceback
            traceback.print_exc()
            return 0
    
    def close(self):
        if self.conn:
            self.conn.close()


# ============================================================================
# MÓDULO: COLETOR DE DADOS DA API
# ============================================================================

class APICollector:
    """Coleta dados da API INMET."""
    
    def __init__(self, url: str, max_retries: int, delays: list):
        self.url = url
        self.max_retries = max_retries
        self.delays = delays
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': Config.USER_AGENT})
    
    def fetch(self) -> Optional[Dict[str, Any]]:
        """Busca dados com retry logic."""
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(self.url, timeout=10)
                data = response.json()
                
                if self._validate(data):
                    return data['dados']
                
                print(f"✗ JSON inválido (tentativa {attempt + 1}/{self.max_retries})")
                
            except requests.exceptions.Timeout:
                print(f"✗ Timeout (tentativa {attempt + 1}/{self.max_retries})")
            except requests.exceptions.RequestException as e:
                print(f"✗ Erro: {e} (tentativa {attempt + 1}/{self.max_retries})")
            except json.JSONDecodeError:
                print(f"✗ Resposta não é JSON (tentativa {attempt + 1}/{self.max_retries})")
            except Exception as e:
                print(f"✗ Erro inesperado: {e}")
            
            # Aguardar antes de tentar novamente
            if attempt < len(self.delays):
                delay = self.delays[attempt]
                print(f"  Aguardando {delay}s...")
                time.sleep(delay)
        
        return None
    
    def _validate(self, data: Dict) -> bool:
        """Valida estrutura e campos obrigatórios."""
        if not isinstance(data, dict) or 'dados' not in data:
            return False
        
        dados = data['dados']
        required = ['DT_MEDICAO', 'HR_MEDICAO', 'TEM_INS', 'UMD_INS', 'PRE_INS']
        
        return all(field in dados and dados[field] is not None for field in required)


# ============================================================================
# ORQUESTRADOR PRINCIPAL
# ============================================================================

class Orchestrator:
    """Orquestrador principal do sistema."""
    
    def __init__(self):
        self.sqlite = SQLiteManager(str(Config.DB_PATH))
        self.mysql = MySQLManager()
        self.collector = APICollector(Config.API_URL, Config.MAX_RETRIES, Config.RETRY_DELAYS)
    
    def run(self):
        """Execução principal."""
        print("=" * 70)
        print(f"ORQUESTRADOR - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        print()
        
        # 1. Conectar SQLite
        print("📀 Conectando SQLite...")
        if not self.sqlite.connect():
            print("✗ FALHA CRÍTICA: SQLite não disponível")
            sys.exit(1)
        print(f"✓ SQLite: {Config.DB_PATH}")
        print()
        
        # 2. Coletar dados da API
        print("🌐 Coletando dados da API INMET...")
        dados = self.collector.fetch()
        
        if dados is None:
            print("✗ Não foi possível obter dados da API")
            self.sqlite.close()
            sys.exit(1)
        
        print(f"✓ Dados obtidos: {dados['DT_MEDICAO']} {dados['HR_MEDICAO']}")
        print()
        
        # 3. Salvar no SQLite
        print("💾 Salvando no SQLite...")
        if self.sqlite.insert(dados):
            print(f"✓ Registro inserido")
        else:
            print(f"⊘ Registro não inserido (duplicata ou erro)")
        
        sqlite_count = self.sqlite.count()
        print(f"📊 Total SQLite: {sqlite_count:,} registros")
        print()
        
        # 4. Limpeza de dados antigos (às 3h da manhã)
        if datetime.now().hour == 3:
            print("🧹 Limpando dados antigos...")
            self.sqlite.cleanup_old_data()
            print()
        
        # 5. Sincronizar com MySQL
        print("☁️  Sincronizando com MySQL...")
        if not self.mysql.connect():
            print("⚠ MySQL não disponível, dados seguros no SQLite")
            self.sqlite.close()
            return
        
        mysql_count = self.mysql.count()
        print(f"📊 Total MySQL: {mysql_count:,} registros")
        
        # Verificar se precisa sincronização completa
        diff = sqlite_count - mysql_count
        
        if diff > 0:
            print(f"⚠ MySQL desatualizado ({diff:,} registros faltando)")
            print("🔄 Sincronização COMPLETA automática...")
            synced = self.mysql.sync_from_sqlite(self.sqlite, full=True)
            print(f"✓ {synced:,} registros sincronizados")
        else:
            print("✓ MySQL sincronizado")
            print("🔄 Sincronizando último registro...")
            synced = self.mysql.sync_from_sqlite(self.sqlite, full=False)
            if synced > 0:
                print(f"✓ Último registro sincronizado")
            else:
                print(f"⊘ Nenhum registro novo")
        
        print()
        print("=" * 70)
        print("✓ EXECUÇÃO CONCLUÍDA")
        print("=" * 70)
        
        # Fechar conexões
        self.sqlite.close()
        self.mysql.close()


# ============================================================================
# PONTO DE ENTRADA
# ============================================================================

def main():
    """Ponto de entrada principal."""
    try:
        orchestrator = Orchestrator()
        orchestrator.run()
    except KeyboardInterrupt:
        print("\n⚠ Interrompido pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ ERRO FATAL: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()