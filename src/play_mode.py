"""전투 진행 모드. 방을 불러오고 플레이어·UI를 world에 넣어 갱신한다."""
from pico2d import (SDL_KEYDOWN, SDL_QUIT, SDLK_ESCAPE, SDLK_F1, SDLK_F3, SDLK_F4, SDLK_h, clear_canvas,
                    get_events, update_canvas)

import config
import game_framework
import game_world
from player import Player
from room import Room
from ui import GameUI

room = None
player = None


def enter():
    global room, player
    game_world.clear()
    room = Room.load('test_01')
    player = Player(room.spawn[0], room.spawn[1], room)
    game_world.add_object(room, game_world.LAYER_BACKGROUND)
    game_world.add_object(player, game_world.LAYER_PLAYER)
    game_world.add_object(GameUI(player), game_world.LAYER_UI)


def exit():
    game_world.clear()


def pause():
    pass


def resume():
    pass


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
        else:
            player.handle_event(event)


def update():
    dt = game_framework.frame_time
    game_world.update(dt)
    player.gauge.tick(dt, room.is_high_haze)
    if player.state == 'DEAD':
        import ending_mode
        ending_mode.result = 'dead'
        game_framework.change_mode(ending_mode)


def draw():
    clear_canvas()
    game_world.render()
    update_canvas()
