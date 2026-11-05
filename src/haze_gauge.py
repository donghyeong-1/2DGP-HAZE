"""헤이즈 중독 게이지. 화면·입력과 무관한 순수 로직이라 단독으로 테스트할 수 있다."""
import config

# 구간 이름
DEAD = 'DEAD'
FADE = 'FADE'
NORMAL = 'NORMAL'
AWAKE = 'AWAKE'
CRITICAL = 'CRITICAL'
OVERLOAD = 'OVERLOAD'

_MULTIPLIERS = {
    FADE: config.MULT_FADE,
    NORMAL: config.MULT_NORMAL,
    AWAKE: config.MULT_AWAKE,
    CRITICAL: config.MULT_CRITICAL,
    OVERLOAD: config.MULT_NORMAL,
    DEAD: config.MULT_NORMAL,
}


class HazeGauge:
    def __init__(self, cap=config.GAUGE_CAP):
        self.cap = cap
        self.value = float(config.GAUGE_START)
        self.zone = self._zone_of(self.value)
        self.decay_interval = config.GAUGE_DECAY_INTERVAL
        self.enhance_cost = config.ENHANCE_COST
        self.enhance_timer = 0.0   # 남은 강화 시간
        self.stun_timer = 0.0      # 오버로드 기절 남은 시간
        self._timer = 0.0          # 감소/상승 주기 타이머
        self._high_haze = False
        self.listeners = []        # 이벤트 수신 함수 목록: f(name, gauge)

    # ----- 구간 판정 -----
    def _zone_of(self, value):
        if value <= 0:
            return DEAD
        if value >= self.cap:
            return OVERLOAD
        if value >= self.cap - config.CRITICAL_MARGIN:
            return CRITICAL
        if value >= config.ZONE_NORMAL_MAX:
            return AWAKE
        if value >= config.ZONE_FADE_MAX:
            return NORMAL
        return FADE

    def _emit(self, name):
        for f in self.listeners:
            f(name, self)

    def _set_zone(self, zone):
        if zone != self.zone:
            old, self.zone = self.zone, zone
            self._emit('zone:' + zone)
            return old
        return None

    # ----- 증감 (모든 변화는 여기를 거친다) -----
    def add(self, delta, reason=''):
        if self.zone == DEAD:
            return
        self.value += delta
        if self.value <= 0:
            self.value = 0.0
            self._set_zone(DEAD)
            self._emit('dead')
            return
        zone = self._zone_of(self.value)
        if zone == OVERLOAD:
            self._set_zone(OVERLOAD)
            self._emit('overload')
            self.stun_timer = config.OVERLOAD_STUN
            self.value = float(config.OVERLOAD_RESET)
            zone = self._zone_of(self.value)
        self._set_zone(zone)

    def drain(self, amount, floor=config.GAUNTLET_FLOOR):
        """건틀릿 충전용 감소. floor 아래로는 내려가지 않는다."""
        room = self.value - floor
        if room > 0:
            self.add(-min(amount, room), 'drain')

    # ----- 시간 경과 -----
    def tick(self, dt, high_haze=False):
        if self.zone == DEAD:
            return
        self.enhance_timer = max(0.0, self.enhance_timer - dt)
        self.stun_timer = max(0.0, self.stun_timer - dt)
        if high_haze != self._high_haze:
            self._high_haze = high_haze
            self._timer = 0.0
        self._timer += dt
        interval = config.HIGH_HAZE_INTERVAL if high_haze else self.decay_interval
        amount = config.HIGH_HAZE_AMOUNT if high_haze else -config.GAUGE_DECAY_AMOUNT
        while self._timer >= interval and self.zone != DEAD:
            self._timer -= interval
            self.add(amount, 'haze' if high_haze else 'decay')

    # ----- E 강화 -----
    @property
    def enhance_min(self):
        return self.enhance_cost + config.ENHANCE_FLOOR

    @property
    def enhanced(self):
        return self.enhance_timer > 0

    def can_enhance(self):
        return self.zone != DEAD and not self.enhanced and self.value >= self.enhance_min

    def use_enhance(self):
        if not self.can_enhance():
            return False
        self.add(-self.enhance_cost, 'enhance')
        self.enhance_timer = config.ENHANCE_TIME
        return True

    # ----- 구간 배율 -----
    def zone_multipliers(self):
        attack, speed = _MULTIPLIERS[self.zone]
        return {'attack': attack, 'speed': speed}
