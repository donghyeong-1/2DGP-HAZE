# Kenney 효과음 원본 (효과음 v2·v3가 쓰는 것만)

- 작가: Kenney Vleugels (Kenney.nl)
- 묶음과 원래 페이지:
  - Impact Sounds — https://kenney.nl/assets/impact-sounds
  - Interface Sounds — https://kenney.nl/assets/interface-sounds
  - Sci-fi Sounds — https://kenney.nl/assets/sci-fi-sounds
  - RPG Audio — https://kenney.nl/assets/rpg-audio
  - Digital Audio — https://kenney.nl/assets/digital-audio
  - UI Audio (압축 안 이름 'UI SFX Set') — https://kenney.nl/assets/ui-audio (2026-11-28 S3: 메뉴 소리)
- 라이선스: CC0 1.0 (출처 표시 의무 없음). 묶음마다 압축에 든 `License.txt`를 그대로 둔다. 그 문구:
  > License (Creative Commons Zero, CC0) http://creativecommons.org/publicdomain/zero/1.0/
  > You may use these assets in personal and commercial projects.
  > Credit (Kenney or www.kenney.nl) would be nice but is not mandatory.
- 받은 날짜: 2026-11-24 (사용자가 kenney.nl에서 받은 압축 `kenney_<묶음>.zip` 다섯). 2026-11-27 효과음 v3에서 같은 압축에서 원본을 더 꺼냈다.
  UI Audio는 사용자가 2026-11-27에 받은 `kenney_ui-audio.zip`(411,949바이트). 2026-11-28에 새 빈 폴더에 음원과 License.txt만 풀어 쓴 8개만 `ui-audio/`에 넣었다(.url·Preview는 쓰지 않음).
  그 License.txt 원문: "UI SFX Set / by Kenney Vleugels (Kenney.nl) / License (Creative Commons Zero, CC0) http://creativecommons.org/publicdomain/zero/1.0/ / You may use these assets in personal and commercial projects. Credit (Kenney or www.kenney.nl) would be nice but is not mandatory."
  11-27에 kenney.nl은 자동 요청에 403을 돌려 원래 페이지의 라이선스 문구를 다시 읽지 못했다. 압축 안의 License.txt와
  사이트 Free Game Dev Assets의 목록(catalog/audio/kenney-*.md: license CC0, verified 2026-11-18, 근거 "Live pack page ... License = Creative Commons CC0")으로 확인했다.
- 쓰는 곳: `tools/make_sfx_v2.py`(→ assets/sfx), `tools/make_sfx_v3.py`(→ assets/sfx_v3, 원본별 쓰임은 assets/sfx_v3/MANIFEST.json).
- 여기에는 쓰는 파일만 넣는다(묶음 전체가 아니다).
