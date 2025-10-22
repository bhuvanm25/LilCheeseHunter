# main.py
import os
import time
from env import GridWorld
from agent import RandomAgent

import gymnasium as gym
import numpy as np

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def main():
    size = 5
    w = size + 2
    env = GridWorld(rows=w, cols=w, size=size, seed=42)
    agent = RandomAgent(seed=1)

    env.reset()

    steps = 5
    delay_s = 0.1

    for t in range(steps):
        clear()
        print(f"Step {t+1}/{steps}")
        env.render()

        action = agent.act(env.agent_pos)
        env.step(action)

        time.sleep(delay_s)

    # final frame
    clear()
    print("Done!")
    env.render()

if __name__ == "__main__":
    main()