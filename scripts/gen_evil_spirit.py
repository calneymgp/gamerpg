import os
import math
import random
from PIL import Image, ImageDraw

def create_ghost_frame(frame_idx, total_frames=4, width=192, height=192):
    """Fantasma estilo lençol: cabeça redonda + corpo/capa pendurada, alto e estreito."""
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    cx = width // 2
    wv = math.sin((frame_idx / total_frames) * 2 * math.pi)
    rng = random.Random(frame_idx * 137 + 19)

    # --- proporções: cabeça ~1/3, corpo ~2/3 da altura ---
    head_cy = 50                    # centro da cabeça
    head_rx, head_ry = 26, 24       # cabeça oval (levemente achatada vertical)
    neck_y = head_cy + head_ry - 4  # onde começa o corpo
    body_bottom = 168               # fim do corpo
    body_h = body_bottom - neck_y
    body_top_w = 36                 # largura no ombro/pescoço
    body_bot_w = 56                 # largura na base (mais largo embaixo = lençol caindo)

    sway = int(wv * 7)              # balanço lateral da capa

    # --- aura externa (fumaça translúcida ao redor) ---
    for r in range(72, 16, -4):
        frac = r / 72.0
        alpha = int(16 * (1 - frac))
        ex = cx + int(wv * 4 * frac)
        ey = 96 + int(wv * 3 * frac)
        draw.ellipse([ex - r, ey - r * 1.2, ex + r, ey + r * 1.2],
                     fill=(10, 12, 22, alpha))

    # --- partículas de fumaça soltas ---
    for _ in range(12):
        angle = rng.uniform(0, math.pi * 2)
        dist = rng.uniform(20, 66)
        pr = rng.uniform(2, 7)
        pa = rng.randint(14, 40)
        px = cx + int(math.cos(angle) * dist + wv * 4)
        py = 96 + int(math.sin(angle) * dist * 1.1)
        draw.ellipse([px - pr, py - pr, px + pr, py + pr],
                     fill=(8, 10, 18, pa))

    # --- corpo (capa/lençol) — formato trapezoidal com laterais onduladas ---
    # desenhamos em fatias horizontais para a lateral ondular
    body_slices = 20
    for s in range(body_slices):
        t = s / body_slices
        y0 = neck_y + t * body_h
        y1 = neck_y + (t + 1.0 / body_slices) * body_h
        # largura varia do ombro até a base
        half_w = (body_top_w + t * (body_bot_w - body_top_w)) / 2
        # ondulação lateral (mais intensa perto da base)
        wave_offset = math.sin(t * 8 + wv * 2) * 5 * t
        left = cx + sway * t + wave_offset - half_w
        right = cx + sway * t + wave_offset + half_w
        body_alpha = 130 + int(t * 40)
        draw.rectangle([left, y0, right, y1],
                       fill=(12, 14, 26, body_alpha))

    # --- borda inferior ondulada (scalloped hem) ---
    hem_y = body_bottom - 8
    hem_waves = 5
    for w in range(hem_waves):
        wave_cx = cx - 36 + w * (72 / (hem_waves - 1)) + sway * 0.7
        wave_r = 9 + abs(math.sin(w * 1.5 + wv)) * 4
        draw.ellipse([wave_cx - wave_r, hem_y - wave_r * 0.6,
                      wave_cx + wave_r, hem_y + wave_r * 0.6],
                     fill=(10, 12, 22, 140))
        # pontas do lençol caindo entre as ondas
        if w < hem_waves - 1:
            tip_x = (wave_cx + (wave_cx + 72 / (hem_waves - 1))) / 2
            tip_len = 6 + rng.uniform(0, 5)
            draw.line([(tip_x, hem_y), (tip_x, hem_y + tip_len)],
                      fill=(14, 16, 28, 100), width=3)

    # --- cabeça ---
    # glow externo
    for gr in range(28, 22, -2):
        ga = int(70 * (1 - gr / 31))
        draw.ellipse([cx - gr, head_cy - gr, cx + gr, head_cy + gr],
                     fill=(14, 16, 28, ga))
    # cabeça principal
    draw.ellipse([cx - head_rx, head_cy - head_ry, cx + head_rx, head_cy + head_ry],
                 fill=(16, 18, 32, 185))
    # núcleo escuro
    draw.ellipse([cx - head_rx + 4, head_cy - head_ry + 4,
                  cx + head_rx - 4, head_cy + head_ry - 4],
                 fill=(8, 9, 16, 210))

    # --- olhos brilhantes ---
    eye_y = head_cy - 3
    eye_off = 9
    for side in [-1, 1]:
        ex = cx + side * eye_off
        # glow
        draw.ellipse([ex - 8, eye_y - 8, ex + 8, eye_y + 8],
                     fill=(90, 160, 255, 50))
        draw.ellipse([ex - 5, eye_y - 5, ex + 5, eye_y + 5],
                     fill=(140, 200, 255, 80))
        # pupila
        draw.ellipse([ex - 3.5, eye_y - 3.5, ex + 3.5, eye_y + 3.5],
                     fill=(200, 235, 255, 250))

    # --- boca (vazio escuro) ---
    mouth_w = 5 + int(abs(wv) * 2)
    mouth_h = 3 + int(abs(wv) * 1.5)
    draw.ellipse([cx - mouth_w, head_cy + 6,
                  cx + mouth_w, head_cy + 6 + mouth_h],
                 fill=(3, 3, 6, 200))

    # --- "braços" de lençol (laterais da capa se erguendo como asas) ---
    for side in [-1, 1]:
        arm_x = cx + side * (body_top_w / 2 + 10 + sway * side * 0.5)
        arm_y = neck_y + 15
        arm_len = 18 + abs(wv) * 6
        arm_r = 7
        # braço aponta pra fora e ligeiramente pra baixo
        arm_tip_x = arm_x + side * arm_len * 0.7
        arm_tip_y = arm_y + arm_len * 0.4
        draw.line([(arm_x, arm_y), (arm_tip_x, arm_tip_y)],
                  fill=(14, 16, 28, 120), width=10)
        draw.ellipse([arm_tip_x - arm_r, arm_tip_y - arm_r,
                      arm_tip_x + arm_r, arm_tip_y + arm_r],
                     fill=(14, 16, 28, 110))

    # --- rastro inferior (fumaça que se desprende da base) ---
    for _ in range(8):
        tx = cx + rng.uniform(-28, 28) + sway * 0.8
        ty = body_bottom + rng.uniform(0, 16)
        tr = rng.uniform(1.5, 4)
        ta = rng.randint(20, 55)
        draw.ellipse([tx - tr, ty - tr, tx + tr, ty + tr],
                     fill=(10, 12, 20, ta))

    return img


def main():
    os.makedirs('public/assets/64/effects', exist_ok=True)
    os.makedirs('public/assets/64/ui', exist_ok=True)

    num_frames = 4
    fw, fh = 192, 192

    sheet = Image.new('RGBA', (fw * num_frames, fh), (0, 0, 0, 0))
    for f in range(num_frames):
        frame = create_ghost_frame(f, num_frames, fw, fh)
        sheet.paste(frame, (f * fw, 0), frame)

    sheet_path = 'public/assets/64/effects/evil_spirit_sheet.png'
    sheet.save(sheet_path)
    print(f"Saved {sheet_path} ({fw * num_frames}x{fh})")

    # Ícone 64x64
    icon = Image.new('RGBA', (64, 64), (20, 15, 30, 220))
    draw = ImageDraw.Draw(icon)
    draw.rectangle([0, 0, 63, 63], outline=(180, 140, 240, 255), width=2)
    ghost_small = create_ghost_frame(0, 4, 192, 192).resize((52, 52), Image.NEAREST)
    icon.alpha_composite(ghost_small, (6, 6))
    icon_path = 'public/assets/64/ui/evil_spirit_icon.png'
    icon.save(icon_path)
    print(f"Saved {icon_path}")


if __name__ == '__main__':
    main()
