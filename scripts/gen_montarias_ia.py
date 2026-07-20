#!/usr/bin/env python3
"""Gera montarias IA via PixelLab (personagem 4 direções + walk quadrúpede).
Uso: python3 scripts/gen_montarias_ia.py [porco|status]
Idempotente: estado compartilhado em public/assets/64/_source/ai_gen/state.json.
Saída: public/assets/64/player/mount/<nome>/{idle,walk}.png + ícone do inventário.
"""
import base64
import io
import json
import os
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AI = os.path.join(ROOT, 'public/assets/64/_source/ai_gen')
STATE_F = os.path.join(AI, 'state.json')
DST = os.path.join(ROOT, 'public/assets/64/player/mount')
ICONS = os.path.join(ROOT, 'public/assets/64/ui/icons')
API = 'https://api.pixellab.ai/v2'

MOUNTS = {
    'porco': {
        'desc': 'chubby fat pink pig with a small brown leather saddle on its back, '
                'rideable mount, cute fantasy RPG animal',
        'size': 64, 'template': 'dog', 'seed': 314,
    },
}


def env():
    out = {}
    for ln in open(os.path.join(ROOT, '.env')):
        ln = ln.strip()
        if ln and not ln.startswith('#') and '=' in ln:
            k, v = ln.split('=', 1)
            out[k.strip()] = v.strip().strip('"')
    return out


KEYS = dict(p.split(':', 1) for p in env()['PIXELLAB_KEYS'].split(';'))


def call(keyname, method, path, body=None, timeout=300):
    req = urllib.request.Request(API + path,
        headers={'Authorization': f'Bearer {KEYS[keyname]}', 'Content-Type': 'application/json'},
        data=json.dumps(body).encode() if body is not None else None, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read()
            return r.status, (json.loads(raw) if 'json' in r.headers.get('Content-Type', '') else raw)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:600]


def remaining(keyname):
    st, d = call(keyname, 'GET', '/balance')
    return float((d.get('subscription') or {}).get('generations') or 0) if st in (200, 201, 202) else 0


def pick_key():
    best = max(KEYS, key=remaining)
    print(f'usando chave {best} ({remaining(best)} gens)')
    return best


def load_state():
    return json.load(open(STATE_F)) if os.path.exists(STATE_F) else {}


def save_state(s):
    json.dump(s, open(STATE_F, 'w'), indent=1)


def poll(fn, label, interval=10, max_s=900):
    t0 = time.time()
    while time.time() - t0 < max_s:
        done, info = fn()
        if done:
            return info
        print(f'  aguardando {label}... ({int(time.time()-t0)}s) {info}', flush=True)
        time.sleep(interval)
    raise SystemExit(f'timeout esperando {label}')


def fetch_img(url):
    from PIL import Image
    return Image.open(io.BytesIO(urllib.request.urlopen(
        urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=60).read())).convert('RGBA')


def icon64(img, pad=4):
    from PIL import Image
    crop = img.crop(img.getbbox())
    side = 64 - 2 * pad
    f = min(side / crop.width, side / crop.height)
    f = max(1, round(f)) if f >= 1 else f
    crop = crop.resize((max(1, round(crop.width * f)), max(1, round(crop.height * f))), Image.NEAREST)
    canvas = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    canvas.paste(crop, ((64 - crop.width) // 2, (64 - crop.height) // 2))
    return canvas


def stage_mount(name):
    from PIL import Image
    spec = MOUNTS[name]
    outdir = os.path.join(DST, name)
    if os.path.exists(os.path.join(outdir, 'walk.png')):
        print(f'{name}: sheets já existem — pulando')
        return
    s = load_state()
    c = s.get('mount_' + name, {})
    if not c.get('character_id'):
        key = pick_key()
        st, resp = call(key, 'POST', '/create-character-with-4-directions', {
            'description': spec['desc'],
            'image_size': {'width': spec['size'], 'height': spec['size']},
            'view': 'low top-down',
            'outline': 'single color black outline',
            'shading': 'basic shading',
            'detail': 'medium detail',
            'seed': spec['seed'],
            'template_id': spec['template'],
        })
        print(f'create-character {name}:', st, str(resp)[:300] if st != 200 else list(resp.keys()))
        if st not in (200, 201, 202):
            raise SystemExit(1)
        c = {'key': key, 'character_id': resp.get('character_id') or resp.get('id')}
        s['mount_' + name] = c
        save_state(s)

    def ready():
        st, d = call(c['key'], 'GET', f"/characters/{c['character_id']}")
        if st not in (200, 201, 202):
            return False, f'http {st}'
        return (True, d) if d.get('rotation_urls') else (False, 'sem rotation_urls ainda')

    poll(ready, f'char {name}')

    s = load_state()
    if not s['mount_' + name].get('walk_requested'):
        st, resp = call(c['key'], 'POST', '/characters/animations', {
            'character_id': c['character_id'],
            'mode': 'template',
            'template_animation_id': 'walk-6-frames',  # quadrúpede
            'animation_name': 'walk',
        })
        print(f'walk {name}:', st, str(resp)[:250] if st != 200 else list(resp.keys()))
        if st not in (200, 409):
            raise SystemExit(1)
        s['mount_' + name]['walk_requested'] = True
        save_state(s)

    def walk_ready():
        st, d = call(c['key'], 'GET', f"/characters/{c['character_id']}")
        if st not in (200, 201, 202):
            return False, f'http {st}'
        walk = next((a for a in (d.get('animations') or [])
                     if a.get('animation_type') in ('walk', 'walk-6-frames')), None)
        have = {x['direction'] for x in (walk or {}).get('directions') or [] if x.get('frames')}
        # jobs de direção podem morrer no servidor — com n/s + um lado pronto,
        # seguimos e espelhamos o lado faltante (flip horizontal)
        if {'north', 'south'} <= have and have & {'east', 'west'}:
            return True, d
        return False, f'walk dirs prontos: {sorted(have)}'

    d = poll(walk_ready, f'walk {name}')
    os.makedirs(outdir, exist_ok=True)
    order = ['north', 'west', 'south', 'east']
    rot = d['rotation_urls']
    mirror_rot = {'west': 'east', 'east': 'west'}
    idles = [fetch_img(rot[k]) if rot.get(k)
             else fetch_img(rot[mirror_rot[k]]).transpose(Image.FLIP_LEFT_RIGHT)
             for k in order]
    S = idles[0].width
    sheet = Image.new('RGBA', (S, S * 4), (0, 0, 0, 0))
    for i, im in enumerate(idles):
        sheet.paste(im, (0, i * S))
    sheet.save(os.path.join(outdir, 'idle.png'))
    walk = next(a for a in d['animations'] if a.get('animation_type') in ('walk', 'walk-6-frames'))
    by_dir = {x['direction']: x['frames'] for x in walk['directions'] if x.get('frames')}
    ncols = max(len(v) for v in by_dir.values())
    ws = Image.new('RGBA', (S * ncols, S * 4), (0, 0, 0, 0))
    mirror = {'west': 'east', 'east': 'west'}
    for r, k in enumerate(order):
        urls = by_dir.get(k) or by_dir.get(mirror.get(k, ''), [])
        flip = k not in by_dir
        if flip:
            print(f'  direção {k} ausente — espelhando {mirror[k]}')
        for col, url in enumerate(urls):
            im = fetch_img(url)
            ws.paste(im.transpose(Image.FLIP_LEFT_RIGHT) if flip else im, (col * S, r * S))
    ws.save(os.path.join(outdir, 'walk.png'))
    json.dump({'frame': S, 'walk_cols': ncols}, open(os.path.join(outdir, 'meta.json'), 'w'))
    icon64(idles[2]).save(os.path.join(ICONS, f'mount_{name}.png'))
    print(f'{name}: idle+walk exportados (frame {S}px, walk {ncols}f) + ícone ✓')


def stage_status():
    for name in KEYS:
        print(f'{name}: {remaining(name)} gens')


if __name__ == '__main__':
    arg = sys.argv[1] if len(sys.argv) > 1 else 'porco'
    stage_status() if arg == 'status' else stage_mount(arg)
