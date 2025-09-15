import pygame
from .blocks.stone import StoneBlock
from .constants import *
from .camera import Camera
from numpy import float32 as fl

class Level:
    def __init__(self):
        self.blocks = []
        self.test()

    def draw(self, surface: pygame.Surface, camera: Camera):
        screen_corners_world = [
            camera.screen_to_world(-BLOCK_SIZE, -BLOCK_SIZE),
            camera.screen_to_world(SCREEN_WIDTH + BLOCK_SIZE, -BLOCK_SIZE),
            camera.screen_to_world(SCREEN_WIDTH + BLOCK_SIZE, SCREEN_HEIGHT + BLOCK_SIZE),
            camera.screen_to_world(-BLOCK_SIZE, SCREEN_HEIGHT + BLOCK_SIZE)
        ]
        
        world_x_coords = [corner[0] for corner in screen_corners_world]
        world_z_coords = [corner[1] for corner in screen_corners_world]
        
        start_x = int(min(world_x_coords)) - 1
        end_x = int(max(world_x_coords)) + 1
        start_z = int(min(world_z_coords)) - 1
        end_z = int(max(world_z_coords)) + 1
        
        if DRAW_GRID:
            self.draw_grid(surface, camera, start_x, end_x, start_z, end_z)
        
        visible_blocks = self.get_blocks_in_area(start_x, start_z, end_x, end_z)
        for block in visible_blocks:
            self.draw_block(surface, camera, block)
        
        if DRAW_BLOCK_COORDINATES:
            self.draw_coordinates(surface, camera, visible_blocks)

    def draw_block(self, surface: pygame.Surface, camera: Camera, block):
        """Draw a single block"""
        corners_world = [
            (block.x - 0.5, block.z - 0.5),
            (block.x + 0.5, block.z - 0.5),
            (block.x + 0.5, block.z + 0.5),
            (block.x - 0.5, block.z + 0.5)
        ]
        
        corners_screen = [camera.world_to_screen(x, z) for x, z in corners_world]
        print(corners_screen)
        
        on_screen = False
        for screen_x, screen_y in corners_screen:
            if (0 <= screen_x < SCREEN_WIDTH and 0 <= screen_y < SCREEN_HEIGHT):
                on_screen = True
                break
        
        if not on_screen:
            return
        
        pygame.draw.polygon(surface, block.color, corners_screen)
        #pygame.draw.polygon(surface, (30, 30, 40), corners_screen, 1)

    def draw_grid(self, surface: pygame.Surface, camera: Camera, start_x: int, end_x: int, start_z: int, end_z: int):
        """Draw grid lines for the visible area"""
        # Draw vertical grid lines
        for x in range(start_x, end_x + 1):
            start_screen = camera.world_to_screen(x, start_z)
            end_screen = camera.world_to_screen(x, end_z)
            pygame.draw.line(surface, GRID_COLOR, start_screen, end_screen, 1)
        
        # Draw horizontal grid lines
        for z in range(start_z, end_z + 1):
            start_screen = camera.world_to_screen(start_x, z)
            end_screen = camera.world_to_screen(end_x, z)
            pygame.draw.line(surface, GRID_COLOR, start_screen, end_screen, 1)

    def draw_coordinates(self, surface: pygame.Surface, camera: Camera, blocks):
        """Draw coordinates only for visible blocks"""
        font = pygame.font.SysFont(FONT, 14)
        
        for block in blocks:
            center_screen = camera.world_to_screen(block.x, block.z)
            
            # Simple visibility check
            if not (0 <= center_screen[0] < SCREEN_WIDTH and 0 <= center_screen[1] < SCREEN_HEIGHT):
                continue
            
            coord_text = f"{int(block.x)},{int(block.z)}"
            text_surface = font.render(coord_text, True, (200, 200, 200))
            
            # Center text in block
            text_x = center_screen[0] - text_surface.get_width() // 2
            text_y = center_screen[1] - text_surface.get_height() // 2
            
            surface.blit(text_surface, (text_x, text_y))

    def get_blocks_in_area(self, start_x: int, start_z: int, end_x: int, end_z: int):
        """Get all blocks within the specified area"""
        return [block for block in self.blocks 
                if start_x <= block.x <= end_x and start_z <= block.z <= end_z]

    def get_block_at(self, x: int, z: int):
        """Find a block at the given world coordinates"""
        for block in self.blocks:
            if int(block.x) == x and int(block.z) == z:
                return block
        return None

    def test(self):
        self.blocks.append(StoneBlock(0, 0, 0))