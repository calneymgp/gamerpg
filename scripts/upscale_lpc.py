#!/usr/bin/env python3
"""Upscale 2x das camadas LPC via Scale2x (AdvMAME2x) — preserva alpha e alinhamento.
Gera public/assets/64/lpc2x/ espelhando public/assets/64/lpc/."""
import os
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'public/assets/64/lpc')
DST = os.path.join(ROOT, 'public/assets/64/lpc2x')


def scale2x(img):
    a = np.array(img.convert('RGBA'))
    H, W = a.shape[:2]
    # vizinhos com borda replicada
    pad = np.pad(a, ((1, 1), (1, 1), (0, 0)), mode='edge')
    E = pad[1:-1, 1:-1]
    B = pad[0:-2, 1:-1]   # cima
    H_ = pad[2:, 1:-1]    # baixo
    D = pad[1:-1, 0:-2]   # esquerda
    F = pad[1:-1, 2:]     # direita
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


count = 0
for dirpath, _, files in os.walk(SRC):
    for f in files:
        if not f.endswith('.png'):
            continue
        rel = os.path.relpath(os.path.join(dirpath, f), SRC)
        dst = os.path.join(DST, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        scale2x(Image.open(os.path.join(dirpath, f))).save(dst)
        count += 1
print(f'{count} sheets upscaled 2x -> {os.path.relpath(DST, ROOT)}')
