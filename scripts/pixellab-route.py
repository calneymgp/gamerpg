#!/usr/bin/env python3
"""Roteador de chaves PixelLab: consulta o saldo de cada conta em PIXELLAB_KEYS
e devolve a de maior saldo. Uso: python3 scripts/pixellab-route.py [--json]"""
import json
import os
import sys
import urllib.request

API = 'https://api.pixellab.ai/v2'


def load_env(path=None):
    path = path or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
    env = {}
    if os.path.exists(path):
        for ln in open(path):
            ln = ln.strip()
            if ln and not ln.startswith('#') and '=' in ln:
                k, v = ln.split('=', 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def get_balance(key):
    """Saldo utilizável: gerações restantes do trial + usd*? (usd raramente usado).
    Resposta: {'credits': {'usd': x}, 'subscription': {'generations': restantes, 'total': 40}}"""
    req = urllib.request.Request(f'{API}/balance', headers={'Authorization': f'Bearer {key}'})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            data = json.loads(r.read())
            gens = (data.get('subscription') or {}).get('generations') or 0.0
            usd = (data.get('credits') or {}).get('usd') or 0.0
            return float(gens) + float(usd) * 10  # usd pago vale ~10 gens/$ (aprox)
    except Exception as e:
        return f'ERRO: {e}'


def balances():
    env = load_env()
    keys = env.get('PIXELLAB_KEYS', '')
    out = []
    for pair in keys.split(';'):
        if ':' not in pair:
            continue
        name, key = pair.split(':', 1)
        out.append({'name': name, 'key': key, 'balance': get_balance(key)})
    return out


def best_key():
    ok = [b for b in balances() if isinstance(b['balance'], float) and b['balance'] > 0]
    if not ok:
        raise SystemExit('nenhuma chave PixelLab com saldo')
    return max(ok, key=lambda b: b['balance'])


if __name__ == '__main__':
    bs = balances()
    if '--json' in sys.argv:
        print(json.dumps(bs))
    else:
        for b in bs:
            print(f"{b['name']:<12} {b['balance']}")
        ok = [b for b in bs if isinstance(b['balance'], float)]
        if ok:
            m = max(ok, key=lambda b: b['balance'])
            print(f"\nmelhor: {m['name']} ({m['balance']})")
