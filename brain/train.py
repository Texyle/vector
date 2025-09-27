import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import time
import numpy as np
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import SubprocVecEnv
from stable_baselines3.common.callbacks import CheckpointCallback
from environment import Environment
from stable_baselines3.common.callbacks import CheckpointCallback
import threading

# Configuration
MACRO_NAME = '4b'
SAVE_PATH = "./logs/continuous_training_logs/"
LOAD_PATH = "./models/"
MODEL = "triple_gg"
TIMESTEPS_PER_CHUNK = 1024*8
NUM_ENVIRONMENTS = 4
ENTROPY_COEF = 0.01

# Create a function to initialize environments
def make_env():
    def _init():
        env = Environment()
        return env
    return _init

if __name__ == "__main__":
    # Create directories
    os.makedirs(SAVE_PATH, exist_ok=True)
    os.makedirs(LOAD_PATH, exist_ok=True)

    # Create parallel environments
    env = SubprocVecEnv([make_env() for _ in range(NUM_ENVIRONMENTS)])

    checkpoint_callback = CheckpointCallback(
        save_freq=TIMESTEPS_PER_CHUNK*15,
        save_path=SAVE_PATH,
        name_prefix="vector_agent",
        save_replay_buffer=False,
        save_vecnormalize=False,
    )

    # Load or initialize model
    model_path = f"{LOAD_PATH}/{MODEL}.zip"
    if os.path.exists(model_path):
        print("Loading existing model...")
        model = PPO.load(model_path, env=env, device="cpu", verbose=2, n_steps=TIMESTEPS_PER_CHUNK, ent_coef = ENTROPY_COEF)
    else:
        print("Initializing new model...")
        model = PPO(
            "MlpPolicy",
            env,
            verbose=2,
            n_steps=TIMESTEPS_PER_CHUNK,
            device="cpu",
            ent_coef=ENTROPY_COEF
        )

    # Train
    print("Starting training...")
    total_timesteps = 0
    try:
        while True:
            start_time = time.time()
            model.learn(
                total_timesteps=TIMESTEPS_PER_CHUNK,
                callback=checkpoint_callback,
                reset_num_timesteps=False
            )
            total_timesteps += TIMESTEPS_PER_CHUNK
            end_time = time.time()
            duration = end_time - start_time
            fps = (TIMESTEPS_PER_CHUNK * NUM_ENVIRONMENTS) / duration
            print(f"Iteration completed. Total timesteps: {total_timesteps}, FPS: {fps:.0f}")
    except KeyboardInterrupt:
        print("Training stopped by user.")
        model.save(f"{SAVE_PATH}/final_vector_agent")
    finally:
        env.close()
