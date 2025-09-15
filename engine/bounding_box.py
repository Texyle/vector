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