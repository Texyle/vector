class BoundingBox:
    def __init__(self, min_x: float, max_x: float, min_y: float, max_y: float, min_z: float, max_z: float):
        self.min_x = min_x
        self.max_x = max_x
        self.min_y = min_y
        self.max_y = max_y
        self.min_z = min_z
        self.max_z = max_z
        
    def grow(self, amount: float):
        self.min_x += amount 
        self.max_x += amount
        self.min_y += amount
        self.max_y += amount
        self.min_z += amount
        self.max_z += amount
    
    def move(self, x: float = 0, y: float = 0, z: float = 0):
        self.min_x += x
        self.max_x += x
        self.min_y += y
        self.max_y += y
        self.min_z += z
        self.max_z += z
        
    def get_center(self):
        center_x = (self.min_x + self.max_x) / 2
        center_y = (self.min_y + self.max_y) / 2
        center_z = (self.min_z + self.max_z) / 2
        return (center_x, center_y, center_z)
    
    def intersects_and_above(self, other_bbox) -> bool:
        x_overlap = (self.min_x <= other_bbox.max_x) and (other_bbox.min_x <= self.max_x)
        above = self.min_y >= other_bbox.max_y
        z_overlap = (self.min_z <= other_bbox.max_z) and (other_bbox.min_z <= self.max_z)
        
        return x_overlap and z_overlap and above