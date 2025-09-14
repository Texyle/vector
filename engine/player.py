import math
import pygame
from .constants import *
from .camera import Camera
from numpy import float32 as fl
from .utils import *

class Player:
    def __init__(self, x: fl, y: fl, z: fl, f: fl):
        self.x = fl(x)
        self.y = fl(y)
        self.z = fl(z)
        self.vx = fl(0.0)
        self.vy = fl(0.0)
        self.vz = fl(0.0)
        self.facing = fl(f)
        self.forward = fl(0.0)
        self.strafe = fl(0.0)
        self.airborne = False
        self.sprinting = False
        self.sneaking = False
        self.jumping = False
        self.prev_slip = None
        self.ground_slip = fl(0.6)
        self.default_rotation = fl(0.0)
        self.rotation_offset = fl(0.0)
        self.rotation_queue = []
        self.turn_queue = []
        self.prev_sprint = False
        self.air_sprint_delay = True
        self.inertia_threshold = 0.005
    
    def draw(self, surface: pygame.Surface, camera: Camera):
        screen_x, screen_z = camera.world_to_screen(fl(self.x), fl(self.z))

        size = BLOCK_SIZE * PLAYER_SIZE
        
        pygame.draw.rect(surface, CHARACTER_COLOR, 
                            (screen_x - size//2, screen_z - size//2, size, size))

        # -90 to make 0 be UP
        angle_rad = math.radians(self.facing + 90)
        end_x = screen_x + math.cos(angle_rad) * FACING_LINE_LENGTH
        end_y = screen_z + math.sin(angle_rad) * FACING_LINE_LENGTH
        pygame.draw.line(surface, FACING_LINE_COLOR, (screen_x, screen_z), (end_x, end_y), 3)
        
        # Draw height indicator
        # height_indicator = 5 + int(self.y / 10)
        # pygame.draw.circle(surface, CHARACTER_COLOR, (screen_x, screen_z), height_indicator, 2)

    def tick(self):
        if self.airborne:
            slip = fl(1)
        else:
            slip = self.ground_slip

        if self.prev_slip is None:
            self.prev_slip = slip

        # Moving the player
        self.x += self.vx
        self.z += self.vz

        # Finalizing momentum
        self.vx *= fl(0.91) * self.prev_slip
        self.vz *= fl(0.91) * self.prev_slip

        # Applying inertia threshold
        if abs(self.vx) < self.inertia_threshold:
            self.vx = 0.0
        if abs(self.vz) < self.inertia_threshold:
            self.vz = 0.0

        # Calculating movement multiplier
        if self.airborne:
            movement = fl(0.02)
            # Sprinting start/stop is (by default) delayed by a tick midair
            if (self.air_sprint_delay and self.prev_sprint) or (not self.air_sprint_delay and self.sprinting):
                movement = fl(movement + movement * 0.3)
        else:
            movement = fl(0.1)
            drag = fl(0.91) * slip
            movement *= fl(0.16277136) / (drag * drag * drag)

        # Applying sprintjump boost
        if self.sprinting and self.jumping:
            facing = fl(self.facing * fl(0.017453292))
            self.vx -= mcsin(facing) * SPRINTJUMP_BOOST
            self.vz += mccos(facing) * SPRINTJUMP_BOOST

        # Applying sneaking
        forward = self.forward
        strafe = self.strafe
        if self.sneaking:
            forward = fl(float(self.forward) * 0.3)
            strafe = fl(float(self.strafe) * 0.3)
        
        forward *= fl(0.98)
        strafe *= fl(0.98)

        distance = fl(strafe * strafe + forward * forward)

        # The if avoids division by zero 
        if distance >= fl(0.0001):

            # Normalizes distance vector only if above 1
            distance = fl(math.sqrt(float(distance)))
            if distance < fl(1.0):
                distance = fl(1.0)

            # Modifies strafe and forward to account for movement
            distance = movement / distance
            forward = forward * distance
            strafe = strafe * distance

            # Adds rotated vectors to velocity
            sin_yaw = fl(mcsin(self.facing * fl(PI) / fl(180.0)))
            cos_yaw = fl(mccos(self.facing * fl(PI) / fl(180.0)))
            self.vx += float(strafe * cos_yaw - forward * sin_yaw)
            self.vz += float(forward * cos_yaw + strafe * sin_yaw)

        self.prev_sprint = self.sprinting
        self.prev_slip = slip

    def set_movement(self, w: bool, a: bool, s: bool, d: bool):
        if w and s:
            self.forward = fl(0.0)
        elif w:
            self.forward = fl(1.0)
        elif s:
            self.forward = fl(-1.0)
        else:
            self.forward = fl(0.0)

        if a and d:
            self.strafe = fl(0.0)
        elif a:
            self.strafe = fl(1.0)
        elif d:
            self.strafe = fl(-1.0)
        else:
            self.strafe = fl(0.0)

    def get_info_text(self):
        out_facing = self.facing % 180

        return [
            "X: {:.{}f}".format(self.x, INFO_PANEL_PRECISION),
            "Y: {:.{}f}".format(self.y, INFO_PANEL_PRECISION),
            "Z: {:.{}f}".format(self.z, INFO_PANEL_PRECISION),
            "F: {:.{}f}".format(out_facing, INFO_PANEL_PRECISION),
            "VX: {:.{}f}".format(self.vx, INFO_PANEL_PRECISION),
            "VY: {:.{}f}".format(self.vy, INFO_PANEL_PRECISION),
            "VZ: {:.{}f}".format(self.vz, INFO_PANEL_PRECISION),
            f"Airborne: {self.airborne}"
        ]
            