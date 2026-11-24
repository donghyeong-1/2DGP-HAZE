# 에셋 출처 (ASSETS)

사용한 모든 이미지·사운드는 아래에 기록한다. (이름 / 출처 URL / 라이선스 / 사용 위치)

## 지금 게임이 쓰는 에셋 (2026-11-19 기준, 이 표가 최신이다)
아래 날짜별 절은 만든 순서대로 쌓인 **기록**이다. 서로 어긋나면 이 표를 따른다. 외부에서 가져온 완성 에셋은 폰트 하나뿐이다.

| 구분 | 위치 | 만든 방법 | 출처·라이선스 |
|---|---|---|---|
| 캐릭터·적·보스와 동작 프레임 | `assets/sprites/unified/` | Codex(agent-sprite-forge `generate2dsprite`, 내장 image_gen)로 원화 → `tools/finish_character.py`로 픽셀화. 작업 기록은 `docs/codex/`, 원화는 `assets/sprites/forge/` | AI 생성물 (이미지 모델명 미제공: 제출 전 확인 필요) |
| 사망·엔딩 화면 | `assets/backgrounds/screen_*.png` | Codex `generate2dmap` (T11) | AI 생성물 |
| 은신처 원경, NPC 3명(정비사·보관인·기록관) 대기 2장씩 | `assets/backgrounds/far_hideout.png`, `assets/sprites/unified/npc_*` | Codex T22 (`generate2dmap`·`generate2dsprite`, 내장 image_gen) | AI 생성물 |
| 철파이프 2단계 강화 동작 6장 (올려베기·내려찍기) | `assets/sprites/unified/n09_s2rise_1~3.png`, `n09_s2slam_1~3.png` | Codex T24 (내장 image_gen, `finish_character.py --like n09_v3b`) 그대로 복사 (2026-11-21) | AI 생성물 |
| 일반 적 4종 피격 2장째·쓰러짐 3장 | `assets/sprites/unified/enemy_<종류>_hurt_2.png`, `enemy_<종류>_death_1~3.png` | Codex T25 (내장 image_gen, `finish_character.py --like <적 마감본>`) 그대로 복사 (2026-11-21) | AI 생성물 |
| 무기 전용 자세 10장 (식칼 3·건틀릿 4·사슬 3) | `assets/sprites/unified/n09_knife_1~3.png`, `n09_gauntlet_1~4.png`, `n09_chain_1~3.png` | Codex T26 (내장 image_gen, `finish_character.py --like n09_v3b`) 그대로 복사 (2026-11-21) | AI 생성물 |
| 투척병 걷기 4장·뒷걸음 2장 | `assets/sprites/unified/enemy_thrower_walk_1~4.png`, `enemy_thrower_back_1~2.png` | Codex T30 (내장 image_gen, 모델명 미제공, `finish_character.py --like enemy_thrower_remake`) 그대로 복사 (2026-11-21) | AI 생성물 |
| 보스 등장 카드 2장 | `assets/backgrounds/boss_card_crasher.png`, `boss_card_ark.png` | Codex T34 (내장 image_gen, 모델명 미제공, hibit 마감) 그대로 복사 (2026-11-21) | AI 생성물 |
| 엔딩 크레딧 장면 3장 | `assets/backgrounds/credits_1~3.png` | Codex T35 (내장 image_gen, 모델명 미제공, hibit 마감) 그대로 복사 (2026-11-21) | AI 생성물 |
| 구역 제목 카드 3장 | `assets/backgrounds/zone_cell.png`, `zone_foundry.png`, `zone_haze.png` | Codex T33 (내장 image_gen, 모델명 미제공, hibit 마감) 그대로 복사 (2026-11-21) | AI 생성물 |
| 멈춘 방 장식 18종 | `assets/decor/<테마>_<이름>.png` | Codex T31 (내장 image_gen, 모델명 미제공, hibit 마감) 그대로 복사 (2026-11-21) | AI 생성물 |
| 대화 초상화 8장 | `assets/portraits/<인물>_1~2.png` | Codex T32 (내장 image_gen, 모델명 미제공) 그대로 복사 (2026-11-21) | AI 생성물 |
| 움직이는 배경 소품 12종 x 4장 | `assets/props/<테마>_<소품>_1~4.png` | Codex T28 (내장 image_gen, 모델명 미제공, hibit 마감) 그대로 복사 (2026-11-21) | AI 생성물 |
| 스팀 상점 그림 (캡슐 4장·라이브러리 배경·로고) | `assets/store/` | Codex T29 (내장 image_gen, 모델명 미제공) + `tools/make_store_art.py`로 로고 합성 (2026-11-21). 게임 안에서는 쓰지 않는다 | AI 생성물 |
| 보스 크래셔 걷기 4장·쓰러짐 2장 | `assets/sprites/unified/boss_crasher_walk_1~4.png`, `boss_crasher_death_1~2.png` | Codex T27 (내장 image_gen, `finish_character.py --like boss_crasher_remake`) 그대로 복사 (2026-11-21) | AI 생성물 |
| 궁극기 컷인 띠, 시전 자세 2장 | `assets/ui/ult_cutin.png`, `assets/sprites/unified/n09_ult_1~2.png` | Codex T23 (내장 image_gen, hibit 마감) | AI 생성물 |
| 타일 세트, 원경, 중경 (6개 테마) | `assets/tiles/tile_set_*.png`, `assets/backgrounds/far_*.png`, `mid_*.png` | `tools/make_world.py` (code-drawn). 원경은 Codex 배경판(T06)에 테마 색을 다시 입힘 | 자체 제작 |
| 전투 이펙트 | `assets/effects/` | `tools/make_fx.py`(타격·폭발·먼지, 궁극기 광역 폭발 `ult-nova-<무기>` 4종), `make_slash_hq.py`(휘두르기), `make_aura.py`(오라). 모두 code-drawn | 자체 제작 (이전 pixelfx 시트는 쓰지 않는다) |
| UI 부품(9칸 판·막대 무늬·게이지 장식·키·칸·바늘) | `assets/ui/ui_*.png` | `tools/make_ui.py` (numpy, code-drawn, 2026-11-18 v3) | 자체 제작 |
| HUD 조각(조준점·미니맵 아이콘·하트), 아이템 아이콘·진열대, 로고 | `assets/ui/` | `tools/make_hud.py`, `make_icons.py`, `make_codeart.py`(codeart2d 스킬의 SVG 렌더러) | 자체 제작 |
| 투사체(고철) | `assets/sprites/unified/proj_scrap.png` | `tools/make_codeart.py` | 자체 제작 |
| 무기 그림(식칼 8방향, 건틀릿 충격파, 무기 아이콘 4종: 철파이프·식칼·건틀릿·사슬, 사슬 줄·갈고리는 실행 중 사각형으로 그림) | `assets/sprites/unified/proj_knife_*`, `proj_blast_*`, `assets/ui/icon_w_*` | `tools/make_weapons.py` (code-drawn) | 자체 제작 |
| 맨손 자세(던지기·건틀릿) | `assets/sprites/unified/n09_punch_1~4.png` | Codex T05 결과(`forge/n09_attack_v3`)를 그대로 복사 | AI 생성물 |
| 피해 숫자 픽셀 글꼴 2종 | `assets/ui/dmg_small.png`, `dmg_big.png` | `tools/make_digits.py` (3x5 점 글꼴, 코드 그림) | 자체 제작 |
| 강화 2·3단계 이펙트 (금·진홍) 8장 | `assets/effects/<hit|pipe-slash|air-spin|aura>-enhanced2·3` | `tools/recolor_fx.py` (보라 시트 색만 다시 칠함) | 자체 제작 |
| 효과음 59종 (11/19 사슬·궁극기·아크 12종, 11/21 무기별 명중 3종·적 예고 4종·환경음 4종, 11/21 식칼·사슬 구간별 9종·무기별 궁극기 마무리 4종·구간 진입·심장·마지막 처치) | `assets/sfx/` | `tools/make_sfx.py` (numpy 합성) | 자체 제작 |
| 배경음악 7곡 (title·explore·boss·ark, 11/21 factory·tower·hideout 추가) | `assets/music/` | `tools/make_music.py` (numpy 작곡·합성) | 자체 제작 |
| 화면 분위기(가장자리 어둡게·흐르는 안개) | `assets/ui/vignette.png`, `assets/backgrounds/fog_strip.png` | `tools/make_atmosphere.py` (numpy 점묘, code-drawn, 2026-11-21) | 자체 제작 |
| 단색 점 | `assets/placeholder/px_*.png` | `tools/make_placeholder_assets.py` | 자체 제작 |
| 폰트 | `assets/fonts/Galmuri11.ttf`, `Galmuri14.ttf` | 갈무리 v2.40.4 (Lee Minseo) | **SIL OFL 1.1** (`assets/fonts/OFL.txt`) |

- 실행 파일 만들기: PyInstaller 6.22.3 (GPL-2.0 + 부트로더 예외: 만든 실행 파일은 우리 라이선스로 배포할 수 있다), `tools/build_exe.py`. 실행 파일에 SDL2 DLL(pysdl2-dll, zlib 라이선스)과 Galmuri 글꼴(OFL, `FONT_LICENSE_OFL.txt`로 같이 넣는다)이 들어간다.
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

2026-11-19 [Codex] T21 assets/sprites/forge/n09_run_v2/frames/ 달리기 8장. 프로젝트 자체 N-09 마스터를 참조한 Codex 내장 image_gen(모델명 미제공) 원화, generate2dsprite 0.5.0 처리, 기존 v3b 팔레트로 hibit 마감. 실제 출처·프롬프트는 assets/sprites/forge/hero_run_v2/provenance.json. 캔버스 105×129·기준점 (55,128), 교대 비율 0.87. 검토 대기.
| 균열의 분노 아이콘 | `assets/ui/icon_fury.png` | `tools/make_fury_icon.py`: Codex T13 공격력 아이콘(`icon_power.png`)의 색상을 보라로 돌림 (2026-11-19) | 자체 제작(파생) |
| 주인공 달리기 8장 (게임용) | `assets/sprites/unified/n09_run_1~8.png` | Codex T21(`forge/n09_run_v2`)에 `tools/soften_run_depth.py`로 앞뒤 팔다리 밝기 차이를 줄인 것 (2026-11-19) | 자체 제작(파생) |

2026-11-19 [Codex] T22 assets/sprites/forge/hideout_v1/far_hideout_v1.png(1920×1080·32색)과 npc_v1/npc_{mechanic,keeper,archivist}_idle_{1,2}.png(대기 6장). Codex 내장 image_gen(모델명 미제공), generate2dmap·generate2dsprite 0.5.0, 프로젝트 hibit 마감 도구로 자체 제작. 원화·도구·프롬프트·측정값은 각 폴더의 provenance.json, NPC 기준점 (64,130), 캔버스 128×132. 검토 대기.

2026-11-19 [Codex] T23 assets/sprites/forge/cutin_v1/cutin_hero_v1.png(1920×420·32색·이진 알파) 및 n09_ult_v1/frames/ult-{1,2}.png(140×132, 기준점 (64,130)). 프로젝트 주인공 마스터를 참조한 Codex 내장 image_gen(모델명 미제공) 생성, generate2dsprite·hibit_plate 0.5.0 및 프로젝트 hibit 도구로 마감. 출처·프롬프트·해시는 각 폴더의 provenance.json. 검토 대기.

2026-11-21 [Codex] T24 assets/sprites/forge/n09_stage2_v1/frames/{s2rise,s2slam}-1~3.png. 프로젝트 N-09 v3b 마스터를 참조한 자체 제작 파생 에셋. Codex 내장 image_gen(모델명 미제공), generate2dsprite 0.5.0 및 프로젝트 hibit 마감. 171×168, 공통 기준점 (70,161), 39색·이진 알파. 원화·프롬프트는 같은 폴더 raw/에 보관. 검토 대기.

2026-11-21 [Codex] T25 assets/sprites/forge/enemy_death_v1/{slum,thrower,guard,hound}/frames/ 수정용 스프라이트 16장(피격 ② 4장·사망 12장). 프로젝트 자체 마스터를 참조한 Codex 내장 image_gen(모델명 미제공)으로 제작하고 generate2dsprite 0.5.0과 기존 종별 hibit 팔레트로 마감. 원화·출처·프롬프트는 assets/sprites/forge/enemy_death_v1/provenance.json. 검토 대기.

2026-11-21 [Codex] T26 assets/sprites/forge/n09_weapon_poses_v1/{knife,gauntlet,chain}/frames/ 10장. 프로젝트 N-09 v3b 마스터와 식칼 투사체·건틀릿 아이콘·사슬 아이콘을 참조한 자체 제작 파생 에셋. Codex 내장 image_gen(모델명 미제공), generate2dsprite 0.5.0과 프로젝트 hibit 마감. 41색·이진 알파. 원화·출처·프롬프트는 assets/sprites/forge/n09_weapon_poses_v1/provenance.json. 검토 대기.

2026-11-21 [Codex] T27 assets/sprites/forge/crasher_walk_death_v1/frames/{walk-1~4,death-1~2}.png 6장. 프로젝트 자체 크래셔 마스터를 참조한 Codex 내장 image_gen(모델명 미제공), generate2dsprite 0.5.0 및 크래셔 기존 hibit 팔레트로 마감. 이진 알파, 불투명 전체 41색. 원화·출처·프롬프트는 assets/sprites/forge/crasher_walk_death_v1/provenance.json. 검토 대기.

2026-11-21 [Codex] T28 assets/sprites/forge/props_anim_v1/<테마>/<소품>/frames/ 배경 소품 12종 48 PNG 및 검토용 GIF 12개. 프로젝트 원경·타일을 참조한 자체 제작 에셋. Codex 내장 image_gen(모델명 미제공), generate2dsprite 0.5.0 및 Agent Sprite Forge hibit 마감기 0.5.0(MIT), 공통 32색·이진 알파·1배. 원화·출처·프롬프트 assets/sprites/forge/props_anim_v1/provenance.json. 검토 대기.

2026-11-21 [Codex] T29 assets/sprites/forge/store_art_v1/ 로고와 캡슐 4장·라이브러리 배경 1장. 프로젝트 자체 이미지 참조 에셋. Codex 내장 image_gen(모델명 미제공), generate2dmap·hibit_plate 0.5.0(MIT) 마감, 파일별 38~48색·1/2/4px 블록. 출처와 프롬프트는 assets/sprites/forge/store_art_v1/provenance.json. 검토 대기.

2026-11-21 [Codex] T30 assets/sprites/forge/thrower_walk_v1/frames/ 고철 투척병 걷기 4장·물러서기 2장. 프로젝트 자체 마스터 참조, Codex 내장 image_gen(모델명 미제공), generate2dsprite 0.5.0과 프로젝트 기존 히비트 팔레트로 마감. 105×131, 발 기준점 (62,127), 이진 알파와 41색. 출처·원화·프롬프트 assets/sprites/forge/thrower_walk_v1/provenance.json. 검토 대기.

2026-11-21 [Codex] T31 assets/sprites/forge/room_decor_v1/<테마>/<소품>.png 정지 장식 18종. 프로젝트 자체 원경·중경·타일·T28 소품 참조. Codex 내장 image_gen(모델명 미제공), generate2dsprite 및 Agent Sprite Forge Hibit 마감기 0.5.0(MIT). 파일별 9~24색·이진 알파·1배. 사용 예정 위치는 슬럼·공장·탑 방의 바닥과 벽·천장. 출처·프롬프트 assets/sprites/forge/room_decor_v1/provenance.json. 검토 대기.

2026-11-21 [Codex] T32 assets/sprites/forge/portraits_v1/<인물>_<1|2>.png 은신처 대화 UI용 초상화 8장. 프로젝트 자체 마스터와 게임 그림 참조, Codex 내장 image_gen(모델명 미제공), generate2dsprite 0.5.0(MIT)과 Pillow 마감, codixel(MIT) 비교판. 200×200, 인물별 공용 32색·이진 알파·1배. 출처와 프롬프트 assets/sprites/forge/portraits_v1/provenance.json. 검토 대기.

2026-11-21 [Codex] T33 assets/sprites/forge/zone_cards_v1/zone_<cell|foundry|haze>.png 구역 전환용 제목 카드 배경 3장. 프로젝트 자체 제목 화면·원경을 참조한 Codex 내장 image_gen(모델명 미제공), generate2dmap 0.5.0(MIT) Hibit 마감, codixel(MIT) 비교판. 1920×400·불투명 32색·1배. 출처와 프롬프트 assets/sprites/forge/zone_cards_v1/provenance.json. 검토 대기.

2026-11-21 [Codex] T34 assets/sprites/forge/boss_cards_v1/boss_card_<crasher|ark>.png 보스방 입장용 카드 2장. 프로젝트 자체 캐릭터·원경·상점 그림 참조, Codex 내장 image_gen(모델명 미제공), generate2dmap 0.5.0(MIT) Hibit 마감, codixel(MIT) 비교판. 1920×400·불투명 32색·1배. 출처와 프롬프트 assets/sprites/forge/boss_cards_v1/provenance.json. 검토 대기.

2026-11-21 [Codex] T35 assets/sprites/forge/credits_scenes_v1/credits_<1|2|3>.png 엔딩 크레딧 배경 3장. 프로젝트 자체 탈출·제목·은신처 그림과 캐릭터 마스터 참조, Codex 내장 image_gen(모델명 미제공), generate2dmap 0.5.0(MIT) Hibit 마감, codixel(MIT) 비교판. 1920×1080·불투명 32색·1배. 출처와 프롬프트 assets/sprites/forge/credits_scenes_v1/provenance.json. 검토 대기.

2026-11-22 [Codex] T36 assets/sprites/forge/drone_v1/ 공장 비행 적 용접 드론 마스터 1장과 동작 13 PNG. 프로젝트 자체 원경·타일·적 그림을 참조한 Codex 내장 image_gen(모델명 미제공), generate2dsprite 및 Agent Sprite Forge Hibit 0.5.0(MIT) 마감, codixel(MIT) 비교판. 마스터 키 90px, 동작 160×136·공통 41색·이진 알파·1배. 출처와 프롬프트 assets/sprites/forge/drone_v1/provenance.json. 검토 대기.

2026-11-22 [Codex] T37 assets/sprites/forge/cart_v1/ 공장 적 자폭 수레 마스터 1장과 동작 11 PNG. 프로젝트 자체 원경·타일·장식 수레·적을 참조한 Codex 내장 image_gen(모델명 미제공), generate2dsprite 및 Agent Sprite Forge Hibit 0.5.0(MIT), codixel(MIT) 비교판. 마스터 키 75px, 동작 160×122·공통 41색·이진 알파·1배. 출처와 프롬프트 assets/sprites/forge/cart_v1/provenance.json. 검토 대기.

2026-11-22 [Codex] T43 assets/sprites/forge/boss_terrain_v1/ 고철 기둥·증기 밸브·용광로 배기구·결정 기둥 각 3장. 프로젝트 자체 원경·타일·소품을 참조한 Codex 내장 image_gen(모델명 미제공), generate2dsprite 및 Agent Sprite Forge Hibit 0.5.0(MIT), codixel(MIT) 비교판. 소품별 공용 32색 이하·이진 알파·1배. 출처와 프롬프트 assets/sprites/forge/boss_terrain_v1/provenance.json. 검토 대기.

2026-11-22 [Claude Code] Codex T36·T37 적용: `assets/sprites/unified/enemy_drone_*`(비행 4·예고 2·분사 3·피격 2·잔해 2·정지 1), `enemy_cart_*`(굴러감 4·예고 3·피격 2·잔해 2·정지 1)로 복사(1배 그대로). 효과음 `windup_drone`·`drone_torch`·`windup_cart`는 `tools/make_sfx.py`로 직접 합성(numpy).

2026-11-22 [Claude Code] Codex T43 적용: `assets/props/boss/`(고철 기둥·증기 밸브·용광로 배기구·결정 기둥 각 3장, 1배 그대로)로 복사. 보스방 지형의 코드 임시 그림을 바꿨다.

2026-11-22 [Codex] T38 assets/sprites/forge/eye_v1/ 탑 벽 포탑 감시 눈 마스터 1장과 동작 10 PNG. 프로젝트 자체 아크·탑 원경·타일·감시 카메라·청록 패널을 참조한 Codex 내장 image_gen(모델명 미제공), generate2dsprite 및 Agent Sprite Forge Hibit 0.5.0(MIT), codixel(MIT) 비교판. 마스터 키 96px, 동작 150×140·공용 46색·이진 알파·1배. 출처와 프롬프트 assets/sprites/forge/eye_v1/provenance.json. 검토 대기.

2026-11-22 [Codex] T39 assets/sprites/forge/knight_v1/ 탑 결정 기사 마스터 1장과 동작 14 PNG. 프로젝트 자체 간수·아크·탑 원경·타일을 참조한 Codex 내장 image_gen(모델명 미제공), generate2dsprite 및 Agent Sprite Forge Hibit 0.5.0(MIT), codixel(MIT) 비교판. 마스터 키 132px, 동작 250×176·공용 41색·이진 알파·1배. 출처와 프롬프트 assets/sprites/forge/knight_v1/provenance.json. 검토 대기.

2026-11-22 [Codex] T40 assets/sprites/forge/wraith_v1/ 탑 헤이즈 망령 마스터 1장과 동작 10 PNG. 프로젝트 자체 각성 오라·아크·탑 원경·타일을 참조한 Codex 내장 image_gen(모델명 미제공), generate2dsprite 및 Agent Sprite Forge Hibit 0.5.0(MIT), codixel(MIT) 비교판. 마스터 키 110px, 동작 192×156·공용 41색·이진 알파·1배. 출처와 프롬프트 assets/sprites/forge/wraith_v1/provenance.json. 검토 대기.

2026-11-22 [Codex] T41 assets/sprites/forge/rat_v1/ 슬럼 헤이즈 쥐 마스터 1장과 동작 9 PNG. 프로젝트 자체 사냥개·폐인·슬럼 원경·타일을 참조한 Codex 내장 image_gen(모델명 미제공), generate2dsprite 및 Agent Sprite Forge Hibit 0.5.0(MIT), codixel(MIT) 비교판. 마스터 키 40px, 동작 124×68·공용 41색·이진 알파·1배. 출처와 프롬프트 assets/sprites/forge/rat_v1/provenance.json. 검토 대기.

2026-11-22 [Codex] T42 assets/sprites/forge/shaman_v1/ 슬럼 누더기 무당 마스터 1장과 동작 11 PNG. 프로젝트 자체 폐인·투척병·보관인·슬럼 원경·타일을 참조한 Codex 내장 image_gen(모델명 미제공), generate2dsprite 및 Agent Sprite Forge Hibit 0.5.0(MIT), codixel(MIT) 비교판. 마스터 키 120px, 동작 192×188·공용 44색·이진 알파·1배. 출처와 프롬프트 assets/sprites/forge/shaman_v1/provenance.json. 검토 대기.

2026-11-22 [Codex] T44 assets/sprites/forge/mutation_ui_v1/ 문양 64×64 4장, 카드 테두리 300×420 3장, 보상 48×48 6장. 프로젝트 자체 UI 아이콘을 참조한 Codex 내장 image_gen(모델명 미제공), generate2dsprite 및 Agent Sprite Forge Hibit 0.5.0(MIT), codixel(MIT) 비교판. 종류별 공용 32색 이하·이진 알파·1배, 테두리 120px 모서리 9분할. 출처와 프롬프트 assets/sprites/forge/mutation_ui_v1/provenance.json. 검토 대기.

2026-11-22 [Codex] T45 assets/sprites/forge/heart_core_v1/ 거대 보스 헤이즈 심장 본체 6장. 프로젝트 자체 아크 마스터·게임 스프라이트·보스 카드·탑과 보스방 원경을 참조한 Codex 내장 image_gen(모델명 미제공), generate2dmap 및 Agent Sprite Forge Hibit 0.5.0(MIT), codixel(MIT) 비교판. 900×560·공용 41색·이진 알파·2px 블록·1배. 출처와 프롬프트 assets/sprites/forge/heart_core_v1/provenance.json. 검토 대기.

2026-11-22 [Codex] T48 assets/sprites/forge/foreground_v1/ 슬럼·공장·탑의 카메라 전경 후보 `fg_cell.png`·`fg_foundry.png`·`fg_haze.png`. 자체 중경을 참조한 Codex 내장 image_gen(모델명 미제공) 신규 생성, generate2dmap Agent Sprite Forge 0.5.0(MIT) 키잉, codixel 픽셀 코어(MIT) 반복 미리보기. 1920×1080·공용 남색 2색·이진 알파·1배. 출처와 프롬프트 assets/sprites/forge/foreground_v1/provenance.json. 검토 대기.

- 2026-11-22: `screen_title`·`screen_death`·`screen_ending`·`credits_1`·`boss_card_crasher`·`boss_card_ark`의 캐릭터 영역만 `tools/pixelize_chars.py`로 픽셀화(자체 가공, 원본 AI 그림은 `assets/concept/bg_ai_original/`). 캐릭터 검은 테두리는 실행 중 `assets.outline_image`로 만든다.
- 2026-11-22: Codex T44(내장 image_gen, 모델명 미제공) 결과를 `assets/ui/mut_*.png`(변이 문양 4), `card_frame_*.png`(카드 테두리 3), `reward_*.png`(방 보상 아이콘 6)으로 그대로 복사. AI 생성물.
2026-11-22 [Claude Code] T48 적용: `assets/backgrounds/fg_cell.png`·`fg_foundry.png`·`fg_haze.png` (Codex T48 foreground_v1 복사, 출처·라이선스는 위 T48 항목과 같음). `Room.draw_foreground`로 UI 아래에 시차 1.35배로 이어 붙여 그린다. 설정 옵션은 만들지 않았다(전투 높이가 비어 있어 가려지지 않음).
- 2026-11-22: Codex T38~T42(내장 image_gen, 모델명 미제공, Hibit 마감) 결과를 `assets/sprites/unified/enemy_(eye|knight|wraith|rat|shaman)_*.png`(59장)로 그대로 복사. AI 생성물. 출처·프롬프트는 `assets/sprites/forge/<이름>_v1/provenance.json`.

2026-11-22 [Codex] T46 assets/sprites/forge/heart_hands_v1/frames/ 헤이즈 심장 기계 오른손 8장. 프로젝트 자체 심장 본체와 아크 장갑을 참조한 Codex 내장 image_gen(모델명 미제공) 신규 생성, generate2dsprite 및 Agent Sprite Forge 0.5.0(MIT) Hibit 마감, codixel 픽셀 코어(MIT) 비교판. 260×260·본체 팔레트 중 공용 39색·이진 알파·2px 블록·1배. 출처와 프롬프트 assets/sprites/forge/heart_hands_v1/provenance.json. 검토 대기.

2026-11-22 [Codex] T47 assets/sprites/forge/heart_arena_v1/의 `far_heart.png`(결전 방 원경 1920×1080) 및 `boss_card_heart.png`(등장 카드 1920×400). 프로젝트 자체 탑·보스방 배경, 아크 카드, 헤이즈 심장 본체와 손을 참조한 Codex 내장 image_gen(모델명 미제공) 신규 생성, generate2dmap 및 Agent Sprite Forge 0.5.0(MIT) Hibit 마감. 파일당 불투명 32색·2px 블록·1배. 출처와 프롬프트 assets/sprites/forge/heart_arena_v1/provenance.json. 검토 대기.
- 2026-11-22: Codex T46·T47(내장 image_gen, 모델명 미제공, Hibit 마감) 결과를 그대로 복사해 게임에 적용. 손 8장 → `assets/sprites/unified/heart_hand_(idle|fist|palm|stun)_1·2.png`(왼손은 좌우 반전), 결전 방 원경 → `assets/backgrounds/far_heart.png`, 등장 카드 → `assets/backgrounds/boss_card_heart.png`. AI 생성물. 출처·프롬프트는 `assets/sprites/forge/heart_hands_v1/provenance.json`, `heart_arena_v1/provenance.json`.

2026-11-23 [Gemini] G01 `assets/sprites/gemini/hero_concepts_v1/` 새 주인공 디자인 시안 3안(`hero_{A,B,C}_{side,sheet,small}.png` 9장). Antigravity 내장 image-generator(모델명 미제공)로 원화 생성 후 PNG 변환, `*_small.png`는 Pillow로 1/24 축소 후 최근접 확대. 검토 대기. docs/gemini/reports/G01.md.
- 2026-11-23: 새 주인공(v6) `assets/sprites/unified/hero6_*.png`, `hero6.json` — PixelLab(pixellab.ai, MCP `create_image_pixflux`·`animate_image_pixminimax`, 체험판)으로 생성, 기준 그림은 Gemini G01 A안(머리를 흰색으로 칠함). 원본·옵션 기록 `assets/sprites/pixellab/hero_v6_test/GENERATION_LOG.md`. 마무리 `tools/apply_pixellab_hero.py`(기준 그림 15색 고정, 머리 위치 맞춤, 최근접 2배). **이용 조건(상업·학업)은 결제 전에 확인해 여기에 적는다.**
- 2026-11-23: 타일·장식·소품·전경(`assets/tiles`, `decor`, `props`, `backgrounds/fg_*`)을 `tools/pixel2x.py`로 2배 픽셀 규격으로 변환(code-drawn 처리, 원본 색만 사용). 원본은 `assets/concept/pixel1x_original/`.

2026-11-23 [Gemini] G04(부분) `assets/sprites/gemini/portraits_v1/hero_portrait.png`(1024×1024). Antigravity 내장 image-generator(`gemini-3.1-flash-image`)로 생성 후 PNG 변환. 나머지 NPC 3장 및 G02·G03은 429 할당량 소진(21:02 KST 초기화)으로 미완료. docs/gemini/reports/G04.md.

2026-11-23 [Codex] T49 `assets/sprites/forge/backdrops_v6/` 슬럼·공장·탑의 v6 원경 3장(960×540)과 반복 중경 3장(1440×540). 기존 프로젝트 배경의 구도를 참고해 Codex 내장 image_gen(모델명 미제공)으로 새로 생성하고 generate2dmap Agent Sprite Forge 0.5.0(MIT)와 Pillow로 마감했다. 파일당 32색·알파 0/255·1픽셀 논리 격자. 출처와 프롬프트 `assets/sprites/forge/backdrops_v6/provenance.json`. 검토 대기.
- 2026-11-23: 빛 번짐 `assets/light/bloom_128.png`, `bloom_256.png` — `tools/make_light.py` code-drawn. 이펙트 시트 전체를 점묘 없는 단색 면으로 다시 그림(make_slash_hq.py, make_fx.py), 예전 시트는 `assets/concept/effects_v6_dither/`.
- 2026-11-24: 주인공 공격 v3 `assets/sprites/unified/hero6_(swing_*, air1, air2, airup, dashcut, e1, s2rise, s2slam, plunge)_*.png` — PixelLab `animate_with_skeleton_v3`(첫 프레임 base96, 손·파이프 키포인트는 `assets/sprites/pixellab/hero_v6_test/raw/v3_kp/gen_v3.py`). 마무리 `tools/apply_pixellab_hero.py`(회색 초승달 제거 추가). 이펙트 `assets/effects/pipe-slash-*-flat.png`, `pipe-slash-finisher-rise.png`은 `tools/make_slash_hq.py`로 코드로 그림(code-drawn, 이미지 모델 없음).
- 2026-11-24: 손맛 다듬기 — `assets/ui/dmg_tiny·small·big.png`(tools/make_digits.py), `assets/light/dot_48.png`(make_light.py), `assets/light/glow_*.png`(make_glow.py: 이펙트 시트를 흐려 만든 빛), `assets/sfx/kill_streak_1~6.wav`·`absorb_done.wav`·`absorb_1~5.wav`(make_sfx.py 합성). 모두 코드로 만듦(code-drawn / code-synthesized, 외부 음원·이미지 모델 없음).
- 2026-11-24: 효과음 v2 녹음 원본 — Kenney(kenney.nl) Impact Sounds 1.0·Interface Sounds·Sci-fi Sounds·RPG Audio·Digital Audio, **CC0 1.0**(개인·교육·상업 사용 가능, 출처 표시 의무 없음). 쓰는 74개만 `assets/sfx_src/kenney/<묶음>/`(License.txt 포함). 가공 `tools/make_sfx_v2.py`(자르기·음 높이·겹치기, 합성 바람·쿵·종소리 추가) → `assets/sfx/*.wav`. 크레딧에 Kenney 표시.
- 2026-11-24: 배경음악 v2 — OpenGameArt.org에서 사용자 승인 후 받음 (`assets/music/`): title.ogg = Rise of Spirit / Alexandr Zhelanov (CC-BY 3.0), hideout.ogg = Galactic Temple / yd (CC0), explore.ogg = EmptyCity / yd (CC0), factory.mp3 = Gi-i Dark Ambient Techno / SouljahdeShiva (CC-BY 3.0), tower.ogg = Ancient Apparitions / marcelofg55 (CC-BY 3.0), combat.ogg = Dark Horse / Centurion_of_war (CC0), boss.mp3 = Battle Theme A / cynicmusic (CC0), ark.mp3 = The 9th Circle V2 / Joth (CC0). CC-BY 곡은 크레딧(credits_mode)에 곡명·작곡가·라이선스 표시. 예전 합성 곡(tools/make_music.py, code-synthesized)은 삭제.

2026-11-24 [Gemini] G05(1·2차) `assets/sprites/gemini/ui_concepts_v1/ui_{A,B,C}_{hud,pause}.png` 6장(1920×1080, 960×540 기준 2× 최근접 PNG). 기존 게임 캡처를 바탕으로 Antigravity 내장 image-generator(`gemini-3.1-flash-image`)로 UI 시안 편집 생성(B안 HUD 우상단 중복 사각형은 원본 캡처 배경 픽셀로 복원). 증강 카드 3장은 429 할당량 소진으로 미생성. 검토 대기(게임 미적용). docs/gemini/reports/G05.md.
- 2026-11-24: 쌍권총 — 겨눔 자세 `assets/sprites/unified/hero6_pistol_1.png`(PixelLab edit_image_pro_flash로 만든 base_pistols를 apply_pixellab_hero.py로), 아이콘 `assets/ui/icon_w_pistol.png`(make_weapons.py, code-drawn), 궁극기 폭발 `assets/effects/ult-nova-pistol`(make_fx.py)·빛(make_glow.py), 총알·총구 섬광은 실행 중 코드로 그림, 소리 shot·shot_*·impact_pistol·ult_final_pistol(make_sfx_v2.py: 합성 + Kenney CC0).
- 2026-11-24: 사슬 고리·작살 갈고리(`weapon.draw_chain`·`draw_hook`)와 건틀릿 돌진 궤적(`weapon.RushTrail`)은 실행 중 코드로 그린다(code-drawn, 새 파일 없음, 빛은 기존 `assets/light/dot_48.png`).
- 2026-11-24: 이펙트 v8 1차 — `assets/effects/hit-(fade·normal·awake·critical·enhanced·enhanced2·enhanced3).png`, `haze-blast.png`와 빛 시트 `assets/light/glow_<같은 이름>.png`를 `tools/make_fx2.py` + `tools/fxkit.py`로 다시 만듦(code-drawn, numpy, 이미지 모델 없음, 방식 참고는 `docs/REFERENCES.md`). 예전 시트는 git 기록에 있다.
- 2026-11-24: 이펙트 v8 2차 — `assets/effects/cut-mark(-big)`, `impact-rays(-big)`, `shock-ring-(s·m·l)`와 빛 시트(`assets/light/glow_<같은 이름>.png`): `tools/make_fx2.py` + `tools/fxkit.py`(code-drawn). 회색조로 굽고 게임이 색을 곱한다.
- 2026-11-24: 이펙트 v8 3차 — `assets/effects/flare.png`(별 섬광)과 `assets/light/glow_flare.png`: `tools/make_fx2.py`(code-drawn). 화풍 참고는 사용자가 준 INARI 화면(그림은 쓰지 않음).
- 2026-11-24: 이펙트 v8 4차 — `flare-s`(작은 별 섬광) 추가, 위험 구간을 레드로 다시 구움: `hit-critical`(make_fx2.py), `pipe-slash-critical(-flat)`(make_slash_hq.py), `aura-critical`(make_aura.py)와 그 빛 시트. 모두 code-drawn.
- 2026-11-24: 큰 마무리 연출 시트 `assets/effects/fin-burst.png`·`exec-crescent.png`와 빛 시트: `tools/make_fx2.py`(code-drawn, haze-fx 절차). 구성은 INARI 영상의 장면 순서를 참고(그림은 쓰지 않음). 처음 만든 도장 시트 exec-disc·exec-star는 삭제.
- 2026-11-24: 이펙트 v8 5차 — `assets/effects/pipe-slash*`(13종), `air-spin*`(4종), `puff`·`surge`·`dust-land`·`quake-blast`·`death-burst`, `ult-nova-*`(5종), `overload-burst`와 빛 시트를 `tools/make_fx2.py`(code-drawn, haze-fx 절차)로 다시 만듦.
- 2026-11-24: `assets/effects/overload-burst.png`(입자로만 만든 폭발)·`overload-gather.png`(모이는 기운)와 빛 시트: `tools/make_fx2.py`(code-drawn). 구성 방식은 pixelfx의 불덩이 입자를 참고(코드·결과물은 쓰지 않음).
- 2026-11-24: `glint`(맞부딪침 반짝임)는 만들었다가 같은 날 삭제(`assets/effects/glint.*`, `assets/light/glow_glint.png`): haze-inari 보류. 레시피는 `tools/make_fx2.py`에 보기 전용 시안으로 남아 있다(`--look glint`, `--look inari-smear`).
- 2026-11-24: 이펙트 v8 7차 — 입자 구성으로 다시 구움(`tools/make_fx2.py` pb_create·pring_create, code-drawn): `hit-*`(7종), `haze-blast`, `ult-nova-*`(5종), `death-burst`, `quake-blast`, 두 겹 시트 `impact-rays(-big)`·`shock-ring-s/m/l`와 그 빛 시트. `aura-stun`(오버로드 기절)은 전기 아크(make_aura.py)에서 붉은 불길 반복 시트로 (make_fx2.py stun_create, 빛 시트 `assets/light/glow_aura-stun.png` 추가).
- 2026-11-24: `assets/effects/flare.png`·`flare-s.png`와 빛 시트를 별 섬광 v2(진한 원반 + 주변광)로 다시 구움: `tools/make_fx2.py` flare_create(code-drawn). 구성은 사용자가 준 INARI 화면을 참고(그림은 쓰지 않음).
