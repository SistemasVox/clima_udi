#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
zona_radiacao.py - Gerenciador de zona de radiação solar
Sistema Sentinela v2.0

RESPONSABILIDADE:
- Classificar radiação em zonas UV
- Detectar mudanças de zona
- Gerar alertas inteligentes
- Verificar alertas críticos
- Detectar transições dia/noite (relatórios)
"""

from config import Config
from datetime import datetime


class ZonaRadiacao:
    """
    Gerenciador de zona de radiação solar (UV)
    """
    
    @staticmethod
    def classificar(radiacao):
        """
        Classifica radiação solar em zonas UV
        Trata valores negativos da API
        
        Args:
            radiacao (float): Radiação em kJ/m²
            
        Returns:
            str: Nome da zona
        """
        # Trata valores negativos retornados pela API
        if radiacao <= 0:
            return "NOITE"
        elif radiacao < 50:
            return "CREPUSCULO"
        elif radiacao < Config.RAD_LIMITS["BAIXA"]:
            return "BAIXA"
        elif radiacao < Config.RAD_LIMITS["MODERADA"]:
            return "MODERADA"
        elif radiacao < Config.RAD_LIMITS["ALTA"]:
            return "ALTA"
        elif radiacao < Config.RAD_LIMITS["MUITO ALTA"]:
            return "MUITO_ALTA"
        else:
            return "EXTREMA"
    
    @staticmethod
    def estimar_uv(radiacao):
        """
        Estima índice UV aproximado
        
        Args:
            radiacao (float): Radiação em kJ/m²
            
        Returns:
            int: Índice UV estimado
        """
        if radiacao <= 0:
            return 0
        # Conversão aproximada: 1 kJ/m² ≈ 0.0035 de Índice UV
        return int(radiacao * 0.0035)
    
    @staticmethod
    def detectar_mudanca(rad_atual, estado_anterior):
        """
        Detecta mudança de zona de radiação
        
        Args:
            rad_atual (float): Radiação atual
            estado_anterior (dict): Estado anterior
            
        Returns:
            dict ou None: Dados da mudança
        """
        zona_atual = ZonaRadiacao.classificar(rad_atual)
        zona_anterior = estado_anterior.get('zona')
        valor_anterior = estado_anterior.get('valor')
        
        # Primeira execução
        if zona_anterior is None:
            return {
                'tipo': 'primeira_leitura',
                'zona_atual': zona_atual,
                'valor_atual': rad_atual
            }
        
        # Houve mudança de zona?
        if zona_atual != zona_anterior:
            return {
                'tipo': 'mudanca_zona',
                'zona_anterior': zona_anterior,
                'zona_atual': zona_atual,
                'valor_anterior': valor_anterior,
                'valor_atual': rad_atual,
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
        rad_ant = mudanca['valor_anterior']
        rad_atual = mudanca['valor_atual']
        timestamp = mudanca['timestamp']
        
        # Emojis por zona
        emojis = {
            'NOITE': '🌙',
            'CREPUSCULO': '🌅',
            'BAIXA': '☁️',
            'MODERADA': '🌤️',
            'ALTA': '☀️',
            'MUITO_ALTA': '🔆',
            'EXTREMA': '☢️'
        }
        
        # Descrições com UV
        uv_ant = ZonaRadiacao.estimar_uv(rad_ant)
        uv_atual = ZonaRadiacao.estimar_uv(rad_atual)
        
        descricoes = {
            'NOITE': 'Noite',
            'CREPUSCULO': f'Crepúsculo',
            'BAIXA': f'Baixa (UV {uv_ant})',
            'MODERADA': f'Moderada (UV {uv_ant})',
            'ALTA': f'Alta (UV {uv_ant})',
            'MUITO_ALTA': f'Muito Alta (UV {uv_ant})',
            'EXTREMA': f'Extrema (UV {uv_ant}+)'
        }
        
        desc_atual = {
            'NOITE': 'Noite',
            'CREPUSCULO': f'Crepúsculo',
            'BAIXA': f'Baixa (UV {uv_atual})',
            'MODERADA': f'Moderada (UV {uv_atual})',
            'ALTA': f'Alta (UV {uv_atual})',
            'MUITO_ALTA': f'Muito Alta (UV {uv_atual})',
            'EXTREMA': f'Extrema (UV {uv_atual}+)'
        }
        
        # Dicas contextuais
        dica = ZonaRadiacao._gerar_dica(zona_anterior=zona_ant, zona_atual=zona_atual)
        
        msg = f"""☀️ MUDANÇA DE RADIAÇÃO
Uberlândia • {timestamp}

Radiação: {rad_atual:.0f} kJ/m²
Zona: {zona_ant} → {zona_atual} {emojis[zona_atual]}

Era: {rad_ant:.0f} kJ/m² ({descricoes[zona_ant]})
Agora: {rad_atual:.0f} kJ/m² ({desc_atual[zona_atual]}){dica}"""
        
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
        # UV Extremo - perigo máximo
        if zona_atual == 'EXTREMA':
            return "\n\n💡 UV EXTREMO - PERIGO!\n❌ NÃO fique ao sol agora\nQueimaduras em minutos\nBusque sombra imediatamente"
        
        # UV Muito Alto
        elif zona_atual == 'MUITO_ALTA':
            return "\n\n💡 UV em nível perigoso\nFPS 50+ obrigatório\nEvite sol 11h-15h\nReaplique protetor a cada 2h"
        
        # UV Alto
        elif zona_atual == 'ALTA':
            return "\n\n💡 UV aumentando\nUse FPS 30+ agora\nEvite exposição prolongada"
        
        # UV Moderado
        elif zona_atual == 'MODERADA':
            return "\n\n💡 UV moderado\nProteção recomendada\nFPS 30+ em exposição prolongada"
        
        # UV Baixo
        elif zona_atual == 'BAIXA':
            if zona_anterior in ['ALTA', 'MUITO_ALTA', 'EXTREMA']:
                return "\n\n💡 UV diminuindo\nRadiação mais segura\nMelhor hora para atividades"
            else:
                return "\n\n💡 UV baixo\nRadiação segura\nProteção básica suficiente"
        
        # Crepúsculo
        elif zona_atual == 'CREPUSCULO':
            if zona_anterior == 'BAIXA':
                return "\n\n💡 Sol se pondo\nRadiação segura agora\nBoa hora para atividades externas"
            else:
                return "\n\n💡 Amanhecendo\nRadiação ainda baixa"
        
        # Noite
        elif zona_atual == 'NOITE':
            return "\n\n💡 Anoiteceu\nSem radiação solar"
        
        return ""
    
    @staticmethod
    def verificar_critico(rad_atual):
        """
        Verifica alertas críticos de radiação
        
        Args:
            rad_atual (float): Radiação atual
            
        Returns:
            list ou None: Lista de alertas críticos
        """
        alertas = []
        
        # CRÍTICO: UV Extremo (>3000 kJ/m²)
        if rad_atual >= Config.RAD_LIMITS["EXTREMA"]:
            alertas.append({
                'tipo': 'uv_extremo',
                'radiacao': rad_atual,
                'uv_index': ZonaRadiacao.estimar_uv(rad_atual)
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
        
        if tipo == 'uv_extremo':
            rad = alerta_data['radiacao']
            uv = alerta_data['uv_index']
            
            # Busca horário do pico de radiação HOJE (dados reais)
            linha_pico = "Pico UV: 12h-14h (PERIGO MÁXIMO)"  # Fallback
            try:
                from database import WeatherDatabase
                db = WeatherDatabase()
                db.connect()
                
                cursor = db.connection.cursor()
                query = """
                SELECT 
                    MAX(rad_glo) as rad_max,
                    hr_medicao
                FROM medicoes
                WHERE DATE(dt_medicao) = CURDATE()
                ORDER BY rad_glo DESC
                LIMIT 1
                """
                cursor.execute(query)
                resultado = cursor.fetchone()
                db.close()
                
                if resultado and resultado['hr_medicao']:
                    # Converte HHMM para formato legível
                    hora_num = int(resultado['hr_medicao'])
                    hora_inicio = hora_num // 100
                    hora_fim = hora_inicio + 2
                    linha_pico = f"Pico UV: {hora_inicio}h-{hora_fim}h (PERIGO MÁXIMO)"
            except Exception as e:
                pass  # Usa fallback
            
            msg = f"""☀️☀️ ALERTA UV ☀️☀️
Uberlândia • {timestamp}

☀️ Radiação: {rad:.0f} kJ/m²
   EXTREMA ☢️ (UV {uv}+)

🚨 RISCO SEVERO À PELE

⚠️ Queimaduras em minutos
⚠️ Dano celular acelerado
⚠️ Risco de câncer de pele

❌ Evite exposição 10h-16h
❌ Não fique ao sol sem proteção

✅ FPS 50+ obrigatório
✅ Reaplique a cada 2h
✅ Use chapéu e óculos
✅ Procure sombra

{linha_pico}"""
            return msg
        
        return None
    
    @staticmethod
    def detectar_transicao(rad_atual, rad_anterior):
        """
        Detecta transições dia/noite para relatórios
        IMPORTANTE: Trata radiação negativa da API como noite (rad <= 0)
        
        Args:
            rad_atual (float): Radiação atual
            rad_anterior (float): Radiação anterior
            
        Returns:
            str ou None: 'bom_dia', 'boa_noite' ou None
        """
        if rad_anterior is None:
            return None
        
        # Transição noite→dia (rad <= 0 → rad > 0)
        # IMPORTANTE: Radiação negativa da API é tratada como noite
        if rad_anterior <= 0 and rad_atual > 0:
            return 'bom_dia'
        
        # Transição dia→noite (rad > 0 → rad <= 0)
        elif rad_anterior > 0 and rad_atual <= 0:
            return 'boa_noite'
        
        return None