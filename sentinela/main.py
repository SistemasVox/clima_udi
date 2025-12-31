#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
main.py - Orquestrador Principal v2.1
Sistema Sentinela v2.0

CORREÇÕES v2.1:
- Fix: IDs não são mais consumidos desnecessariamente
- Fix: Radiação negativa detecta Bom Dia corretamente
- Fix: Anti-spam aprimorado em todas as camadas
- Fix: Estados sempre salvos após processamento
"""

import sys
import subprocess
import json
from datetime import datetime

# Imports dos módulos do sistema
from database import WeatherDatabase
from state_manager import StateManager
from zona_temperatura import ZonaTemperatura
from zona_umidade import ZonaUmidade
from zona_vento import ZonaVento
from zona_chuva import ZonaChuva
from zona_radiacao import ZonaRadiacao
from zona_pressao import ZonaPressao
from message_composer import MessageComposer
from config import Config


def log(mensagem):
    """Função auxiliar de log"""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {mensagem}")


def enviar_whatsapp(mensagem):
    """
    Envia mensagem via WhatsApp
    
    Returns:
        bool: True se enviou com sucesso
    """
    numeros = Config.WHATSAPP_NUMBERS
    cmd = ['python3', 'send_whatsapp.py', '-n', numeros, '-m', mensagem]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            log(f"❌ Erro ao enviar WhatsApp: {result.stderr}")
            return False
        
        response = json.loads(result.stdout)
        resultados = response.get('results', {})
        sucesso = all(r.get('code') == 0 for r in resultados.values())
        
        if sucesso:
            log(f"✅ Mensagem enviada para {len(resultados)} número(s)")
        else:
            log(f"⚠️ Falha em alguns envios")
        
        return sucesso
        
    except subprocess.TimeoutExpired:
        log("❌ Timeout ao enviar WhatsApp")
        return False
    except Exception as e:
        log(f"❌ Erro ao enviar WhatsApp: {e}")
        return False


def processar_zonas(leitura, leitura_1h, acumulado_24h, state_mgr):
    """
    Processa todas as zonas e retorna resultados
    
    Returns:
        tuple: (alertas_inteligentes, alertas_criticos, estados_atuais, transicao)
    """
    alertas_inteligentes = []
    alertas_criticos = []
    estados_atuais = {}
    transicao = None
    
    # TEMPERATURA
    temp_atual = leitura['tem_ins']
    estado_ant = state_mgr.get_zone_state('temperatura')
    mudanca = ZonaTemperatura.detectar_mudanca(temp_atual, estado_ant)
    
    if mudanca:
        zona_atual = mudanca['zona_atual']
        estados_atuais['temperatura'] = (zona_atual, temp_atual)
        
        if mudanca['tipo'] == 'mudanca_zona':
            msg = ZonaTemperatura.gerar_alerta_inteligente(mudanca)
            if msg:
                alertas_inteligentes.append(('temperatura', mudanca, msg))
    
    criticos = ZonaTemperatura.verificar_critico(temp_atual, leitura_1h)
    if criticos:
        alertas_criticos.extend([(c['tipo'], c) for c in criticos])
    
    # UMIDADE
    umid_atual = leitura['umd_ins']
    estado_ant = state_mgr.get_zone_state('umidade')
    mudanca = ZonaUmidade.detectar_mudanca(umid_atual, estado_ant)
    
    if mudanca:
        zona_atual = mudanca['zona_atual']
        estados_atuais['umidade'] = (zona_atual, umid_atual)
        
        if mudanca['tipo'] == 'mudanca_zona':
            msg = ZonaUmidade.gerar_alerta_inteligente(mudanca)
            if msg:
                alertas_inteligentes.append(('umidade', mudanca, msg))
    
    criticos = ZonaUmidade.verificar_critico(umid_atual)
    if criticos:
        alertas_criticos.extend([(c['tipo'], c) for c in criticos])
    
    # VENTO
    vento_atual = leitura['ven_vel']
    rajada_atual = leitura['ven_raj']
    estado_ant = state_mgr.get_zone_state('vento')
    mudanca = ZonaVento.detectar_mudanca(vento_atual, estado_ant)
    
    if mudanca:
        zona_atual = mudanca['zona_atual']
        estados_atuais['vento'] = (zona_atual, vento_atual)
        
        if mudanca['tipo'] == 'mudanca_zona':
            msg = ZonaVento.gerar_alerta_inteligente(mudanca, rajada=rajada_atual)
            if msg:
                alertas_inteligentes.append(('vento', mudanca, msg))
    
    criticos = ZonaVento.verificar_critico(vento_atual, rajada_atual)
    if criticos:
        alertas_criticos.extend([(c['tipo'], c) for c in criticos])
    
    # CHUVA
    chuva_atual = leitura.get('chuva') or 0
    estado_ant = state_mgr.get_zone_state('chuva')
    mudanca = ZonaChuva.detectar_mudanca(chuva_atual, estado_ant)
    
    if mudanca:
        zona_atual = mudanca['zona_atual']
        estados_atuais['chuva'] = (zona_atual, chuva_atual)
        
        if mudanca['tipo'] == 'mudanca_zona':
            msg = ZonaChuva.gerar_alerta_inteligente(mudanca)
            if msg:
                alertas_inteligentes.append(('chuva', mudanca, msg))
    
    criticos = ZonaChuva.verificar_critico(chuva_atual, acumulado_24h)
    if criticos:
        alertas_criticos.extend([(c['tipo'], c) for c in criticos])
    
    # RADIAÇÃO
    rad_atual = leitura['rad_glo']
    rad_anterior = leitura_1h['rad_glo'] if leitura_1h else None
    estado_ant = state_mgr.get_zone_state('radiacao')
    mudanca = ZonaRadiacao.detectar_mudanca(rad_atual, estado_ant)
    
    if mudanca:
        zona_atual = mudanca['zona_atual']
        estados_atuais['radiacao'] = (zona_atual, rad_atual)
        
        if mudanca['tipo'] == 'mudanca_zona':
            msg = ZonaRadiacao.gerar_alerta_inteligente(mudanca)
            if msg:
                alertas_inteligentes.append(('radiacao', mudanca, msg))
    
    criticos = ZonaRadiacao.verificar_critico(rad_atual)
    if criticos:
        alertas_criticos.extend([(c['tipo'], c) for c in criticos])
    
    transicao = ZonaRadiacao.detectar_transicao(rad_atual, rad_anterior)
    
    # PRESSÃO
    pressao_atual = leitura['pre_ins']
    estado_ant = state_mgr.get_zone_state('pressao')
    mudanca = ZonaPressao.detectar_mudanca(pressao_atual, estado_ant)
    
    if mudanca:
        zona_atual = mudanca['zona_atual']
        estados_atuais['pressao'] = (zona_atual, pressao_atual)
        
        if mudanca['tipo'] == 'mudanca_zona':
            # Calcula delta para mensagem
            from database import WeatherDatabase
            db_temp = WeatherDatabase()
            db_temp.connect()
            delta_3h = db_temp.get_pressure_variation(3)
            db_temp.close()
            
            msg = ZonaPressao.gerar_alerta_inteligente(mudanca, delta_3h=delta_3h)
            if msg:
                alertas_inteligentes.append(('pressao', mudanca, msg))
    
    # Verifica críticos de pressão
    from database import WeatherDatabase
    db_temp = WeatherDatabase()
    db_temp.connect()
    delta_1h = db_temp.get_pressure_variation(1)
    db_temp.close()
    
    criticos = ZonaPressao.verificar_critico(pressao_atual, delta_1h)
    if criticos:
        alertas_criticos.extend([(c['tipo'], c) for c in criticos])
    
    return alertas_inteligentes, alertas_criticos, estados_atuais, transicao


def main():
    """Função principal"""
    log("=" * 60)
    log("INÍCIO - Sistema Sentinela v2.1")
    log("=" * 60)
    
    db = WeatherDatabase()
    if not db.connect():
        log("❌ ERRO: Falha ao conectar MySQL")
        return 1
    
    try:
        # Buscar leituras
        leitura = db.get_latest_reading()
        if not leitura:
            log("❌ ERRO: Nenhuma leitura encontrada")
            return 1
        
        log(f"✅ Leitura: {leitura['timestamp']}")
        
        # Buscar leituras anteriores usando dt_medicao + hr_medicao
        # API INMET atualiza a cada HORA, não a cada 5 minutos
        leitura_1h = db.get_reading_hours_ago(1)    # 1 hora atrás
        leitura_3h = db.get_reading_hours_ago(3)    # 3 horas atrás
        
        # Debug: mostrar se encontrou leituras anteriores
        if leitura_1h:
            log(f"  📊 Leitura 1h atrás encontrada")
        if leitura_3h:
            log(f"  📊 Leitura 3h atrás encontrada")
        
        acumulado_24h = db.get_accumulated_rain_24h()
        
        # Carregar estados
        state_mgr = StateManager()
        
        # Processar zonas
        log("\n🔍 Processando zonas...")
        alertas_inteligentes, alertas_criticos, estados_atuais, transicao = processar_zonas(
            leitura, leitura_1h, acumulado_24h, state_mgr
        )
        
        # ATUALIZAR ESTADOS (sempre, independente de alertas)
        for zona_nome, (zona_atual, valor_atual) in estados_atuais.items():
            state_mgr.update_zone_state(zona_nome, zona_atual, valor_atual)
        
        # ENVIAR ALERTAS INTELIGENTES
        log(f"\n📤 {len(alertas_inteligentes)} alertas inteligentes")
        for zona_nome, mudanca, mensagem in alertas_inteligentes:
            log(f"  📨 {zona_nome}")
            enviar_whatsapp(mensagem)
        
        # ENVIAR ALERTAS CRÍTICOS (com controle anti-spam)
        tipos_criticos = [
            'calor_extremo', 'frio_extremo', 'mudanca_brusca',
            'ar_muito_seco', 'vento_forte', 
            'chuva_intensa', 'chuva_acumulada',
            'uv_extremo', 'queda_brusca', 'pressao_muito_baixa'
        ]
        
        criticos_ativos = {t: False for t in tipos_criticos}
        for tipo, dados in alertas_criticos:
            criticos_ativos[tipo] = True
        
        log(f"\n🚨 {len([t for t in criticos_ativos.values() if t])} críticos ativos")
        
        for tipo in tipos_criticos:
            ativo = criticos_ativos[tipo]
            deve_enviar = state_mgr.should_send_critical(tipo, ativo)
            
            if deve_enviar and ativo:
                log(f"  🚨 {tipo}")
                
                # Encontra dados
                dados = None
                for t, d in alertas_criticos:
                    if t == tipo:
                        dados = d
                        break
                
                if dados:
                    msg = None
                    if tipo in ['calor_extremo', 'frio_extremo', 'mudanca_brusca']:
                        msg = ZonaTemperatura.gerar_alerta_critico(dados)
                    elif tipo == 'ar_muito_seco':
                        msg = ZonaUmidade.gerar_alerta_critico(dados)
                    elif tipo == 'vento_forte':
                        msg = ZonaVento.gerar_alerta_critico(dados)
                    elif tipo in ['chuva_intensa', 'chuva_acumulada']:
                        msg = ZonaChuva.gerar_alerta_critico(dados)
                    elif tipo == 'uv_extremo':
                        msg = ZonaRadiacao.gerar_alerta_critico(dados)
                    elif tipo in ['queda_brusca', 'pressao_muito_baixa']:
                        msg = ZonaPressao.gerar_alerta_critico(dados)
                    
                    if msg and enviar_whatsapp(msg):
                        state_mgr.update_critical_state(tipo, True)
            
            elif deve_enviar and not ativo:
                # Crítico finalizou
                state_mgr.update_critical_state(tipo, False)
        
        # RELATÓRIOS
        if transicao:
            log(f"\n🌅 Transição: {transicao}")
            
            if transicao == 'bom_dia':
                if state_mgr.should_send_report('bom_dia', leitura['rad_glo'], 
                                                leitura_1h['rad_glo'] if leitura_1h else None):
                    resumo = db.get_night_summary()
                    if resumo:
                        msg = MessageComposer.compor_relatorio_bom_dia(resumo, leitura)
                        if enviar_whatsapp(msg):
                            state_mgr.update_report('bom_dia')
            
            elif transicao == 'boa_noite':
                if state_mgr.should_send_report('boa_noite', leitura['rad_glo'],
                                                leitura_1h['rad_glo'] if leitura_1h else None):
                    resumo = db.get_day_summary()
                    if resumo:
                        msg = MessageComposer.compor_relatorio_boa_noite(resumo, leitura)
                        if enviar_whatsapp(msg):
                            state_mgr.update_report('boa_noite')
        
        # ALERTA GERAL
        deve_enviar, motivo = state_mgr.should_send_general_alert(
            leitura['tem_ins'], leitura['umd_ins'], leitura['pre_ins']
        )
        
        if deve_enviar:
            log(f"\n📋 Alerta geral: {motivo}")
            
            delta_temp = db.get_temperature_variation(3)
            delta_pressao = db.get_pressure_variation(3)
            
            insights = MessageComposer.gerar_insights(
                leitura, leitura_3h, delta_temp, delta_pressao
            )
            
            variacao = {'temp': delta_temp, 'pressao': delta_pressao}
            if leitura_3h:
                variacao['umid'] = leitura['umd_ins'] - leitura_3h['umd_ins']
            
            msg = MessageComposer.compor_alerta_geral(leitura, variacao, insights)
            
            if enviar_whatsapp(msg):
                state_mgr.update_general_alert(
                    leitura['tem_ins'], leitura['umd_ins'], leitura['pre_ins']
                )
        
        # SALVAR ESTADOS
        state_mgr.save()
        
        log("\n" + "=" * 60)
        log("✅ CONCLUÍDO")
        log("=" * 60)
        
        return 0
        
    except Exception as e:
        log(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        return 1
        
    finally:
        db.close()


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)