"""전투 진행 모드. 방을 불러오고 플레이어·UI를 world에 넣어 갱신한다."""
from pico2d import (SDL_KEYDOWN, SDL_QUIT, SDLK_ESCAPE, SDLK_F1, SDLK_F3, SDLK_F4, SDLK_F5, SDLK_h, clear_canvas,
                    get_events, hide_cursor, show_cursor, update_canvas)

import assets
import camera
import config
import effects
import game_framework
import game_world
from player import Player
from stage import Stage
from ui import GameUI

room = None
player = None
stage = None
clear_notice = 0.0  # "방 클리어" 안내를 보여 줄 남은 시간
message = ''        # 아이템 획득·구매 실패 같은 짧은 안내
message_time = 0.0


def enter():
    global room, player, stage, clear_notice, message_time
    message_time = 0.0
    hide_cursor()  # 화면의 조준점(십자)을 대신 쓴다
    game_world.clear()
    effects.reset()
    clear_notice = 0.0
    player = Player(0, 0, None)
    player.gauge.listeners.append(_on_gauge_event)
    player.gauge.change_listeners.append(_on_gauge_change)
    stage = Stage(player)
    stage.on_clear = _on_room_cleared
    stage.on_message = _show_message
    stage.start()
    room = stage.room
    game_world.add_object(player, game_world.LAYER_PLAYER)
    game_world.add_object(GameUI(player, stage), game_world.LAYER_UI)


def _show_message(text):
    global message, message_time
    message, message_time = text, 2.5
    assets.play_sound('pickup')


def _on_room_cleared(stage_):
    global clear_notice
    clear_notice = 3.0
    assets.play_sound('pickup')
    effects.add_trauma(0.2)


# 게이지 변화 중 화면에 글자로 보여 줄 것들 (시간 경과는 너무 잦아서 뺀다)
_FLOAT_REASONS = {'hit', 'kill', 'damaged', 'enhance'}


def _on_gauge_change(delta, reason):
    if reason in _FLOAT_REASONS and delta != 0:
        color = (130, 235, 225) if delta > 0 else (240, 110, 120)
        effects.float_text(player.x, player.y + config.PLAYER_HB_H + 40, f'{delta:+g}%', color)


def _on_gauge_event(name, gauge):
    if name == 'overload':
        assets.play_sound('overload')


def exit():
    game_world.clear()
    show_cursor()


def pause():
    show_cursor()


def resume():
    hide_cursor()


def handle_events():
    import pause_mode
    for event in get_events():
        if event.type == SDL_QUIT:
            game_framework.quit()
        elif event.type == SDL_KEYDOWN and event.key == SDLK_ESCAPE:
            game_framework.push_mode(pause_mode)
        elif event.type == SDL_KEYDOWN and event.key == SDLK_F1:
            config.DEBUG = not config.DEBUG
        elif event.type == SDL_KEYDOWN and config.DEBUG and event.key == SDLK_F3:
            player.gauge.add(10, 'debug')
        elif event.type == SDL_KEYDOWN and config.DEBUG and event.key == SDLK_F4:
            player.gauge.add(-10, 'debug')
        elif event.type == SDL_KEYDOWN and config.DEBUG and event.key == SDLK_h:
            player.take_hit(10)
        elif event.type == SDL_KEYDOWN and config.DEBUG and event.key == SDLK_F5:
            stage.cleared.discard(stage.coord)  # 현재 방을 처음 상태로 다시 시작한다
            stage.enter_room(stage.coord)
        else:
            player.handle_event(event)


def update():
    dt = game_framework.frame_time
    effects.tick_shake(dt)
    if effects.tick_hit_stop(dt):  # 명중한 순간 화면이 잠깐 멈춘다
        return
    global clear_notice, room, message_time
    clear_notice = max(0.0, clear_notice - dt)
    message_time = max(0.0, message_time - dt)
    game_world.update(dt)
    stage.update()
    room = stage.room
    camera.update(player, room, dt)
    if room.locked:
        clear_notice = 0.0  # 새 방에 들어오면 이전 방의 클리어 안내를 지운다
    player.gauge.tick(dt, room.is_high_haze)
    if stage.finished:
        import ending_mode
        ending_mode.result = 'clear'
        game_framework.change_mode(ending_mode)
        return
    if player.state == 'DEAD':
        import ending_mode
        ending_mode.result = 'dead'
        game_framework.change_mode(ending_mode)


def draw():
    clear_canvas()
    game_world.render(_apply_shake)
    assets.draw_offset = (0, 0)
    update_canvas()


def _apply_shake(layer):
    """세계 레이어에는 카메라 이동과 화면 흔들림을 걸고 UI는 제자리에 둔다. 둘 다 정수 픽셀이다."""
    if layer < game_world.LAYER_UI:
        sx, sy = effects.shake_offset()
        cx, cy = camera.offset()
        assets.draw_offset = (cx + sx, cy + sy)
    else:
        assets.draw_offset = (0, 0)
