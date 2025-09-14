class Block:
    def __init__(self, x: int, y: int, z: int, blockage: bool = True):
        self.x = x
        self.y = y
        self.z = z
        self.blockage = blockage
        self.color = (0, 0, 0)