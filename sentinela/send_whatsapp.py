#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
import sys
import urllib.request
import urllib.error
from typing import Dict, Any

# Configurações Fixas (Baseadas no script original)
API_URL = "xxxxxxxxxxxxxxxxxxxx"
API_PASS = "xxxxxxxxxxxxxxxxxxxx"
TIMEOUT = 10

def send_message(number: str, text: str) -> Dict[str, Any]:
    """
    Realiza o envio para a API e mapeia o resultado.
    Code 0: Sucesso | 1: Erro Temporário | 2: Erro Permanente
    """
    payload = {
        "number": number.strip(),
        "text": text,
        "password": API_PASS
    }
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        API_URL, 
        data=data, 
        headers={'Content-Type': 'application/json'},
        method='POST'
    )

    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
            status = response.getcode()
            if status in [200, 201]:
                return {"code": 0, "http_status": status, "detail": "Success"}
            else:
                return {"code": 1, "http_status": status, "detail": "Unexpected success status"}
                
    except urllib.error.HTTPError as e:
        # Erros 400 e 403 são considerados permanentes conforme requisito
        code = 2 if e.code in [400, 403] else 1
        return {"code": code, "http_status": e.code, "detail": str(e.reason)}
        
    except (urllib.error.URLError, TimeoutError) as e:
        # Erros de rede, DNS ou Timeout são temporários
        return {"code": 1, "http_status": None, "detail": str(e.reason if hasattr(e, 'reason') else e)}
        
    except Exception as e:
        return {"code": 1, "http_status": None, "detail": f"Internal Error: {str(e)}"}

def main():
    parser = argparse.ArgumentParser(description="Envio direto de WhatsApp via API")
    parser.add_argument("-n", "--numbers", required=True, help="Números separados por vírgula")
    parser.add_argument("-m", "--message", required=True, help="Mensagem de texto")
    
    args = parser.parse_args()
    
    numbers = [n.strip() for n in args.numbers.split(",") if n.strip()]
    results = {}
    all_success = True

    for num in numbers:
        res = send_message(num, args.message)
        results[num] = res
        if res["code"] != 0:
            all_success = False

    # Saída JSON formatada
    print(json.dumps({"results": results}, indent=2))

    # Exit code 0 se todos sucesso, 1 caso contrário
    sys.exit(0 if all_success else 1)

if __name__ == "__main__":
    main()