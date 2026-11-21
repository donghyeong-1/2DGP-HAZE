// 카드 두 장을 확대·축소 없이 위아래로 놓는다.
const { join } = require("node:path");
const { homedir } = require("node:os");
const P = require(join(homedir(), ".codex/skills/codixel/core/pixel.js"));

const cards = ["crasher", "ark"].map((boss) =>
  P.load(join(__dirname, "boss_card_" + boss + ".png"))
);
P.save(P.sheet(cards, { cols: 1, scale: 1, gap: 0 }), join(__dirname, "sheet_1x.png"));
