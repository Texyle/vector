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
            low=np.array([0., 0., 0., 0., 0., 0., -180.0], dtype=np.float32),
            high=np.array([1., 1., 1., 1., 1., 1., 180.0], dtype=np.float32),
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
            shape=(40,), 
            dtype=np.float32
        )
        
        self.current_step = 0

        self.current_observation = None
        self.steps_in_placement = 0
        self.max_steps = 150
        self.attempt_until_macro = 0
        self.macro_n = 39
        self.best_offset = -999.0
        
        self.velocity_reward = 0
        self.distance_reward = 0
        self.total_reward = 0
        self.current_distance = 0.0
        self.moved_forward = False
        
        self.prev_inputs = {}
        
        self.landed_n = 0
        self.landed = False
        
    def reset(self, seed=None):
        super().reset(seed=seed)
        
        self.attempt_until_macro += 1
        if self.attempt_until_macro >= MACRO_SAVING_INTERVALS:
            self.save_macro(MACRO_NAME, self.macro_n)
            self.macro_n += 1
            self.attempt_until_macro = 0
            print(f"Landing rate: {self.landed_n / MACRO_SAVING_INTERVALS:.2f}% ({self.landed_n}/{MACRO_SAVING_INTERVALS})")
            self.landed_n = 0
        
        # Reset game engine state
        self.engine.reset()
        
        self.inputs_n = 0
        self.turns_n = 0
        self.moved_forward = False
        
        # Get initial observation for placement phase
        observation = self._get_navigation_observation()
        info = {}
        
        self.current_step = 0
        self.landed = False
        
        return observation, info
    
    def step(self, action):        
        reward = 0
        terminated = False
        truncated = False
        info = {}
        self.current_step += 1
                                                        
        key_actions_flat = action[:6]
        mouse_action = action[6:]

        discrete_actions = (key_actions_flat > 0.5).astype(np.int8)

        keys = {
            'W': bool(discrete_actions[0]),
            'A': bool(discrete_actions[1]),
            'S': bool(discrete_actions[2]),
            'D': bool(discrete_actions[3]),
            'sprint': bool(discrete_actions[4]),
            'space': bool(discrete_actions[5])
        }
        
        info_lines = [
            f"PB: {self.best_offset:.5f}",
            f"Reward: {self.total_reward:.5f}"
        ]
        
        self.engine.apply_player_input(keys, mouse_action[0])
        self.engine.handle_events()
        self.engine.tick()
        self.engine.draw(keys, info_lines)
        
        observation = self._get_navigation_observation()
        
        # Calculate reward
        reward = self.calculate_navigation_reward()
        self.total_reward = reward
        
        # Check termination conditions
        if self.engine.total_offset > 0:
            terminated = True
            reward += 5.0
            self.landed_n += 1
            # self.save_macro(MACRO_NAME + "_LANDED", self.macro_n)
        elif self.engine.player_died():
            terminated = True
        elif self.current_step > self.max_steps:
            reward -= 10.0
            truncated = True
            info['truncated'] = True
        
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
            goal_y - player_y,
            goal_z - player_z
        ], dtype=np.float32)
        
        velocity = np.array([vx, vy, vz])
        
        blockage_rays = []
        ground_rays = []
        
        for i in range(RAYCAST_NUMBER):
            angle = (i / RAYCAST_NUMBER) * 2 * math.pi
        
            #blockage_rays.append(self.engine.raycast(player_x, player_y, player_z, PLAYER_HEIGHT, angle))
            blockage_rays.append(0)
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
        
        return navigation_obs
    
    def calculate_navigation_reward(self):
        reward = -0.0005 * self.current_step
        
        if self.engine.player_died() or self.engine.reached_goal():
            offset = self.engine.total_offset
            if offset > -998:
                if offset < -3:
                    reward = offset
                elif offset < -1:
                    reward = offset * 2 + 3
                elif offset < 0:
                    reward = (offset + 3) ** 2 - 3 + math.log(1/(-offset+10 ** (-10)))
                else:
                    reward = 16 + offset*100 
                                
                if offset > self.best_offset:
                    self.best_offset = offset
                    
                    if offset > 0.02:
                        self.save_macro(MACRO_NAME + "_NEW_PB_" + str(offset), self.macro_n)

            else:
                reward -= 10
                
        # if self.current_step >= 36:
        #     reward -= 0.01 * self.current_step - 36
        
        # if self.engine.player_died():
        #     reward -= 2
        
        # # if self.prev_inputs != {}:
        # #     for key in keys.keys():
        # #         if keys[key] != self.prev_inputs[key]:
        # #             reward -= 0.01
        # # self.prev_inputs = keys
        # if turn > 0.01:
        #     reward -= 0.01

        # velocity = self.engine.get_player_velocity()
        
        # self.velocity_reward = 0

        # player_pos = self.engine.get_player_bbox()
        # goal_pos = self.engine.get_goal()
        # player_center = player_pos.get_center()

        # goal_dir_vector = np.array([goal_pos[0] - player_center[0], goal_pos[2] - player_center[2]])
        
        # goal_dir_length = np.linalg.norm(goal_dir_vector)
        # if goal_dir_length > 0:
        #     goal_dir_normalized = goal_dir_vector / goal_dir_length

        #     velocity_vector = np.array([velocity[0], velocity[2]])
        #     dot_product = np.dot(velocity_vector, goal_dir_normalized)
            
        #     if dot_product > 0:
        #         velocity_vector = np.array([velocity[0], velocity[2]])
        #         velocity_magnitude = np.linalg.norm(velocity_vector)
        #         if velocity_magnitude > 0.2:
        #             self.velocity_reward = np.sign(dot_product) * np.abs(dot_product)**2
        #         self.moved_forward = True
        #     else:
        #         if self.moved_forward:
        #             self.velocity_reward = -0.1
            
        # reward += self.velocity_reward
        
        # current_distance = self.engine.get_offset_total()
        # self.current_distance = current_distance
        
        # if current_distance >= 0:
        #     reward_multiplier = current_distance * 100
        # elif current_distance > -10:
        #     reward_multiplier = abs(1 / (current_distance))     
        #     reward += reward_multiplier * 0.1
        #     self.distance_reward = reward_multiplier * 0.1
        # else:
        #     self.distance_reward = 0
        
        # if self.engine.is_colliding_wall():
        #     reward -= 1
            
        # # if self.current_step > 20:
        # #     if player_pos.intersects_and_above(start_pos, True):
        # #         reward -= 0.1
            
        # self.total_reward = reward
        
        # reward -= 0.001 * self.current_step ** 2
        
        return reward
    
    def save_macro(self, name, iteration):
        return self.engine.save_macro(name, iteration)