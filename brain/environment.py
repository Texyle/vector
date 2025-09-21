import numpy as np
import gymnasium as gym
from gymnasium import spaces
from engine.engine import Engine
from engine.constants import *
import math
import pygame

class Environment(gym.Env):
    metadata = {'render.modes': ['human']}
    
    def __init__(self):
        super(Environment, self).__init__()
        
        self.engine = Engine()
        self.clock = pygame.time.Clock()
        
        """
        Unified Action Space
        
        A single Box that combines all actions:
        - placement (3 values)
        - navigation (6 MultiBinary + 1 Box = 7 values)
        Total shape: (10,)
        """
        self.action_space = spaces.Box(
            low=np.array([0.0, 0.0, -1, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, -1]),
            high=np.array([1.0, 1.0, 1, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1]),
            dtype=np.float32
        )
        
        """ 
        Unified Observation Space
        
        A single Box that combines all observations:
        - placement (7 values)
        - navigation (39 values)
        Total shape: (46,)
        """
        self.observation_space = spaces.Box(
            low=-np.inf,
            high=np.inf, 
            shape=(7 + 39,), 
            dtype=np.float32
        )
        
        # Define the shapes of the sub-spaces for internal use
        self.placement_obs_shape = 7
        self.navigation_obs_shape = 39
        self.placement_action_shape = 3
        self.navigation_action_shape = 7
        
        self.current_step = 0

        self.phase = "placement"
        self.current_observation = None
        self.steps_in_placement = 0
        self.max_steps = 150
        self.attempt_until_macro = 0
        self.macro_n = 1
        self.best_offset = -999.0
        
        self.velocity_reward = 0
        self.distance_reward = 0
        self.total_reward = 0
        self.current_distance = 0.0
        
        self.landed = 0
        
    def reset(self, seed=None):
        super().reset(seed=seed)
        
        self.attempt_until_macro += 1
        if self.attempt_until_macro >= MACRO_SAVING_INTERVALS:
            self.save_macro(MACRO_NAME, self.macro_n)
            self.macro_n += 1
            self.attempt_until_macro = 0
            print(f"Landing rate: {self.landed / MACRO_SAVING_INTERVALS:.2f}% ({self.landed}/{MACRO_SAVING_INTERVALS})")
            self.landed = 0
        
        # Reset game engine state
        self.engine.reset()
        
        # Reset phase to placement
        self.phase = "placement"
        self.steps_in_placement = 0
        
        # Get initial observation for placement phase
        observation = self._get_placement_observation()
        info = {}
        
        self.current_step = 0
        
        return observation, info
    
    def step(self, action):
        reward = 0
        terminated = False
        truncated = False
        info = {}
        self.current_step += 1
                
        if self.phase == "placement":
            # The agent outputs a single array. Extract the relevant part.
            placement_action = action[:self.placement_action_shape]
            relative_x, relative_z, facing = placement_action
            facing *= 180
                        
            bounds = self.engine.get_start_bounds()
            absolute_x = bounds.min_x + relative_x * (bounds.max_x - bounds.min_x)
            absolute_z = bounds.min_z + relative_z * (bounds.max_z - bounds.min_z)
                        
            self.engine.spawn_player(absolute_x, bounds.min_y, absolute_z, facing)
            
            self.phase = "navigation"
            observation = self._get_navigation_observation()
            
            return observation, reward, terminated, truncated, info
                            
        else: # self.phase == "navigation"
            # Extract the navigation part of the action
            navigation_action = action[self.placement_action_shape:]
            key_actions_flat = navigation_action[:6]
            mouse_action = navigation_action[6:]
            
            keys = {
                'W': bool(key_actions_flat[0]),
                'A': bool(key_actions_flat[1]),
                'S': bool(key_actions_flat[2]),
                'D': bool(key_actions_flat[3]),
                'sprint': bool(key_actions_flat[4]),
                'space': bool(key_actions_flat[5])
            }
            mouse_delta = mouse_action[0] * 45
            
            info_lines = [
                f"Velocity R: {self.velocity_reward:.4f}",
                f"Distance R : {self.distance_reward:.4f}", 
                f"Total R: {self.total_reward:.4f}",
                f"Offset: {self.current_distance:.5f}",
                f"PB: {self.best_offset:.5f}"
            ]
            
            self.engine.apply_player_input(keys, mouse_delta)
            self.engine.handle_events()
            self.engine.tick()
            self.engine.draw(keys, info_lines)
            
            observation = self._get_navigation_observation()
            
            # Calculate reward
            reward, offset = self.calculate_navigation_reward()
            
            if offset > self.best_offset:
                self.best_offset = offset
                self.save_macro(MACRO_NAME + "_NEW_PB", self.macro_n)
            
            # Check termination conditions
            if self.engine.reached_goal():
                terminated = True
                reward += 5.0
                self.landed += 1
                self.save_macro(MACRO_NAME + "_LANDED", self.macro_n)
            elif self.engine.player_died():
                terminated = True
                reward -= 100
            elif self.current_step > self.max_steps:
                truncated = True
                info['truncated'] = True
                
            # Add info for debugging. Access observation keys correctly.
            info["distance_to_goal"] = np.linalg.norm(observation[:3])
            info["velocity"] = np.linalg.norm(observation[-3:])
            
            self.clock.tick(self.engine.tick_rate)
        
        return observation, reward, terminated, truncated, info
    
    def _get_placement_observation(self):
        goal_x, goal_y, goal_z = self.engine.get_goal()
        start_bounds = self.engine.get_start_bounds()
        
        placement_obs = np.array([
            goal_x, goal_y, goal_z,
            start_bounds.min_x, start_bounds.max_x,
            start_bounds.min_z, start_bounds.max_z
        ], dtype=np.float32)
        
        # Pad with zeros to match the total observation space size
        navigation_padding = np.zeros(self.navigation_obs_shape, dtype=np.float32)
        return np.concatenate([placement_obs, navigation_padding])
    
    def _get_navigation_observation(self):
        player_x, player_y, player_z = self.engine.get_player_position()
        goal_x, goal_y, goal_z = self.engine.get_goal()
        vx, vy, vz = self.engine.get_player_velocity()
        facing = self.engine.get_player_facing()
        
        dist_to_goal = np.array([
            goal_x - player_x,
            goal_z - player_z
        ], dtype=np.float32)
        
        velocity = np.array([vx, vy, vz])
        
        blockage_rays = []
        ground_rays = []
        
        for i in range(RAYCAST_NUMBER):
            angle = (i / RAYCAST_NUMBER) * 2 * math.pi
        
            blockage_rays.append(self.engine.raycast(player_x, player_y, player_z, PLAYER_HEIGHT, angle))
            ground_rays.append(self.engine.raycast(player_x, player_y-1.25, player_z, 1.25, angle, inverted=True))
        
        distance_to_ground = self.engine.get_distance_to_ground()
        
        navigation_obs = np.concatenate([
            dist_to_goal,
            np.array(blockage_rays),
            np.array(ground_rays),
            np.array([distance_to_ground]),
            np.array([facing]),
            velocity
        ], dtype=np.float32)
        
        placement_padding = np.zeros(self.placement_obs_shape, dtype=np.float32)
        return np.concatenate([placement_padding, navigation_obs])
    
    def calculate_navigation_reward(self):
        reward = -0.0001

        velocity = self.engine.get_player_velocity()
        player_pos = self.engine.get_player_bbox()
        goal_pos = self.engine.get_goal()
        player_center = player_pos.get_center()

        goal_dir_vector = np.array([goal_pos[0] - player_center[0], goal_pos[2] - player_center[2]])
        
        goal_dir_length = np.linalg.norm(goal_dir_vector)
        if goal_dir_length > 0:
            goal_dir_normalized = goal_dir_vector / goal_dir_length
        else:
            return 1.0

        velocity_vector = np.array([velocity[0], velocity[2]])
        dot_product = np.dot(velocity_vector, goal_dir_normalized)
        dot_product = np.sign(dot_product) * np.abs(dot_product)**2
        reward += dot_product
        
        self.velocity_reward = dot_product
        
        current_distance = self.engine.get_offset_total()
        self.current_distance = current_distance
        
        if current_distance >= 0:
            reward_multiplier = current_distance ** 2
        elif current_distance > -4:
            reward_multiplier = abs(1 / (current_distance))     
            reward += reward_multiplier * 0.1
            self.distance_reward = reward_multiplier * 0.1
        else:
            self.distance_reward = 0
        
        if self.engine.is_colliding_wall():
            reward -= 1
            
        # if self.current_step > 20:
        #     if player_pos.intersects_and_above(start_pos, True):
        #         reward -= 0.1
            
        self.total_reward = reward
        
        return reward, current_distance
    
    def save_macro(self, name, iteration):
        return self.engine.save_macro(name, iteration)