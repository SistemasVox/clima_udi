#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
zona_pressao.py - Gerenciador de zona de pressão atmosférica
Sistema Sentinela v2.0

RESPONSABILIDADE:
- Classificar pressão em zonas
- Detectar mudanças de zona
- Gerar alertas inteligentes
- Verificar alertas críticos
"""

from datetime import datetime


class ZonaPressao:
    """
    Gerenciador de zona de pressão atmosférica
    """
    
    @staticmethod
    def classificar(pressao):
        """
        Classifica pressão atmosférica em zonas
        
        Args:
            pressao (float): Pressão em hPa
            
        Returns:
            str: Nome da zona
        """
        if pressao < 1005:
            return "MUITO_BAIXA"
        elif pressao < 1010:
            return "BAIXA"
        elif pressao < 1020:
            return "NORMAL"
        elif pressao < 1025:
            return "ALTA"
        else:
            return "MUITO_ALTA"
    
    @staticmethod
    def detectar_mudanca(pressao_atual, estado_anterior):
        """
        Detecta mudança de zona de pressão
        
        Args:
            pressao_atual (float): Pressão atual
            estado_anterior (dict): Estado anterior
            
        Returns:
            dict ou None: Dados da mudança
        """
        zona_atual = ZonaPressao.classificar(pressao_atual)
        zona_anterior = estado_anterior.get('zona')
        valor_anterior = estado_anterior.get('valor')
        
        # Primeira execução
        if zona_anterior is None:
            return {
                'tipo': 'primeira_leitura',
                'zona_atual': zona_atual,
                'valor_atual': pressao_atual
            }
        
        # Houve mudança de zona?
        if zona_atual != zona_anterior:
            return {
                'tipo': 'mudanca_zona',
                'zona_anterior': zona_anterior,
                'zona_atual': zona_atual,
                'valor_anterior': valor_anterior,
                'valor_atual': pressao_atual,
                'timestamp': datetime.now().strftime('%d/%m/%Y %H:%M')
            }
        
        return None
    
    @staticmethod
    def gerar_alerta_inteligente(mudanca, delta_3h=None):
        """
        Gera mensagem de alerta inteligente
        
        Args:
            mudanca (dict): Dados da mudança
            delta_3h (float): Variação em 3 horas (opcional)
            
        Returns:
            str ou None: Mensagem formatada
        """
        if mudanca['tipo'] == 'primeira_leitura':
            return None
        
        zona_ant = mudanca['zona_anterior']
        zona_atual = mudanca['zona_atual']
        pressao_ant = mudanca['valor_anterior']
        pressao_atual = mudanca['valor_atual']
        timestamp = mudanca['timestamp']
        
        # Emojis por zona
        emojis = {
            'MUITO_BAIXA': '📉📉',
            'BAIXA': '📉',
            'NORMAL': '➡️',
            'ALTA': '📈',
            'MUITO_ALTA': '📈📈'
        }
        
        # Descrições
        descricoes = {
            'MUITO_BAIXA': 'Muito Baixa (tempestade)',
            'BAIXA': 'Baixa (instável)',
            'NORMAL': 'Normal (estável)',
            'ALTA': 'Alta (estável)',
            'MUITO_ALTA': 'Muito Alta (anticiclone)'
        }
        
        # Linha de variação 3h
        linha_variacao = ""
        if delta_3h is not None:
            sinal = "+" if delta_3h > 0 else ""
            linha_variacao = f"\n\nVariação 3h: {sinal}{delta_3h:.1f} hPa"
        
        # Dicas contextuais
        dica = ZonaPressao._gerar_dica(zona_anterior=zona_ant, zona_atual=zona_atual)
        
        msg = f"""📊 MUDANÇA DE PRESSÃO
Uberlândia • {timestamp}

Pressão: {pressao_atual:.1f} hPa
Zona: {zona_ant} → {zona_atual} {emojis[zona_atual]}

Era: {pressao_ant:.1f} hPa ({descricoes[zona_ant]})
Agora: {pressao_atual:.1f} hPa ({descricoes[zona_atual]}){linha_variacao}{dica}"""
        
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
        # Pressão muito baixa - perigo
        if zona_atual == 'MUITO_BAIXA':
            return "\n\n💡 Pressão em colapso\n🚨 Tempestade se aproximando\nCondições se agravando\nFique atento aos alertas"
        
        # Pressão baixa - instável
        elif zona_atual == 'BAIXA':
            if zona_anterior in ['NORMAL', 'ALTA', 'MUITO_ALTA']:
                return "\n\n💡 Pressão caindo\nTempo pode instabilizar\nPossível chuva se aproximando"
            else:
                return "\n\n💡 Pressão baixa\nTempo instável\nChuva provável"
        
        # Pressão alta - estabilizando
        elif zona_atual == 'ALTA':
            if zona_anterior in ['BAIXA', 'MUITO_BAIXA']:
                return "\n\n💡 Pressão subindo\nTempo estabilizando\nPossível frente fria passou\nCéu deve limpar"
            else:
                return "\n\n💡 Pressão alta\nTempo estável\nBoas condições"
        
        # Pressão muito alta
        elif zona_atual == 'MUITO_ALTA':
            return "\n\n💡 Pressão muito alta\nTempo firme e estável\nCéu limpo esperado\nPossível friagem à noite"
        
        # Pressão normal
        elif zona_atual == 'NORMAL':
            if zona_anterior in ['BAIXA', 'MUITO_BAIXA']:
                return "\n\n💡 Pressão normalizando\nTempo melhorando"
            elif zona_anterior in ['ALTA', 'MUITO_ALTA']:
                return "\n\n💡 Pressão caindo\nCondições podem mudar"
            else:
                return "\n\n💡 Pressão estável\nCondições normais"
        
        return ""
    
    @staticmethod
    def verificar_critico(pressao_atual, delta_1h):
        """
        Verifica alertas críticos de pressão
        
        Args:
            pressao_atual (float): Pressão atual
            delta_1h (float): Variação em 1 hora
            
        Returns:
            list ou None: Lista de alertas críticos
        """
        alertas = []
        
        # CRÍTICO 1: Queda brusca (>5 hPa/h) - tempestade
        if delta_1h < -5.0:
            alertas.append({
                'tipo': 'queda_brusca',
                'pressao_atual': pressao_atual,
                'delta': delta_1h
            })
        
        # CRÍTICO 2: Pressão muito baixa (<1005 hPa)
        elif pressao_atual < 1005:
            alertas.append({
                'tipo': 'pressao_muito_baixa',
                'pressao_atual': pressao_atual
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
        
        if tipo == 'queda_brusca':
            pressao = alerta_data['pressao_atual']
            delta = alerta_data['delta']
            
            msg = f"""📉📉 ALERTA PRESSÃO 📉📉
Uberlândia • {timestamp}

📊 Pressão: {pressao:.1f} hPa
   QUEDA BRUSCA ⚠️

Variação: {delta:.1f} hPa/1h ↓↓

🚨 COLAPSO ATMOSFÉRICO

⚠️ Tempestade se formando
⚠️ Condições se agravando
⚠️ Possível chuva intensa

✅ Fique em local seguro
✅ Acompanhe alertas
✅ Prepare-se para chuva

Emergência: 193 / 199"""
            return msg
        
        elif tipo == 'pressao_muito_baixa':
            pressao = alerta_data['pressao_atual']
            
            msg = f"""📉📉 ALERTA PRESSÃO 📉📉
Uberlândia • {timestamp}

📊 Pressão: {pressao:.1f} hPa
   MUITO BAIXA ⚠️

🚨 CONDIÇÕES ADVERSAS

⚠️ Tempestade ativa ou iminente
⚠️ Tempo muito instável
⚠️ Risco de chuva forte

✅ Evite deslocamentos
✅ Mantenha-se informado
✅ Prepare abrigo seguro

Emergência: 193 / 199"""
            return msg
        
        return None
