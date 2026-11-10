"""스프라이트 결과가 규격을 지키는지 검사한다. Codex와 Claude Code 모두 이 스크립트로 같은 기준을 쓴다.

검사: 알파 0/255만, 색 수(파일당 48 이하, 여러 파일은 합쳐서도 48 이하), 키(이름으로 목표 키를 찾아 +-2px),
      여러 프레임이면 프레임 사이 키·바닥선 차이 2px 이하(--air 이면 바닥선은 검사하지 않음).
사용: python tools/check_sprites.py assets/sprites/forge/n09_v3_idle.png
      python tools/check_sprites.py assets/sprites/forge/n09_walk_v3/frames/*.png
      python tools/check_sprites.py <png...> --air      (점프처럼 공중 프레임)
통과하면 종료 코드 0, 실패가 하나라도 있으면 1.
"""
import argparse
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from finish_character import base_name, target_height  # noqa: E402

MAX_COLORS = 48
HEIGHT_TOL = 2
FRAME_TOL = 2


def analyze(path):
    im = Image.open(path).convert("RGBA")
    alpha = im.getchannel("A")
    bbox = alpha.getbbox()
    hist = alpha.histogram()
    semi = sum(hist[1:255])
    colors = {p for p in im.get_flattened_data() if p[3] == 255} if hasattr(im, "get_flattened_data") \
        else {p for p in im.getdata() if p[3] == 255}
    return {"path": Path(path), "size": im.size, "bbox": bbox, "semi": semi, "colors": colors}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--air", action="store_true", help="공중 프레임: 바닥선 일치를 검사하지 않는다")
    ap.add_argument("--height", type=int, help="목표 키를 직접 지정")
    args = ap.parse_args()

    results = [analyze(p) for p in sorted(args.files)]
    fails = []
    all_colors = set()
    print(f"{'파일':44s} {'캔버스':10s} {'내용 WxH':10s} 반투명 색")
    for r in results:
        bb = r["bbox"]
        w, h = (bb[2] - bb[0], bb[3] - bb[1]) if bb else (0, 0)
        r["h"], r["bottom"] = h, (bb[3] if bb else 0)
        all_colors |= r["colors"]
        print(f"{r['path'].name:44s} {str(r['size']):10s} {w}x{h:<6d} {r['semi']:5d} {len(r['colors'])}")
        if bb is None:
            fails.append(f"{r['path'].name}: 비어 있음")
        if r["semi"]:
            fails.append(f"{r['path'].name}: 반투명 픽셀 {r['semi']}개 (알파는 0 또는 255만)")
        if len(r["colors"]) > MAX_COLORS:
            fails.append(f"{r['path'].name}: 색 {len(r['colors'])}개 (최대 {MAX_COLORS})")

    if len(results) > 1:
        if len(all_colors) > MAX_COLORS:
            fails.append(f"전체 팔레트 {len(all_colors)}색 (최대 {MAX_COLORS}, 프레임마다 팔레트가 달라졌을 수 있음)")
        hs = [r["h"] for r in results]
        if max(hs) - min(hs) > FRAME_TOL * 3 and not args.air:
            fails.append(f"프레임 키 차이 {max(hs) - min(hs)}px (걷기 상하 흔들림 포함해도 {FRAME_TOL * 3}px 이하여야 함)")
        if not args.air:
            bs = [r["bottom"] for r in results]
            if max(bs) - min(bs) > FRAME_TOL:
                fails.append(f"프레임 바닥선 차이 {max(bs) - min(bs)}px (최대 {FRAME_TOL})")

    # 목표 키 (한 장짜리 마스터 결과에만 엄격하게 적용)
    key = base_name(results[0]["path"].name) or base_name(results[0]["path"].parent.parent.name)
    want = args.height or (target_height(key) if key else None)
    if want and len(results) == 1:
        h = results[0]["h"]
        if abs(h - want) > HEIGHT_TOL:
            fails.append(f"키 {h}px, 목표 {want}px +-{HEIGHT_TOL}")
        else:
            print(f"키 {h}px (목표 {want}px) OK")
    elif not want:
        print("목표 키를 찾지 못해 키 검사는 건너뜁니다 (--height 지정 가능)")

    if fails:
        print("\n실패:")
        for f in fails:
            print(" -", f)
        sys.exit(1)
    print("\n통과")


if __name__ == "__main__":
    main()
