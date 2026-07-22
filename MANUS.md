# MANUS.md — Instructions for Manus AI Agent

Welcome Manus! This repository is **GameRPG Lab**, a 2D top-down RPG visual laboratory & sprite creation engine.

---

## 🎯 Core Principles & Architecture

1. **Static Stack (No Build/Backend)**:
   - **Frontend**: Pure HTML5 + ES6 JavaScript + Phaser 4.2.1 (`public/vendor/phaser.min.js`).
   - **No Node.js / npm / bundler required**.
   - **Execution**: Simply serve `public/` using `python3 -m http.server 8310 --directory ./public`.
   - **Testing**: Open `http://localhost:8310/demo64/` in a browser.

2. **Asset Standard (64×64 Grid)**:
   - All runtime game assets live in `public/assets/64/`.
   - **Terrain**: `public/assets/64/terrain/` (tileset maps, autotiling, bridges, animated water).
   - **Creatures/Monsters**: `public/assets/64/creatures/<biome>/<creature>/` (`idle.png`, `walk.png`).
   - **Player (Paper Doll LPC)**: `public/assets/64/player/equip/` (`body/`, `head/`, `feet/`, `legs/`, `torso/`, `weapon/`).
   - **Mounts**: `public/assets/64/player/mount/` (`horse_brown/`, `piggy/`, `slime/`, etc.).

---

## 🚀 How to Run & Test Changes

```bash
# Start local static server
python3 -m http.server 8310 --directory ./public

# Access demo
http://localhost:8310/demo64/
```

> **Cache Busting**: When modifying `public/demo64/game.js` or `public/shared/engine.js`, increment the `?v=<version>` tag in `public/demo64/index.html` scripts to force browser reload.

---

## 🎨 Sprite Creation Workflows & Scripts

### 1. Generating & Adding New Creatures / Monsters
- Store raw sprite frames or AI outputs.
- Post-process: ensure transparent background (magenta/green chroma key removal), grid alignment, and 64×64 scaling.
- Structure in `public/assets/64/creatures/<biome>/<name>/`:
  - `idle.png`: horizontal animation sheet (e.g. 4-6 frames).
  - `walk.png`: horizontal animation sheet (e.g. 6-8 frames).
- Register the mob in `public/demo64/game.js` in `PRELOAD` and `CREATE_MOBS`.

### 2. Creating New Mounts ("Domar / Taming")
Use `scripts/gen_montaria.py`:
```bash
python3 scripts/gen_montaria.py <mount_name> \
  --desc "<description for AI generation>" \
  --ref <path_to_idle_sheet> \
  --ref-fw 64 --ref-fh 64 \
  --anim-desc "<gallop animation style description>"
```
This script automatically generates 4-direction rotations + walk cycle, measures rider bobbing, and outputs files into `public/assets/64/player/mount/<mount_name>/`.

### 3. AI Generation Pipeline (PixelLab API)
- API Keys stored in `.env` (copy from `.env.example`).
- Script `scripts/pixellab-route.py` balances generations across keys.
- Script `scripts/gen_neve.py` demonstrates full biome generation (tilesets, trees, monsters, hero skin).

---

## 🛠️ Key Engine Components (`public/shared/engine.js`)

- **`RPGLab.FreeWalker`**: Free-form movement with AABB circle collision sliding against walls (`walkablePx`).
- **`RPGLab.HomeWanderer`**: Elastic tether AI for NPCs/Monsters wandering near their spawn point.
- **`RPGLab.GridWalker`**: Grid-based movement (Tibia tile-by-tile style).
- **`RPGLab.Joystick` & `RPGLab.ActionButton`**: Virtual touch UI for mobile support.

---

## 📑 Documentation References

- **Full Frontend Documentation**: [`docs/FRONTEND.md`](docs/FRONTEND.md)
- **Autotiling & Map Recipe Guide**: [`docs/TILES.md`](docs/TILES.md)
- **Asset Licenses & Credits**: [`CREDITS.md`](CREDITS.md)
