# air_down2: 수직 내리꽂기. gen_v3.py의 frame()/IK를 그대로 쓰고, 다리를 높이 접는 "tuck" 자세를 더한다.
# 0~1 머리 위로 들기, 2 손이 가슴 높이로 내려오며 파이프는 위·뒤, 3~7 손은 허리 앞, 파이프는 수직 아래.
# 몸을 위로 올려(oy -0.10~-0.12) 파이프 끝이 캔버스 안에 들어오게 한다.
import json, os
import gen_v3 as G

_orig = G.frame


def frame_tuck(hand, ang, body=(0, 0), lean=0.0, legs="stand", k=0.0, plen=1.0):
    if legs != "tuck":
        return _orig(hand, ang, body=body, lean=lean, legs=legs, k=k, plen=plen)
    kp, tip = _orig(hand, ang, body=body, lean=lean, legs="air", k=k, plen=plen)
    P = {j["label"]: (j["x"], j["y"]) for j in kp}
    rh, lh = P["RIGHT HIP"], P["LEFT HIP"]
    P["RIGHT KNEE"] = (rh[0] + 0.07, rh[1] + 0.02)
    P["RIGHT LEG"] = (rh[0] + 0.02, rh[1] + 0.08)
    P["LEFT KNEE"] = (lh[0] + 0.04, lh[1] + 0.04)
    P["LEFT LEG"] = (lh[0] - 0.02, lh[1] + 0.10)
    kp = [{"label": n, "x": round(x, 3), "y": round(y, 3)} for n, (x, y) in P.items()]
    return kp, tip


R = G.R
AIR = dict(legs="air")
frames = [
    (R[0], R[1], R[2], AIR),
    (0.03, -0.14, -90, AIR),
    (0.06, 0.02, -120, dict(legs="air", lean=0.01)),
    (0.04, 0.16, 90, dict(body=(0, -0.07), legs="tuck", lean=0.02)),
    (0.02, 0.19, 90, dict(body=(0, -0.09), legs="tuck", lean=0.02)),
    (0.02, 0.19, 90, dict(body=(0, -0.09), legs="tuck", lean=0.02)),
    (0.02, 0.19, 90, dict(body=(0, -0.09), legs="tuck", lean=0.02)),
    (0.02, 0.19, 90, dict(body=(0, -0.08), legs="tuck", lean=0.02)),
]
kps, tips = [], []
for hx, hy, ang, kw in frames:
    kp, tip = frame_tuck((hx, hy), ang, **kw)
    kps.append(kp)
    tips.append([round(tip[0], 3), round(tip[1], 3)])
D = os.path.dirname(os.path.abspath(__file__))
json.dump(kps, open(os.path.join(D, "air_down2.json"), "w"), separators=(",", ":"))
t = json.load(open(os.path.join(D, "tips.json")))
t["air_down2"] = tips
json.dump(t, open(os.path.join(D, "tips.json"), "w"))
for i, (kp, tp) in enumerate(zip(kps, tips)):
    P = {j["label"]: j for j in kp}
    sole = max(P["RIGHT LEG"]["y"], P["LEFT LEG"]["y"])
    print(i, "hand", (P["RIGHT ARM"]["x"], P["RIGHT ARM"]["y"]), "tip", tp, "tip below sole px %.0f" % ((tp[1] - sole) * 96))
print(json.dumps(kps, separators=(",", ":")))
