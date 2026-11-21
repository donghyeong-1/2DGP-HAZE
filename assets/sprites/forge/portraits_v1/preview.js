// 게임 대기 스프라이트와 초상화를 같은 픽셀 배율로 확인한다.
const { join } = require("node:path");
const { homedir } = require("node:os");
const P = require(join(homedir(), ".codex/skills/codixel/core/pixel.js"));

const sprites = join(__dirname, "../../unified");
const expressions = {
  n09: ["NEUTRAL", "DETERMINED"],
  mechanic: ["GRUFF", "SMIRK"],
  keeper: ["CALM", "WORRIED"],
  archivist: ["THINKING", "STARTLED"],
};
const entries = Object.entries(expressions).flatMap(([actor, labels]) => {
  const basename = actor === "n09" ? actor : "npc_" + actor;
  const idle = P.load(join(sprites, basename + "_idle_1.png"));
  const cell = new P.Buf(128, 200);
  cell.sprite(idle, Math.floor((cell.w - idle.w) / 2), Math.floor((cell.h - idle.h) / 2));
  return [
    { buf: cell, label: actor.toUpperCase() + " GAME 1X" },
    ...labels.map((label, index) => ({
      buf: P.load(join(__dirname, actor + "_" + (index + 1) + ".png")),
      label,
    })),
  ];
});
const sheet = P.sheet(entries, {
  cols: 3, gap: 10, scale: 1, labelScale: 1,
  bg: [15, 22, 35], check: [[48, 59, 70], [42, 52, 64]],
});
P.save(sheet, join(__dirname, "sheet_1x.png"));
