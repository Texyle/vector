from .block import Block

class StoneBlock(Block):
    def __init__(self, x: int, y: int, z: int, blockage: bool = True):
        super().__init__(x, y, z, blockage)
        self.color = (130, 130, 130)