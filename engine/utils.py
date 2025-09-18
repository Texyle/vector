import math 
from .constants import *
from numpy import float32 as fl

def mcsin(rad):
    if ANGLES == 65536:
        index = int(rad * fl(10430.378)) & 65535
        return fl(math.sin(index * math.pi * 2.0 / 65536))
    else:
        return math.sin(rad)

def mccos(rad):
    if ANGLES == 65536:
        index = int(rad * fl(10430.378) + fl(16384.0)) & 65535
        return fl(math.sin(index * math.pi * 2.0 / 65536))
    else:
        return math.cos(rad)
    
def ray_bbox_intersection(ray_ox, ray_oy, ray_oz, 
                        ray_dx, ray_dy, ray_dz,
                        box_min_x, box_max_x,
                        box_min_y, box_max_y,
                        box_min_z, box_max_z,
                        height: float):

    box_min_y = height - 0.01
    box_max_y = height + 0.01
    ray_oy = height
    ray_dy = 0
    
    inv_dx = 1.0 / ray_dx if ray_dx != 0 else float('inf')
    inv_dy = 1.0 / ray_dy if ray_dy != 0 else float('inf')
    inv_dz = 1.0 / ray_dz if ray_dz != 0 else float('inf')
    
    t1 = (box_min_x - ray_ox) * inv_dx
    t2 = (box_max_x - ray_ox) * inv_dx
    t3 = (box_min_y - ray_oy) * inv_dy
    t4 = (box_max_y - ray_oy) * inv_dy
    t5 = (box_min_z - ray_oz) * inv_dz
    t6 = (box_max_z - ray_oz) * inv_dz
    
    tmin = max(min(t1, t2), min(t3, t4), min(t5, t6))
    tmax = min(max(t1, t2), max(t3, t4), max(t5, t6))
    
    if tmax < 0:
        return None
    
    if tmin > tmax:
        return None
    
    if tmin < 0:
        return tmax if tmax <= MAX_RAYCAST_DISTANCE else None
    
    return tmin if tmin <= MAX_RAYCAST_DISTANCE else None

def point_in_bbox(x, y, z, bbox, height = 0):
    if not (bbox.min_x <= x <= bbox.max_x and bbox.min_z <= z <= bbox.max_z):
        return False
    
    if height == 0:
        return bbox.min_y <= y <= bbox.max_y
    else:
        line_min_y = y
        line_max_y = y + height
        return (line_min_y <= bbox.max_y and line_max_y >= bbox.min_y)
    
def find_exit_point(x, y, z, dir_x, dir_y, dir_z, bbox):
    intersections = []
    
    if dir_x != 0:
        t_east = (bbox.max_x - x) / dir_x
        if t_east > 0:
            y_east = y + dir_y * t_east
            z_east = z + dir_z * t_east
            if (bbox.min_y <= y_east <= bbox.max_y and 
                bbox.min_z <= z_east <= bbox.max_z):
                intersections.append((t_east, bbox.max_x, y_east, z_east))
        
        t_west = (bbox.min_x - x) / dir_x
        if t_west > 0:
            y_west = y + dir_y * t_west
            z_west = z + dir_z * t_west
            if (bbox.min_y <= y_west <= bbox.max_y and 
                bbox.min_z <= z_west <= bbox.max_z):
                intersections.append((t_west, bbox.min_x, y_west, z_west))
    
    if dir_y != 0:
        t_top = (bbox.max_y - y) / dir_y
        if t_top > 0:
            x_top = x + dir_x * t_top
            z_top = z + dir_z * t_top
            if (bbox.min_x <= x_top <= bbox.max_x and 
                bbox.min_z <= z_top <= bbox.max_z):
                intersections.append((t_top, x_top, bbox.max_y, z_top))
        
        t_bottom = (bbox.min_y - y) / dir_y
        if t_bottom > 0:
            x_bottom = x + dir_x * t_bottom
            z_bottom = z + dir_z * t_bottom
            if (bbox.min_x <= x_bottom <= bbox.max_x and 
                bbox.min_z <= z_bottom <= bbox.max_z):
                intersections.append((t_bottom, x_bottom, bbox.min_y, z_bottom))
    
    if dir_z != 0:
        t_north = (bbox.max_z - z) / dir_z
        if t_north > 0:
            x_north = x + dir_x * t_north
            y_north = y + dir_y * t_north
            if (bbox.min_x <= x_north <= bbox.max_x and 
                bbox.min_y <= y_north <= bbox.max_y):
                intersections.append((t_north, x_north, y_north, bbox.max_z))
        
        t_south = (bbox.min_z - z) / dir_z
        if t_south > 0:
            x_south = x + dir_x * t_south
            y_south = y + dir_y * t_south
            if (bbox.min_x <= x_south <= bbox.max_x and 
                bbox.min_y <= y_south <= bbox.max_y):
                intersections.append((t_south, x_south, y_south, bbox.min_z))
    
    if not intersections:
        return None
    
    closest_t, exit_x, exit_y, exit_z = min(intersections, key=lambda x: x[0])
    
    return exit_x, exit_y, exit_z, closest_t