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
| 효과음 9종 | `assets/sfx/` | `tools/make_sfx.py`로 코드 합성(사각파·삼각파·잡음). 외부 음원 없음 | 직접 제작, 제한 없음(CC0로 취급) | 점프·2단 점프·대시·착지·피격·사망·오버로드 연결, 줍기·E 강화는 연결 전 |
| 임시 타일·배경 | `assets/placeholder/` | `tools/make_placeholder_assets.py` | 직접 제작 | 실제 타일 에셋으로 교체 예정 |
| BGM | (없음) | | | 후보만 정함 (아래) |

**이미지 생성 모델 (확인된 범위)**: Codex CLI 0.144.4, 대화 모델 설정은 `gpt-6.1-sol`(`~/.codex/config.toml`). 캐릭터 이미지는 Codex 내장 image_gen 도구로 생성했고(`master.json`의 `route: host-image_gen`), **이미지 모델명은 도구가 반환하지 않아 알 수 없다**. 콘셉트 이미지(2026-10-31)는 Gemini이며 모델명은 기록이 없다. 제출 전에 Codex 앱·계정 화면 또는 공식 문서에서 이미지 생성 모델명과 이용 조건(상업·공개 사용 가능 여부)을 확인해 이 줄을 채운다.

**BGM 후보 (아직 내려받지 않음, 사용 전 각 페이지에서 라이선스를 직접 확인)**
- Dark Sci-Fi Audio Pack (SRG774, OpenGameArt, CC0로 표기, 루프용 트랙 5개) https://opengameart.org/content/dark-sci-fi-audio-pack
- Ambience Pack 1 - Sci Fi Horror (Joth, OpenGameArt, CC0로 표기, 약 1분 루프 5개) https://opengameart.org/content/ambience-pack-1-sci-fi-horror
- Elevator To Reactor (Hazmat Harry): 같은 페이지에 CC-BY 트랙이 섞여 있어 트랙별 확인 필요
- 쓰지 않는 것: Dark Ambience Loop (qubodup)는 CC-BY 3.0/GPL이라 조건이 까다롭다.
