#!/usr/bin/env python3
"""Tileset de calçamento da vila (WhatsApp JPEG 1600², grade 6×6, fundo magenta)
→ atlas game-ready public/assets/64/terrain/vila.png (384×384, frames r*6+c, 64px).

Tratamentos: fatiamento pela grade detectada, chroma key magenta com tolerância
p/ artefato JPEG, erosão de 1px de halo, downscale premultiplicado ~246→64 e
alpha binarizado (borda crisp de pixel art).
"""
import numpy as np
from PIL import Image
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / 'assets/vila_calcamento/vila_calcamento_raw.jpg'
OUT = ROOT / 'public/assets/64/terrain/vila.png'
TILE = 64

im = np.asarray(Image.open(SRC).convert('RGB')).astype(int)
r, g, b = im[..., 0], im[..., 1], im[..., 2]

# máscara magenta generosa (JPEG espalha o croma): r e b altos, g bem abaixo,
# mais um critério "rosado" p/ blends de borda (tijolo tem b baixo, não entra)
mag = ((r > 130) & (b > 130) & (g < r - 55) & (g < b - 55)) | \
      ((r > 120) & (b > 110) & (g < r - 40) & (g < b - 40))

# grade: faixas de linhas/colunas ≥95% magenta são calhas
def cell_ranges(axis_mean):
    runs, s = [], None
    for i, v in enumerate(axis_mean):
        if v > 0.95 and s is None: s = i
        elif v <= 0.95 and s is not None: runs.append((s, i)); s = None
    if s is not None: runs.append((s, len(axis_mean)))
    # inset 2px: descarta colunas de transição meio-magenta do JPEG
    return [(a2 + 2, b1 - 2) for (_, a2), (b1, _) in zip(runs, runs[1:])]

cols = cell_ranges(mag.mean(axis=0))
rows = cell_ranges(mag.mean(axis=1))
assert len(cols) == 6 and len(rows) == 6, f'grade inesperada: {len(cols)}x{len(rows)}'

# erosão 1px da máscara de opacidade (mata franja magenta da borda)
opaque = ~mag
er = opaque.copy()
er[1:, :] &= opaque[:-1, :]; er[:-1, :] &= opaque[1:, :]
er[:, 1:] &= opaque[:, :-1]; er[:, :-1] &= opaque[:, 1:]

atlas = Image.new('RGBA', (6 * TILE, 6 * TILE), (0, 0, 0, 0))
for ri, (y0, y1) in enumerate(rows):
    for ci, (x0, x1) in enumerate(cols):
        rgb = im[y0:y1, x0:x1].astype(np.uint8)
        a = (er[y0:y1, x0:x1] * 255).astype(np.uint8)
        # premultiplica antes do downscale p/ não vazar cor do fundo
        pm = rgb.astype(float) * (a[..., None] / 255.0)
        cell = np.dstack([pm.astype(np.uint8), a])
        small = Image.fromarray(cell, 'RGBA').resize((TILE, TILE), Image.BOX)
        sa = np.asarray(small).astype(float)
        alpha = sa[..., 3]
        keep = alpha > 127  # binariza: pixel art não tem meia-transparência
        out = np.zeros((TILE, TILE, 4), np.uint8)
        safe = np.maximum(alpha, 1)[..., None]
        out[..., :3] = np.clip(sa[..., :3] / safe * 255.0, 0, 255).astype(np.uint8)
        out[..., 3] = np.where(keep, 255, 0).astype(np.uint8)
        out[~keep] = 0
        atlas.paste(Image.fromarray(out, 'RGBA'), (ci * TILE, ri * TILE))

# frame 36 (linha 7): grama pura sintetizada da faixa de grama do frame 31
# (linhas 36-63), empilhada com espelho vertical p/ esconder a emenda
final = Image.new('RGBA', (6 * TILE, 7 * TILE), (0, 0, 0, 0))
final.paste(atlas, (0, 0))
band = atlas.crop((1 * TILE, 5 * TILE + 36, 2 * TILE, 6 * TILE))  # 64×28
grass = Image.new('RGBA', (TILE, TILE))
y, flip = 0, False
while y < TILE:
    grass.paste(band.transpose(Image.FLIP_TOP_BOTTOM) if flip else band, (0, y))
    y += band.height; flip = not flip
final.paste(grass, (0, 6 * TILE))

OUT.parent.mkdir(parents=True, exist_ok=True)
final.save(OUT)
print('ok', OUT, final.size)
