import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import time
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv
from environment import Environment

# Add the parent directory to path (same as in your training script)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_trained_agent(model_path="vector_agent"):
    # Load the trained model
    try:
        model = PPO.load(model_path)
        print(f"Loaded trained model from {model_path}")
    except FileNotFoundError:
        print(f"No trained model found at {model_path}")
        return
    
    # Create environment (same as training setup)
    env = Environment()
    env = DummyVecEnv([lambda: env])
    
    # Reset the environment
    obs = env.reset()
    single_env = env.envs[0]  # Get the underlying environment
    
    print("Starting test run...")
    print("Press Ctrl+C to stop the test")
    
    episode_count = 0
    total_reward = 0
    
    try:
        while True:
            # Get the current phase
            current_phase = single_env.phase
            
            # Get action from the trained model
            action, _states = model.predict(obs, deterministic=True)
            full_action = action[0]  # Extract action for the first environment
            
            print(current_phase)
            
            if current_phase == "placement":
                print("Phase: Placement - Choosing start position")
                
                # Extract placement action (first 3 dimensions)
                placement_action = full_action[:3]  # [relative_x, relative_z, facing]
                relative_x, relative_z, facing = placement_action
                
                # Convert to absolute coordinates
                bounds = single_env.engine.get_start_bounds()
                absolute_x = bounds.min_x + relative_x * (bounds.max_x - bounds.min_x)
                absolute_z = bounds.min_z + relative_z * (bounds.max_z - bounds.min_z)
                
                print(f"Chosen position: ({absolute_x:.2f}, {absolute_z:.2f}), Facing: {facing:.2f}°")
                
                # Spawn the player
                single_env.engine.spawn_player(absolute_x, bounds.min_y, absolute_z, facing)
                
                # Manually transition to navigation phase
                single_env.phase = "navigation"
                
                # Get new observation for navigation phase
                obs = np.array([single_env._get_navigation_observation()])
                
            else:  # navigation phase
                # Extract navigation action (last 7 dimensions)
                navigation_action = full_action[3:]  # [W, A, S, D, sprint, space, mouse]
                key_actions_flat = navigation_action[:6]
                mouse_action = navigation_action[6:]
                
                # Convert to key states (threshold at 0.5 for binary actions)
                active_keys = {
                    'W': bool(key_actions_flat[0] > 0.5),
                    'A': bool(key_actions_flat[1] > 0.5),
                    'S': bool(key_actions_flat[2] > 0.5),
                    'D': bool(key_actions_flat[3] > 0.5),
                    'sprint': bool(key_actions_flat[4] > 0.5),
                    'space': bool(key_actions_flat[5] > 0.5)
                }
                
                # Take a step in the environment
                obs, rewards, dones, infos = env.step(action)
                
                # Update total reward
                total_reward += rewards[0]
                
                # Print debug info
                print(f"Reward: {rewards[0]:.2f}, Total: {total_reward:.2f}, Phase: Navigation")
                
                # Render the game with active keys
                single_env.engine.draw(active_keys)
            
            # Add a small delay to make the visualization watchable
            time.sleep(0.005)
            
            # Check if episode ended (only in navigation phase)
            if current_phase == "navigation" and dones[0]:
                episode_count += 1
                print(f"Episode {episode_count} completed! Total reward: {total_reward:.2f}")
                print("Resetting environment...")
                
                # Reset environment
                obs = env.reset()
                single_env = env.envs[0]  # Refresh reference after reset
                total_reward = 0
                single_env.engine.draw({})
                
    except KeyboardInterrupt:
        print(f"\nTest stopped by user. Completed {episode_count} episodes.")
    
    finally:
        env.close()
        print("Environment closed.")

if __name__ == "__main__":
    test_trained_agent("vector_agent")