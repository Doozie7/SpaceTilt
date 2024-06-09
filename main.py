# SpaceTilt Game
# by John Powell, June 2024
# Portions of the code attributed to Russ Hughes (GitHub: russhughes)

from machine import Pin, I2C, SPI, ADC, PWM
import utime
import random
import math
import gc9a01
from qmi8658 import QMI8658
from tft_config import config
import vga1_8x8 as font
import vga1_bold_16x16 as font2

# Constants
SHIP_POLY = [(-7, -7), (7, 0), (-7, 7), (-3, 0), (-7, -7)]
EXPLOSION_POLY = [(-4, -4), (-4, 4), (4, 4), (4, -4), (-4, -4)]
ASTEROID_RADIUS = [5, 10, 16]
ASTEROID_SCALE = [0.33, 0.66, 1.0]
ASTEROID_POLY = [
    (-5, -15), (-2, -13), (11, -14), (15, -7), (14, 0),
    (16, 5), (11, 16), (7, 16), (-7, 14), (-14, 7),
    (-13, 1), (-14, -8), (-11, -15), (-5, -15)
]
FRAME_TIME = 60

# Initialize display and sensors
tft = config()
qmi8658 = QMI8658()
old_timer_text = ""

class Poly:
    """Class to represent and manipulate polygons."""
    def __init__(self, polygon, x=None, y=None, v_x=None, v_y=None, angle=None, spin=None, scale=None, radius=None, max_velocity=3, counter=0):
        self.polygon = polygon if scale is None else [(int(scale * x[0]), int(scale * x[1])) for x in polygon]
        self.x = random.randint(0, tft.width()) if x is None else x
        self.y = random.randint(0, tft.height()) if y is None else y
        self.angle = float(0) if angle is None else angle
        self.spin = random.randint(-3, 3) / 16 if spin is None else spin
        self.velocity_x = random.uniform(0.50, 0.99) * 6 - 3 + 0.75 if v_x is None else v_x
        self.velocity_y = random.uniform(0.50, 0.99) * 6 - 3 + 0.75 if v_y is None else v_y
        self.radius = radius
        self.max_velocity = max_velocity
        self.counter = counter

    def rotate(self, rad):
        """Rotate the polygon."""
        self.angle += rad
        if self.angle > 2 * math.pi:
            self.angle = 0
        elif self.angle < 0:
            self.angle = 2 * math.pi

    def move(self):
        """Move the polygon based on its velocity."""
        if self.spin != 0:
            self.rotate(self.spin)
        self.x += int(self.velocity_x)
        self.y += int(self.velocity_y)
        self.x %= tft.width()
        self.y %= tft.height()

    def draw(self, color):
        """Draw the polygon on the display."""
        tft.polygon(self.polygon, self.x, self.y, color, self.angle, 0, 0)

    def collision(self, poly):
        """Check for collision with another polygon."""
        return abs(((self.x - poly.x) * (self.x - poly.x) + (self.y - poly.y) * (self.y - poly.y)) < (self.radius + poly.radius) * (self.radius + poly.radius))

def show_splash_screen(tft, image_path):
    """Display splash screen."""
    tft.jpg(image_path, 0, 0)
    utime.sleep(3)
    tft.fill(gc9a01.BLACK)

def draw_timer(tft, minutes, seconds):
    """Draw the timer at the bottom of the screen."""
    global old_timer_text
    timer_text = f"Time: {minutes:02d}:{seconds:02d}"
    if old_timer_text != timer_text:
        old_timer_text = timer_text
        tft.fill_rect(0, tft.height() - 20, tft.width(), 20, gc9a01.BLACK)
        text_width = len(timer_text) * 8
        tft.text(font, timer_text, (tft.width() - text_width) // 2, tft.height() - 20, gc9a01.WHITE)

def create_asteroid(size, x=None, y=None, v_x=None, v_y=None):
    """Create an asteroid of a given size."""
    return Poly(
        ASTEROID_POLY,
        x=x,
        y=y,
        v_x=v_x,
        v_y=v_y,
        scale=ASTEROID_SCALE[size],
        radius=ASTEROID_RADIUS[size],
        counter=size)

def update_ship():
    """Update the ship's position and orientation based on accelerometer data."""
    acc_x, acc_y, _ = qmi8658.Read_XYZ()
    
    rad_max = 2 * math.pi
    ship_rad_frame = rad_max / 16
    ship_accel_frame = 0.9
    ship_drag_frame = 0.025    

    # accelerometer reading for the x-axis
    ship.velocity_y -= acc_x * ship_accel_frame
    ship.velocity_x += acc_y * ship_accel_frame

    ship.velocity_y -= ship.velocity_x * ship_drag_frame
    ship.velocity_x += ship.velocity_y * ship_drag_frame

    # Gradually rotate the ship in the direction of travel
    if ship.velocity_x != 0 or ship.velocity_y != 0:
        target_angle = math.atan2(ship.velocity_y, ship.velocity_x)
        angle_difference = target_angle - ship.angle
        angle_difference = (angle_difference + math.pi) % (2 * math.pi) - math.pi  # Normalize angle difference
        ship.angle += angle_difference * 0.2  # Adjust 0.1 to change rotation speed

    # Ensure ship.angle is always positive
    ship.angle %= 2 * math.pi

    if ship.velocity_x > ship.max_velocity:
        ship.velocity_x = ship.max_velocity
    elif ship.velocity_x < -ship.max_velocity:
        ship.velocity_x = -ship.max_velocity

    if ship.velocity_y > ship.max_velocity:
        ship.velocity_y = ship.max_velocity
    elif ship.velocity_y < -ship.max_velocity:
        ship.velocity_y = -ship.max_velocity

    if abs(ship.velocity_x) < 0.1:
        ship.velocity_x = 0.0

    if abs(ship.velocity_y) < 0.1:
        ship.velocity_y = 0.0

    ship.move()
    ship.draw(gc9a01.WHITE)
    
    # Uncomment to display ship's angle
    # t_display = f"{ship.angle:.2f}"
    # tft.fill_rect(0, 0, tft.width(), 20, gc9a01.BLACK)
    # text_width = len(t_display) * 8
    # tft.text(font, t_display, (tft.width() - text_width) // 2, 20, gc9a01.WHITE)

def update_asteroids():
    """Update the position and draw the asteroids."""
    not_hit = True
    for asteroid in asteroids:
        asteroid.draw(gc9a01.BLACK)
        asteroid.move()
        asteroid.draw(gc9a01.WHITE)
        if asteroid.collision(ship):
            ship.draw(gc9a01.BLACK)
            ship.velocity_x = 0.0
            ship.velocity_y = 0.0
            not_hit = False
    return not_hit

def explode_ship():
    """Handle ship explosion animation."""
    ship.counter += 1
    if ship.counter % 2 == 0:
        tft.polygon(EXPLOSION_POLY, ship.x, ship.y, gc9a01.BLACK, 0.785398)
        tft.polygon(EXPLOSION_POLY, ship.x, ship.y, gc9a01.WHITE)
    else:
        tft.polygon(EXPLOSION_POLY, ship.x, ship.y, gc9a01.WHITE, 0.785398)
        tft.polygon(EXPLOSION_POLY, ship.x, ship.y, gc9a01.BLACK)
    if ship.counter > 25:
        tft.polygon(EXPLOSION_POLY, ship.x, ship.y, gc9a01.BLACK)
        ship.x = width >> 1
        ship.y = height >> 1
        ship.counter = 0
        return True
    return False

def game_loop():
    """Main game loop."""
    global ship, asteroids, ship_alive, start_time

    start_time = utime.ticks_ms()

    # Game loop
    while True:
        last_frame = utime.ticks_ms()

        elapsed_time_ms = utime.ticks_diff(utime.ticks_ms(), start_time)
        elapsed_time_s = elapsed_time_ms // 1000
        minutes = elapsed_time_s // 60
        seconds = elapsed_time_s % 60

        # Draw the timer at the bottom of the screen
        draw_timer(tft, minutes, seconds)

        if len(asteroids) == 0:
            asteroids = [create_asteroid(2), create_asteroid(2), create_asteroid(2)]
            
        ship.draw(gc9a01.BLACK)

        if ship_alive:
            update_ship()
        else:
            ship_alive = explode_ship()
            start_time = utime.ticks_ms()

        not_hit = update_asteroids()
        if ship_alive:
            ship_alive = not_hit
        else:
            display_game_over(minutes, seconds)
            break

        # Frame rate control
        while utime.ticks_diff(utime.ticks_ms(), last_frame) < FRAME_TIME:
            pass

def display_game_over(minutes, seconds):
    """Display Game Over screen."""
    tft.fill(gc9a01.BLACK)
    
    # Game Over text
    game_over_text = "GAME OVER"
    text_width = len(game_over_text) * 16
    tft.text(font2, game_over_text, (tft.width() - text_width) // 2, (tft.height() // 2) - 10, gc9a01.RED)
    
    # Your Time text
    timer_text = f"Time: {minutes:02d}:{seconds:02d}"
    timer_text_width = len(timer_text) * 8
    tft.text(font, timer_text, (tft.width() - timer_text_width) // 2, (tft.height() // 2) + 20, gc9a01.WHITE)
    
    utime.sleep(3)

def main():
    while True:
        # Show splash screen
        show_splash_screen(tft, "/assets/splash.jpg")

        # Initialize game variables
        global ship, asteroids, ship_alive, width, height

        width = tft.width()
        height = tft.height()

        ship_alive = True

        ship = Poly(
            SHIP_POLY,
            x=width >> 1,
            y=height >> 1,
            v_x=0,
            v_y=0,
            radius=7,
            spin=0.0
        )

        asteroids = []

        game_loop()

if __name__ == '__main__':
    main()
