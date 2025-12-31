#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
zona_chuva.py - Gerenciador de zona de chuva
Sistema Sentinela v2.0

RESPONSABILIDADE:
- Classificar chuva em zonas de intensidade
- Detectar mudanças de zona
- Gerar alertas inteligentes
- Verificar alertas críticos
"""

from config import Config
from datetime import datetime


class ZonaChuva:
    """
    Gerenciador de zona de intensidade de chuva
    """
    
    @staticmethod
    def classificar(chuva_mm):
        """
        Classifica intensidade da chuva
        
        Args:
            chuva_mm (float): Precipitação em mm/h
            
        Returns:
            str: Nome da zona
        """
        if chuva_mm == 0:
            return "SEM_CHUVA"
        elif chuva_mm < Config.CHUVA_LIMITS["GAROA"]:
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
    def detectar_mudanca(chuva_atual, estado_anterior):
        """
        Detecta mudança de zona de chuva
        
        Args:
            chuva_atual (float): Intensidade atual
            estado_anterior (dict): Estado anterior
            
        Returns:
            dict ou None: Dados da mudança
        """
        zona_atual = ZonaChuva.classificar(chuva_atual)
        zona_anterior = estado_anterior.get('zona')
        valor_anterior = estado_anterior.get('valor')
        
        # Primeira execução
        if zona_anterior is None:
            return {
                'tipo': 'primeira_leitura',
                'zona_atual': zona_atual,
                'valor_atual': chuva_atual
            }
        
        # Houve mudança de zona?
        if zona_atual != zona_anterior:
            return {
                'tipo': 'mudanca_zona',
                'zona_anterior': zona_anterior,
                'zona_atual': zona_atual,
                'valor_anterior': valor_anterior,
                'valor_atual': chuva_atual,
                'timestamp': datetime.now().strftime('%d/%m/%Y %H:%M')
            }
        
        return None
    
    @staticmethod
    def gerar_alerta_inteligente(mudanca):
        """
        Gera mensagem de alerta inteligente
        
        Args:
            mudanca (dict): Dados da mudança
            
        Returns:
            str ou None: Mensagem formatada
        """
        if mudanca['tipo'] == 'primeira_leitura':
            return None
        
        zona_ant = mudanca['zona_anterior']
        zona_atual = mudanca['zona_atual']
        chuva_ant = mudanca['valor_anterior']
        chuva_atual = mudanca['valor_atual']
        timestamp = mudanca['timestamp']
        
        # Emojis por zona
        emojis = {
            'SEM_CHUVA': '☀️',
            'GAROA': '🌦️',
            'FRACA': '🌧️',
            'MODERADA': '🌧️🌧️',
            'FORTE': '⛈️',
            'MUITO_FORTE': '🌊'
        }
        
        # Descrições
        descricoes = {
            'SEM_CHUVA': 'Sem chuva',
            'GAROA': 'Garoa (leve)',
            'FRACA': 'Fraca',
            'MODERADA': 'Moderada',
            'FORTE': 'Forte (torrencial)',
            'MUITO_FORTE': 'Muito Forte (dilúvio)'
        }
        
        # Dicas contextuais
        dica = ZonaChuva._gerar_dica(zona_anterior=zona_ant, zona_atual=zona_atual)
        
        msg = f"""🌧️ MUDANÇA DE CHUVA
Uberlândia • {timestamp}

Chuva: {chuva_atual:.1f} mm/h
Zona: {zona_ant} → {zona_atual} {emojis[zona_atual]}

Era: {chuva_ant:.1f} mm/h ({descricoes[zona_ant]})
Agora: {chuva_atual:.1f} mm/h ({descricoes[zona_atual]}){dica}"""
        
        return msg
    
    @staticmethod
    def _gerar_dica(zona_anterior, zona_atual):
        """
        Gera dica contextual baseada na transição
        
        Args:
            zona_anterior (str): Zona anterior
            zona_atual (str): Zona atual
            
        Returns:
            str: Dica formatada
        """
        # Chuva muito forte - perigo
        if zona_atual == 'MUITO_FORTE':
            return "\n\n💡 CHUVA TORRENCIAL!\n🚨 Alagamentos rápidos\nNÃO saia de casa\nEmergência: 193/199"
        
        # Chuva forte
        elif zona_atual == 'FORTE':
            return "\n\n💡 Chuva forte!\n⚠️ Risco de alagamentos\nNÃO atravesse água acumulada\nEvite deslocamentos"
        
        # Chuva moderada
        elif zona_atual == 'MODERADA':
            return "\n\n💡 Chuva aumentando\nPoças se formando\nEvite áreas baixas\nAtenção ao dirigir"
        
        # Chuva fraca
        elif zona_atual == 'FRACA':
            return "\n\n💡 Chuva intensificando\nVisibilidade reduzindo\nDirija com cuidado"
        
        # Garoa
        elif zona_atual == 'GAROA':
            if zona_anterior == 'SEM_CHUVA':
                return "\n\n💡 Começou a chover\nChuva fraca/garoa\nGuarda-chuva recomendado"
            else:
                return "\n\n💡 Chuva diminuindo\nApenas garoa agora"
        
        # Parou de chover
        elif zona_atual == 'SEM_CHUVA':
            if zona_anterior in ['FORTE', 'MUITO_FORTE', 'MODERADA']:
                return "\n\n💡 Chuva parou\nCuidado com poças e alagamentos\nEstradas podem estar escorregadias"
            else:
                return "\n\n💡 Chuva cessou\nCondições normalizando"
        
        return ""
    
    @staticmethod
    def verificar_critico(chuva_atual, acumulado_24h):
        """
        Verifica alertas críticos de chuva
        
        Args:
            chuva_atual (float): Intensidade atual
            acumulado_24h (float): Acumulado em 24h
            
        Returns:
            list ou None: Lista de alertas críticos
        """
        alertas = []
        
        # CRÍTICO 1: Intensidade muito forte (>50 mm/h)
        if chuva_atual >= Config.CHUVA_LIMITS["MUITO_FORTE"]:
            alertas.append({
                'tipo': 'chuva_intensa',
                'intensidade': chuva_atual,
                'acumulado_24h': acumulado_24h
            })
        
        # CRÍTICO 2: Acumulado perigoso (>50 mm em 24h)
        elif acumulado_24h > Config.CHUVA_ACUMULADA_ALERTA:
            alertas.append({
                'tipo': 'chuva_acumulada',
                'intensidade': chuva_atual,
                'acumulado_24h': acumulado_24h
            })
        
        return alertas if alertas else None
    
    @staticmethod
    def gerar_alerta_critico(alerta_data):
        """
        Gera mensagem de alerta crítico
        
        Args:
            alerta_data (dict): Dados do alerta
            
        Returns:
            str: Mensagem formatada
        """
        tipo = alerta_data['tipo']
        timestamp = datetime.now().strftime('%d/%m/%Y %H:%M')
        
        if tipo == 'chuva_intensa':
            intensidade = alerta_data['intensidade']
            acumulado = alerta_data['acumulado_24h']
            
            msg = f"""🌧️🌧️ ALERTA CHUVA 🌧️🌧️
Uberlândia • {timestamp}

🌧️ Intensidade: {intensidade:.1f} mm/h
   MUITO FORTE 🌊

📊 Acumulado:
   1h: {intensidade:.1f} mm
   24h: {acumulado:.1f} mm {'⚠️' if acumulado > 50 else ''}

🚨 RISCO DE ENCHENTE

⚠️ Alagamentos de vias
⚠️ Transbordamento de córregos
⚠️ Deslizamentos (áreas risco)

❌ NÃO atravesse alagamentos
❌ NÃO dirija em vias alagadas
❌ Evite áreas baixas

✅ Procure local elevado
✅ Mantenha-se informado

Emergência: 193 / 199"""
            return msg
        
        elif tipo == 'chuva_acumulada':
            intensidade = alerta_data['intensidade']
            acumulado = alerta_data['acumulado_24h']
            
            msg = f"""🌧️🌧️ ALERTA CHUVA 🌧️🌧️
Uberlândia • {timestamp}

📊 Acumulado 24h: {acumulado:.1f} mm ⚠️
   ACIMA DO LIMITE ({Config.CHUVA_ACUMULADA_ALERTA} mm)

🌧️ Intensidade atual: {intensidade:.1f} mm/h

🚨 RISCO DE ALAGAMENTO

⚠️ Solo saturado
⚠️ Risco de enchentes
⚠️ Córregos podem transbordar

❌ Evite áreas de risco
❌ NÃO atravesse água acumulada
❌ Não dirija em vias alagadas

✅ Fique em local seguro
✅ Monitore boletins

Emergência: 193 / 199"""
            return msg
        
        return None
