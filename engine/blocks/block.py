from ..bounding_box import BoundingBox

class Block:
    def __init__(self, x: int, y: int, z: int, blockage: bool = True, ground: bool = True):
        self.x = x
        self.y = y
        self.z = z
        self.blockage = blockage
        self.ground = ground
        self.bounding_box = None
        self.color = (0, 0, 0)
        
    def get_bounding_box(self) -> BoundingBox:
        return self.bounding_box