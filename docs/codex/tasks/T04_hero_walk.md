# T04 주인공 걷기 프레임 (2×2 시트 4프레임)

먼저 `docs/codex/COMMON.md`를 읽고 그 규칙을 따른다. **앞 작업 T01이 `done`일 때만 시작한다.** (영상 경로가 없어서 이미지 격자 방식으로 한다. 이 방식이 되는지 보는 첫 시험이다.)

## 목표
주인공 v3의 걷기 주기 4프레임을 한 장의 2×2 시트로 만들고, 같은 크기·같은 팔레트로 마무리한다.

## 입력
- 정체성·화풍: `assets/sprites/forge/hero_v3/master/master_rgba.png`
- 크기·색 기준: `assets/sprites/forge/n09_v3/finish.json`, `assets/sprites/forge/n09_v3/palette.json`

## 요구사항
- 오른쪽 옆모습, 마젠타 배경, 평면 색면·음영은 `COMMON.md` 4절과 같게.
- 4프레임 걷기 주기: ① 앞발 접촉 ② 몸이 내려감 ③ 다리가 지나감 ④ 몸이 올라감. 팔은 다리와 반대로 흔든다.
- **모든 칸에서** 머리 높이(몸 위아래 흔들림 제외), 몸 크기, 의상, 얼굴이 같아야 한다. 발이 닿는 바닥선도 같아야 한다.
- 캐릭터가 칸 경계를 넘거나 잘리지 않게 여백을 둔다.
- 먼 쪽 다리는 가까운 쪽보다 두 단계 이상 어둡게 해서 구분한다.

## 절차
1. `$generate2dsprite`의 `asset` 대상, `walk` 모드(2×2, 4프레임)로 시트 1장 생성. 영상은 쓰지 않는다. 저장: `assets/sprites/forge/hero_walk_v3/`.
2. 같은 스킬의 `process`로 키잉·정렬·칸 분할해서 프레임 4장을 만든다 (프레임 폴더: `assets/sprites/forge/hero_walk_v3/frames_raw/`).
3. 마무리: `python tools/finish_character.py assets/sprites/forge/hero_walk_v3/frames_raw n09_walk_v3 --like n09_v3`
   (`--like`는 `n09_v3`의 크기 비율과 팔레트를 그대로 쓴다. 결과: `assets/sprites/forge/n09_walk_v3/frames/*.png`와 `n09_walk_v3_strip_1x.png`)
4. 검사: `python tools/check_sprites.py assets/sprites/forge/n09_walk_v3/frames/*.png` 통과. (프레임 사이 높이·바닥선 차이가 2px 이하여야 한다)
5. 보고서 `docs/codex/reports/T04.md` 작성, 상태 `review`.

## 합격 기준
- [ ] `check_sprites.py` 통과 (프레임 간 높이·바닥선 차이 2px 이하, 팔레트가 n09_v3와 같음)
- [ ] 4프레임을 순서대로 이어 봤을 때 걷는 동작으로 읽힌다 (strip 이미지로 판단)
- [ ] 얼굴·옷이 달라진 프레임이 없다
- [ ] 보고서에 프레임 사이 흔들림, 실패한 시도를 솔직히 적었다

## 안 될 때
프레임 사이 얼굴이나 옷이 계속 달라지면 3번까지 시도하고 멈춘다. 보고서에 어떤 프레임이 어떻게 달랐는지, 원본 시트 경로를 적는다. (그 경우 Claude Code가 코드 리깅 방식을 쓴다.)
