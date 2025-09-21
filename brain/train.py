import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import time
import numpy as np
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv
from stable_baselines3.common.callbacks import CheckpointCallback
from environment import Environment

macro_name = '4b'

# Path configuration
SAVE_PATH = "./models/"
os.makedirs(SAVE_PATH, exist_ok=True)

# Environment and Model Parameters
TIMESTEPS_PER_CHUNK = 4096

# Create and wrap the environment
env = DummyVecEnv([lambda: Environment()])

# Setup Checkpoint Callback
checkpoint_callback = CheckpointCallback(
    save_freq=TIMESTEPS_PER_CHUNK,
    save_path=SAVE_PATH,
    name_prefix="vector_agent"
)

# Check if saved model exists and load it
model_path = f"{SAVE_PATH}/triple_2.zip"
if os.path.exists(model_path):
    print("Loading existing model...")
    model = PPO.load(model_path, env=env, device="cpu")
    total_timesteps = model.num_timesteps
    print(f"Resuming from {total_timesteps} timesteps")
else:
    print("Initializing new model...")
    model = PPO(
        "MlpPolicy",
        env,
        verbose=0,
        n_steps=TIMESTEPS_PER_CHUNK,
        tensorboard_log="./logs/",
        device="cpu"
    )
    total_timesteps = 0

print("Starting continuous training...")

# Track total training time and iteration count
total_training_start_time = time.time()
iteration = 1

try:
    while True:
        start_time = time.time()
        print(f"\n=== Starting Training Iteration {iteration} ===")

        # Continue training
        model.learn(
            total_timesteps=TIMESTEPS_PER_CHUNK,
            callback=checkpoint_callback,
            reset_num_timesteps=False  # Keep timestep count continuous
        )
        
        # Calculate metrics
        end_time = time.time()
        duration = end_time - start_time
        total_timesteps += TIMESTEPS_PER_CHUNK
        fps = TIMESTEPS_PER_CHUNK / duration

        total_training_time = time.time() - total_training_start_time
        hours = int(total_training_time // 3600)
        minutes = int((total_training_time % 3600) // 60)
        seconds = int(total_training_time % 60)

        print(f"\nIteration {iteration} completed:")
        print(f"  Total timesteps: {total_timesteps}")
        print(f"  Iteration duration: {duration:.2f} seconds")
        print(f"  Total training time: {hours:02d}:{minutes:02d}:{seconds:02d}")
        print(f"  FPS: {fps:.0f}")
        print("-----------------------------")

        iteration += 1

except KeyboardInterrupt:
    total_training_time = time.time() - total_training_start_time
    hours = int(total_training_time // 3600)
    minutes = int((total_training_time % 3600) // 60)
    seconds = int(total_training_time % 60)

    print(f"\nTraining stopped by user after {hours:02d}:{minutes:02d}:{seconds:02d}")
    print("Saving final model...")
    model.save(f"{SAVE_PATH}/final_vector_agent")
    print("Final model saved.")

env.close()