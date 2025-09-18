import numpy as np
import gymnasium as gym
from gymnasium import spaces
from ..engine import Engine

class Environment(gym.Env):
    metadata = {'render.modes': ['human']}
    
    def __init__(self):
        super(Environment, self).__init__()
        
        self.engine = Engine()
        
        """
        Action space
        
        Placement phase:
        - Relative X and Z coordinate from 0 to 1
        - Facing
        
        Navigation phase:
        - Binary W, A, S, D, Sprint, Space inputs
        - Continuous mouse movement input
        """
        
        self.placement_action_space = spaces.Box(
            low=np.array([0.0, 0.0, 0.0]),
            high=np.array([1.1, 1.1, 360.0]),
            dtype=np.float32
        )
        
        self.navigation_action_space = spaces.Tuple([
            spaces.MultiBinary(6),
            spaces.Box(low=-90.0, high=90.0, shape=(1,), dtype=np.float32)
        ])
        
        self.action_space = spaces.Tuple([
            spaces.MultiBinary(6),
            
            spaces.Box(low=-90.0, high=90.0, shape=(1,), dtype=np.float32)
        ])
        
        """ 
        Observation phase
        
        Placement phase:
        - Goal X
        - Goal Y
        - Goal Z
        - Starting block min X
        - Starting block max X
        - Starting block min Z
        - Starting block max Z
        
        Navigation phase:
        - Distance to goal on X
        - Distance to goal on Y
        - Distance to goal on Z
        - 16 raycasts at current Y to find blockages
        - 16 inverted raycasts at Y-1 to find ground edges
        - Distance to ground
        - Current facing
        - Velocity on all axis
        """
        
        self.placement_observation_space = spaces.Box(
            low=-np.inf,
            high=np.inf, 
            shape=(7,),
            dtype=np.float32
        )
        
        self.nagivation_observation_space = spaces.Box(
            low=-np.inf, 
            high=np.inf, 
            shape=(3 + 16 + 16 + 1 + 1 + 3,), 
            dtype=np.float32
        )
        
        self.phase = "placement"
        self.observation_space = self.placement_observation_space
        self.current_observation = None
        self.steps_in_placement = 0
        self.max_placement_steps = 5
        
    def reset(self, seed=None):
        super().reset(seed=seed)
        
        # Reset game engine state
        # self.game_engine.reset_level()
        
        # Reset phase to placement
        self.phase = "placement"
        self.observation_space = self.placement_observation_space
        self.steps_in_placement = 0
        
        # Get initial observation for placement phase
        observation = self._get_placement_observation()
        info = {}
        
        return observation, info
    
    def step(self, action):
        reward = 0
        terminated = False
        truncated = False
        info = {}
        
        if self.phase == "placement":
            relative_x = action[0]
            relative_z = action[1] 
            facing = action[3]
            
            bounds = self.game_engine.get_start_area_bounds()
            absolute_x = bounds['min_x'] + relative_x * (bounds.max_x - bounds.min_x)
            absolute_z = bounds['min_z'] + relative_z * (bounds.max_z - bounds.min_z)
            
            self.engine.spawn_player(absolute_x, bounds.min_y, absolute_z, facing)
            
            self.phase = "navigation"
            observation = self._get_navigation_observation()
                    
        else:
            key_actions, mouse_action = action
            keys = {
                'W': bool(key_actions[0]),
                'A': bool(key_actions[1]),
                'S': bool(key_actions[2]),
                'D': bool(key_actions[3]),
                'sprint': bool(key_actions[4]),
                'space': bool(key_actions[5])
            }
            mouse_delta = mouse_action[0]
            
            # Apply action to game engine
            self.engine.apply_player_input(keys, mouse_delta)
            self.engine.update()
            
            # Get new observation
            observation = self._get_navigation_observation()
            
            # Calculate reward
            reward = self._calculate_navigation_reward()
            
            # Check termination conditions
            if self.game_engine.player_reached_goal():
                terminated = True
                reward += 100.0  # Large success reward
            elif self.game_engine.player_died() or self.game_engine.player_stuck():
                terminated = True
                reward -= 20.0  # Penalty for failure
                
            # Add info for debugging
            info["distance_to_goal"] = np.linalg.norm(observation[0:3])
            info["velocity"] = np.linalg.norm(observation[-3:])
        
        return observation, reward, terminated, truncated, info
    
    def _get_placement_observation(self):
        goal_x, goal_y, goal_z = self.engine.get_goal_position()
        start_bounds = self.engine.get_start_area_bounds()
        
        observation = np.array([
            goal_x, goal_y, goal_z,
            start_bounds.min_x, start_bounds.max_x,
            start_bounds.min_z, start_bounds.max_z
        ], dtype=np.float32)
        
        return observation
    
    def _get_navigation_observation(self):
        player_x, player_y, player_z = self.engine.get_player_position()
        goal_x, goal_y, goal_z = self.engine.get_goal_position()
        vx, vy, vz = self.engine.get_player_velocity()
        
        dist_to_goal = np.array([
            goal_x - player_x,
            goal_y - player_y,
            goal_z - player_z
        ], dtype=np.float32)
        
        raycast_directions = np.linspace(-180, 180, 16)
        blockage_rays = []
        ground_rays = []
        
        for angle in raycast_directions:
            # Horizontal raycasts for blockages
            direction = (np.cos(np.radians(angle)), np.sin(np.radians(angle)), 0)
            hit, distance = self.game_engine.raycast(player_pos, direction)
            blockage_rays.append(distance if hit else 999.0)
            
            # Downward raycasts for ground edges
            down_direction = (0, -1, 0)  # Straight down
            hit, ground_dist = self.game_engine.raycast(player_pos, down_direction)
            ground_rays.append(ground_dist if hit else 999.0)
        
        # Distance to ground (shortest of the downward rays)
        distance_to_ground = min(ground_rays)
        
        # Combine all observations
        observation = np.concatenate([
            dist_to_goal,                    # 3 values
            np.array(blockage_rays),         # 16 values
            np.array(ground_rays),           # 16 values
            np.array([distance_to_ground]),  # 1 value
            velocity                         # 3 values
        ], dtype=np.float32)
        
        return observation