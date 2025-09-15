from .block import Block
from ..bounding_box import BoundingBox

class StoneBlock(Block):
    def __init__(self, x: int, y: int, z: int, blockage: bool = True):
        super().__init__(x, y, z, blockage)
        self.color = (130, 130, 130)
        self.bounding_box = BoundingBox(x, x+1, y, y+1, z, z+1)