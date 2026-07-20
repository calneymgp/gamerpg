#!/usr/bin/env python3
"""Montarias LPC: extrai os cavalos de [LPC] Horse Riding 0.9.0 (bluecarrot16,
CC-BY 3.0 / OGA-BY 3.0), aplica Scale2x (mesmo pipeline do paper doll) e gera
sheets em public/assets/64/player/mount/<cor>/ + ícones do inventário.
Idempotente: zip cacheado em assets/lpc_ride/."""
import io
import os
import urllib.request
import zipfile

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, 'assets/lpc_ride/LPC_ride_0.9.0.zip')
DST = os.path.join(ROOT, 'public/assets/64/player/mount')
ICONS = os.path.join(ROOT, 'public/assets/64/ui/icons')
URL = 'https://opengameart.org/sites/default/files/LPC_ride_0.9.0.zip'

# pastas do zip -> cor (identificado por cor média do pelo)
COLORS = {'1': 'cinza', '2': 'dourado', '3': 'marrom', '4': 'preto', '5': 'branco'}
# prefixo do zip -> ciclo (b = camada atrás do cavaleiro, f = na frente)
CYCLES = {'s': 'stand', 'w': 'walk', 'r': 'gallop'}


def scale2x(img):
    a = np.array(img.convert('RGBA'))
    H, W = a.shape[:2]
    pad = np.pad(a, ((1, 1), (1, 1), (0, 0)), mode='edge')
    E = pad[1:-1, 1:-1]
    B = pad[0:-2, 1:-1]
    H_ = pad[2:, 1:-1]
    D = pad[1:-1, 0:-2]
    F = pad[1:-1, 2:]
    eq = lambda x, y: np.all(x == y, axis=-1)
    b_d, b_f = eq(B, D), eq(B, F)
    h_d, h_f = eq(H_, D), eq(H_, F)
    b_h, d_f = eq(B, H_), eq(D, F)
    out = np.empty((H * 2, W * 2, 4), dtype=a.dtype)
    c0 = (b_d & ~b_h & ~d_f)[..., None]
    c1 = (b_f & ~b_h & ~d_f)[..., None]
    c2 = (h_d & ~b_h & ~d_f)[..., None]
    c3 = (h_f & ~b_h & ~d_f)[..., None]
    out[0::2, 0::2] = np.where(c0, D, E)
    out[0::2, 1::2] = np.where(c1, F, E)
    out[1::2, 0::2] = np.where(c2, D, E)
    out[1::2, 1::2] = np.where(c3, F, E)
    return Image.fromarray(out)


def icon64(img, pad=4):
    """Recorta o bbox e centraliza num canvas 64x64 (nearest para pixel art)."""
    box = img.getbbox()
    crop = img.crop(box)
    side = 64 - 2 * pad
    f = min(side / crop.width, side / crop.height)
    f = max(1, round(f)) if f >= 1 else f  # inteiro quando ampliar
    crop = crop.resize((max(1, round(crop.width * f)), max(1, round(crop.height * f))),
                       Image.NEAREST)
    canvas = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    canvas.paste(crop, ((64 - crop.width) // 2, (64 - crop.height) // 2))
    return canvas


if not os.path.exists(CACHE):
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    req = urllib.request.Request(URL, headers={'User-Agent': 'Mozilla/5.0'})
    with open(CACHE, 'wb') as fh:
        fh.write(urllib.request.urlopen(req).read())
    print('baixado:', os.path.relpath(CACHE, ROOT))

z = zipfile.ZipFile(CACHE)
count = 0
for folder, cor in COLORS.items():
    outdir = os.path.join(DST, cor)
    os.makedirs(outdir, exist_ok=True)
    for pref, cycle in CYCLES.items():
        for layer in 'bf':
            im = Image.open(io.BytesIO(z.read(f'{folder}/{pref}{layer}.png')))
            scale2x(im).save(os.path.join(outdir, f'{cycle}_{layer}.png'))
            count += 1
    # ícone: frame sul parado (linha 2, col 0), atrás+frente compostos
    sb = Image.open(io.BytesIO(z.read(folder + '/sb.png'))).convert('RGBA')
    sf = Image.open(io.BytesIO(z.read(folder + '/sf.png'))).convert('RGBA')
    frame = Image.alpha_composite(sb, sf).crop((0, 256, 128, 384))
    icon64(frame).save(os.path.join(ICONS, f'horse_{cor}.png'))
    print(cor, 'ok')

# ícone "a pé": botas do paper doll (frame sul parado do feet)
feet = Image.open(os.path.join(ROOT, 'public/assets/64/player/equip/feet/walk.png'))
icon64(feet.convert('RGBA').crop((0, 256, 128, 384))).save(
    os.path.join(ICONS, 'dismount.png'))

# métricas de alinhamento (coords do frame 128 original) para o game.js
sb = Image.open(io.BytesIO(z.read('3/sb.png'))).convert('RGBA')
sf = Image.open(io.BytesIO(z.read('3/sf.png'))).convert('RGBA')
for d, row in [('n', 0), ('w', 1), ('s', 2), ('e', 3)]:
    frame = Image.alpha_composite(sb, sf).crop((0, row * 128, 128, (row + 1) * 128))
    print('stand', d, 'bbox:', frame.getbbox())
g = Image.alpha_composite(
    Image.open(io.BytesIO(z.read('3/rb.png'))).convert('RGBA'),
    Image.open(io.BytesIO(z.read('3/rf.png'))).convert('RGBA'))
for c in range(4):
    frame = g.crop((c * 128, 2 * 128, (c + 1) * 128, 3 * 128))
    print('gallop s f%d bbox:' % c, frame.getbbox())
print(f'{count} sheets -> {os.path.relpath(DST, ROOT)}')
