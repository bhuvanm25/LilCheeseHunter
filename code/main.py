import sys
import os
import random
from collections import deque
import pygame
import math

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

from env import GridWorld, WALL
from q_agent import QLearningAgent
from pygame_viewer import PygameViewer

# Base training config (these get scaled per-map later)
NUM_EPISODES_PER_TILE = 1000
MAX_STEPS = 250

ALPHA = 0.2
GAMMA = 0.95
EPSILON_START = 1.0
EPSILON_MIN = 0.05
EPSILON_DECAY = 0.995

# Animation and playback settings
USE_PYGAME = True
FPS_TRAIN = 50
FPS_PLAY = 25

# Early-stopping window for “this goal is learned”
SUCCESS_WINDOW = 150
SUCCESS_THRESHOLD = 0.97

# Optional logging to file
LOG_TO_FILE = False
LOG_FILE = "training_log.txt"

if LOG_TO_FILE:
    sys.stdout = open(LOG_FILE, "w", encoding="utf-8")


def make_state(env, goal_pos: tuple[int, int]):
    # Simple state: agent row/col + goal row/col
    ar, ac = env.agent_pos
    gr, gc = goal_pos
    return ar, ac, gr, gc


def run_goal_episode(env,
                     agent: QLearningAgent,
                     goal_pos: tuple[int, int],
                     max_steps: int,
                     viewer: PygameViewer | None,
                     train: bool) -> tuple[int, bool, int]:
    # Run one episode to a specific goal tile (train or just play)
    total_reward = 0
    success = False
    steps_used = 0

    env.current_step = 0
    env.current_max_steps = max_steps
    env.current_total_reward = 0

    # Only render if viewer exists and training animation is enabled
    render = (
        (viewer is not None)
        and getattr(viewer, "show_animation", True)
        and getattr(env, "in_training", False)
    )

    state = make_state(env, goal_pos)

    for t in range(1, max_steps + 1):
        steps_used = t

        if render:
            if not viewer.draw(env):
                return total_reward, success, steps_used

        action = agent.act(state)
        _, reward, done = env.step_to_goal(action, goal_pos)
        next_state = make_state(env, goal_pos)

        if train:
            agent.learn(state, action, reward, next_state, done)

        total_reward += reward
        state = next_state

        env.current_step = t
        env.current_total_reward = total_reward

        if render:
            if not viewer.draw(env):
                return total_reward, success, steps_used

        if done:
            if env.agent_pos == goal_pos:
                success = True
            break

    return total_reward, success, steps_used


def all_goal_tiles(env):
    # All non-wall, non-trap tiles are possible “goals” for training
    traps = set(getattr(env, "_traps", []))
    goals = []

    for r in range(env.rows):
        for c in range(env.cols):
            pos = (r, c)
            if env.grid[r][c] == WALL:
                continue
            if pos in traps:
                continue
            goals.append(pos)

    return goals


def random_start_position(env, goals):
    # Random walkable start position (not in traps) or fallback to home
    traps = set(getattr(env, "_traps", []))
    candidates = [g for g in goals if g not in traps]
    if not candidates:
        return env.home_pos
    return random.choice(candidates)


def train_on_single_goal(env,
                         agent: QLearningAgent,
                         viewer: PygameViewer | None,
                         goal_pos: tuple[int, int],
                         all_goals: list[tuple[int, int]],
                         tile_index: int,
                         total_tiles: int,
                         rewards_log: list[float],
                         steps_log: list[int],
                         success_log: list[int]):
    # Focus training on one goal tile until success-rate is high enough
    env._cheeses = [goal_pos]
    env.cheese_mask = env._full_cheese_mask()

    success_window = deque(maxlen=SUCCESS_WINDOW)
    agent.epsilon = EPSILON_START

    if not hasattr(env, "reward_window"):
        env.reward_window = deque(maxlen=SUCCESS_WINDOW)

    for ep in range(NUM_EPISODES_PER_TILE):
        # Epsilon-decay over episodes
        agent.epsilon = max(EPSILON_MIN, agent.epsilon * EPSILON_DECAY)

        # For HUD / debug overlay
        env.training_tile_index = tile_index
        env.training_total_tiles = total_tiles
        env.training_episode = ep + 1
        env.training_max_episodes_for_this_tile = NUM_EPISODES_PER_TILE
        env.training_epsilon = agent.epsilon

        start_pos = random_start_position(env, all_goals)
        env.agent_pos = start_pos

        ep_reward, success, steps_used = run_goal_episode(
            env,
            agent,
            goal_pos=goal_pos,
            max_steps=MAX_STEPS,
            viewer=viewer,
            train=True,
        )

        # Log for plotting + overlay
        env.training_last_reward = ep_reward
        env.reward_window.append(ep_reward)
        env.training_avg_reward = sum(env.reward_window) / len(env.reward_window)

        rewards_log.append(ep_reward)
        steps_log.append(steps_used)
        success_log.append(1 if success else 0)

        success_window.append(1 if success else 0)

        # Early-stop when recent success-rate is good enough
        if len(success_window) == success_window.maxlen:
            rate = sum(success_window) / len(success_window)
            env.training_success_rate = rate
            if rate >= SUCCESS_THRESHOLD:
                break

    env._cheeses = []
    env.cheese_mask = 0


def train_all_goals(env,
                    agent: QLearningAgent,
                    viewer: PygameViewer | None,
                    rewards_log: list[float],
                    steps_log: list[int],
                    success_log: list[int]):
    # Train across all walkable goal tiles in random order
    goals = all_goal_tiles(env)
    random.shuffle(goals)

    env.in_training = True
    env.training_total_tiles = len(goals)
    env.training_tile_index = 0
    env.training_episode = 0
    env.training_max_episodes_for_this_tile = NUM_EPISODES_PER_TILE

    for i, goal in enumerate(goals):
        print(f"[Train] Goal {i + 1}/{len(goals)} at {goal}")
        train_on_single_goal(
            env,
            agent,
            viewer,
            goal,
            goals,
            tile_index=i,
            total_tiles=len(goals),
            rewards_log=rewards_log,
            steps_log=steps_log,
            success_log=success_log,
        )

    env.in_training = False
    env._cheeses = []
    env.cheese_mask = 0


def go_to_target(env, agent, viewer, target_pos):
    # Greedy run from current position to a given target (no learning)
    agent.epsilon = 0.0

    env._cheeses = [target_pos]
    env.cheese_mask = env._full_cheese_mask()

    state = make_state(env, target_pos)
    steps_left = MAX_STEPS
    total_reward = 0

    while steps_left > 0:
        action = agent.act(state)
        _, reward, done = env.step_to_goal(action, target_pos)
        next_state = make_state(env, target_pos)
        state = next_state
        total_reward += reward

        env.current_step = MAX_STEPS - steps_left + 1
        env.current_max_steps = MAX_STEPS
        env.current_total_reward = total_reward

        if viewer is not None:
            if not viewer.draw(env):
                break

        steps_left -= 1

        if env.agent_pos == target_pos or done:
            break


def go_home(env, agent, viewer):
    # Convenience: go to the home tile (if defined)
    if env.home_pos is None:
        return

    go_to_target(env, agent, viewer, env.home_pos)


def interactive_loop(env, agent, viewer):
    # “Playground” loop: user clicks a tile and the agent runs there
    agent.epsilon = 0.0
    traps = set(getattr(env, "_traps", []))

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                viewer.close()
                return

            # Let viewer handle slider / UI events (FPS slider etc.)
            viewer._handle_slider_event(event)

            # Close training-report overlay with Esc
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if viewer.show_report_overlay:
                    viewer.show_report_overlay = False
                continue

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos

                # If report overlay is open, allow closing via X button
                if viewer.show_report_overlay and viewer.report_close_rect is not None:
                    if viewer.report_close_rect.collidepoint((mx, my)):
                        viewer.show_report_overlay = False
                        continue

                # Clicks on the sidebar area
                if mx >= viewer.grid_width:
                    # Report button
                    if (
                        viewer.report_button_rect is not None
                        and viewer.report_button_rect.collidepoint((mx, my))
                        and getattr(env, "has_training_report", False)
                        and viewer.report_surface is not None
                    ):
                        viewer.show_report_overlay = True
                        continue

                    # Skip / pause animation toggle
                    if viewer.skip_button_rect.collidepoint((mx, my)):
                        viewer.show_animation = not viewer.show_animation
                        continue

                    continue

                # Clicks on the grid area
                pos = viewer.cell_at_pixel(mx, my)
                if pos is None:
                    continue

                r, c = pos
                tile = env.grid[r][c]
                cell = (r, c)

                # Clicking home tile → run home and exit to launcher
                if cell == env.home_pos:
                    go_home(env, agent, viewer)
                    running = False
                    viewer.close()
                    return

                # Ignore walls and traps as targets
                if tile == WALL:
                    continue
                if cell in traps:
                    continue

                # Run to clicked tile
                go_to_target(env, agent, viewer, cell)

        # Reset episode stats while idle
        env.current_step = 0
        env.current_total_reward = 0
        env.current_max_steps = 0
        if viewer is not None:
            if not viewer.draw(env, handle_events=False):
                running = False


def select_map_pygame(maps_dir: str, candidates: list[str]) -> str | None:
    # Pygame menu to pick a map from cleaned/ directory
    pygame.init()
    width, height = 600, 400
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Lil Cheese Hunter™ - Playground")
    font = pygame.font.SysFont(None, 28)
    clock = pygame.time.Clock()

    selected_idx = 0
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.display.quit()
                return None

            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_DOWN, pygame.K_s):
                    selected_idx = (selected_idx + 1) % len(candidates)
                elif event.key in (pygame.K_UP, pygame.K_w):
                    selected_idx = (selected_idx - 1) % len(candidates)
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    running = False
                elif event.key == pygame.K_ESCAPE:
                    pygame.display.quit()
                    return None

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                line_h = 40
                margin_top = 60

                # Click on a row to select that map
                for i, name in enumerate(candidates):
                    y = margin_top + i * line_h
                    rect = pygame.Rect(40, y - 10, width - 80, line_h - 5)
                    if rect.collidepoint(mx, my):
                        selected_idx = i
                        running = False
                        break

                # Back button
                back_rect = pygame.Rect(40, height - 60, 120, 36)
                if back_rect.collidepoint(mx, my):
                    pygame.display.quit()
                    return None

        screen.fill((20, 20, 30))

        title = font.render(
            "Select a map (up/down, Enter/Space, Esc = Back)",
            True,
            (255, 255, 255),
        )
        screen.blit(title, (40, 20))

        line_h = 40
        margin_top = 60

        # Draw map list
        for i, name in enumerate(candidates):
            y = margin_top + i * line_h
            rect = pygame.Rect(40, y - 10, width - 80, line_h - 5)

            if i == selected_idx:
                pygame.draw.rect(screen, (80, 80, 120), rect, border_radius=6)
            else:
                pygame.draw.rect(screen, (60, 60, 60), rect, 1, border_radius=6)

            text = font.render(f"[{i}] {name}", True, (255, 255, 255))
            screen.blit(text, (50, y))

        # Back button at bottom
        back_rect = pygame.Rect(40, height - 60, 120, 36)
        pygame.draw.rect(screen, (60, 120, 200), back_rect, border_radius=6)
        pygame.draw.rect(screen, (230, 230, 240), back_rect, 1, border_radius=6)
        back_label = font.render("Back", True, (0, 0, 0))
        screen.blit(
            back_label,
            (back_rect.centerx - back_label.get_width() // 2,
             back_rect.centery - back_label.get_height() // 2),
        )

        pygame.display.flip()
        clock.tick(30)

    chosen_name = candidates[selected_idx]
    full_path = os.path.join(maps_dir, chosen_name)

    pygame.display.quit()
    return full_path


def choose_training_mode_pygame(has_table: bool) -> str:
    # Small dialog: use existing Q-table or retrain (or quit)
    if not has_table:
        return "train"

    pygame.init()
    width, height = 500, 260
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Lil Cheese Hunter™ - Playground")
    font = pygame.font.SysFont(None, 28)
    clock = pygame.time.Clock()

    btn_w, btn_h = 140, 40
    center_x = width // 2

    retrain_rect = pygame.Rect(center_x - btn_w - 10, 140, btn_w, btn_h)
    continue_rect = pygame.Rect(center_x + 10, 140, btn_w, btn_h)
    quit_rect = pygame.Rect(center_x - btn_w // 2, 190, btn_w, btn_h)

    selected = "train"
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.display.quit()
                return "quit"
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_LEFT, pygame.K_a):
                    selected = "train"
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    selected = "continue"
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    pygame.display.quit()
                    return selected
                elif event.key == pygame.K_ESCAPE:
                    pygame.display.quit()
                    return "quit"
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                if retrain_rect.collidepoint(mx, my):
                    pygame.display.quit()
                    return "train"
                elif continue_rect.collidepoint(mx, my):
                    pygame.display.quit()
                    return "continue"
                elif quit_rect.collidepoint(mx, my):
                    pygame.display.quit()
                    return "quit"

        screen.fill((20, 20, 30))

        title = font.render("Q-table found for this map.", True, (255, 255, 255))
        sub = font.render("What do you want to do?", True, (200, 200, 200))
        screen.blit(title, (40, 40))
        screen.blit(sub, (40, 70))

        def draw_button(rect, label, is_selected):
            if is_selected:
                bg = (100, 100, 160)
                border = 0
            else:
                bg = (60, 60, 80)
                border = 2
            pygame.draw.rect(screen, bg, rect, border_radius=6)
            if border:
                pygame.draw.rect(screen, (200, 200, 220), rect, border, border_radius=6)
            txt = font.render(label, True, (255, 255, 255))
            txt_rect = txt.get_rect(center=rect.center)
            screen.blit(txt, txt_rect)

        draw_button(retrain_rect, "Retrain", selected == "train")
        draw_button(continue_rect, "Continue", selected == "continue")
        draw_button(quit_rect, "Quit", False)

        pygame.display.flip()
        clock.tick(30)


def generate_training_report_plot(rewards,
                                  steps,
                                  success,
                                  window: int = 50,
                                  filename: str = "training_report.png") -> str:
    # Build a PNG with reward/steps/success curves over episodes
    base_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base_dir, filename)

    if not rewards:
        print("[WARN] No rewards logged; skipping report generation.")
        return path

    episodes = np.arange(len(rewards))

    plt.figure(figsize=(12, 6))

    # Rewards
    plt.subplot(3, 1, 1)
    if len(rewards) >= window:
        ma = np.convolve(rewards, np.ones(window) / window, mode="valid")
        plt.plot(np.arange(window - 1, window - 1 + len(ma)), ma)
    else:
        plt.plot(episodes, rewards)
    plt.title("Rewards per Episode")
    plt.xlabel("Episode")
    plt.ylabel("Reward")

    # Steps
    plt.subplot(3, 1, 2)
    if len(steps) >= window:
        ma = np.convolve(steps, np.ones(window) / window, mode="valid")
        plt.plot(np.arange(window - 1, window - 1 + len(ma)), ma)
    else:
        plt.plot(episodes, steps)
    plt.title("Steps per Episode")
    plt.xlabel("Episode")
    plt.ylabel("Steps")

    # Success
    plt.subplot(3, 1, 3)
    if len(success) >= window:
        ma = np.convolve(success, np.ones(window) / window, mode="valid")
        plt.plot(np.arange(window - 1, window - 1 + len(ma)), ma)
    else:
        plt.plot(episodes, success)
    plt.title("Success (1 = success, 0 = fail)")
    plt.xlabel("Episode")
    plt.ylabel("Success")

    plt.tight_layout()
    plt.savefig(path)
    plt.close()

    print(f"[Info] Training report saved to {path}")
    return path


def main():
    # Top-level entry: pick a map, train/load Q-table, then playground
    global MAX_STEPS, NUM_EPISODES_PER_TILE

    maps_dir = "cleaned"
    if not os.path.isdir(maps_dir):
        raise SystemExit(f"No 'cleaned' folder found. Put your map JSONs in ./{maps_dir}")

    candidates = sorted(f for f in os.listdir(maps_dir) if f.lower().endswith(".json"))
    if not candidates:
        raise SystemExit(f"No .json maps found in ./{maps_dir}")

    map_path = select_map_pygame(maps_dir, candidates)
    if map_path is None:
        print("User cancelled map selection — returning to navigation.")
        return

    map_name = os.path.splitext(os.path.basename(map_path))[0]

    print(f"[Info] Loaded map: {map_path}")
    env = GridWorld.from_json(map_path, seed=0)
    print(f"[Info] Map size: {env.rows}x{env.cols}")

    # If multiple home tiles exist, pick the first as “main home”
    if getattr(env, "_homes", []):
        env.set_home(0)

    # Push base RL hyper-parameters into env (for HUD/debug)
    env.alpha = ALPHA
    env.gamma = GAMMA
    env.epsilon = EPSILON_START

    # Approximate “walkable area” to scale episodes/steps
    walkable = 0
    for r in range(env.rows):
        for c in range(env.cols):
            if env.grid[r][c] != WALL:
                walkable += 1

    steps_dynamic = int(2.5 * walkable)
    episodes_dynamic = 100 * math.ceil(math.sqrt(walkable))

    MAX_STEPS = max(50, steps_dynamic)
    NUM_EPISODES_PER_TILE = max(100, episodes_dynamic)

    print(f"[Info] Dynamic MAX_STEPS: {MAX_STEPS}")
    print(f"[Info] Dynamic NUM_EPISODES_PER_TILE: {NUM_EPISODES_PER_TILE}")

    env.max_steps = MAX_STEPS
    env.episodes_per_tile = NUM_EPISODES_PER_TILE

    # Q-table file for this map
    qtables_dir = "qtables"
    os.makedirs(qtables_dir, exist_ok=True)
    qtable_path = os.path.join(qtables_dir, f"qtable_{map_name}_generic_goal.pkl")

    has_table = os.path.isfile(qtable_path)
    mode = choose_training_mode_pygame(has_table)

    if mode == "quit":
        print("User cancelled at training-mode selection.")
        return

    # Load or create agent / Q-table
    if mode == "continue" and has_table:
        print(f"[Info] Using existing Q-table → {qtable_path}")
        agent = QLearningAgent.load(qtable_path)
        agent.epsilon = 0.0
        trained_new = False
        print("[Info] Using existing Q-table in greedy mode (ε=0).")
    else:
        if has_table:
            print("[Info] Retraining: existing Q-table will be overwritten.")
        else:
            print("[Info] No Q-table found. Training a new one...")
        agent = QLearningAgent(alpha=ALPHA, gamma=GAMMA, epsilon=EPSILON_START, seed=0)
        trained_new = True

    # Viewer for training + playground (if Pygame is available)
    viewer = None
    if USE_PYGAME:
        try:
            viewer = PygameViewer(env.rows, env.cols)
        except Exception as e:
            print(f"[Info] Pygame unavailable ({e}).")
            viewer = None

    # Let viewer know it can expect a training report
    env.has_training_report = True

    try:
        if trained_new:
            # Logs for reward/steps/success curves
            rewards_per_episode: list[float] = []
            steps_per_episode: list[int] = []
            success_per_episode: list[int] = []

            train_all_goals(
                env,
                agent,
                viewer,
                rewards_log=rewards_per_episode,
                steps_log=steps_per_episode,
                success_log=success_per_episode,
            )

            agent.save(qtable_path)
            print(f"\n[Info] Saved Q-table → {qtable_path}")
            agent.epsilon = 0.0

            # Generate PNG report for overlay
            if viewer is not None and len(rewards_per_episode) > 0:
                report_path = generate_training_report_plot(
                    rewards_per_episode,
                    steps_per_episode,
                    success_per_episode,
                )
                env.has_training_report = True
                viewer.load_report_image(os.path.basename(report_path))
        else:
            agent.epsilon = 0.0

        if viewer is not None:
            viewer.show_animation = True

        # Reset world and enter interactive “click to go here” mode
        env.reset()

        interactive_loop(env, agent, viewer)

    finally:
        if viewer:
            viewer.close()


if __name__ == "__main__":
    main()
