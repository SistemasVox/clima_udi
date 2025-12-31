#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
zona_temperatura.py - Gerenciador de zona de temperatura
Sistema Sentinela v2.0

RESPONSABILIDADE:
- Classificar temperatura em zonas de conforto
- Detectar mudanças de zona
- Gerar alertas inteligentes
- Verificar alertas críticos
"""

from config import Config
from datetime import datetime


class ZonaTemperatura:
    """
    Gerenciador de zona de conforto térmico
    """
    
    @staticmethod
    def classificar(temperatura):
        """
        Classifica temperatura em zona de conforto
        
        Args:
            temperatura (float): Temperatura em °C
            
        Returns:
            str: Nome da zona (FRIO, FRESCO, IDEAL, MORNO, QUENTE, MUITO_QUENTE, EXTREMO)
        """
        if temperatura < Config.CONFORTO_FRIO:
            return "FRIO"
        elif temperatura < Config.CONFORTO_FRESCO:
            return "FRESCO"
        elif temperatura < Config.CONFORTO_IDEAL:
            return "IDEAL"
        elif temperatura < Config.CONFORTO_MORNO:
            return "MORNO"
        elif temperatura < Config.CONFORTO_QUENTE:
            return "QUENTE"
        elif temperatura < Config.CONFORTO_MUITO_QUENTE:
            return "MUITO_QUENTE"
        else:
            return "EXTREMO"
    
    @staticmethod
    def detectar_mudanca(temp_atual, estado_anterior):
        """
        Detecta se houve mudança de zona de conforto
        
        Args:
            temp_atual (float): Temperatura atual
            estado_anterior (dict): Estado anterior da zona
            
        Returns:
            dict ou None: Dados da mudança ou None se não houver mudança
        """
        zona_atual = ZonaTemperatura.classificar(temp_atual)
        zona_anterior = estado_anterior.get('zona')
        valor_anterior = estado_anterior.get('valor')
        
        # Primeira execução (sem estado anterior)
        if zona_anterior is None:
            return {
                'tipo': 'primeira_leitura',
                'zona_atual': zona_atual,
                'valor_atual': temp_atual
            }
        
        # Houve mudança de zona?
        if zona_atual != zona_anterior:
            return {
                'tipo': 'mudanca_zona',
                'zona_anterior': zona_anterior,
                'zona_atual': zona_atual,
                'valor_anterior': valor_anterior,
                'valor_atual': temp_atual,
                'timestamp': datetime.now().strftime('%d/%m/%Y %H:%M')
            }
        
        return None
    
    @staticmethod
    def gerar_alerta_inteligente(mudanca):
        """
        Gera mensagem de alerta inteligente para mudança de zona
        
        Args:
            mudanca (dict): Dados da mudança detectada
            
        Returns:
            str ou None: Mensagem formatada ou None
        """
        if mudanca['tipo'] == 'primeira_leitura':
            return None  # Não envia na primeira vez
        
        zona_ant = mudanca['zona_anterior']
        zona_atual = mudanca['zona_atual']
        temp_ant = mudanca['valor_anterior']
        temp_atual = mudanca['valor_atual']
        timestamp = mudanca['timestamp']
        
        # Emojis por zona
        emojis = {
            'FRIO': '🥶',
            'FRESCO': '🌡️',
            'IDEAL': '✅',
            'MORNO': '🌤️',
            'QUENTE': '🔥',
            'MUITO_QUENTE': '🥵',
            'EXTREMO': '🔴'
        }
        
        # Descrições
        descricoes = {
            'FRIO': 'Frio (precisa agasalho)',
            'FRESCO': 'Fresco (ótima troca de calor)',
            'IDEAL': 'Confortável (perfeito)',
            'MORNO': 'Morno (começando esquentar)',
            'QUENTE': 'Quente (desconfortável)',
            'MUITO_QUENTE': 'Muito quente (suor, fadiga)',
            'EXTREMO': 'Calor extremo (risco à saúde)'
        }
        
        # Dicas contextuais por transição
        dica = ZonaTemperatura._gerar_dica(zona_anterior=zona_ant, zona_atual=zona_atual)
        
        msg = f"""🌡️ MUDANÇA DE CONFORTO
Uberlândia • {timestamp}

Temperatura: {temp_atual:.1f}°C
Conforto: {zona_ant} → {zona_atual} {emojis[zona_atual]}

Era: {temp_ant:.1f}°C ({descricoes[zona_ant]})
Agora: {temp_atual:.1f}°C ({descricoes[zona_atual]}){dica}"""
        
        return msg
    
    @staticmethod
    def _gerar_dica(zona_anterior, zona_atual):
        """
        Gera dica contextual baseada na transição de zona
        
        Args:
            zona_anterior (str): Zona anterior
            zona_atual (str): Zona atual
            
        Returns:
            str: Dica formatada
        """
        # Aquecimento perigoso
        if zona_atual in ['MUITO_QUENTE', 'EXTREMO']:
            return "\n\n💡 Calor aumentando\nUse roupas leves e hidrate-se\nEvite atividades intensas"
        
        # Resfriamento perigoso
        elif zona_atual == 'FRIO':
            return "\n\n💡 Temperatura caindo\nAgasalho pesado recomendado\nAtenção com crianças e idosos"
        
        # Zona confortável
        elif zona_atual in ['FRESCO', 'IDEAL']:
            if zona_anterior in ['QUENTE', 'MUITO_QUENTE', 'EXTREMO']:
                return "\n\n💡 Temperatura aliviando\nAmbiente mais confortável\nBom momento para atividades"
            else:
                return "\n\n💡 Temperatura agradável\nConforto térmico ideal"
        
        # Aquecimento moderado
        elif zona_atual == 'QUENTE':
            return "\n\n💡 Ambiente esquentando\nVentilação recomendada\nHidrate-se regularmente"
        
        # Aquecimento leve
        elif zona_atual == 'MORNO':
            return "\n\n💡 Temperatura subindo\nAmbiente começando a aquecer"
        
        return ""
    
    @staticmethod
    def verificar_critico(temp_atual, leitura_anterior):
        """
        Verifica se há alertas críticos relacionados à temperatura
        
        Args:
            temp_atual (float): Temperatura atual
            leitura_anterior (dict): Leitura anterior do banco
            
        Returns:
            list ou None: Lista de alertas críticos ou None
        """
        alertas = []
        
        # CRÍTICO 1: Calor extremo (>33°C)
        if temp_atual > Config.CONFORTO_MUITO_QUENTE:
            alertas.append({
                'tipo': 'calor_extremo',
                'temperatura': temp_atual,
                'limiar': Config.CONFORTO_MUITO_QUENTE
            })
        
        # CRÍTICO 2: Frio extremo (<16°C - ALERTA_TEMP_BAIXA do config)
        if temp_atual < Config.TEMP_BAIXA:
            alertas.append({
                'tipo': 'frio_extremo',
                'temperatura': temp_atual,
                'limiar': Config.TEMP_BAIXA
            })
        
        # CRÍTICO 3: Mudança brusca (≥5°C em 1h)
        if leitura_anterior:
            temp_anterior = leitura_anterior.get('tem_ins')
            if temp_anterior:
                delta = temp_atual - temp_anterior
                if abs(delta) >= 5.0:
                    alertas.append({
                        'tipo': 'mudanca_brusca',
                        'delta': delta,
                        'temp_anterior': temp_anterior,
                        'temp_atual': temp_atual,
                        'direcao': 'queda' if delta < 0 else 'subida'
                    })
        
        return alertas if alertas else None
    
    @staticmethod
    def gerar_alerta_critico(alerta_data):
        """
        Gera mensagem de alerta crítico
        
        Args:
            alerta_data (dict): Dados do alerta crítico
            
        Returns:
            str: Mensagem formatada
        """
        tipo = alerta_data['tipo']
        timestamp = datetime.now().strftime('%d/%m/%Y %H:%M')
        
        if tipo == 'calor_extremo':
            temp = alerta_data['temperatura']
            msg = f"""🔥🔥 ALERTA CALOR 🔥🔥
Uberlândia • {timestamp}

🌡️ {temp:.1f}°C
   MUITO QUENTE 🥵

🚨 RISCO À SAÚDE

❌ Evite sol 10h-16h
❌ Atividades físicas intensas

✅ Hidrate-se a cada 15min
✅ Use FPS 50+
✅ Procure sombra/ar condicionado

⚠️ Sinais de alerta:
Tontura, náusea, confusão → SAMU 192"""
            return msg
        
        elif tipo == 'frio_extremo':
            temp = alerta_data['temperatura']
            msg = f"""❄️❄️ ALERTA FRIO ❄️❄️
Uberlândia • {timestamp}

🌡️ {temp:.1f}°C
   FRIO 🥶

🚨 TEMPERATURA BAIXA

⚠️ Risco de hipotermia

✅ Agasalhos pesados obrigatórios
✅ Proteja crianças e idosos
✅ Recolha animais de estimação
✅ Atenção com aquecedores

Temperatura crítica abaixo de 16°C"""
            return msg
        
        elif tipo == 'mudanca_brusca':
            delta = alerta_data['delta']
            temp_ant = alerta_data['temp_anterior']
            temp_atual = alerta_data['temp_atual']
            direcao = alerta_data['direcao']
            
            emoji = "❄️❄️" if direcao == 'queda' else "🔥🔥"
            titulo = "QUEDA BRUSCA" if direcao == 'queda' else "SUBIDA BRUSCA"
            
            msg = f"""{emoji} ALERTA MUDANÇA {emoji}
Uberlândia • {timestamp}

🌡️ Temp: {temp_atual:.1f}°C (era {temp_ant:.1f}°C)
   Variação: {delta:+.1f}°C em 1h {'↓↓' if delta < 0 else '↑↑'}

🚨 {titulo} DE TEMPERATURA

⚠️ Mudança atmosférica brusca
⚠️ Tempo instável

✅ Tenha agasalho à mão
✅ Acompanhe previsão
✅ Temperatura pode continuar {"caindo" if direcao == 'queda' else "subindo"}"""
            
            return msg
        
        return None
