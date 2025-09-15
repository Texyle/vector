import pygame
from .blocks.stone import StoneBlock
from .constants import *
from .camera import Camera
from numpy import float32 as fl
from .bounding_box import BoundingBox
from .blocks.block import Block

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
        start_y = 0
        end_y = 100
        
        if DRAW_GRID:
            self.draw_grid(surface, camera, start_x, end_x, start_z, end_z)
        
        visible_blocks = self.get_blocks_in_area(start_x, end_x, start_y, end_y, start_z, end_z)
        for block in visible_blocks:
            self.draw_block(surface, camera, block)
        
        if DRAW_BLOCK_COORDINATES:
            self.draw_coordinates(surface, camera, visible_blocks)

    def draw_block(self, surface: pygame.Surface, camera: Camera, block: Block):
        corners_world = [
            (block.x, block.z),
            (block.x + 1, block.z),
            (block.x + 1, block.z + 1),
            (block.x, block.z + 1)
        ]
        
        corners_screen = [camera.world_to_screen(x, z) for x, z in corners_world]
        
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
        for x in range(start_x, end_x + 1):
            start_screen = camera.world_to_screen(x, start_z)
            end_screen = camera.world_to_screen(x, end_z)
            pygame.draw.line(surface, GRID_COLOR, start_screen, end_screen, 1)
        
        for z in range(start_z, end_z + 1):
            start_screen = camera.world_to_screen(start_x, z)
            end_screen = camera.world_to_screen(end_x, z)
            pygame.draw.line(surface, GRID_COLOR, start_screen, end_screen, 1)

    def draw_coordinates(self, surface: pygame.Surface, camera: Camera, blocks):
        font = pygame.font.SysFont(FONT, 14)
        
        for block in blocks:
            center_screen = camera.world_to_screen(block.x+0.5, block.z+0.5)
            
            if not (0 <= center_screen[0] < SCREEN_WIDTH and 0 <= center_screen[1] < SCREEN_HEIGHT):
                continue
            
            coord_text = f"{int(block.x)},{int(block.z)}"
            text_surface = font.render(coord_text, True, (200, 200, 200))
            
            text_x = center_screen[0] - text_surface.get_width() // 2
            text_y = center_screen[1] - text_surface.get_height() // 2
            
            surface.blit(text_surface, (text_x, text_y))
            
    def check_collision(self, bounding_box: BoundingBox) -> Block:
        blocks = self.get_blocks_in_area(int(bounding_box.min_x)-1, int(bounding_box.max_x)+1,
                                         int(bounding_box.min_y), int(bounding_box.max_y),
                                         int(bounding_box.min_z)-1, int(bounding_box.max_z)+1)
        
        for block in blocks:
            if block.blockage is False:
                continue
            
            if self.bbox_intersect(bounding_box, block.get_bounding_box()):
                return block
            
        return None

    def bbox_intersect(self, bbox1: BoundingBox, bbox2: BoundingBox) -> bool:
        return (bbox1.min_x < bbox2.max_x and 
                bbox1.max_x > bbox2.min_x and
                bbox1.min_y < bbox2.max_y and
                bbox1.max_y > bbox2.min_y and
                bbox1.min_z < bbox2.max_z and
                bbox1.max_z > bbox2.min_z)

    def get_blocks_in_area(self, start_x: int, end_x: int, start_y: int, end_y: int, start_z: int, end_z: int):
        return [block for block in self.blocks 
                if start_x <= block.x <= end_x and start_z <= block.z <= end_z and start_y <= block.y <= end_y]

    def test(self):
        self.blocks.append(StoneBlock(3, 21, 0, blockage=False))
        self.blocks.append(StoneBlock(3, 21, 1))
        self.blocks.append(StoneBlock(3, 21, 2, blockage=False))