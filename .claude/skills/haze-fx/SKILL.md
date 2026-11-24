---
name: haze-fx
description: 헤이즈의 전투 이펙트(타격 불꽃, 폭발, 베기 궤적, 고리, 먼지, 궁극기 연출)를 새로 만들거나 고칠 때 쓰는 제작 절차. tools/fxkit.py로 색 시트와 빛 시트를 굽고, 모아 보기 그림을 눈으로 보며 세 번 이상 고친다. "이펙트가 블록 같다", "이나리처럼", "타격감 이펙트", 새 기술의 이펙트가 필요할 때 쓴다. 실행 중 사각형(draw_rect_color)으로 이펙트를 그리려는 순간에도 먼저 이 스킬을 본다.
---

# haze-fx: 이펙트 제작

2026-11-24 사용자 요청으로 만들었다. 방식은 patch-gg/pixelfx(MIT)와 Hugo Duprez의 Sprite Fusion VFX 글에서 배웠고,
코드·결과물은 가져오지 않았다(전부 자체 구현, `docs/REFERENCES.md`). 목표 화풍은 INARI: 흰색이 주, 색은 가장자리와 강조.

## 1. 기준 (이펙트 하나가 통과해야 하는 것)
1. **선과 빛으로 만든다.** 1~3px 줄기·고리·불티·가시. 넓은 단색 면은 터지는 1~2프레임(흰 주인공 프레임)에만 쓴다.
   밝기는 빛 층이 맡는다. 색 층에 큰 원반·사각형·바퀴살 무늬가 보이면 실패다.
2. **단계가 있다.** (모으기) → 터짐: 흰 주인공 프레임 1~2장 → 퍼짐: 줄기·고리가 빠르게 나가 느려진다(out_expo) →
   머무름: 불티·알갱이·파편 → 긴 소멸. 타격은 0.3~0.5초, 큰 폭발은 0.7~1.0초.
3. **진짜 움직임.** 불티는 속도만큼 늘어나고 떨어지고 바닥에서 튄다. 파편은 돌며 날아간다. 빠르게 터지고 천천히 흩어진다(끌림).
4. **사라질 때 점무늬를 쓰지 않는다.** 가늘어지거나, 끊어지거나(gaps), 줄어들거나, 2x2 조각으로 부서진다(`a` 인자). 체크무늬 디더 금지.
5. **고르지 않게.** 줄기 각도·길이·출발 시간을 조금씩 흔든다(각도는 고르게 나눈 뒤 흔든다: 한쪽으로 몰리지 않게). 완전한 원·같은 길이 바퀴살은 기계가 그린 티가 난다.
6. **1배에서 읽힌다.** 주인공(논리 65x61px) 옆에 놓고 크기를 본다. 보통 타격은 주인공 키의 1~1.5배, 강화·폭발은 2~3배.
7. **색은 `fxkit.RAMPS`에서만.** 색 띠 5단(어두움→밝음→흰색). 색 언어: haze 기본 / awake / critical / violet 강화1·사슬 /
   gold 강화2 / crimson 강화3·표식·처형 / mint 쌍권총 / ember 건틀릿 / fade / dust.
8. **규칙.** 색 층은 알파 0/255(칠하는 순간 정해진다), 빛 층만 부드럽다(`assets/light/`, 픽셀 규칙의 빛 층 예외).
   실행 중 회전·확대 없음: 방향이 필요하면 변형(variants)을 미리 굽는다. 난수는 seed로만.

## 2. 절차
1. **참고를 본다.** 사용자가 준 영상·그림이 있으면 프레임별로 본다(브라우저로 프레임을 모아 본다). 없으면 비슷한 기존 이펙트의 모아 보기.
2. **한 줄로 말한다.** "흰 십자 섬광 → 가는 줄기 8개와 끊어진 고리 → 불티가 떨어지며 식는다"처럼. 이 문장이 create 함수의 주석이 된다.
3. **`tools/make_fx2.py`에 meta + create를 쓴다** (아래 3절).
4. **굽고 본다**: `python tools/make_fx2.py --look <이름>` → `shots/fx/<이름>.png` (게임 파일은 그대로). Read로 그림을 본다.
5. **가장 어색한 것 하나를 고치고 다시 본다. 세 번 이상.** 자주 나오는 것: 빛이 원반처럼 뭉침(glow k 합이 255를 넘음),
   공 같은 연기, 너무 고른 원, 가는 선만 있어 힘이 없음(첫 2프레임에 굵은 흰 덩어리가 필요), 끝이 갑자기 끊김.
6. **게임 파일로 굽는다**: `python tools/make_fx2.py <이름>` → `assets/effects/<이름>.png·json`, `assets/light/glow_<이름>.png`.
   json의 `duration`이 있으면 게임이 부르는 쪽 시간 대신 그 시간으로 재생한다(`effects.SheetEffect`).
7. **실제 창에서 본다** (`playtest-capture` 스킬). 캐릭터·배경 위에서 묻히거나 과하지 않은지.
8. `python tests/test_pixel_assets.py`, `docs/ASSETS.md`에 한 줄(code-drawn).

## 3. fxkit 쓰는 법
좌표: (0,0)이 기준점(맞은 자리·발밑), x 오른쪽, **y 아래**. 1 = 논리 픽셀 = 화면 2px. 120Hz로 시뮬레이션, 30fps로 굽는다.

```python
META = dict(size=[88, 88], origin=[44, 44], duration=0.42, fps=30, options=dict(ramp='haze', seed=3))

def create(o):
    R = RAMPS[o['ramp']]; rng = Rng(o['seed'])
    ps = Particles(rng, R, ground=None); lights = Lights()
    lights.add(0, 0, 34, R[2], 95, 0.32)                 # 넓은 바탕 빛
    ps.burst(SPARK, 0, 0, 9, (150, 430), (0.16, 0.36), up=40)
    t = [0.0]
    class Fx:
        def update(self, dt): t[0] += dt; ps.update(dt); lights.update(dt)
        def draw(self, p):
            if t[0] < 0.07: p.disc(0, 0, 5, WHITE)       # 주인공 프레임
            ps.draw(p); lights.draw(p)
    return Fx()
```

| 그리기 (Painter) | 쓰임 |
|---|---|
| `px` `line(x0,y0,x1,y1,c,w)` | 점, 선 |
| `needle(x0,y0,x1,y1,c,w,tip)` | 굵게 시작해 가늘어지는 가시·줄기. 끝 색(tip)은 보통 흰색 |
| `disc` `poly(pts,c)` | 원, 삼각 파편·마름모 |
| `ring(x,y,r,w,c,a,sy,gaps,phase)` | 고리. `sy<1` 바닥에 누운 타원, `gaps` 끊어진 고리 |
| `shade(x0,y0,x1,y1,fn,ramp)` | 칸마다 식으로 그리는 모양(초승달 등): fn(X,Y) → 색 띠 번호 배열 |
| `glow(x,y,r,c,k)` `glow_ring` `glow_line` | 빛 층. k 기준: 바탕 60~110, 터지는 심 120~170, 불티 20~35 |
| 모든 도형의 `a` | 1 미만이면 2x2 조각으로 부서지며 사라진다 |

입자 `Particles(rng, ramp, ground)`: `SPARK`(늘어나는 두 색 불티, 중력·튐·빛) `MOTE`(알갱이) `SHARD`(도는 삼각 파편)
`EMBER`(떠오르는 잿불) `PUFF`(연기 덩이, 작게만). `burst(kind, x, y, n, (속도), (수명), spread, aim, up, size, delay)`.
`Lights().add(x, y, r, color, k, life)`: 번쩍이고 스러지는 빛.

## 4. 실행 중 코드로 그리는 이펙트
`draw_rect_color` 사각형으로 만든 이펙트(고리·방사선·베기 자국·궤적)는 블록처럼 보인다(사용자 지적). 새로 만들 때는 시트로 굽고
`effects.spawn(이름, x, y)`로 띄운다. 길이·방향이 실행 중에 정해지는 것(사슬 줄, 대시 궤적)만 코드로 그리되 2px 칸과 빛 층을 쓴다.

## 5. 지금 있는 것
- v8 시트(`make_fx2.py`): hit-fade·normal·awake·critical·enhanced·enhanced2·enhanced3, haze-blast.
- v8 두 겹 시트(색을 게임이 입힌다, `fxkit.export_tint` + `effects.draw_tint_sheet`): cut-mark·cut-mark-big(8각도, SlashMark), impact-rays·impact-rays-big(8방향, ImpactBurst), shock-ring-s·m·l(ImpactRing). 색이 공격마다 다른 이펙트는 이 방식으로: create(o)에서 `o['layer']`가 'tint'면 회색조(`fxkit.GRAY`) 몸통·빛, 'core'면 흰 심만 그린다.
- 휘두르기 궤적(`make_slash_hq.py`)은 v7에서 이미 흰 초승달 + 청록 가장자리로 만들어 그대로 둔다(사용자가 바꾸자고 하면 fxkit의 shade로).
- 아직 예전 방식: `make_fx.py`의 나머지(puff·surge·quake-blast·death-burst·dust-land·ult-nova·overload-burst 등),
  실행 중 사각형 이펙트(effects.py의 PathSlash·LightPillar·ground_slam·처치 연출, weapon.py의 DashStreak·RushTrail·표식). 순서대로 옮긴다.
