# 주인공 공격 v3 키포인트 생성기
# 손(파이프 쥔 앞손) 경로, 파이프 방향, 몸 자세를 프레임마다 정하고 2관절 IK로 팔꿈치를 계산한다.
# 결과: <동작>.json (keypoints 8프레임), tips.json (계획한 파이프 끝 좌표, 0~1)
import json, math, os
D = os.path.dirname(os.path.abspath(__file__))
BASE = {"NOSE": (0.5621, 0.4107), "NECK": (0.4982, 0.4648), "RIGHT SHOULDER": (0.5339, 0.4605), "RIGHT ELBOW": (0.5642, 0.5384),
        "RIGHT ARM": (0.6638, 0.5947), "LEFT SHOULDER": (0.4625, 0.4692), "LEFT ELBOW": (0.3823, 0.5038), "LEFT ARM": (0.3564, 0.5601),
        "RIGHT HIP": (0.5382, 0.6359), "RIGHT KNEE": (0.5642, 0.781), "RIGHT LEG": (0.5837, 0.9282), "LEFT HIP": (0.5079, 0.638),
        "LEFT KNEE": (0.4906, 0.7788), "LEFT LEG": (0.4365, 0.9195), "RIGHT EYE": (0.5599, 0.3977), "LEFT EYE": (0.5512, 0.3977),
        "RIGHT EAR": (0.5404, 0.3955), "LEFT EAR": (0.5253, 0.3955)}
UPPER = ["NOSE", "NECK", "RIGHT SHOULDER", "LEFT SHOULDER", "RIGHT EYE", "LEFT EYE", "RIGHT EAR", "LEFT EAR"]
L1, L2, PIPE = 0.083, 0.112, 0.27


def ik(S, H, down=True):
    dx, dy = H[0] - S[0], H[1] - S[1]
    d = math.hypot(dx, dy)
    d2 = min(max(d, 0.04), L1 + L2 - 0.004)
    if d2 != d:
        H = (S[0] + dx / d * d2, S[1] + dy / d * d2)
    a = math.atan2(dy, dx)
    c = (L1 * L1 + d2 * d2 - L2 * L2) / (2 * L1 * d2)
    b = math.acos(max(-1, min(1, c)))
    e1 = (S[0] + L1 * math.cos(a + b), S[1] + L1 * math.sin(a + b))
    e2 = (S[0] + L1 * math.cos(a - b), S[1] + L1 * math.sin(a - b))
    E = e1 if (e1[1] >= e2[1]) == down else e2
    return E, H


def frame(hand, ang, body=(0, 0), lean=0.0, legs="stand", k=0.0, plen=1.0):
    ox, oy = body
    P = {}
    for n, (x, y) in BASE.items():
        P[n] = (x + ox + (lean if n in UPPER else 0), y + oy)
    rh, lh = P["RIGHT HIP"], P["LEFT HIP"]
    if legs == "stand":
        P["RIGHT KNEE"] = (BASE["RIGHT KNEE"][0] + ox, BASE["RIGHT KNEE"][1] + oy * 0.5)
        P["RIGHT LEG"] = (BASE["RIGHT LEG"][0] + ox, 0.928)
        P["LEFT KNEE"] = (BASE["LEFT KNEE"][0] + ox, BASE["LEFT KNEE"][1] + oy * 0.5)
        P["LEFT LEG"] = (BASE["LEFT LEG"][0] + ox, 0.92)
    elif legs == "lunge":
        P["RIGHT KNEE"] = (rh[0] + 0.06 + 0.04 * k, rh[1] + 0.12)
        P["RIGHT LEG"] = (rh[0] + 0.08 + 0.06 * k, 0.928)
        P["LEFT KNEE"] = (lh[0] - 0.05 - 0.03 * k, lh[1] + 0.14)
        P["LEFT LEG"] = (lh[0] - 0.12 - 0.06 * k, 0.92)
    elif legs == "crouch":
        P["RIGHT KNEE"] = (rh[0] + 0.08, rh[1] + 0.10)
        P["RIGHT LEG"] = (rh[0] + 0.05, 0.928)
        P["LEFT KNEE"] = (lh[0] - 0.01, lh[1] + 0.12)
        P["LEFT LEG"] = (lh[0] - 0.09, 0.92)
    elif legs == "air":
        P["RIGHT KNEE"] = (rh[0] + 0.08, rh[1] + 0.07)
        P["RIGHT LEG"] = (rh[0] + 0.03, rh[1] + 0.15)
        P["LEFT KNEE"] = (lh[0] + 0.03, lh[1] + 0.10)
        P["LEFT LEG"] = (lh[0] - 0.05, lh[1] + 0.17)
    elif legs == "kneel":
        P["RIGHT KNEE"] = (rh[0] + 0.09, rh[1] + 0.08)
        P["RIGHT LEG"] = (rh[0] + 0.08, 0.928)
        P["LEFT KNEE"] = (lh[0] - 0.02, 0.905)
        P["LEFT LEG"] = (lh[0] - 0.13, 0.925)
    # 뒷팔: 기준 그림과 같은 상대 위치
    LS = P["LEFT SHOULDER"]
    P["LEFT ELBOW"] = (LS[0] - 0.080, LS[1] + 0.035)
    P["LEFT ARM"] = (LS[0] - 0.106, LS[1] + 0.091)
    # 앞팔(파이프)
    S = P["RIGHT SHOULDER"]
    E, H = ik(S, (S[0] + hand[0], S[1] + hand[1]), down=hand[1] > -0.05)
    P["RIGHT ELBOW"], P["RIGHT ARM"] = E, H
    a = math.radians(ang)
    tip = (H[0] + PIPE * plen * math.cos(a), H[1] + PIPE * plen * math.sin(a))
    kp = [{"label": n, "x": round(min(max(x, 0.01), 0.99), 3), "y": round(min(max(y, 0.01), 0.99), 3)} for n, (x, y) in P.items()]
    return kp, tip


R = (0.13, 0.135, -63)  # 기준 자세의 손 위치·파이프 각도


def rd(**kw):
    return (R[0], R[1], R[2], kw)


AIR = dict(legs="air")
M = {
    # A 땅
    "g1": [rd(), (-0.10, 0.03, 180, {}), (-0.14, 0.02, 178, dict(lean=-0.02)), (0.00, 0.06, 100, dict(plen=0.35, body=(0.01, 0))),
           (0.17, 0.06, 0, dict(body=(0.03, 0), legs="lunge", k=0.3)), (0.17, 0.11, 20, dict(body=(0.03, 0), legs="lunge", k=0.3)),
           (0.15, 0.14, 35, dict(body=(0.02, 0))), rd()],
    "g2": [rd(), (-0.02, -0.12, -110, {}), (-0.05, -0.16, -135, dict(lean=-0.02)), (0.08, -0.13, -60, {}), (0.17, -0.03, 0, dict(body=(0.02, 0.01))),
           (0.15, 0.12, 60, dict(body=(0.03, 0.02), legs="lunge", k=0.4)), (0.12, 0.15, 75, dict(body=(0.02, 0.02))), rd()],
    "g3": [rd(), (-0.12, 0.05, 180, dict(lean=-0.03)), (-0.06, 0.07, 150, dict(plen=0.6)), (0.04, 0.06, 100, dict(plen=0.35, body=(0.02, 0))),
           (0.18, 0.05, 0, dict(body=(0.04, 0), legs="lunge", k=0.6)), (0.17, 0.03, -12, dict(body=(0.04, 0), legs="lunge", k=0.6)),
           (0.04, 0.08, 160, dict(plen=0.6, body=(0.02, 0))), rd()],
    "up": [rd(), (0.10, 0.16, 70, dict(body=(0, 0.03), legs="crouch")), (0.05, 0.19, 100, dict(body=(0, 0.04), legs="crouch")),
           (0.15, 0.09, 20, dict(body=(0.01, 0.02))), (0.12, -0.10, -60, {}), (0.04, -0.17, -95, dict(body=(0, -0.01))), (0.02, -0.15, -110, {}), rd()],
    "low": [rd(), (-0.10, 0.16, 175, dict(body=(0, 0.05), legs="crouch")), (-0.13, 0.17, 172, dict(body=(0, 0.06), legs="crouch")),
            (0.02, 0.19, 120, dict(plen=0.4, body=(0.01, 0.06), legs="crouch")), (0.17, 0.17, 8, dict(body=(0.02, 0.06), legs="crouch")),
            (0.18, 0.15, 12, dict(body=(0.02, 0.06), legs="crouch")), (0.15, 0.15, 25, dict(body=(0.01, 0.04), legs="crouch")), rd()],
    "dash": [rd(), (-0.10, 0.08, 178, dict(body=(0.02, 0.04), legs="lunge", k=0.5, lean=0.02)), (-0.12, 0.08, 175, dict(body=(0.06, 0.05), legs="lunge", k=0.8, lean=0.03)),
             (0.02, 0.10, 110, dict(plen=0.4, body=(0.10, 0.05), legs="lunge", k=1)), (0.17, 0.09, 3, dict(body=(0.13, 0.05), legs="lunge", k=1)),
             (0.17, 0.12, 15, dict(body=(0.14, 0.05), legs="lunge", k=1)), (0.15, 0.14, 30, dict(body=(0.12, 0.03), legs="lunge", k=0.6)),
             (R[0], R[1], R[2], dict(body=(0.10, 0)))],
    # B 공중
    "air1": [(R[0], R[1], R[2], AIR), (-0.10, 0.02, 180, AIR), (-0.14, 0.01, 178, dict(legs="air", lean=-0.02)), (0.00, 0.05, 100, dict(plen=0.35, legs="air")),
             (0.17, 0.05, 0, AIR), (0.17, 0.10, 20, AIR), (0.14, 0.13, 35, AIR), (R[0], R[1], R[2], AIR)],
    "air2": [(R[0], R[1], R[2], AIR), (-0.10, 0.10, 150, AIR), (-0.10, -0.10, -145, dict(legs="air", lean=-0.02)), (0.02, -0.17, -95, AIR),
             (0.15, -0.09, -30, AIR), (0.17, 0.06, 30, AIR), (0.06, 0.17, 95, AIR), (R[0], R[1], R[2], AIR)],
    "air_up": [(R[0], R[1], R[2], AIR), (0.10, 0.15, 70, AIR), (0.06, 0.18, 100, AIR), (0.15, 0.08, 20, AIR),
               (0.12, -0.10, -60, AIR), (0.04, -0.17, -95, AIR), (0.02, -0.15, -110, AIR), (R[0], R[1], R[2], AIR)],
    "air_down": [(R[0], R[1], R[2], AIR), (0.03, -0.14, -90, AIR), (0.04, -0.17, -95, dict(legs="air", lean=-0.01)), (0.12, -0.03, 40, AIR),
                 (0.10, 0.15, 90, AIR), (0.10, 0.17, 90, AIR), (0.10, 0.16, 88, AIR), (0.10, 0.15, 85, AIR)],
    # C E 강화·증강
    "e1": [rd(), (0.00, -0.15, -120, {}), (0.16, 0.11, 55, dict(body=(0.02, 0.01), legs="lunge", k=0.3)), (0.10, 0.16, 90, dict(body=(0.02, 0.02))),
           (-0.03, 0.15, 150, dict(body=(0.01, 0.02))), (0.15, -0.09, -50, dict(body=(0.03, 0), legs="lunge", k=0.4)), (0.13, -0.06, -40, dict(body=(0.02, 0))), rd()],
    "e2_rise": [rd(), (0.10, 0.17, 70, dict(body=(0, 0.05), legs="crouch")), (0.05, 0.19, 100, dict(body=(0, 0.06), legs="crouch")),
                (0.16, 0.07, 15, dict(body=(0.01, 0.0))), (0.13, -0.11, -60, dict(body=(0.01, -0.03))), (0.03, -0.18, -98, dict(body=(0, -0.05), legs="air")),
                (0.01, -0.17, -112, dict(body=(0, -0.05), legs="air")), (0.02, -0.15, -105, dict(body=(0, -0.04), legs="air"))],
    "e2_slam": [(0.02, -0.15, -105, dict(body=(0, -0.04), legs="air")), (-0.03, -0.17, -130, dict(body=(0, -0.05), legs="air", lean=-0.02)),
                (0.06, -0.15, -70, dict(body=(0.01, -0.03), legs="air")), (0.17, -0.04, 0, dict(body=(0.02, 0))),
                (0.15, 0.13, 65, dict(body=(0.03, 0.06), legs="crouch")), (0.13, 0.17, 80, dict(body=(0.03, 0.07), legs="crouch")),
                (0.12, 0.17, 82, dict(body=(0.02, 0.06), legs="crouch")), rd()],
    "ult": [rd(), (-0.02, -0.13, -120, {}), (0.16, 0.10, 50, dict(body=(0.02, 0.01), legs="lunge", k=0.3)), (-0.11, 0.05, 180, dict(body=(0.01, 0.01))),
            (0.18, 0.05, 0, dict(body=(0.04, 0.01), legs="lunge", k=0.6)), (0.05, 0.18, 110, dict(body=(0.03, 0.04), legs="crouch")),
            (0.10, -0.14, -80, dict(body=(0.03, -0.01))), rd()],
    "combo4": [rd(), (0.02, 0.03, 180, dict(plen=0.8, lean=0.01)), (-0.01, 0.02, 182, dict(plen=0.8, lean=0.02)), (0.08, 0.00, 120, dict(plen=0.35, body=(0.02, 0))),
               (0.18, -0.01, -4, dict(body=(0.04, 0), legs="lunge", k=0.5)), (0.17, -0.03, -15, dict(body=(0.04, 0), legs="lunge", k=0.5)),
               (0.15, 0.06, 10, dict(body=(0.02, 0))), rd()],
    "combo5": [rd(), (-0.13, 0.06, 182, dict(lean=-0.04, body=(-0.01, 0.01))), (-0.07, 0.08, 150, dict(plen=0.6, body=(0, 0.02))),
               (0.04, 0.07, 100, dict(plen=0.3, body=(0.03, 0.02), legs="lunge", k=0.5)), (0.19, 0.05, 0, dict(body=(0.06, 0.02), legs="lunge", k=1)),
               (0.18, 0.02, -15, dict(body=(0.06, 0.02), legs="lunge", k=1)), (0.03, 0.08, 165, dict(plen=0.6, body=(0.04, 0.01))), rd()],
    "quake": [rd(), (0.02, -0.14, -95, dict(body=(0, -0.03), legs="air")), (0.00, -0.17, -100, dict(body=(0, -0.04), legs="air")),
              (0.12, -0.02, 20, dict(body=(0.01, 0.0))), (0.14, 0.20, 88, dict(body=(0.03, 0.08), legs="kneel")), (0.14, 0.20, 88, dict(body=(0.03, 0.08), legs="kneel")),
              (0.14, 0.19, 86, dict(body=(0.03, 0.08), legs="kneel")), (0.13, 0.17, 80, dict(body=(0.02, 0.05), legs="crouch"))],
    "flash": [rd(), (-0.06, 0.12, 160, dict(body=(0, 0.05), legs="crouch", lean=-0.01)), (-0.07, 0.12, 162, dict(body=(0, 0.06), legs="crouch")),
              (0.10, 0.07, 10, dict(body=(0.10, 0.05), legs="lunge", k=1)), (0.18, 0.04, 0, dict(body=(0.16, 0.05), legs="lunge", k=1)),
              (0.16, 0.10, 30, dict(body=(0.18, 0.05), legs="lunge", k=0.8)), (0.15, 0.12, 35, dict(body=(0.18, 0.04), legs="lunge", k=0.6)),
              (0.15, 0.12, 35, dict(body=(0.18, 0.04), legs="lunge", k=0.6))],
}

if __name__ == "__main__":
    tips = {}
    for name, frames in M.items():
        kps, tp = [], []
        for hx, hy, ang, kw in frames:
            kp, tip = frame((hx, hy), ang, **kw)
            kps.append(kp)
            tp.append([round(tip[0], 3), round(tip[1], 3)])
        json.dump(kps, open(os.path.join(D, name + ".json"), "w"), separators=(",", ":"))
        tips[name] = tp
    json.dump(tips, open(os.path.join(D, "tips.json"), "w"))
    print("ok", list(M))
