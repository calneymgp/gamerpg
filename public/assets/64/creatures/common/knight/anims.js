// Auto-generated Phaser 4 sprite config. pixelArt:true in game config!
export function preloadSprites(scene) {
  scene.load.spritesheet('walk-right-q', 'sprites/walk-right-q.png', { frameWidth: 64, frameHeight: 64 });
  scene.load.spritesheet('walk-right', 'sprites/walk-right.png', { frameWidth: 64, frameHeight: 64 });
}

export function createAnims(scene) {
  scene.anims.create({ key: 'walk-right-q', frames: scene.anims.generateFrameNumbers('walk-right-q', { start: 0, end: 7 }), frameRate: 8, repeat: -1 });
  scene.anims.create({ key: 'walk-right', frames: scene.anims.generateFrameNumbers('walk-right', { start: 0, end: 7 }), frameRate: 8, repeat: -1 });
}

// Reverse trick: to walk-while-casting facing right, play a '*-left' anim
//   with setFlipX + reversed frames (anim.msPerFrame<0 or a reversed clone).
