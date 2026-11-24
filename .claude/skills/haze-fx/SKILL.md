---
name: haze-fx
description: 헤이즈의 전투 이펙트(타격 불꽃, 폭발, 베기 궤적, 고리, 먼지, 궁극기 연출)를 새로 만들거나 고칠 때 쓰는 제작 절차. tools/fxkit.py로 색 시트와 빛 시트를 굽고, 모아 보기 그림을 눈으로 보며 세 번 이상 고친다. "이펙트가 블록 같다", "이나리처럼", "타격감 이펙트", 새 기술의 이펙트가 필요할 때 쓴다. 실행 중 사각형(draw_rect_color)으로 이펙트를 그리려는 순간에도 먼저 이 스킬을 본다.
---

# haze-fx: 이펙트 제작

2026-11-24 사용자 요청으로 만들었다. 방식은 patch-gg/pixelfx(MIT)와 Hugo Duprez의 Sprite Fusion VFX 글에서 배웠고,
코드·결과물은 가져오지 않았다(전부 자체 구현, `docs/REFERENCES.md`). 목표 화풍은 INARI.

**이펙트는 반드시 이 절차로 만든다 (2026-11-24 사용자 지적).** 장면마다 납작한 도형을 한 장씩 찍거나(도장), 실행 중 사각형으로
그리면 품질이 떨어진다: 불티·조각·빛이 시간에 따라 흐르지 않기 때문이다. 급해도 create(o)에 시간·입자·빛을 넣고 모아 보기를 세 번 본다.

## 1. 기준 (이펙트 하나가 통과해야 하는 것)
1. **작은 타격은 선과 빛으로, 큰 일격은 진한 색 면으로.** 평타·불꽃은 1~3px 줄기·고리·불티·가시로 만들고 밝기는 빛 층이 맡는다.
   대시 베기·처형·궁극기 같은 큰 일격은 **진한 원래 색의 큰 면**(원반·네 갈래 별·초승달)이 주인공이고, 흰색은 가운데 작은 별·불티·빛줄기뿐이다
   (사용자: "흰색보다 진한 원래 색의 영역이 더 크다"). 큰 면은 민짜로 두지 않는다: 한 단계 밝은 테두리, 안쪽의 끊어진 가는 고리, 둘레 빛.
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

## 1-2. 도형으로 그리지 않는다: 불규칙한 픽셀 입자로 구성한다 (2026-11-24 사용자 지적, 가장 중요)
"뾰족뾰족이나 동그라미 같은, 파이썬으로 짠 도형 느낌"이 나면 실패다. pixelfx의 폭발도 원반·가시를 그리지 않는다:
**식어 가는 작은 불덩이 입자 수십~수백 개**가 겹쳐 몸통이 되고, 한 방향으로 줄지어 쏜 불덩이가 혀가 되고, 비슷한 속도로 퍼진 작은
불덩이가 들쭉날쭉한 띠(고리)가 된다. 우리 도구도 같다:
- **몸통** = `FLAME` 수십 개 (크기·속도·수명을 넓게 흩는다). `Particles.cool_pow`를 올리면 오래 뜨겁다(금방 검붉어지면 탁하다).
- **터지는 순간의 흰 덩어리** = 흰색 위주 색 띠(`ramp=`)를 준 큰 `FLAME` 열댓 개. `disc`·`needle`로 흰 별을 그리지 않는다.
- **가시·혀** = 한 방향으로 `FLAME`을 촘촘히(겹치게) 줄지어 쏜다. 듬성듬성하면 구슬 꿴 것처럼 보인다.
- **고리** = 작은 `FLAME` 백여 개를 각도는 무작위, 속도는 비슷하게. 각도를 고르게 나누면 목걸이처럼 보인다.
- **파편** = `CHUNK`(불규칙한 2~4칸 픽셀 덩어리)와 `SPARK`. **모이는 기운** = `STREAK`(점점 빨라지는 점선).
- 덩이 모양은 `p.blob`(각도마다 반지름이 다른 울퉁불퉁한 원). 눈에 보이는 큰 모양에 `disc`·`ring`·`needle`을 그대로 쓰지 않는다
  (1~2px 선·작은 반짝임에는 써도 된다). 또렷한 원 모양 빛(`glow_ring`)도 도형으로 읽힌다: 번지는 둥근 빛(`glow`·`Lights`)만 쓴다.
- 본보기: `make_fx2.py`의 `over_create`(오버로드 폭발)·`gather_create`(모이는 기운).

## 2. 절차
1. **참고를 본다.** 사용자가 준 영상·그림이 있으면 프레임별로 본다(브라우저로 프레임을 모아 본다). 없으면 비슷한 기존 이펙트의 모아 보기.
2. **한 줄로 말한다.** "흰 십자 섬광 → 가는 줄기 8개와 끊어진 고리 → 불티가 떨어지며 식는다"처럼. 이 문장이 create 함수의 주석이 된다.
3. **`tools/make_fx2.py`에 meta + create를 쓴다** (아래 3절).
4. **굽고 본다**: `python tools/make_fx2.py --look <이름>` → `shots/fx/<이름>.png` (게임 파일은 그대로). Read로 그림을 본다.
5. **가장 어색한 것 하나를 고치고 다시 본다. 세 번 이상.** 큰 폭발은 가는 선의 고리만으로는 "터진다"는 느낌이 없다(오버로드 반려):
   첫 두세 장에 꽉 찬 흰 덩어리, 이어서 꽉 찬 색 면이 부풀어야 한다. 자주 나오는 것: 빛이 원반처럼 뭉침(glow k 합이 255를 넘음),
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
- **휘두르기 초승달·가로 베기·회전 베기는 `tools/make_slash_hq.py`의 예전 그림을 쓴다.** fxkit으로 다시 구운 판(`make_fx2.py`의 SLASHES·SPINS)은
  사용자가 반려했다(2026-11-24: "초승달이 아니라 찌그러지고, 빛나는 효과가 사라져 밋밋하다"). 교훈: 잘 되어 있던 것을 화풍을 맞춘다고 통째로
  바꾸지 않는다. 바꾸려면 예전 그림과 나란히 놓고 모양·빛이 더 나은지 먼저 본다(기준 6의 '주인공 옆'처럼 '예전 것 옆').
- 먼지·연기·솟는 기운·바닥 충격·소멸(`MISC`), 궁극기 광역 폭발 ult-nova 5종과 오버로드 폭발(헤이즈 폭발을 색·크기 `k`로).
- 큰 마무리(처형·궁극기, `weapon.FinisherCut`): `fin-burst`(가시 -> 작은 원반 -> 큰 별 -> 진한 원반 -> 고리 -> 토막, 0.54초 16장)와
  `exec-crescent`(예고 초승달 5장). 화면 전체를 가르는 빛줄기·검은 띠·실루엣만 게임이 그린다. 별 섬광 `flare`·`flare-s`.
- 오버로드: `overload-gather`(기운이 모임) -> `overload-burst`(입자로만 만든 폭발). 게임에서는 `effects.OverloadPop`이 실제 시간으로 재생하고
  `src/postfx.py`가 화면을 당기고(zoom) 번지게(방사 블러) 하고 일렁이게(wobble) 한다. 큰 연출에 화면 왜곡이 필요하면 `postfx.play(keys, 화면x, 화면y)`.
- **도형으로 만든 채 남아 있는 것(입자 구성으로 다시 만들 대상)**: 타격 불꽃 hit-*(십자·가시·고리), haze-blast·ult-nova(가시·고리), 충격 방사선·고리·베기 자국,
  바닥 충격·소멸, 처형 fin-burst(원반·네 갈래 별), 별 섬광 flare.
- 아직 예전 방식: dash-strike(창 모양)·shockwave(보스 충격파, 반복)·오라(make_aura.py),
  실행 중 사각형 이펙트(effects.py의 PathSlash·LightPillar·ground_slam·처치 연출 KillSlash, weapon.py의 RushTrail·표식·사슬). DashStreak는 사용자가 마음에 들어 해 그대로.
