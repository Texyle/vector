import pygame
from engine.engine import Engine

def main():
    pygame.init()
    pygame.display.set_caption("Vector Engine")
    
    engine = Engine()
    engine.run()
    
    pygame.quit()

if __name__ == "__main__":
    main()