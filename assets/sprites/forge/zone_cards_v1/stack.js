// 장별 원본 크기를 유지한 세로 비교판.
const { join } = require("node:path");
const { homedir } = require("node:os");
const P = require(join(homedir(), ".codex/skills/codixel/core/pixel.js"));

const cards = ["cell", "foundry", "haze"].map((theme) =>
  P.load(join(__dirname, "zone_" + theme + ".png"))
);
P.save(P.sheet(cards, { cols: 1, scale: 1, gap: 0 }), join(__dirname, "sheet_1x.png"));
