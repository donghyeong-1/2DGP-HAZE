"""T20 원화를 공통 크기로 등록하고 프로젝트 hibit 도구로 마감한다."""
import json
import os
import subprocess
import sys
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parent
FORGE = ROOT.parent
REPO = ROOT.parents[3]
REFERENCE = FORGE / "remake_t01_t03/finished/boss_ark_remake"
ORIGIN = (550, 950)
SIZE = (1400, 1250)
ACTIONS = {
    "A": [
        ("barrage", [0, 1]), ("slash", [2, 3, 4]), ("absorb", [5, 6]),
        ("overcharge", [7, 8]), ("field", [9, 10]),
    ],
    "B": [("idle", [0, 1]), ("walk", [2, 3, 4, 5]), ("vanish", [6]),
          ("appear", [7]), ("hurt", [8])],
    "C": [("phase", [0]), ("death", [1, 2])],
}


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, document):
    path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")


def main():
    group = sys.argv[1]
    folder = ROOT / group
    source = Image.open(folder / "processed/raw-sheet-clean.png").convert("RGBA")
    spec = read_json(folder / "registration_spec.json")
    width = source.width // len(spec["poses"])
    env = dict(os.environ, PYTHONUTF8="1")
    temp = folder / "temp"
    temp.mkdir(exist_ok=True)
    env.update(TEMP=str(temp), TMP=str(temp))
    for action, indices in ACTIONS[group]:
        working = folder / action
        raw = working / "registered"
        raw.mkdir(parents=True, exist_ok=False)
        records = []
        for n, index in enumerate(indices, 1):
            cell = source.crop((index*width, 0, (index+1)*width, source.height))
            point = spec["poses"][index]
            bounds = cell.getchannel("A").point(lambda x: 255 if x >= 128 else 0).getbbox()
            scale = spec["scale"]
            stance = (point["root_x"], bounds[3] - 1)
            shift = (stance[0] - ORIGIN[0]/scale, stance[1] - ORIGIN[1]/scale)
            result = cell.transform(SIZE, Image.Transform.AFFINE,
                                    (1/scale, 0, shift[0], 0, 1/scale, shift[1]),
                                    Image.Resampling.BICUBIC)
            box = result.getbbox()
            assert box[0] > 8 and box[1] > 8 and box[2] < SIZE[0]-8 and box[3] < SIZE[1]-8
            result.save(raw / f"{action}-{n}.png")
            records.append({"frame": n, "sheet_cell": index+1, "source_root": stance,
                            "source_box": bounds, "scale_to_master": scale})
        write_json(raw / "registration.json", {"sourceRoot": ORIGIN, "frames": records})
        name = f"boss_ark_{action}_v1"
        command = [sys.executable, "-B", str(REPO / "tools/finish_character.py"),
                   str(raw), name, "--like", "remake_t01_t03/finished/boss_ark_remake"]
        run = subprocess.run(command, env=env, text=True, encoding="utf-8", capture_output=True)
        (working / "finish_stdout.txt").write_text(run.stdout + run.stderr, encoding="utf-8")
        if run.returncode:
            sys.exit(run.stdout + run.stderr)
        print(run.stdout.strip())
        output = FORGE / name
        metadata = read_json(output / "finish.json")
        automatic = metadata["anchor"]
        root = [round(a+(x-b)*metadata["scale"]) for a, x, b in
                zip(automatic, ORIGIN, metadata["anchorSource"])]
        boundaries = [Image.open(path).getchannel("A").getbbox()[3]
                      for path in (output / "frames").glob("*.png")]
        assert len(set(boundaries)) == 1
        root[1] = boundaries[0]
        metadata["anchorAutomatic"] = automatic
        metadata["anchor"] = root
        metadata["engine"]["sourceAnchor"] = root
        for display in metadata["displaySizes"]:
            if display["label"] == "1x":
                display["anchor"] = root
        metadata["gameRegistration"] = {
            "method": "원화의 허리 기준을 공통 바닥선에 등록. 1배 PNG 재샘플링 없음",
            "sourceRoot": ORIGIN, "finishedRoot": root,
            "registration": str((raw / "registration.json").relative_to(FORGE)).replace(chr(92), "/"),
        }
        write_json(output / "finish.json", metadata)
        print(action, metadata["size"], "anchor", root)


if __name__ == "__main__":
    main()
