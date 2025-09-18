from .block import Block
from ..bounding_box import BoundingBox

class Connection:
    POSITIVE_X = (1, 0)
    NEGATIVE_X = (-1, 0)
    POSITIVE_Z = (0, 1)
    NEGATIVE_Z = (0, -1)

class GlassPane(Block):
    def __init__(self, x: int, y: int, z: int, blockage: bool = True, connections: list[tuple] = [], goal: bool = True):
        super().__init__(x, y, z, blockage)
        self.color = (130, 130, 130)
        
        if not connections:
            connections.append(Connection.POSITIVE_X)
            connections.append(Connection.NEGATIVE_X)
            connections.append(Connection.POSITIVE_Z)
            connections.append(Connection.NEGATIVE_Z)
            self.bounding_box.append(BoundingBox(x+6/16, x+8/16, y, y+1, z, z+1))
            
        if Connection.POSITIVE_X in connections:
            self.bounding_box.append(BoundingBox(x, x+8/16, y, y+1, z+7/16, z+9/16))
        if Connection.NEGATIVE_X in connections:
            self.bounding_box.append(BoundingBox(x+8/16, x+1, y, y+1, z+7/16, z+9/16))
        if Connection.POSITIVE_Z in connections:
            self.bounding_box.append(BoundingBox(x+7/16, x+9/16, y, y+1, z, z+8/16))
        if Connection.NEGATIVE_Z in connections:
            self.bounding_box.append(BoundingBox(x+7/16, x+9/16, y, y+1, z+8/16, z+1))