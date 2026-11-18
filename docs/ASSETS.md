# 에셋 출처 (ASSETS)

사용한 모든 이미지·사운드는 아래에 기록한다. (이름 / 출처 URL / 라이선스 / 사용 위치)

## 지금 게임이 쓰는 에셋 (2026-11-17 기준, 이 표가 최신이다)
아래 날짜별 절은 만든 순서대로 쌓인 **기록**이다. 서로 어긋나면 이 표를 따른다. 외부에서 가져온 완성 에셋은 폰트 하나뿐이다.

| 구분 | 위치 | 만든 방법 | 출처·라이선스 |
|---|---|---|---|
| 캐릭터·적·보스와 동작 프레임 | `assets/sprites/unified/` | Codex(agent-sprite-forge `generate2dsprite`, 내장 image_gen)로 원화 → `tools/finish_character.py`로 픽셀화. 작업 기록은 `docs/codex/`, 원화는 `assets/sprites/forge/` | AI 생성물 (이미지 모델명 미제공: 제출 전 확인 필요) |
| 사망·엔딩 화면 | `assets/backgrounds/screen_*.png` | Codex `generate2dmap` (T11) | AI 생성물 |
| 타일 세트, 원경, 중경 (6개 테마) | `assets/tiles/tile_set_*.png`, `assets/backgrounds/far_*.png`, `mid_*.png` | `tools/make_world.py` (code-drawn). 원경은 Codex 배경판(T06)에 테마 색을 다시 입힘 | 자체 제작 |
| 전투 이펙트 | `assets/effects/` | `tools/make_fx.py`(타격·폭발·먼지), `make_slash_hq.py`(휘두르기), `make_aura.py`(오라). 모두 code-drawn | 자체 제작 (이전 pixelfx 시트는 쓰지 않는다) |
| HUD 조각, 아이템 아이콘·진열대, 로고 | `assets/ui/` | `tools/make_hud.py`, `make_icons.py`, `make_codeart.py`(codeart2d 스킬의 SVG 렌더러) | 자체 제작 |
| 투사체(고철) | `assets/sprites/unified/proj_scrap.png` | `tools/make_codeart.py` | 자체 제작 |
| 무기 그림(식칼 8방향, 건틀릿 충격파, 무기 아이콘 4종: 철파이프·식칼·건틀릿·사슬, 사슬 줄·갈고리는 실행 중 사각형으로 그림) | `assets/sprites/unified/proj_knife_*`, `proj_blast_*`, `assets/ui/icon_w_*` | `tools/make_weapons.py` (code-drawn) | 자체 제작 |
| 맨손 자세(던지기·건틀릿) | `assets/sprites/unified/n09_punch_1~4.png` | Codex T05 결과(`forge/n09_attack_v3`)를 그대로 복사 | AI 생성물 |
| 효과음 21종 | `assets/sfx/` | `tools/make_sfx.py` (numpy 합성) | 자체 제작 |
| 배경음악 3곡 | `assets/music/` | `tools/make_music.py` (numpy 작곡·합성) | 자체 제작 |
| 단색 점 | `assets/placeholder/px_*.png` | `tools/make_placeholder_assets.py` | 자체 제작 |
| 폰트 | `assets/fonts/Galmuri11.ttf`, `Galmuri14.ttf` | 갈무리 v2.40.4 (Lee Minseo) | **SIL OFL 1.1** (`assets/fonts/OFL.txt`) |

- 쓰는 스킬·도구(개발용, 게임에 포함되지 않음)는 `docs/SKILLS.md`에 있다. agent-sprite-forge와 codixel은 MIT, gamedev-skills는 Apache-2.0.
- 엔딩 크레딧(`src/credits_mode.py`의 `CREDITS`)에 표기한다: Galmuri font by Lee Minseo (SIL OFL 1.1), AI 생성 이미지(Codex 내장 이미지 생성, 모델명 미제공), 개발 환경(pico2d, transitions MIT, numpy, Pillow), 나머지는 자체 제작. 이 표가 바뀌면 크레딧도 함께 고친다.
- 게임에서 더는 쓰지 않는 것(기록용으로만 남음): `assets/sprites/unified_legacy/`, `assets/sprites/detailed/`, `assets/concept/`, `assets/presentation_examples/`(발표 자료용).

---

# 아래는 날짜별 기록

| 이름 | 출처 | 라이선스 | 사용 위치 |
|---|---|---|---|
| `n09.png` | Gemini (모델명 확인 필요), 2026-10-31 생성. 원본 `assets/concept/source/protagonist_illust.webp` | 생성물 이용 조건 확인 필요 | 이전 발표용 (현재 미사용) |
| `enemy_slum.png` | Gemini (모델명 확인 필요), 2026-10-31 생성. 원본 `assets/concept/source/enemy_sheet.webp` | 생성물 이용 조건 확인 필요 | 이전 발표용 (현재 미사용) |
| `enemy_thrower.png` | Gemini (모델명 확인 필요), 2026-10-31 생성. 원본 `assets/concept/source/enemy_sheet.webp` | 생성물 이용 조건 확인 필요 | 이전 발표용 (현재 미사용) |
| `enemy_hound.png` | Gemini (모델명 확인 필요), 2026-10-31 생성. 원본 `assets/concept/source/enemy_sheet.webp` | 생성물 이용 조건 확인 필요 | 이전 발표용 (현재 미사용) |
| `enemy_guard.png` | Gemini (모델명 확인 필요), 2026-10-31 생성. 원본 `assets/concept/source/enemy_sheet.webp` | 생성물 이용 조건 확인 필요 | 이전 발표용 (현재 미사용) |
| `boss_crasher.png` | Gemini (모델명 확인 필요), 2026-10-31 생성. 원본 `assets/concept/source/enemy_sheet.webp` | 생성물 이용 조건 확인 필요 | 이전 발표용 (현재 미사용) |
| `boss_ark.png` | Gemini (모델명 확인 필요), 2026-10-31 생성. 원본 `assets/concept/source/enemy_sheet.webp` | 생성물 이용 조건 확인 필요 | 이전 발표용 (현재 미사용) |

## 새 발표용 이미지 (2026-10-31)

OpenAI 내장 이미지 생성 도구로 제작. 정확한 모델명은 도구에서 제공되지 않아 확인 필요. 생성물 이용 조건 확인 필요.

| 파일 | 대상 | 사용 위치 |
|---|---|---|
| `n09_codex.png` | 화이트 | 이전 PPT용 (현재 미사용) |
| `enemy_slum_codex.png` | 슬럼 폐인 | 이전 PPT용 (현재 미사용) |
| `enemy_thrower_codex.png` | 고철 투척병 | 이전 PPT용 (현재 미사용) |
| `enemy_hound_codex.png` | 안개 사냥개 | 이전 PPT용 (현재 미사용) |
| `enemy_guard_codex.png` | 중장갑 간수 | 이전 PPT용 (현재 미사용) |
| `boss_crasher_codex.png` | 크래셔 | 이전 PPT용 (현재 미사용) |
| `boss_ark_codex.png` | 아크 | 이전 PPT용 (현재 미사용) |

## 게임용 정적 스프라이트 시안 (2026-10-31)

OpenAI 내장 이미지 생성 도구로 직접 생성(모델명 미제공, 이용 조건 확인 필요). 원본은 `assets/sprites/source/`, 후처리 PNG는 `assets/sprites/`. 모두 오른쪽 방향의 기본 자세 1프레임이며 애니메이션은 미제작. 현재 게임에는 미연동.

| 파일 | 대상 | 캔버스 |
|---|---|---|
| `n09_idle.png` | 화이트 | 32×32 |
| `enemy_slum_idle.png` | 슬럼 폐인 | 32×32 |
| `enemy_thrower_idle.png` | 고철 투척병 | 32×32 |
| `enemy_hound_idle.png` | 안개 사냥개 | 32×32 |
| `enemy_guard_idle.png` | 중장갑 간수 | 32×32 |
| `boss_crasher_idle.png` | 크래셔 | 32×32 |
| `boss_ark_idle.png` | 아크 (악역 이미지 재생성) | 32×32 |

## 주인공 원본 기준 도트 기본 자세 시안 (2026-10-31)

`assets/sprites/detailed/`의 `n09_idle.png`, `enemy_slum_idle.png`, `enemy_thrower_idle.png`, `enemy_hound_idle.png`, `enemy_guard_idle.png`, `boss_crasher_idle.png`, `boss_ark_idle.png`: OpenAI 내장 이미지 생성 도구(모델명 미제공), 각 1536×1024 RGBA 원본. 게임 애니메이션 및 스프라이트 시트는 미제작이며 투명도와 픽셀 격자는 후처리 검증 필요. 이용 조건 확인 필요.
| `assets/sprites/unified/*_idle.png` (7종) | `assets/sprites/detailed/`의 Codex 생성 이미지를 `tools/pixelize_sprites.py`로 가공(80px 기준 축소, 공통 약 60색 팔레트, 외곽선). 생성 모델명 확인 필요 | 생성물 이용 조건 확인 필요 | 게임 구현용 임시 스프라이트 |

2026-10-31: `detailed/enemy_thrower_idle.png`, `detailed/enemy_guard_idle.png`를 OpenAI 내장 이미지 생성 도구(모델명 미제공)로 수정하고 `unified/`의 해당 두 파일에 기존 공통 팔레트를 적용했다. 이전 상세 원본은 `detailed/previous/`에 보존. 이용 조건 확인 필요.

2026-11-01: `assets/sprites/unified/n09_idle.png`는 발표 PPT 1·3장과 기획서 PPT 7장에, 적·보스 6종의 `*_idle.png`는 발표 PPT 8장과 기획서 PPT 12·13장에 사용한다. PPT 생성 시에만 원본 픽셀을 정수 배율로 확대하며 게임용 원본은 보존한다. 현재는 게임 구현용 임시 기본 자세 시안이다.

## 발표용 설계 목업 (2026-11-01)

`assets/presentation_examples/*.png` (15종): `tools/make_mockups.py`로 직접 그린 설계 스케치. 우리 스프라이트(`assets/sprites/unified/`)와 도형, 시스템 폰트(맑은 고딕)만 사용했고 외부 이미지는 쓰지 않았다. 실제 구현 화면이 아니며 그림에 "설계 목업"이라고 표시했다. 사용 위치: 발표 PPT 1~10장, 기획서 PPT 전반.

## 개발용 임시 이미지 (2026-11-05)
- `assets/placeholder/*.png` (타일, 배경, 단색 점): `tools/make_placeholder_assets.py`로 직접 생성한 이미지. 외부 에셋이 아니며 저작권 문제 없음. 실제 타일·UI 에셋을 정하면 교체한다.

## 폰트 (2026-11-07)
| 파일 | 제작자 | 출처 | 라이선스 | 용도 |
|---|---|---|---|---|
| `assets/fonts/Galmuri14.ttf`, `Galmuri11.ttf` (v2.40.4) | Lee Minseo (quiple) | https://github.com/quiple/galmuri | SIL OFL 1.1 (`assets/fonts/OFL.txt`) | 게임 안 글자 (14px 본문, 11px 작은 글자) |

- 폰트 파일은 수정하지 않고 그대로 포함한다. 파일 자체를 단독으로 판매하지 않는다.
- 엔딩 크레딧의 `[External Assets]`에 "Galmuri font by Lee Minseo (SIL OFL 1.1)"를 표기한다.

## 이펙트 (2026-11-07)
| 파일 | 제작자 | 출처 | 라이선스 | 비고 |
|---|---|---|---|---|
| `assets/effects/*` | patch-gg (pixelfx) | https://github.com/patch-gg/pixelfx | MIT (`pixelfx-LICENSE`, `pixelfx-NOTICE.md`) | pixelfx 코드로 렌더링 후 `tools/finish_effects.py`로 알파 디더·48색·15fps로 마무리. 일부 코드는 Hugo Duprez(Sprite Fusion VFX), rehan-remade(Hollow Crown)의 MIT 코드를 바탕으로 함 |

- pixelfx의 `Patch Pixel` 폰트(gallery/fonts)는 별도 권리라서 쓰지 않는다.
- 엔딩 크레딧에 pixelfx, Hugo Duprez, rehan-remade를 표기한다.

## 이미지 생성 스킬 (2026-11-07, 개발 도구이며 게임에 포함되지 않음)
- 설치된 스킬·도구 전체 현황은 `docs/SKILLS.md`.
- agent-sprite-forge (0x0funky, MIT, commit 6b3da5c): `~/.codex/skills`와 `~/.claude/skills`에 설치. 그 도구로 만든 에셋은 사용한 모델·날짜·프롬프트를 `docs/image_prompts.md`에 기록하고 이 표에 추가한다.
- awesome-gamedev-agent-skills (gamedev-skills, Apache-2.0, 2026-11-15): game-feel, platformer, input-systems, physics-tuning, level-design, game-ui-ux, roguelike, pygame-core 8개를 `~/.claude/skills`에 설치(참고 지침 문서이며 게임에 포함되지 않음). 자세한 평가는 `docs/REFERENCES.md`.
- codixel (mankidev, MIT, commit 604a9dc): `~/.claude/skills/codixel`에 설치(SKILL.md와 core/pixel.js).

## 주인공 스틸컷 시험 (2026-11-07)

| 파일 | 출처 | 라이선스 | 사용 위치 |
|---|---|---|---|
| `assets/sprites/forge/n09_idle_trial.png` | OpenAI Codex 내장 image_gen, 모델명 미제공. 기존 `unified/n09_idle.png` 참조, hibit 후처리 | 생성물 이용 조건 확인 필요 | 사용자 승인 전 시험 시안, 게임 미적용 |

| `assets/sprites/forge/hero_v2/n09_v2_idle.png` | Codex 내장 image_gen, 모델명 미제공, 2026-11-07. 기존 주인공 및 시험 원화 참조 | 생성물 이용 조건 확인 필요 | 승인 전 시험 시안, 게임 미적용 |

## 적·보스 마스터 v2 시험 (2026-11-07)

| 파일 | 출처 | 라이선스 | 사용 위치 |
|---|---|---|---|
| `assets/sprites/forge/enemy_slum_v2/enemy_slum_v2_idle.png` | Codex 내장 image_gen, 모델명 미제공. 기존 캐릭터와 주인공 v2 참조 | 생성물 이용 조건 확인 필요 | 승인 전 시험 시안, 게임 미적용 |
| `assets/sprites/forge/enemy_thrower_v2/enemy_thrower_v2_idle.png` | Codex 내장 image_gen, 모델명 미제공. 기존 캐릭터와 주인공 v2 참조 | 생성물 이용 조건 확인 필요 | 승인 전 시험 시안, 게임 미적용 |
| `assets/sprites/forge/enemy_guard_v2/enemy_guard_v2_idle.png` | Codex 내장 image_gen, 모델명 미제공. 기존 캐릭터와 주인공 v2 참조 | 생성물 이용 조건 확인 필요 | 승인 전 시험 시안, 게임 미적용 |
| `assets/sprites/forge/enemy_hound_v2/enemy_hound_v2_idle.png` | Codex 내장 image_gen, 모델명 미제공. 기존 캐릭터와 주인공 v2 참조 | 생성물 이용 조건 확인 필요 | 승인 전 시험 시안, 게임 미적용 |
| `assets/sprites/forge/boss_crasher_v2/boss_crasher_v2_idle.png` | Codex 내장 image_gen, 모델명 미제공. 기존 캐릭터와 주인공 v2 참조 | 생성물 이용 조건 확인 필요 | 승인 전 시험 시안, 게임 미적용 |
| `assets/sprites/forge/boss_ark_v2/boss_ark_v2_idle.png` | Codex 내장 image_gen, 모델명 미제공. 기존 캐릭터와 주인공 v2 참조 | 생성물 이용 조건 확인 필요 | 승인 전 시험 시안, 게임 미적용 |

## 현재 에셋 현황 요약 (2026-11-11, 위의 옛 표보다 우선)
| 구분 | 위치 | 만든 방법 | 출처·라이선스 | 상태 |
|---|---|---|---|---|
| 캐릭터 7종(주인공·적 4·보스 2) | `assets/sprites/unified/` | Codex(agent-sprite-forge `generate2dsprite` + `finish_frames` hibit)로 만든 납작한 원화를 `tools/finish_character.py`로 픽셀화. 원화·결과는 `assets/sprites/forge/` | AI 생성물. 이미지 모델명은 아래 참고 | 사용 중 (구 파일은 `unified_legacy/`) |
| 이펙트 8종 | `assets/effects/` | pixelfx 렌더 후 `tools/finish_effects.py` | pixelfx MIT (`pixelfx-LICENSE`) | 보관 (아직 게임 연결 전) |
| 폰트 | `assets/fonts/` | 갈무리 14px·11px | SIL OFL 1.1 (`OFL.txt`) | 사용 중 |
| 효과음 13종 (2주차에 휘두르기·적 피격·적 사망·투척 4종 추가) | `assets/sfx/` | `tools/make_sfx.py`로 코드 합성(사각파·삼각파·잡음). 외부 음원 없음 | 직접 제작, 제한 없음(CC0로 취급) | 점프·2단 점프·대시·착지·피격·사망·오버로드 연결, 줍기·E 강화는 연결 전 |
| 임시 타일·배경 | `assets/placeholder/` | `tools/make_placeholder_assets.py` | 직접 제작 | 실제 타일 에셋으로 교체 예정 |
| BGM | (없음) | | | 후보만 정함 (아래) |

**이미지 생성 모델 (확인된 범위)**: Codex CLI 0.144.4, 대화 모델 설정은 `gpt-6.1-sol`(`~/.codex/config.toml`). 캐릭터 이미지는 Codex 내장 image_gen 도구로 생성했고(`master.json`의 `route: host-image_gen`), **이미지 모델명은 도구가 반환하지 않아 알 수 없다**. 콘셉트 이미지(2026-10-31)는 Gemini이며 모델명은 기록이 없다. 제출 전에 Codex 앱·계정 화면 또는 공식 문서에서 이미지 생성 모델명과 이용 조건(상업·공개 사용 가능 여부)을 확인해 이 줄을 채운다.

**BGM 후보 (아직 내려받지 않음, 사용 전 각 페이지에서 라이선스를 직접 확인)**
- Dark Sci-Fi Audio Pack (SRG774, OpenGameArt, CC0로 표기, 루프용 트랙 5개) https://opengameart.org/content/dark-sci-fi-audio-pack
- Ambience Pack 1 - Sci Fi Horror (Joth, OpenGameArt, CC0로 표기, 약 1분 루프 5개) https://opengameart.org/content/ambience-pack-1-sci-fi-horror
- Elevator To Reactor (Hazmat Harry): 같은 페이지에 CC-BY 트랙이 섞여 있어 트랙별 확인 필요
- 쓰지 않는 것: Dark Ambience Loop (qubodup)는 CC-BY 3.0/GPL이라 조건이 까다롭다.

## 코드로 그린 에셋 (2026-11-11, 이미지 모델 없음, 직접 제작)
| 파일 | 만든 방법 | 비고 |
|---|---|---|
| `assets/ui/logo.png` (320×96) | `tools/codeart/make_logo.py`가 SVG를 생성 → agent-sprite-forge의 codeart2d 렌더러(`svg_render.py --crisp --strict-qc`)로 1배 렌더 | 타이틀 로고 "HAZE". 알파 0/255, 8색 |
| `assets/sprites/unified/proj_scrap.png` (42×24) | `tools/codeart/make_scrap.py` → codeart2d 렌더러 (`python tools/make_codeart.py proj_scrap`) | 고철 투척병이 던지는 고철 파이프 조각. 코드로 그린 것(code-drawn). 알파 0/255, 9색 |
| `assets/effects/pipe-slash.png`, `pipe-slash-finisher.png`, `pipe-slash-enhanced.png` (+ `.json`) | `tools/make_slash.py` → **codeart2d 스킬의 `fx_build.py`**(fx.v1 slash + sparks, `--route pixel --strict-qc`)가 그리고 시트로 묶음. 이미지 모델 없음 | 철파이프 휘두르기. 5방향(오른쪽·오른쪽 위·위·오른쪽 아래·아래)×6프레임, 왼쪽은 좌우 반전. 일반(청백), 3타(주황), E 강화(청록)에 충격 불꽃 포함. 알파 0/255, 팔레트 정확(스킬 QA 통과). code-drawn |
| `assets/effects/pipe-slash-fade/awake/critical.png`, `pipe-slash-enhanced.png` (+ `.json`) | `tools/make_slash.py` (codeart2d `fx_build.py`) | 게이지 구간(페이드·각성·위험)과 E 강화(보라)별 휘두르기. 구간마다 색·크기가 다름. code-drawn |
| `assets/effects/aura-fade/awake/critical/enhanced.png` (+ `.json`) | `tools/make_aura.py`: **주인공 실루엣**(n09_idle.png 알파) 거리장 + 위로 흐르는 주기적 fBm 노이즈로 **불꽃 혀**를 만들고 4톤+베이어 디더링으로 양자화, 불씨 입자와 지면 광채를 더함. 결과를 PixelSpec(codeart2d.pixelspec.v1)으로 만들어 **codeart2d `render_pixelspec.py --strict-qc`**로 검사·렌더링 (240×320, 16프레임 반복) | 구간별 오라 4종: 페이드(흐릿한 적갈색), 각성(청록 불꽃), 위험(크고 거센 주황 화염), 강화 준비(보라 에너지 소용돌이). 노멀은 없음. 발 아래 중앙이 기준점. 참고 방향은 픽셀 화염 오라 에셋팩들(OpenGameArt fire aura 128×128 14프레임, 에너지 오라 팩)의 구성과 크기이며 도면을 옮기지 않았다. code-drawn |
| `assets/effects/overload-burst.png` (+ `.json`) | `tools/make_aura.py` (codeart2d `fx_build.py`) | 오버로드 폭발 한 번(링+섬광+불꽃). code-drawn |
| `assets/effects/air-spin-enhanced.png` (+ `.json`) | `tools/make_slash.py` (codeart2d `fx_build.py`) | 강화된 점프 평타(보라 회전 베기). code-drawn |
| `assets/effects/dash-strike.png`, `air-spin.png` (+ `.json`) | `tools/make_slash.py` (codeart2d `fx_build.py`) | 내려찍기(dash-strike의 아래 방향)와 점프 평타(회전 베기 360도). 대시 평타는 시트가 아니라 `effects.PathSlash`가 지나온 경로를 사각 블록으로 그리는 직선(코드 그림, 정수 좌표) |
| `assets/sfx/swing_{fade,awake,critical,enhanced}.wav` | `tools/make_sfx.py` (코드 합성) | 구간·강화별 휘두르기 소리 4종 |
| `assets/tiles/tile_solid_{a,b,c}.png`, `tile_oneway.png`, `tile_spike.png` (40×40) | `tools/codeart/make_tiles.py` → 같은 렌더러 | 벽 3변형(칸 위치로 선택), 얇은 바닥, 가시. 알파 0/255, 3~9색 |
- 전체 재생성: `python tools/make_codeart.py`. 팔레트는 `tools/codeart/palette.json`.
- 이 에셋은 코드로 직접 그린 것이라 외부 저작권이 없고, 엔딩 크레딧에는 "code-drawn"으로 표기한다. (codeart2d 스킬은 MIT, `docs/ASSETS.md`의 agent-sprite-forge 항목 참고)
- 기존 `assets/placeholder/`의 타일은 더 이상 게임에서 쓰지 않는다 (배경 `bg.png`와 단색 점은 계속 사용).

2026-11-11 [Codex] T01 `assets/sprites/forge/n09_v3_idle.png`: Codex image_gen(모델명 미제공), 기존 주인공 참조 후 hibit 처리. 생성물 이용 조건 확인 필요, 검토 대기·게임 미적용.

2026-11-11 [Codex] T01 `assets/sprites/forge/n09_v3b_idle.png`. 프로젝트 주인공 참조로 Codex 내장 image_gen(모델명 미제공) 생성 후 generate2dsprite hibit 마감. 생성물 이용 조건 확인 필요. 검토 대기.

2026-11-11 [Codex] T02 `assets/sprites/forge/enemy_slum_v3_idle.png`, `enemy_thrower_v3_idle.png`, `enemy_guard_v3_idle.png`. 프로젝트 캐릭터를 참조해 Codex 내장 image_gen(모델명 미제공)으로 생성하고 generate2dsprite hibit 방식으로 마감했다. 생성물 이용 조건 확인 필요. 검토 대기.

2026-11-11 [Codex] T01~T03 캐릭터 7종 재제작 후보 `assets/sprites/forge/remake_t01_t03/finished/`. Codex 내장 image_gen(모델명 미제공, 생성물 이용 조건 확인 필요), agent-sprite-forge 6b3da5c(MIT), hibit 마감. 검토 대기.
| `assets/effects/aura-stun.png` (+ `.json`) | `tools/make_aura.py` (PixelSpec, codeart2d `render_pixelspec.py --strict-qc`) | 오버로드 기절 중 몸을 감싸는 전기 아크와 머리 위를 도는 별 (240×320, 16프레임 반복). `overload-burst`는 정수 2배로 다시 만듦. code-drawn |
| `assets/sfx/overload_zap.wav`, `stun_end.wav` | `tools/make_sfx.py` (합성) | 오버로드 폭발 치직 소리, 기절에서 깨어나는 소리. 직접 합성, 저작권 문제 없음 |
| `assets/effects/pipe-slash*.png`, `dash-strike.png`, `air-spin*.png` (+ `.json`) | `tools/make_slash_hq.py` (numpy + Pillow로 직접 그림, 이미지 모델 없음; 이전 `make_slash.py`의 fx_build 판을 대체) | 휘두르기 계열 검기 전부를 다시 만듦: 꼬리·머리가 뾰족한 초승달, 머리가 앞서고 꼬리가 따라잡는 스윙, 바깥 가장자리 흰 코어의 4톤+베이어 디더링, 1px 외곽선, 보조 호·링·섬광·불꽃. 190~310칸 격자에 그려 정수 2배(json scale=2). 방향 5종은 미리 돌려 그림. 구간·강화별 모양이 다르다. code-drawn |
| `assets/tiles/tile_set_<테마>.png` (cell, foundry, haze, gold, shop, boss) | `tools/make_world.py` (numpy + Pillow, 이미지 모델 없음, code-drawn) | v2(2026-11-17): 16열 x 9줄 타일 세트(칸 60x60, 캐릭터와 같은 1배 픽셀 밀도). 이어지는 석조 무늬 벽(이웃 마스크 16종 x 4사분면), 벽 속, 얇은 바닥, 가시, 벽 소품 6종, 매달린·바닥 소품 14종, 문틀·쇠창살·문 빛, 램프 빛. 배치는 `src/room.py`의 ATLAS 설명과 같다 |
| `assets/backgrounds/far_<테마>.png`, `mid_<테마>.png` | `tools/make_world.py` | 원경(1920x1080, 화면 고정): Codex 배경판(`assets/sprites/forge/backgrounds_v1`, T06)에 테마 색을 다시 입힌 것. 중경(1920x1200, 가로 반복 시차 배경): 코드로 그린 기둥·들보·사슬 실루엣. 이전 `bg_<테마>.png`와 `tools/make_tiles_hq.py`는 삭제 |

2026-11-16 [Codex] T04 n09_walk_v3b 및 T06 backgrounds_v1 제작 후보. Codex 내장 image_gen(모델명 미제공, 생성물 이용 조건 확인 필요), agent-sprite-forge 6b3da5c(MIT), hibit. 검토 대기.

2026-11-16 [Codex] T05 대기·공격·피격·점프 14프레임. Codex 내장 image_gen(모델명 미제공), agent-sprite-forge 6b3da5c(MIT), 기존 v3b 팔레트로 hibit. 검토 대기. docs/codex/reports/T05.md.
| `assets/sprites/unified/n09_walk_1~4.png` | Codex T04 결과(`forge/n09_walk_v3b/frames/`)를 2026-11-16 게임에 적용 | 주인공 걷기 4프레임(86x125, 발 기준점 x=37). 달리는 이동 거리에 맞춰 넘어간다(`config.WALK_FRAME_PX`). AI 생성 + hibit 후처리 |
| `assets/sprites/unified/{enemy_slum,enemy_thrower,enemy_guard,enemy_hound,boss_crasher,boss_ark}_idle.png` | Codex T02·T03 재제작(`forge/remake_t01_t03/finished/`)을 2026-11-16 게임에 적용 | 음영·디테일을 강화한 적·보스 6종으로 교체(사냥개는 fit판). 주인공 재제작판(T01 remake)은 걷기와 비율이 달라 보류 |
| `assets/sprites/unified/n09_idle_1~4.png`, `n09_hurt_1~2.png`, `n09_jump_1~4.png` | Codex T05 결과(`forge/n09_breathe_v3`, `n09_hurt_v3`, `n09_jump_v3b`)를 2026-11-16 게임에 적용 | 주인공 숨쉬기 대기 4·피격 2·점프(상승·정점·하강) 4프레임. 프레임마다 발 기준점이 달라 `config.PLAYER_FRAMES`의 기준점으로 맞춰 그린다. 공격 프레임(빈손 펀치)은 쓰지 않고 T07(철파이프 공격)로 다시 시킨다 |

2026-11-16 [Codex] T07 철파이프 공격 5방향 15프레임. Codex 내장 image_gen(모델명 미제공), agent-sprite-forge 6b3da5c(MIT), 기존 v3b 팔레트로 hibit. 검토 대기. docs/codex/reports/T07.md.
| `assets/sprites/unified/n09_swing_{side,up,down,upfwd,downfwd}_1~3.png` | Codex T07 결과(`forge/n09_swing_*_v3`)를 2026-11-16 게임에 적용 | 철파이프를 든 공격 자세 5방향 x 3프레임(준비·타격·마무리). 조준 방향으로 고르고 왼쪽은 좌우 반전. 방향마다 캔버스·발 기준점이 달라 `config.PLAYER_FRAMES`에 기준점을 둔다 |

2026-11-16 [Codex] T08 대시·내려찍기·사망 7프레임. Codex 내장 image_gen(모델명 미제공), agent-sprite-forge 6b3da5c(MIT), 기존 v3b 팔레트로 hibit. 검토 대기. docs/codex/reports/T08.md.
| `assets/sprites/unified/n09_dash_1~2.png`, `n09_plunge_1~2.png`, `n09_death_1~3.png` | Codex T08 결과(`forge/n09_dash_v3`, `n09_plunge_v3`, `n09_death_v3`)를 2026-11-16 게임에 적용 | 주인공 대시 자세 2·내려찍기(파이프를 아래로 겨눔) 2·사망(젖혀짐·무릎 꿇음·엎어짐) 3프레임. 캔버스와 발 기준점이 달라 `config.PLAYER_FRAMES`의 기준점으로 맞춰 그린다 |

2026-11-16 [Codex] T09 폐인·투척병 12프레임. Codex 내장 image_gen(모델명 미제공), agent-sprite-forge 6b3da5c(MIT), T02 재제작 팔레트로 hibit. 검토 대기. docs/codex/reports/T09.md.

2026-11-16 [Codex] T10 크래셔 11프레임. Codex 내장 image_gen(모델명 미제공), agent-sprite-forge 6b3da5c(MIT), T03 재제작 팔레트로 hibit. 검토 대기. docs/codex/reports/T10.md.
| `assets/sprites/unified/enemy_slum_{walk_1~4,attack_1~3,hurt_1}.png`, `enemy_thrower_{throw_1~3,hurt_1}.png` | Codex T09 결과(`forge/enemy_slum_walk_v3c_registered`, `enemy_slum_attack_v3`, `enemy_slum_hurt_v3`, `enemy_thrower_throw_v3`, `enemy_thrower_hurt_v3`)를 2026-11-16 게임에 적용 | 슬럼 걷기 4·공격 3(예고·타격·회복)·피격 1, 투척병 던지기 3·피격 1. 발 기준점은 `config.ENEMY_FRAMES` |

2026-11-16 [Codex] T11 사망·엔딩 화면 후보 2장 assets/sprites/forge/screens_v1/screen_*.png. Codex 내장 image_gen(모델명 미제공), agent-sprite-forge 6b3da5c(MIT), generate2dmap hibit 32색. 검토 대기. docs/codex/reports/T11.md.
| `assets/sprites/unified/boss_crasher_{idle_1~2,smash_1~3,charge_1~2,leap_1~3,hurt_1}.png` | Codex T10 결과(`forge/boss_crasher_*_v3`, 돌진은 `charge_v3b`)를 2026-11-16 게임에 적용 | 크래셔 대기 2·찍기(예고·내려침·마무리) 3·돌진 2·도약(웅크림·공중·착지) 3·피격 1프레임. 발 기준점은 `config.ENEMY_FRAMES`, 도약 공중 프레임은 뜬 높이(41px)만큼 기준점을 낮춘다 |
| `assets/backgrounds/screen_death.png`, `screen_ending.png` | Codex T11 결과(`forge/screens_v1/screen_*_v3.png`)를 2026-11-16 게임에 적용 | 사망 화면(쓰러진 주인공, 헤이즈가 걷히는 감옥 복도)과 엔딩 화면(탈출구로 걸어 나가는 뒷모습). 1920x1080 32색, 글자는 게임이 얹는다 |
| `assets/ui/icon_<id>.png` (cap absorb steady enhance resist dash power vigor heal shard), `assets/ui/pedestal_gold.png`, `pedestal_shop.png`, `pedestal_gone.png` | `tools/make_icons.py` (numpy + Pillow, 이미지 모델 없음) | 아이템 아이콘 10종(48x48, 24x24 격자의 정수 2배, 색 4~7개)과 진열대 3종(120x150). 진열대·HUD·황금방/정비방에 쓴다. Codex T13·T14가 합격하면 같은 이름으로 교체. code-drawn |
| `assets/presentation_examples/demo_combat_v2.png` | 실제 게임 캡처 (2026-11-17) | 2차 발표 1장 데모 화면 (각성 구간 전투, 충격선, HUD 아이콘) |

2026-11-17 [Codex] T13 아이템 아이콘 후보 10종 assets/sprites/forge/icons_v1/icon_*.png. Codex 내장 image_gen(모델명 미제공), agent-sprite-forge 6b3da5c(MIT), 팔레트 잠금 hibit. 검토 대기. docs/codex/reports/T13.md.

## HUD 조각 (2026-11-17, code-drawn, 자체 제작)
| 파일 | 만든 방법 | 비고 |
|---|---|---|
| `assets/ui/hud_*.png` 16개 (게이지 양끝 장식, 바늘, 대시 칸 on/off, 콤보 칸 off/on/fin, 조준점 ready/wait, 미니맵 아이콘 gold/boss/shop/haze, 하트, E 키) | `tools/make_hud.py` (Pillow, 이미지 모델 없음) | 도트 1px, 알파 0/255, 외곽선 #0b1020. 틀은 `src/ui.py`의 `_frame`이 사각형으로 입체 테두리를 그린다. 설계는 game-ui-ux 스킬 지침(색만으로 뜻을 전하지 않기, 글자 18px 이상, 대비)을 따랐다 |

## 배경음악 (2026-11-17, 자체 제작)
| 파일 | 만든 방법 | 비고 |
|---|---|---|
| `assets/music/title.wav` (27.4초), `explore.wav` (38.4초), `boss.wav` (27.4초) | `tools/make_music.py` (numpy로 직접 작곡·합성, 외부 음원·샘플 없음) | 22050Hz 모노 16비트, 반복 재생용(꼬리를 처음으로 넘겨 이음매 없음). D단조. 타이틀·엔딩은 느린 패드와 종소리, 탐험·전투는 100 BPM, 보스전은 140 BPM. 저작권 문제 없음 |
- 이전에 조사한 외부 BGM 후보(OpenGameArt)는 쓰지 않는다.

## Codex 에셋 적용 (2026-11-17)
- `assets/ui/icon_*.png` 10종, `assets/ui/pedestal_*.png` 3종, `assets/backgrounds/screen_title.png`, `assets/sprites/unified/n09_swing_*` 15프레임을 Codex 결과(T13, T14, T16, T15)로 교체했다. 모두 agent-sprite-forge + Codex 내장 image_gen(모델명 미제공)으로 만든 AI 생성물이다. 이전의 코드 그림 아이콘·진열대(`tools/make_icons.py`)는 더 쓰지 않는다.

2026-11-17 [Codex] T12 간수·사냥개 23프레임(`assets/sprites/forge/enemy_guard_*_v3/frames/`, `enemy_hound_*_v3*/frames/`). 자체 캐릭터 마스터를 참조해 Codex 내장 image_gen(모델명 미제공)으로 생성하고 기존 팔레트로 hibit 마감. 생성물 이용 조건 확인 필요. 2026-11-17 [Claude Code] 검토 합격, `tools/apply_enemy_frames.py`로 `assets/sprites/unified/enemy_{hound,guard}_*_N.png`에 복사해 게임에 적용.

2026-11-17 [Codex] T17 `assets/sprites/forge/n09_walk_v4/frames/` 8프레임. 기존 프로젝트 캐릭터 참조를 바탕으로 Codex 내장 image_gen(모델명 미제공) 생성, v3b 팔레트로 hibit 마감. 생성물 이용 조건 확인 필요. 검토 대기.

2026-11-17 [Codex] T17 v4b `assets/sprites/forge/n09_walk_v4b/frames/` 8장. 프로젝트 N-09 걷기 시안을 Codex 내장 image_gen(모델명 미제공)으로 편집한 뒤 v3b 팔레트로 마감. 생성물 이용 조건 확인 필요. 2026-11-17 [Claude Code] 검토 합격, `assets/sprites/unified/n09_walk_1~8.png`로 게임에 적용(T04의 4장을 대신함).

2026-11-17~18 [Codex] T18 `assets/sprites/forge/n09_swing_*_v5/frames/` 25장(기존 T15 15장, 새 중간·회수 10장). 프로젝트 N-09 원화를 참조해 generate2dsprite 0.5.0과 Codex 내장 image_gen(모델명 미제공)으로 제작하고 기존 v3b 팔레트로 hibit 마감. 원화·프롬프트 기록 `assets/sprites/forge/hero_pipe_v5/provenance.json`, 2026-11-18 [Claude Code] 검토 합격, `assets/sprites/unified/n09_swing_*_1~5.png`로 게임에 적용.

2026-11-18 [Codex] T19 `assets/sprites/forge/{n09_run_v1,n09_run_trans_v1}/frames/` 13장. 프로젝트 N-09 마스터를 참조해 generate2dsprite 0.5.0과 Codex 내장 image_gen(모델명 미제공)으로 제작하고 v3b 팔레트로 hibit 마감. 원화와 출처는 `assets/sprites/forge/hero_run_v1/provenance.json`, 2026-11-18 [Claude Code] 검토 합격, `assets/sprites/unified/n09_run_1~8.png`, `n09_run_trans_1~5.png`로 게임에 적용.

2026-11-18 [Codex] T20 assets/sprites/forge/boss_ark_*_v1/frames/ 12동작 23장. 프로젝트 자체 아크 마스터를 참조해 generate2dsprite 0.5.0 + Codex 내장 image_gen(모델명 미제공) 생성, 기존 아크 팔레트로 hibit 마감. 출처·원화·프롬프트는 assets/sprites/forge/ark_actions_v1/provenance.json. 2026-11-18 [Claude Code] 검토 합격, `tools/apply_enemy_frames.py`로 `assets/sprites/unified/boss_ark_*_N.png`에 복사.
