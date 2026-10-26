IMU_GRAVITY = 16384.0
# Axis 0 / sign as used by the stock merge_conflict tilt games.
TILT_FULL = 0.25
TILT_DEADZONE = 0.04
TILT_SMOOTH_MS = 80


class Controls:
    """Movement: physical LEFT/RIGHT and tilt steer sideways, the touch pad steers in 8 directions."""

    def __init__(self, tilt=False):
        self.tilt = tilt
        self.level = 0.0
        self.flip = False
        self.lean = 0.0

    def calibrate(self):
        self.level = badge.imu()[0] / IMU_GRAVITY
        self.flip = badge.upside_down()
        self.lean = 0.0

    def axis(self, dt_ms):
        """(x, y) movement, each from -1 to 1."""
        move = 0.0
        if badge.buttons.held(BUTTON_LEFT):
            move -= 1.0
        if badge.buttons.held(BUTTON_RIGHT):
            move += 1.0

        # Diagonals on the touch pad come back as (1, 1); keep them at full speed, not faster.
        pad = badge.pad.direction()
        size = max(1.0, pad.length())
        move += pad.x / size
        rise = pad.y / size

        if self.tilt:
            raw = badge.imu()[0] / IMU_GRAVITY - self.level
            if self.flip:
                raw = -raw
            self.lean += (raw - self.lean) * min(1.0, dt_ms / TILT_SMOOTH_MS)
            size = abs(self.lean)
            if size > TILT_DEADZONE:
                sign = 1.0 if self.lean > 0 else -1.0
                move += sign * (size - TILT_DEADZONE) / (TILT_FULL - TILT_DEADZONE)

        return max(-1.0, min(1.0, move)), rise
