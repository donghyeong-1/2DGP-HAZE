// 실제 스프라이트 픽셀 그대로 동작별 한 줄에서 비교한다.
const { join } = require("node:path");
const { homedir } = require("node:os");
const P = require(join(homedir(), ".codex/skills/codixel/core/pixel.js"));

const actions = { roll: 4, arm: 3, hurt: 2, wreck: 2 };
const entries = Object.entries(actions).flatMap(([action, count]) =>
  Array.from({ length: 4 }, (_, i) => i < count
    ? { buf: P.load(join(__dirname, "frames", action + "-" + (i + 1) + ".png")), label: action + "-" + (i + 1) }
    : { buf: new P.Buf(160, 122) })
);
P.save(P.sheet(entries, {
  cols: 4, gap: 6, scale: 1, labelScale: 1,
  bg: [19, 24, 35], check: [[49, 59, 70], [42, 52, 64]],
}), join(__dirname, "comparison_1x.png"));
