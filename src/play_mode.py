"""전투 진행 모드. 방을 불러오고 플레이어·UI를 world에 넣어 갱신한다."""
from pico2d import (SDL_KEYDOWN, SDL_QUIT, SDLK_ESCAPE, SDLK_F1, SDLK_F3, SDLK_F4, SDLK_F5, SDLK_F6, SDLK_F7, SDLK_F8,
                    SDLK_F9, SDLK_h, clear_canvas, get_events, hide_cursor, show_cursor, update_canvas)

import assets
import camera
import config
import effects
import game_framework
import game_world
import options
from player import Player
from stage import Stage
from ui import GameUI

room = None
player = None
stage = None
clear_notice = 0.0  # "방 클리어" 안내를 보여 줄 남은 시간
message = ''        # 아이템 획득·구매 실패 같은 짧은 안내
message_time = 0.0
TEST_KEYS = {SDLK_F6: 'stage1', SDLK_F7: 'stage2', SDLK_F8: 'stage3', SDLK_F9: 'boss'}   # 테스트 모드 바로가기


def enter():
    global room, player, stage, clear_notice, message_time
    message_time = 0.0
    hide_cursor()  # 화면의 조준점(십자)을 대신 쓴다
    game_world.clear()
    effects.reset()
    import drama
    drama.reset()
    clear_notice = 0.0
    import meta
    meta.ensure_loaded()
    player = Player(0, 0, None)
    meta.apply_to_player(player)                      # 은신처 영구 강화와 맡겨 둔 물건 (새 판 시작)
    player.gauge.listeners.append(_on_gauge_event)
    player.gauge.change_listeners.append(_on_gauge_change)
    stage = Stage(player, name='hideout')             # 판은 은신처에서 시작한다 (출발 문 -> 스테이지 1)
    stage.on_clear = _on_room_cleared
    stage.on_message = _show_message
    stage.on_pickup = _on_pickup
    stage.on_mutation = _on_mutation
    stage.on_npc = _on_npc
    stage.on_practice = _on_practice
    stage.start()
    room = stage.room
    game_world.add_object(player, game_world.LAYER_PLAYER)
    from atmosphere import Atmosphere
    from ambience import Ambience
    game_world.add_object(Atmosphere(player, stage), game_world.LAYER_UI)   # 구간 색·비네트·안개 (HUD보다 먼저 = 아래)
    game_world.add_object(Ambience(stage), game_world.LAYER_UI)             # 구역 환경음 (그림 없음)
    from tutorial import Tutorial
    game_world.add_object(GameUI(player, stage), game_world.LAYER_UI)
    from offscreen import OffscreenMarkers
    game_world.add_object(OffscreenMarkers(player, stage), game_world.LAYER_UI)  # 화면 밖 적 화살표 (큰 방·남은 적이 적을 때)
    from practice import PracticeHud
    game_world.add_object(PracticeHud(stage), game_world.LAYER_UI)          # 연습장 초당 피해 (연습장에서만 그린다)
    game_world.add_object(Tutorial(player, stage), game_world.LAYER_UI)     # 처음 안내판 (HUD 위에)
    from zone_card import ZoneCard
    card = ZoneCard(stage)
    game_world.add_object(card, game_world.LAYER_UI)                        # 구역 제목 카드 (Codex T33, 맨 위)
    from boss_intro import BossIntro
    game_world.add_object(BossIntro(stage, player, card), game_world.LAYER_UI)   # v8 보스 등장씬·보스 한 줄 대사 (카드 위)
    assets.play_music(music_for(stage))


def music_for(stage):
    """지금 방에 맞는 곡: 은신처 곡, 살아 있는 보스가 있으면 보스 곡(보스마다 MUSIC, 기본 'boss'),
    적이 남아 방이 잠겨 있으면 전투곡(v7), 아니면 스테이지 탐험곡. 보스 등장씬의 정적 동안은 None(곡 없음)."""
    name = getattr(stage, 'name', '')
    if name in ('hideout', 'practice'):
        return 'hideout'
    import boss_intro
    if boss_intro.music_held(stage):           # O2-1: 보스 등장씬의 정적 (이름 띠가 뜰 때 보스 곡)
        return None
    boss = stage.boss
    if boss is not None and boss.alive:
        return getattr(boss, 'MUSIC', 'boss')
    room_ = getattr(stage, 'room', None)
    if room_ is not None and getattr(room_, 'locked', False):
        return 'combat'
    return STAGE_MUSIC.get(name, 'explore')


STAGE_MUSIC = {'stage1': 'explore', 'stage2': 'factory', 'stage3': 'tower'}   # 11/21 퀄리티 계획 2-3


def _on_npc(npc):
    """은신처 NPC 앞에서 F: 그 NPC의 창을 연다. 연습장 표지판이면 연습장으로."""
    if npc.kind == 'practice':
        _go_stage('practice')
        return
    import npc_mode
    npc_mode.kind = npc.kind
    npc_mode.player = player
    game_framework.push_mode(npc_mode)


def draw_frozen():
    """멈춘 게임 화면 (NPC 창이 아래에 깐다)."""
    game_world.render(_apply_shake)
    assets.draw_offset = (0, 0)


def _show_message(text):
    global message, message_time
    message, message_time = text, 2.5
    assets.play_sound('pickup')


def _on_mutation(choices):
    """변이 보상 방을 깼다: 셋 중 하나를 고르는 카드 창을 위에 쌓는다."""
    import mutation_mode
    mutation_mode.setup(player, choices)
    game_framework.push_mode(mutation_mode)


def _on_pickup(item_id, text):
    """아이템을 얻었다: 화면 아래 이름·효과 띠."""
    assets.play_sound('pickup')
    for obj in game_world.world[game_world.LAYER_UI]:
        if hasattr(obj, 'show_pickup'):
            obj.show_pickup(item_id, text)


def _on_room_cleared(stage_):
    global clear_notice
    clear_notice = 3.0
    import drama
    assets.play_sound('kill_last')                     # 방의 마지막 적: 깊은 일격 + 종소리 (11/21)
    effects.request_hit_stop(drama.LAST_KILL_STOP)     # 그 순간 잠깐 멈춘다
    effects.add_trauma(0.2)
    boss = getattr(stage_, 'boss', None)
    effects.request_slow_motion(*(config.SLOW_BOSS if boss is not None and not boss.alive else config.SLOW_CLEAR))


# 게이지 변화 중 화면에 글자로 보여 줄 것들 (시간 경과는 너무 잦아서 뺀다)
_FLOAT_REASONS = {'hit', 'kill', 'damaged', 'enhance'}


def _on_gauge_change(delta, reason):
    if reason in _FLOAT_REASONS and delta != 0:
        color = (130, 235, 225) if delta > 0 else (240, 110, 120)
        import drama
        drama.gauge_number(player.x, player.y + config.PLAYER_HB_H + 40, delta, color)   # v7: 피해 숫자와 같은 글꼴


def _on_gauge_event(name, gauge):
    if name == 'overload':
        assets.play_sound('overload')


def exit():
    assets.set_music_duck(1.0)                     # 다른 화면으로 가면 음악 크기를 되돌린다
    game_world.clear()
    show_cursor()


def pause():
    show_cursor()
    if player is not None:
        player.release_inputs()                    # 다른 화면이 뜬다: 누르고 있던 키를 뗀 것으로 (떼는 신호가 그 화면으로 간다)


def resume():
    hide_cursor()
    if player is not None:
        player.sync_inputs()                       # 돌아왔다: 실제로 눌려 있는 키만 다시 누른 것으로


def handle_events():
    import pause_mode
    import boss_intro
    for event in get_events():
        if event.type == SDL_QUIT:
            game_framework.quit()
        elif boss_intro.freezing and boss_intro.filter_event(event) != 'pass':   # v8 보스 등장씬: Enter·Space로 넘긴다
            if boss_intro.filter_event(event) == 'advance':
                for obj in game_world.world[game_world.LAYER_UI]:
                    if isinstance(obj, boss_intro.BossIntro):
                        obj.advance()
        elif event.type == SDL_KEYDOWN and event.key == SDLK_ESCAPE:
            game_framework.push_mode(pause_mode)
        elif event.type == SDL_KEYDOWN and event.key in TEST_KEYS and options.test_mode:
            _test_jump(TEST_KEYS[event.key])              # v7 테스트 모드 바로가기
        elif event.type == SDL_KEYDOWN and event.key == SDLK_F1:
            config.DEBUG = not config.DEBUG
        elif event.type == SDL_KEYDOWN and config.DEBUG and event.key == SDLK_F3:
            player.gauge.add(10, 'debug')
        elif event.type == SDL_KEYDOWN and config.DEBUG and event.key == SDLK_F4:
            player.gauge.add(-10, 'debug')
        elif event.type == SDL_KEYDOWN and config.DEBUG and event.key == SDLK_h:
            player.take_hit(10, source='debug')
        elif event.type == SDL_KEYDOWN and config.DEBUG and event.key == SDLK_F5:
            stage.cleared.discard(stage.coord)  # 현재 방을 처음 상태로 다시 시작한다
            stage.enter_room(stage.coord)
        else:
            player.handle_event(event)


def update():
    global clear_notice, room, message_time, stage
    dt = game_framework.frame_time
    import cut_in
    if cut_in.running():                         # O1 실루엣 컷인: 실제 시간으로 그것만 돌고 세계는 멈춘다 (흔들림·대사도 그 뒤에)
        cut_in.update(dt)
        return
    effects.tick_shake(dt)
    if effects.tick_hit_stop(dt):  # 명중한 순간 화면이 잠깐 멈춘다
        return
    import zone_card
    import boss_intro
    if zone_card.freezing or boss_intro.freezing:   # 보스 등장씬·등장 카드 동안은 그것만 움직이고 싸움은 멈춘다 (Codex T34, v8)
        for obj in game_world.world[game_world.LAYER_UI]:
            if isinstance(obj, (zone_card.ZoneCard, boss_intro.BossIntro)):
                obj.update(dt)
        if boss_intro.effects_live():                # O2-2 크래셔 착지: 멈춘 동안에도 착지 이펙트(먼지·충격)는 돈다 (슬로모션 포함)
            scale = effects.time_scale()
            effects.tick_slow_motion(dt)
            for obj in list(game_world.world[game_world.LAYER_EFFECT]):
                if type(obj).__module__ == 'effects':
                    obj.update(dt * scale)
        assets.play_music(music_for(stage))      # 멈춘 동안에도: 이름 띠가 열리면 보스 곡 (O2-1)
        return
    scale = effects.time_scale()   # 슬로 모션: 게임 시간만 느려지고, 슬로 모션 자체는 실제 시간으로 줄어든다
    effects.tick_slow_motion(dt)
    dt *= scale
    clear_notice = max(0.0, clear_notice - dt)
    message_time = max(0.0, message_time - dt)
    game_world.update(dt)
    stage.update()
    room = stage.room
    assets.play_music(music_for(stage))
    camera.update(player, room, dt)
    if room.locked:
        clear_notice = 0.0  # 새 방에 들어오면 이전 방의 클리어 안내를 지운다
    if stage.name not in ('hideout', 'practice'):  # 은신처·연습장에서는 게이지가 줄지 않는다 (안전한 곳)
        player.gauge.tick(dt, room.is_high_haze)
    player.tick_run_clock(dt, stage.name)        # 판 기록의 시간 (은신처 제외)
    import drama
    drama.tick(dt, player)                       # 구간 번쩍임이 줄고, 체력이 낮거나 위험 구간이면 심장이 뛴다
    assets.set_music_duck(drama.music_duck(player.gauge.zone))   # 페이드 구간은 음악이 먹먹하게
    if stage.finished:
        import stage as stage_mod
        nxt = stage_mod.next_stage(stage)              # 다음 구역 (체력·게이지·아이템·무기·조각은 그대로)
        if nxt is None:                                  # 마지막 구역(탑)을 끝냈다: 탈출
            import ending_mode
            ending_mode.result = 'clear'
            game_framework.change_mode(ending_mode)
            return
        stage = nxt
        room = stage.room
        for obj in game_world.world[game_world.LAYER_UI]:
            if hasattr(obj, 'stage'):
                obj.stage = stage
        return
    if player.state == 'DEAD' and player.dead_time >= config.DEATH_SCREEN_DELAY:   # 쓰러지는 동작을 보여 준 뒤 사망 화면으로
        import ending_mode
        ending_mode.result = 'dead'
        game_framework.change_mode(ending_mode)


def _on_practice():
    """연습장에서 F: 연습 메뉴."""
    import practice_mode
    practice_mode.stage, practice_mode.player = stage, player
    game_framework.push_mode(practice_mode)


def _go_stage(name):
    """같은 플레이어로 name 구역의 시작 방을 연다 (연습장, 테스트 모드 바로가기)."""
    global stage, room
    import stage as stage_mod
    stage = stage_mod.jump_to(stage, name)
    player.no_death = name == 'practice'         # 연습장: 불러낸 적에게 맞아도 쓰러지지 않는다
    room = stage.room
    for obj in game_world.world[game_world.LAYER_UI]:
        if hasattr(obj, 'stage'):
            obj.stage = stage
    camera.snap(player, stage.room)
    assets.play_music(music_for(stage))


def _test_jump(target):
    """테스트 모드: 'stage1'~'stage3'이면 그 구역 시작 방, 'boss'면 지금 구역의 보스·관문 방으로."""
    global stage, room
    import stage as stage_mod
    if target == 'boss':
        coord = stage_mod.boss_room(stage)
        if coord is None:
            return
        stage.enter_room(coord, 'L')
    else:
        stage = stage_mod.jump_to(stage, target)
    room = stage.room
    for obj in game_world.world[game_world.LAYER_UI]:
        if hasattr(obj, 'stage'):
            obj.stage = stage
    camera.snap(player, stage.room)
    assets.play_music(music_for(stage))


def draw():
    import postfx
    clear_canvas()
    postfx.begin()                                 # 연출 중이면 세계 층을 그림판에 그린다 (당김·블러·왜곡, 11/24)
    game_world.render(_apply_shake)
    postfx.end()                                   # UI 층이 없을 때를 대비 (이미 끝냈으면 아무 일도 없다)
    assets.draw_offset = (0, 0)
    import transition
    transition.draw()                              # 화면 전환 점묘 (계획 4-3, 가장 위)
    update_canvas()


def _apply_shake(layer):
    """세계 레이어에는 카메라 이동과 화면 흔들림을 걸고 UI는 제자리에 둔다. 둘 다 정수 픽셀이다."""
    if layer == game_world.LAYER_ENEMY and room is not None:
        room.draw_foreground()                     # 전경 실루엣: 타일 위, 적·보스·주인공 아래 (캐릭터가 가장 위, 11/22)
    if layer == game_world.LAYER_UI:
        import postfx
        postfx.end()                               # 세계 층까지만 왜곡한다: UI는 화면에 그대로
    if layer < game_world.LAYER_UI:
        sx, sy = effects.shake_offset()
        cx, cy = camera.offset()
        assets.draw_offset = (cx + sx, cy + sy)
    else:
        assets.draw_offset = (0, 0)
