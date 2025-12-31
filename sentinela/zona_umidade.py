#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
zona_umidade.py - Gerenciador de zona de umidade
Sistema Sentinela v2.0

RESPONSABILIDADE:
- Classificar umidade em zonas
- Detectar mudanças de zona
- Gerar alertas inteligentes
- Verificar alertas críticos
"""

from datetime import datetime


class ZonaUmidade:
    """
    Gerenciador de zona de umidade relativa do ar
    """
    
    @staticmethod
    def classificar(umidade):
        """
        Classifica umidade em zonas
        
        Args:
            umidade (float): Umidade relativa em %
            
        Returns:
            str: Nome da zona
        """
        if umidade < 30:
            return "MUITO_SECA"
        elif umidade < 40:
            return "SECA"
        elif umidade < 50:
            return "BOA"
        elif umidade < 70:
            return "OTIMA"
        elif umidade < 85:
            return "ALTA"
        else:
            return "MUITO_ALTA"
    
    @staticmethod
    def detectar_mudanca(umid_atual, estado_anterior):
        """
        Detecta mudança de zona de umidade
        
        Args:
            umid_atual (float): Umidade atual
            estado_anterior (dict): Estado anterior
            
        Returns:
            dict ou None: Dados da mudança
        """
        zona_atual = ZonaUmidade.classificar(umid_atual)
        zona_anterior = estado_anterior.get('zona')
        valor_anterior = estado_anterior.get('valor')
        
        # Primeira execução
        if zona_anterior is None:
            return {
                'tipo': 'primeira_leitura',
                'zona_atual': zona_atual,
                'valor_atual': umid_atual
            }
        
        # Houve mudança de zona?
        if zona_atual != zona_anterior:
            return {
                'tipo': 'mudanca_zona',
                'zona_anterior': zona_anterior,
                'zona_atual': zona_atual,
                'valor_anterior': valor_anterior,
                'valor_atual': umid_atual,
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
        umid_ant = mudanca['valor_anterior']
        umid_atual = mudanca['valor_atual']
        timestamp = mudanca['timestamp']
        
        # Emojis por zona
        emojis = {
            'MUITO_SECA': '🏜️',
            'SECA': '⚠️',
            'BOA': '👍',
            'OTIMA': '✅',
            'ALTA': '💧',
            'MUITO_ALTA': '💦💦'
        }
        
        # Descrições
        descricoes = {
            'MUITO_SECA': 'Ar muito seco (crítico)',
            'SECA': 'Ar seco',
            'BOA': 'Boa',
            'OTIMA': 'Ótima (confortável)',
            'ALTA': 'Alta (elevada)',
            'MUITO_ALTA': 'Muito alta (saturação)'
        }
        
        # Dicas contextuais
        dica = ZonaUmidade._gerar_dica(zona_anterior=zona_ant, zona_atual=zona_atual)
        
        msg = f"""💧 MUDANÇA DE UMIDADE
Uberlândia • {timestamp}

Umidade: {umid_atual:.0f}%
Zona: {zona_ant} → {zona_atual} {emojis[zona_atual]}

Era: {umid_ant:.0f}% ({descricoes[zona_ant]})
Agora: {umid_atual:.0f}% ({descricoes[zona_atual]}){dica}"""
        
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
        # Ar muito seco - crítico
        if zona_atual == 'MUITO_SECA':
            return "\n\n💡 Ar muito seco - alerta\nAumente ingestão de água\nUmidificador recomendado\nAtenção: vias respiratórias"
        
        # Ar seco
        elif zona_atual == 'SECA':
            return "\n\n💡 Ar ficando seco\nHidrate-se mais\nHidratante na pele recomendado"
        
        # Ar saturado
        elif zona_atual == 'MUITO_ALTA':
            return "\n\n💡 Ar saturado\nSensação de abafamento\nChuva muito provável"
        
        # Alta umidade
        elif zona_atual == 'ALTA':
            return "\n\n💡 Umidade aumentando\nAr mais pesado\nPossível chuva se aproximando"
        
        # Umidade ideal
        elif zona_atual in ['BOA', 'OTIMA']:
            if zona_anterior in ['MUITO_SECA', 'SECA']:
                return "\n\n💡 Umidade melhorando\nConforto respiratório ideal"
            elif zona_anterior in ['ALTA', 'MUITO_ALTA']:
                return "\n\n💡 Umidade normalizando\nAr mais leve e confortável"
            else:
                return "\n\n💡 Umidade ideal\nConforto respiratório"
        
        return ""
    
    @staticmethod
    def verificar_critico(umid_atual):
        """
        Verifica alertas críticos de umidade
        
        Args:
            umid_atual (float): Umidade atual
            
        Returns:
            list ou None: Lista de alertas críticos
        """
        alertas = []
        
        # CRÍTICO: Ar muito seco (<20%)
        if umid_atual < 20:
            alertas.append({
                'tipo': 'ar_muito_seco',
                'umidade': umid_atual
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
        
        if tipo == 'ar_muito_seco':
            umid = alerta_data['umidade']
            msg = f"""🏜️🏜️ ALERTA AR SECO 🏜️🏜️
Uberlândia • {timestamp}

💧 Umidade: {umid:.0f}%
   AR MUITO SECO ⚠️

🚨 NÍVEL CRÍTICO

⚠️ Risco respiratório elevado
⚠️ Ressecamento de mucosas
⚠️ Possível sangramento nasal

✅ Aumente ingestão de água
✅ Use umidificador
✅ Hidratante nasal
✅ Evite exercícios intensos

Umidade crítica abaixo de 20%"""
            return msg
        
        return None
