# 에셋 출처 (ASSETS)

사용한 모든 이미지·사운드는 아래에 기록한다. (이름 / 출처 URL / 라이선스 / 사용 위치)

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
- agent-sprite-forge (0x0funky, MIT, commit 6b3da5c): `~/.codex/skills`와 `~/.claude/skills`에 설치. 그 도구로 만든 에셋은 사용한 모델·날짜·프롬프트를 `docs/image_prompts.md`에 기록하고 이 표에 추가한다.
- codixel (mankidev, MIT, commit 604a9dc): `~/.claude/skills/codixel`에 설치(SKILL.md와 core/pixel.js).
