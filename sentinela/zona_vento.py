#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
zona_vento.py - Gerenciador de zona de vento
Sistema Sentinela v2.0

RESPONSABILIDADE:
- Classificar vento em zonas (Escala Beaufort)
- Detectar mudanças de zona
- Gerar alertas inteligentes
- Verificar alertas críticos
"""

from datetime import datetime


# Constantes da Escala Beaufort (do config.py)
VENTO_CALMO = 0.3
VENTO_ARAGEM = 1.5
VENTO_BRISA_LEVE = 3.3
VENTO_BRISA_MODERADA = 5.4
VENTO_BRISA_FRESCA = 7.9
VENTO_MODERADO = 10.7
VENTO_FORTE = 13.8


class ZonaVento:
    """
    Gerenciador de zona de vento (Escala Beaufort)
    """
    
    @staticmethod
    def classificar(velocidade):
        """
        Classifica vento pela Escala Beaufort
        
        Args:
            velocidade (float): Velocidade em m/s
            
        Returns:
            str: Nome da zona Beaufort
        """
        if velocidade < VENTO_CALMO:
            return "CALMO"
        elif velocidade < VENTO_ARAGEM:
            return "ARAGEM"
        elif velocidade < VENTO_BRISA_LEVE:
            return "BRISA_LEVE"
        elif velocidade < VENTO_BRISA_MODERADA:
            return "BRISA_MODERADA"
        elif velocidade < VENTO_BRISA_FRESCA:
            return "BRISA_FRESCA"
        elif velocidade < VENTO_MODERADO:
            return "MODERADO"
        elif velocidade < VENTO_FORTE:
            return "FORTE"
        else:
            return "VENTANIA"
    
    @staticmethod
    def detectar_mudanca(vento_atual, estado_anterior):
        """
        Detecta mudança de zona de vento
        
        Args:
            vento_atual (float): Velocidade atual do vento
            estado_anterior (dict): Estado anterior
            
        Returns:
            dict ou None: Dados da mudança
        """
        zona_atual = ZonaVento.classificar(vento_atual)
        zona_anterior = estado_anterior.get('zona')
        valor_anterior = estado_anterior.get('valor')
        
        # Primeira execução
        if zona_anterior is None:
            return {
                'tipo': 'primeira_leitura',
                'zona_atual': zona_atual,
                'valor_atual': vento_atual
            }
        
        # Houve mudança de zona?
        if zona_atual != zona_anterior:
            return {
                'tipo': 'mudanca_zona',
                'zona_anterior': zona_anterior,
                'zona_atual': zona_atual,
                'valor_anterior': valor_anterior,
                'valor_atual': vento_atual,
                'timestamp': datetime.now().strftime('%d/%m/%Y %H:%M')
            }
        
        return None
    
    @staticmethod
    def gerar_alerta_inteligente(mudanca, rajada=None):
        """
        Gera mensagem de alerta inteligente
        
        Args:
            mudanca (dict): Dados da mudança
            rajada (float): Velocidade da rajada (opcional)
            
        Returns:
            str ou None: Mensagem formatada
        """
        if mudanca['tipo'] == 'primeira_leitura':
            return None
        
        zona_ant = mudanca['zona_anterior']
        zona_atual = mudanca['zona_atual']
        vento_ant = mudanca['valor_anterior']
        vento_atual = mudanca['valor_atual']
        timestamp = mudanca['timestamp']
        
        # Emojis por zona
        emojis = {
            'CALMO': '😴',
            'ARAGEM': '🍃',
            'BRISA_LEVE': '🌿',
            'BRISA_MODERADA': '💨',
            'BRISA_FRESCA': '🌬️',
            'MODERADO': '💨💨',
            'FORTE': '🌪️',
            'VENTANIA': '🌀'
        }
        
        # Descrições
        descricoes = {
            'CALMO': 'Calmo',
            'ARAGEM': 'Aragem (suave)',
            'BRISA_LEVE': 'Brisa Leve',
            'BRISA_MODERADA': 'Brisa Moderada',
            'BRISA_FRESCA': 'Brisa Fresca',
            'MODERADO': 'Vento Moderado',
            'FORTE': 'Vento Forte',
            'VENTANIA': 'Ventania'
        }
        
        # Linha adicional de rajada
        linha_rajada = ""
        if rajada and rajada > vento_atual:
            linha_rajada = f"\nRajadas: {rajada:.1f} m/s ({rajada * 3.6:.0f} km/h)"
        
        # Dicas contextuais
        dica = ZonaVento._gerar_dica(zona_anterior=zona_ant, zona_atual=zona_atual)
        
        msg = f"""💨 MUDANÇA DE VENTO
Uberlândia • {timestamp}

Vento: {vento_atual:.1f} m/s
Zona: {zona_ant} → {zona_atual} {emojis[zona_atual]}

Era: {vento_ant:.1f} m/s ({descricoes[zona_ant]})
Agora: {vento_atual:.1f} m/s ({descricoes[zona_atual]}){linha_rajada}{dica}"""
        
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
        # Ventania perigosa
        if zona_atual == 'VENTANIA':
            return "\n\n💡 Vento muito forte! ⚠️\nGalhos podem quebrar\nEvite áreas abertas\nRecolha objetos soltos"
        
        # Vento forte
        elif zona_atual == 'FORTE':
            return "\n\n💡 Vento perigoso\n⚠️ Galhos podem quebrar\nEvite áreas abertas\nRecolha objetos do quintal"
        
        # Vento moderado
        elif zona_atual == 'MODERADO':
            return "\n\n💡 Vento intensificando\nÁrvores pequenas balançam\nCuidado com objetos soltos"
        
        # Brisa fresca
        elif zona_atual == 'BRISA_FRESCA':
            return "\n\n💡 Vento aumentando\nGalhos balançando\nObjetos leves podem voar"
        
        # Brisas leves
        elif zona_atual in ['BRISA_LEVE', 'BRISA_MODERADA']:
            return "\n\n💡 Vento aumentando\nSensação térmica mais fresca\nVentilação natural boa"
        
        # Calmaria
        elif zona_atual in ['CALMO', 'ARAGEM']:
            if zona_anterior in ['FORTE', 'VENTANIA', 'MODERADO']:
                return "\n\n💡 Vento diminuindo\nCondições normalizando"
            else:
                return "\n\n💡 Vento calmo\nCondições tranquilas"
        
        return ""
    
    @staticmethod
    def verificar_critico(vento_atual, rajada_atual):
        """
        Verifica alertas críticos de vento
        
        Args:
            vento_atual (float): Velocidade sustentada
            rajada_atual (float): Velocidade da rajada
            
        Returns:
            list ou None: Lista de alertas críticos
        """
        alertas = []
        
        # CRÍTICO: Rajadas fortes (>15 m/s = 54 km/h)
        LIMITE_RAJADA_CRITICA = 15.0  # m/s
        
        if rajada_atual and rajada_atual > LIMITE_RAJADA_CRITICA:
            alertas.append({
                'tipo': 'vento_forte',
                'vento_sustentado': vento_atual,
                'rajada': rajada_atual,
                'beaufort': ZonaVento.classificar(rajada_atual)
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
        
        if tipo == 'vento_forte':
            vento = alerta_data['vento_sustentado']
            rajada = alerta_data['rajada']
            beaufort = alerta_data['beaufort']
            
            msg = f"""🌀🌀 ALERTA VENTO 🌀🌀
Uberlândia • {timestamp}

💨 Rajadas: {rajada:.1f} m/s ({rajada * 3.6:.0f} km/h)
   {beaufort.upper()} ⚠️

💨 Sustentado: {vento:.1f} m/s ({vento * 3.6:.0f} km/h)
   Beaufort: {ZonaVento.classificar(vento)}

🚨 RISCO DE DANOS

⚠️ Queda de árvores/galhos
⚠️ Objetos soltos voando
⚠️ Estruturas precárias

❌ Evite áreas abertas
❌ Não fique sob árvores
❌ Cuidado com placas/toldos

✅ Recolha objetos do quintal
✅ Feche portas e janelas

Duração prevista: 2-3h"""
            return msg
        
        return None
