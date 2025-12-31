#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
message_composer.py - Compositor de mensagens
Sistema Sentinela v2.0

RESPONSABILIDADE:
- Compor mensagem de alerta geral
- Compor relatórios Bom Dia / Boa Noite
"""

from config import Config
from datetime import datetime


class MessageComposer:
    """
    Compositor de mensagens do sistema
    """
    
    @staticmethod
    def compor_alerta_geral(leitura, variacao_3h=None, insights=None):
        """
        Compõe mensagem de alerta geral (G1 Refinado)
        
        Args:
            leitura (dict): Leitura atual do banco
            variacao_3h (dict): Variações em 3h (opcional)
            insights (list): Lista de insights (opcional)
            
        Returns:
            str: Mensagem formatada
        """
        timestamp = datetime.now().strftime('%d/%m/%Y %H:%M')
        
        # Temperatura
        temp = leitura['tem_ins']
        temp_sen = leitura['tem_sen']
        conforto = Config.get_conforto_termico(temp)
        
        # Umidade
        umid = leitura['umd_ins']
        if umid < 40:
            desc_umid = "Ar seco"
        elif umid < 70:
            desc_umid = "Ótima"
        else:
            desc_umid = "Alta"
        
        # Vento
        vento = leitura['ven_vel']
        vento_desc = Config.get_beaufort_scale(vento)
        
        # Chuva
        chuva = leitura.get('chuva') or 0
        if chuva == 0:
            chuva_desc = "Sem chuva"
        else:
            intensidade = Config.get_chuva_intensity(chuva)
            chuva_desc = intensidade.replace('_', ' ').title()
        
        # Radiação
        rad = leitura['rad_glo']
        if rad <= 0:
            rad_zona = "Noite"
            rad_desc = "Noite"
        else:
            rad_zona = Config.get_rad_zone(rad)
            uv_est = int(rad * 0.0035)
            
            if rad_zona == "BAIXA":
                rad_desc = f"Baixa • UV {uv_est}"
            elif rad_zona == "MODERADA":
                rad_desc = f"Moderada • UV {uv_est} (use proteção)"
            elif rad_zona == "ALTA":
                rad_desc = f"Alta • UV {uv_est} (FPS 30+)"
            elif rad_zona == "MUITO ALTA":
                rad_desc = f"Muito Alta • UV {uv_est}+ (FPS 50+)"
            elif rad_zona == "EXTREMA":
                rad_desc = f"EXTREMA • UV {uv_est}+ (PERIGO)"
            else:
                rad_desc = rad_zona.title()
        
        # Pressão
        pressao = leitura['pre_ins']
        if pressao < 1010:
            pressao_desc = "Em queda"
        elif pressao > 1020:
            pressao_desc = "Estável"
        else:
            pressao_desc = "Estável"
        
        # Monta mensagem base
        msg = f"""🌡️ CLIMA UBERLÂNDIA
🕒 {timestamp}

🌡️ Temp: {temp:.1f}°C (Sens: {temp_sen:.1f}°C)
   {conforto[2]}

💧 Umidade: {umid:.0f}% ({desc_umid})

💨 Vento: {vento:.1f} m/s ({vento_desc})

🌧️ Chuva: {chuva:.1f} mm ({chuva_desc})

☀️ Radiação: {rad:.0f} kJ/m²
   {rad_desc}

📊 Pressão: {pressao:.1f} hPa ({pressao_desc})"""
        
        # Adiciona variações se houver
        if variacao_3h:
            msg += "\n\n📈 Variação 3h:"
            if variacao_3h.get('temp'):
                delta_temp = variacao_3h['temp']
                seta = "↑" if delta_temp > 0 else "↓"
                msg += f"\n   Temp: {delta_temp:+.1f}°C {seta}"
            if variacao_3h.get('umid'):
                delta_umid = variacao_3h['umid']
                seta = "↑" if delta_umid > 0 else "↓"
                msg += f"\n   Umidade: {delta_umid:+.0f}% {seta}"
            if variacao_3h.get('pressao'):
                delta_pressao = variacao_3h['pressao']
                seta = "↑" if delta_pressao > 0 else "↓"
                msg += f"\n   Pressão: {delta_pressao:+.1f} hPa {seta}"
        
        # Adiciona insights se houver
        if insights:
            msg += "\n\n🧠 Insights:"
            for insight in insights:
                msg += f"\n• {insight}"
        
        return msg
    
    @staticmethod
    def compor_relatorio_bom_dia(resumo_noite, leitura_atual):
        """
        Compõe relatório Bom Dia
        
        Args:
            resumo_noite (dict): Dados do resumo da noite
            leitura_atual (dict): Leitura atual
            
        Returns:
            str: Mensagem formatada
        """
        timestamp = datetime.now().strftime('%d/%m/%Y às %H:%M')
        
        # Duração da noite
        duracao_h = resumo_noite.get('duracao_horas', 0)
        duracao_m = resumo_noite.get('duracao_minutos', 0)
        inicio = resumo_noite.get('inicio')
        fim = resumo_noite.get('fim')
        
        if inicio and fim:
            inicio_str = inicio.strftime('%H:%M')
            fim_str = fim.strftime('%H:%M')
            linha_duracao = f"Duração: {duracao_h}h {duracao_m}min ({inicio_str}-{fim_str})"
        else:
            linha_duracao = f"Duração: {duracao_h}h {duracao_m}min"
        
        # Condições atuais
        temp_atual = leitura_atual['tem_ins']
        umid_atual = leitura_atual['umd_ins']
        vento_atual = leitura_atual['ven_vel']
        pressao_atual = leitura_atual['pre_ins']
        rad_atual = leitura_atual['rad_glo']
        
        # Classifica condições atuais
        conforto = Config.get_conforto_termico(temp_atual)
        
        if umid_atual < 70:
            desc_umid = "Ótima"
        else:
            desc_umid = "Alta"
        
        vento_desc = Config.get_beaufort_scale(vento_atual)
        
        if rad_atual < 50:
            rad_desc = "Crepúsculo"
        else:
            rad_zona = Config.get_rad_zone(rad_atual)
            rad_desc = rad_zona.title()
        
        msg = f"""☀️ BOM DIA UBERLÂNDIA
📅 {timestamp}

━━━━━━━━━━━━━━━━━━━━━
🌙 RESUMO DA NOITE

{linha_duracao}
Temp mínima: {resumo_noite.get('temp_min', 0):.1f}°C
Temp máxima: {resumo_noite.get('temp_max', 0):.1f}°C
Umidade média: {resumo_noite.get('umid_media', 0):.0f}%
Chuva acumulada: {resumo_noite.get('chuva_total', 0):.1f} mm
Rajada máxima: {resumo_noite.get('rajada_max', 0):.1f} m/s

━━━━━━━━━━━━━━━━━━━━━
🌡️ CONDIÇÕES ATUAIS

Temperatura: {temp_atual:.1f}°C ({conforto[2]})
Umidade: {umid_atual:.0f}% ({desc_umid})
Vento: {vento_atual:.1f} m/s ({vento_desc})
Pressão: {pressao_atual:.1f} hPa (Estável)
Radiação: {rad_atual:.0f} kJ/m² ({rad_desc})

━━━━━━━━━━━━━━━━━━━━━
💡 DICA DO DIA

Manhã agradável para exercícios.
Use protetor solar após 10h.
Hidrate-se bem durante o dia.

Tenha um ótimo dia! ✨"""
        
        return msg
    
    @staticmethod
    def compor_relatorio_boa_noite(resumo_dia, leitura_atual):
        """
        Compõe relatório Boa Noite
        
        Args:
            resumo_dia (dict): Dados do resumo do dia
            leitura_atual (dict): Leitura atual
            
        Returns:
            str: Mensagem formatada
        """
        timestamp = datetime.now().strftime('%d/%m/%Y às %H:%M')
        
        # Duração do dia
        duracao_h = resumo_dia.get('duracao_horas', 0)
        duracao_m = resumo_dia.get('duracao_minutos', 0)
        inicio = resumo_dia.get('inicio')
        fim = resumo_dia.get('fim')
        
        if inicio and fim:
            inicio_str = inicio.strftime('%H:%M')
            fim_str = fim.strftime('%H:%M')
            linha_duracao = f"Duração: {duracao_h}h {duracao_m}min ({inicio_str}-{fim_str})"
        else:
            linha_duracao = f"Duração: {duracao_h}h {duracao_m}min"
        
        # Radiação máxima
        rad_max = resumo_dia.get('rad_max', 0)
        rad_zona = Config.get_rad_zone(rad_max)
        uv_est = int(rad_max * 0.0035)
        
        if rad_zona in ["MUITO ALTA", "EXTREMA"]:
            rad_linha = f"Radiação máxima: {rad_max:.0f} kJ/m²\n   Zona: {rad_zona} (UV {uv_est}) ⚠️"
        else:
            rad_linha = f"Radiação máxima: {rad_max:.0f} kJ/m² (UV {uv_est})"
        
        # Condições atuais
        temp_atual = leitura_atual['tem_ins']
        umid_atual = leitura_atual['umd_ins']
        vento_atual = leitura_atual['ven_vel']
        pressao_atual = leitura_atual['pre_ins']
        
        conforto = Config.get_conforto_termico(temp_atual)
        
        if umid_atual < 70:
            desc_umid = "Boa"
        else:
            desc_umid = "Alta"
        
        vento_desc = Config.get_beaufort_scale(vento_atual)
        
        msg = f"""🌙 BOA NOITE UBERLÂNDIA
📅 {timestamp}

━━━━━━━━━━━━━━━━━━━━━
☀️ RESUMO DO DIA

{linha_duracao}
Temp máxima: {resumo_dia.get('temp_max', 0):.1f}°C
Temp mínima: {resumo_dia.get('temp_min', 0):.1f}°C
Umidade mínima: {resumo_dia.get('umid_min', 0):.0f}%
{rad_linha}
Chuva acumulada: {resumo_dia.get('chuva_total', 0):.1f} mm
Rajada máxima: {resumo_dia.get('rajada_max', 0):.1f} m/s

━━━━━━━━━━━━━━━━━━━━━
🌡️ CONDIÇÕES ATUAIS

Temperatura: {temp_atual:.1f}°C ({conforto[2]})
Umidade: {umid_atual:.0f}% ({desc_umid})
Vento: {vento_atual:.1f} m/s ({vento_desc})
Pressão: {pressao_atual:.1f} hPa (Estável)
Radiação: 0 kJ/m² (Noite)

━━━━━━━━━━━━━━━━━━━━━
💡 DICA DA NOITE

Noite agradável e tranquila.
Agasalho leve pode ser útil.
Bom momento para caminhada.

Tenha uma ótima noite! ✨"""
        
        return msg
    
    @staticmethod
    def gerar_insights(leitura_atual, leitura_3h_atras, delta_temp, delta_pressao):
        """
        Gera insights inteligentes baseados nas condições e histórico
        
        Args:
            leitura_atual (dict): Leitura atual
            leitura_3h_atras (dict): Leitura de 3h atrás
            delta_temp (float): Variação de temperatura
            delta_pressao (float): Variação de pressão
            
        Returns:
            list: Lista de insights
        """
        insights = []
        
        temp_atual = leitura_atual['tem_ins']
        umid_atual = leitura_atual['umd_ins']
        pressao_atual = leitura_atual['pre_ins']
        rad_atual = leitura_atual['rad_glo']
        
        # === TEMPERATURA ===
        if delta_temp < -2.0:
            if delta_temp < -4.0:
                insights.append("Temperatura em queda acentuada")
                insights.append("Possível frente fria aproximando")
            else:
                insights.append("Temperatura em queda")
        elif delta_temp > 3.0:
            if delta_temp > 5.0:
                insights.append("Temperatura subindo rapidamente")
                if temp_atual > 30:
                    insights.append("Atenção: calor intensificando")
            else:
                insights.append("Temperatura em elevação")
        
        # === PRESSÃO ===
        if delta_pressao < -3.0:
            insights.append("Pressão em queda acentuada")
            insights.append("Tempo pode instabilizar")
        elif delta_pressao < -1.5:
            insights.append("Pressão caindo - tempo instável")
        elif delta_pressao > 3.0:
            insights.append("Pressão subindo rapidamente")
            insights.append("Tempo estabilizando")
        elif delta_pressao > 1.5:
            insights.append("Pressão em elevação")
        
        # === UMIDADE ===
        if umid_atual < 30:
            insights.append("Ar muito seco - hidrate-se")
        elif umid_atual > 85:
            insights.append("Ar saturado - chuva provável")
        
        # === RADIAÇÃO UV ===
        if rad_atual > 3000:  # UV Extremo
            insights.append("Radiação solar intensa")
            insights.append("UV extremo - evite exposição")
        elif rad_atual > 2000:  # UV Muito Alto
            insights.append("UV alto - use proteção")
        
        # === CONFORTO TÉRMICO ===
        if temp_atual < 18:
            insights.append("Temperatura baixa - agasalho necessário")
        elif temp_atual > 32:
            insights.append("Calor intenso - evite exposição solar")
        
        # === CONDIÇÕES COMBINADAS ===
        # Calor + Ar Seco = Desconforto
        if temp_atual > 30 and umid_atual < 40:
            if "Atenção: calor intensificando" not in insights:
                insights.append("Atenção: calor intensificando")
        
        # Pressão baixa + Umidade alta = Chuva iminente
        if pressao_atual < 1010 and umid_atual > 80:
            if "Ar saturado - chuva provável" not in insights:
                insights.append("Chuva pode ocorrer em breve")
        
        return insights