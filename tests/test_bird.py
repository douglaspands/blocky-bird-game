from src.bird import Bird
from src.config import FLAP_IMPULSE, GRAVITY, HITBOX_SCALE, MAX_FALL_SPEED


def test_gravity_accumulates_each_frame():
    bird = Bird(100, 100)
    bird.update()
    assert bird.vel_y == GRAVITY
    bird.update()
    assert bird.vel_y == GRAVITY * 2


def test_fall_speed_is_capped():
    bird = Bird(100, 100)
    for _ in range(200):
        bird.update()
    assert bird.vel_y == MAX_FALL_SPEED


def test_top_of_screen_clamps_position_without_negative_velocity():
    bird = Bird(100, 0)
    bird.vel_y = -5
    bird.update()
    assert bird.pos.y == 0
    assert bird.vel_y == 0


def test_flap_sets_impulse_and_upward_angle():
    bird = Bird(100, 300)
    bird.flap()
    assert bird.vel_y == FLAP_IMPULSE
    assert bird.angle == 30


def test_angle_interpolates_down_while_falling():
    bird = Bird(100, 100)
    bird.update()
    assert bird.angle < 0
    first_angle = bird.angle
    bird.update()
    assert bird.angle <= first_angle


def test_angle_never_exceeds_max_down():
    bird = Bird(100, 100)
    for _ in range(100):
        bird.update()
    assert bird.angle == -60


def test_hitbox_is_scaled_and_centered_on_sprite():
    bird = Bird(100, 200)
    rect = bird.rect
    assert rect.width == round(bird.size * HITBOX_SCALE)
    assert rect.height == round(bird.size * HITBOX_SCALE)
    assert rect.centerx == round(bird.pos.x + bird.size / 2)
    assert rect.centery == round(bird.pos.y + bird.size / 2)


def test_update_idle_bobs_without_gravity():
    bird = Bird(100, 300)
    bird.update_idle()
    assert bird.vel_y == 0
    assert bird.angle == 0
