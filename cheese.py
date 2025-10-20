# cheese.py  (offline version)

import gymnasium as gym
from stable_baselines3 import PPO
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import DummyVecEnv

# ---- CONFIG ----
env_id = "LunarLander-v2"
model_name = "ppo-LunarLander-v2"

# ---- TRAIN ----
print("Creating environment...")
env = gym.make(env_id)

print("Initializing PPO model...")
model = PPO(
    policy="MlpPolicy",
    env=env,
    n_steps=1024,
    batch_size=64,
    n_epochs=4,
    gamma=0.999,
    gae_lambda=0.98,
    ent_coef=0.01,
    verbose=1,
)

print("Training...")
model.learn(total_timesteps=200_000)  # tweak for longer runs
model.save(model_name)
print(f"✅ Model saved as {model_name}.zip")

# ---- EVALUATE LOCALLY ----
eval_env = DummyVecEnv([lambda: Monitor(gym.make(env_id, render_mode="human"))])

obs = eval_env.reset()
for _ in range(1000):
    action, _ = model.predict(obs)
    obs, reward, done, info = eval_env.step(action)
    eval_env.render()
    if done.any():
        obs = eval_env.reset()

eval_env.close()
print("✅ Finished local evaluation")
