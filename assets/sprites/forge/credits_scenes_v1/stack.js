// 세 장을 실제 게임 크기 그대로 위아래로 배치한다.
const { join } = require("node:path");
const { homedir } = require("node:os");
const P = require(join(homedir(), ".codex/skills/codixel/core/pixel.js"));

const plates = [1, 2, 3].map((scene) => P.load(join(__dirname, "credits_" + scene + ".png")));
P.save(P.sheet(plates, { cols: 1, scale: 1, gap: 0 }), join(__dirname, "sheet_1x.png"));
