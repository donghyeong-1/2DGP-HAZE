"""저장·설정 파일을 안전하게 읽고 쓴다 (2026-11-21 퀄리티 계획 3-2).

쓰기: 임시 파일(.tmp)에 다 쓴 뒤 바꿔 끼운다(os.replace). 쓰다가 꺼져도 원래 파일은 그대로 남는다.
      바꾸기 전 파일이 멀쩡하면 .bak으로 남긴다(바로 전 저장).
읽기: 깨진 파일은 .broken으로 복사해 두고(나중에 덮어써 지워지지 않게) .bak에서 읽는다. 둘 다 안 되면 None.
실패는 모두 log에 남기고 예외를 내지 않는다.
"""
import json
import os
import shutil

import log


def _read(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def read_json(path):
    """파일의 JSON 값. 없으면 None. 깨졌으면 .broken으로 남기고 .bak을 읽는다(그것도 안 되면 None)."""
    if not os.path.exists(path):
        return None
    try:
        return _read(path)
    except (OSError, ValueError) as e:            # ValueError: JSON·글자 인코딩이 깨짐
        log.error(f'저장 파일이 깨졌다: {path}', e)
        try:
            shutil.copyfile(path, path + '.broken')
        except OSError as e2:
            log.error(f'깨진 파일을 남기지 못했다: {path}', e2)
    try:
        data = _read(path + '.bak')
        log.write(f'바로 전 저장(.bak)에서 되살렸다: {path}')
        return data
    except (OSError, ValueError):
        log.write(f'되살릴 저장이 없어 기본값으로 시작한다: {path}')
        return None


def write_json(path, data):
    """임시 파일에 쓰고 바꿔 끼운다. 성공하면 True."""
    tmp = path + '.tmp'
    try:
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        if os.path.isfile(path):
            try:
                _read(path)                          # 멀쩡한 파일만 .bak으로 (깨진 것으로 .bak을 덮지 않게)
                shutil.copyfile(path, path + '.bak')
            except (OSError, ValueError):
                pass
        os.replace(tmp, path)
        return True
    except (OSError, TypeError, ValueError) as e:
        log.error(f'저장하지 못했다: {path}', e)
        try:
            if os.path.isfile(tmp):
                os.remove(tmp)
        except OSError:
            pass
        return False
