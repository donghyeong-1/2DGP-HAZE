// 모든 동작 프레임을 같은 기준점과 1배 크기로 비교한다.
const { join } = require("node:path");
const { homedir } = require("node:os");
const P = require(join(homedir(), ".codex/skills/codixel/core/pixel.js"));

const groups = [
  ["fly-1", "fly-2", "fly-3", "fly-4"],
  ["aim-1", "aim-2", "fire-1", "fire-2", "fire-3"],
  ["hurt-1", "hurt-2", "death-1", "death-2"],
];
const entries = groups.flatMap((group) => Array.from({ length: 5 }, (_, index) => {
  const id = group[index];
  return id ? { buf: P.load(join(__dirname, "frames", id + ".png")), label: id } :
    { buf: new P.Buf(160, 136) };
}));
P.save(P.sheet(entries, {
  cols: 5, scale: 1, gap: 5, labelScale: 1,
  bg: [19, 24, 35], check: [[48, 59, 70], [42, 52, 64]],
}), join(__dirname, "comparison_1x.png"));
