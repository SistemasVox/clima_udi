#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
state_manager.py - Gerenciador de estados (State Machine)
Sistema Sentinela v2.0

RESPONSABILIDADE:
- Carregar estados anteriores (states.json)
- Salvar estados atuais
- Comparar estado anterior vs estado atual
- NÃO usa cooldown temporal - apenas mudança de zona
"""

import json
import os
from datetime import datetime
from pathlib import Path


class StateManager:
    """
    Gerenciador de estados - Máquina de estados pura
    """
    
    def __init__(self, state_file='states.json'):
        self.state_file = Path(__file__).parent / state_file
        self.backup_file = Path(__file__).parent / 'states_backup.json'
        self.states = self.load()
    
    def load(self):
        """
        Carrega estados do arquivo JSON
        
        Returns:
            dict: Estados carregados ou estados padrão
        """
        if not self.state_file.exists():
            print("📝 Primeira execução - criando states.json")
            return self._create_default_states()
        
        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                states = json.load(f)
                print(f"✅ Estados carregados: {self.state_file}")
                return states
        except Exception as e:
            print(f"⚠️ Erro ao carregar estados: {e}")
            print("📝 Criando estados padrão")
            return self._create_default_states()
    
    def save(self):
        """
        Salva estados no arquivo JSON
        Cria backup antes de salvar
        
        Returns:
            bool: True se salvou com sucesso
        """
        try:
            # Backup do estado anterior
            if self.state_file.exists():
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    backup_data = f.read()
                with open(self.backup_file, 'w', encoding='utf-8') as f:
                    f.write(backup_data)
            
            # Salva novo estado
            self.states['timestamp'] = datetime.now().isoformat()
            
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(self.states, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Estados salvos: {self.state_file}")
            return True
        except Exception as e:
            print(f"❌ Erro ao salvar estados: {e}")
            return False
    
    def _create_default_states(self):
        """
        Cria estrutura padrão de estados (primeira execução)
        
        Returns:
            dict: Estados iniciais vazios
        """
        return {
            "timestamp": datetime.now().isoformat(),
            "versao": "2.0",
            "temperatura": {
                "zona": None,
                "valor": None,
                "ultima_mudanca": None
            },
            "umidade": {
                "zona": None,
                "valor": None,
                "ultima_mudanca": None
            },
            "vento": {
                "zona": None,
                "valor": None,
                "ultima_mudanca": None
            },
            "chuva": {
                "zona": None,
                "valor": None,
                "ultima_mudanca": None
            },
            "radiacao": {
                "zona": None,
                "valor": None,
                "ultima_mudanca": None
            },
            "pressao": {
                "zona": None,
                "valor": None,
                "ultima_mudanca": None
            },
            "alerta_geral": {
                "ultima_temp": None,
                "ultima_umid": None,
                "ultima_pressao": None,
                "ultimo_envio": None
            },
            "relatorios": {
                "ultimo_bom_dia": None,
                "ultimo_boa_noite": None
            }
        }
    
    def get_zone_state(self, zona_nome):
        """
        Retorna estado de uma zona específica
        
        Args:
            zona_nome (str): Nome da zona (temperatura, umidade, etc)
            
        Returns:
            dict: Estado da zona ou dict vazio
        """
        return self.states.get(zona_nome, {
            "zona": None,
            "valor": None,
            "ultima_mudanca": None
        })
    
    def update_zone_state(self, zona_nome, zona_atual, valor_atual):
        """
        Atualiza estado de uma zona após envio bem-sucedido
        
        Args:
            zona_nome (str): Nome da zona
            zona_atual (str): Nova zona
            valor_atual (float): Novo valor
        """
        self.states[zona_nome] = {
            "zona": zona_atual,
            "valor": valor_atual,
            "ultima_mudanca": datetime.now().isoformat()
        }
        print(f"📝 Estado atualizado: {zona_nome} → {zona_atual} ({valor_atual})")
    
    def update_general_alert(self, temp, umid, pressao):
        """
        Atualiza estado do alerta geral
        
        Args:
            temp (float): Temperatura enviada
            umid (float): Umidade enviada
            pressao (float): Pressão enviada
        """
        self.states['alerta_geral'] = {
            "ultima_temp": temp,
            "ultima_umid": umid,
            "ultima_pressao": pressao,
            "ultimo_envio": datetime.now().isoformat()
        }
        print(f"📝 Alerta geral atualizado")
    
    def update_report(self, tipo):
        """
        Atualiza timestamp do último relatório
        
        Args:
            tipo (str): 'bom_dia' ou 'boa_noite'
        """
        if tipo == 'bom_dia':
            self.states['relatorios']['ultimo_bom_dia'] = datetime.now().isoformat()
        elif tipo == 'boa_noite':
            self.states['relatorios']['ultimo_boa_noite'] = datetime.now().isoformat()
        
        print(f"📝 Relatório registrado: {tipo}")
    
    def get_critical_state(self, tipo_critico):
        """
        Retorna estado de um alerta crítico
        
        Args:
            tipo_critico (str): Nome do alerta crítico
            
        Returns:
            bool: True se está ativo
        """
        if 'alertas_criticos' not in self.states:
            self.states['alertas_criticos'] = {}
        
        return self.states['alertas_criticos'].get(tipo_critico, {}).get('ativo', False)
    
    def update_critical_state(self, tipo_critico, ativo):
        """
        Atualiza estado de um alerta crítico
        
        Args:
            tipo_critico (str): Nome do alerta crítico
            ativo (bool): True se o alerta está ativo agora
        """
        if 'alertas_criticos' not in self.states:
            self.states['alertas_criticos'] = {}
        
        self.states['alertas_criticos'][tipo_critico] = {
            'ativo': ativo,
            'ultima_mudanca': datetime.now().isoformat()
        }
        
        status = "ATIVO" if ativo else "INATIVO"
        print(f"📝 Crítico atualizado: {tipo_critico} → {status}")
    
    def should_send_critical(self, tipo_critico, ativo_agora):
        """
        Verifica se deve enviar alerta crítico
        Só envia se o estado mudou (ativo→inativo ou inativo→ativo)
        
        Args:
            tipo_critico (str): Nome do alerta crítico
            ativo_agora (bool): Estado atual
            
        Returns:
            bool: True se deve enviar
        """
        estado_anterior = self.get_critical_state(tipo_critico)
        
        # Se mudou de estado, deve enviar
        if estado_anterior != ativo_agora:
            return True
        
        return False
    
    def should_send_general_alert(self, temp_atual, umid_atual, pressao_atual):
        """
        Verifica se deve enviar alerta geral
        Baseado nos limites de variação do config.py
        
        Args:
            temp_atual (float): Temperatura atual
            umid_atual (float): Umidade atual
            pressao_atual (float): Pressão atual
            
        Returns:
            tuple: (bool, str) - (deve_enviar, motivo)
        """
        from config import Config
        
        estado_geral = self.states.get('alerta_geral', {})
        
        # Primeira execução
        if estado_geral.get('ultima_temp') is None:
            return (True, "Primeira leitura")
        
        # Variação de temperatura
        delta_temp = abs(temp_atual - estado_geral['ultima_temp'])
        if delta_temp >= Config.LIMITE_TEMP:
            return (True, f"Temp: {estado_geral['ultima_temp']:.1f}→{temp_atual:.1f}°C")
        
        # Variação de umidade
        delta_umid = abs(umid_atual - estado_geral['ultima_umid'])
        if delta_umid >= Config.LIMITE_UMIDADE:
            return (True, f"Umid: {estado_geral['ultima_umid']:.0f}→{umid_atual:.0f}%")
        
        # Variação de pressão
        delta_pressao = abs(pressao_atual - estado_geral['ultima_pressao'])
        if delta_pressao >= Config.LIMITE_PRESSAO:
            return (True, f"Pressão: {estado_geral['ultima_pressao']:.1f}→{pressao_atual:.1f} hPa")
        
        # Atualização periódica (6 horas sem envio)
        if estado_geral.get('ultimo_envio'):
            try:
                ultimo = datetime.fromisoformat(estado_geral['ultimo_envio'])
                agora = datetime.now()
                horas = (agora - ultimo).total_seconds() / 3600
                
                if horas >= 6:
                    return (True, f"Atualização periódica ({int(horas)}h)")
            except:
                pass
        
        return (False, "")
    
    def should_send_report(self, tipo, rad_atual, rad_anterior):
        """
        Verifica se deve enviar relatório (Bom Dia / Boa Noite)
        
        Args:
            tipo (str): 'bom_dia' ou 'boa_noite'
            rad_atual (float): Radiação atual
            rad_anterior (float): Radiação da leitura anterior
            
        Returns:
            bool: True se deve enviar
        """
        relatorios = self.states.get('relatorios', {})
        
        if tipo == 'bom_dia':
            # Transição noite→dia (rad <= 0 → rad > 0)
            if rad_anterior is not None and rad_anterior <= 0 and rad_atual > 0:
                # Verifica se já enviou hoje
                ultimo = relatorios.get('ultimo_bom_dia')
                if ultimo:
                    try:
                        ultimo_dt = datetime.fromisoformat(ultimo)
                        if ultimo_dt.date() == datetime.now().date():
                            return False  # Já enviou hoje
                    except:
                        pass
                return True
        
        elif tipo == 'boa_noite':
            # Transição dia→noite (rad > 0 → rad <= 0)
            if rad_anterior is not None and rad_anterior > 0 and rad_atual <= 0:
                # Verifica se já enviou hoje
                ultimo = relatorios.get('ultimo_boa_noite')
                if ultimo:
                    try:
                        ultimo_dt = datetime.fromisoformat(ultimo)
                        if ultimo_dt.date() == datetime.now().date():
                            return False  # Já enviou hoje
                    except:
                        pass
                return True
        
        return False
    
    def reset_all_states(self):
        """
        Reseta todos os estados (usar com cuidado!)
        """
        print("⚠️ RESETANDO TODOS OS ESTADOS")
        self.states = self._create_default_states()
        self.save()
    
    def print_summary(self):
        """
        Imprime resumo dos estados atuais
        """
        print("\n" + "="*50)
        print("📊 RESUMO DOS ESTADOS ATUAIS")
        print("="*50)
        
        for zona in ['temperatura', 'umidade', 'vento', 'chuva', 'radiacao', 'pressao']:
            estado = self.states.get(zona, {})
            zona_nome = estado.get('zona') or 'N/A'
            valor = estado.get('valor')
            
            # Formata valor
            if valor is None:
                valor_str = 'N/A'
            else:
                valor_str = f"{valor:.1f}"
            
            print(f"{zona.title():12} | Zona: {zona_nome:15} | Valor: {valor_str}")
        
        print("="*50 + "\n")
