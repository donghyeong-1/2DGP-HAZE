// 소품별 세 상태를 같은 바닥선과 1배 크기로 놓는다.
const { join } = require("node:path");
const { homedir } = require("node:os");
const P = require(join(homedir(), ".codex/skills/codixel/core/pixel.js"));
const specs = {
  scrap_pillar: ["FALLING", "PLANTED", "CRUMBLING"],
  steam_valve: ["OPEN / STEAM", "STRUCK", "CLOSED"],
  furnace_vent: ["OFF", "WARNING", "IMMINENT"],
  crystal_pillar: ["RISING", "STANDING", "BREAKING"],
};
const tiles = Object.entries(specs).flatMap(([prop, labels]) => labels.map((label, i) => {
  const art = P.load(join(__dirname, prop, (i+1) + ".png"));
  const cell = new P.Buf(190, art.h);
  cell.sprite(art, Math.floor((cell.w-art.w)/2), 0);
  return { buf: cell, label: prop.replace("_"," ").toUpperCase() + " / " + label };
}));
P.save(P.sheet(tiles, {
  cols: 3, gap: 6, labelScale: 1, scale: 1,
  bg: [20,26,37], check: [[48,58,68],[41,50,62]],
}), join(__dirname, "comparison_1x.png"));
