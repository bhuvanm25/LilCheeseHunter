# TreatQuest Development Plan

## Stage 1: Basic Movement
- ✅ **Goal:** Place the agent ("Jerry") inside a box and make it move randomly.
- **Status:** Done.
- **Note:** We are not implementing learning yet.

---


## Stage 2: Episode Setup
To structure learning and exploration, we’ll define *episodes*.

### Episode Flow
1. **Spawn Entities:**
   - 🧀 *Spawn Cheese*.
   - 🪤 *Spawn Trap*.
   - 🐭 *Spawn Jerry*.
2. **Inform Jerry:**
   - Tell Jerry the known positions of traps and treats.
   - Jerry will use this info to compare against its Q-data (later on).
3. **Movement Logic:**
   - Jerry moves step by step until:
     - He reaches the cheese → **Reward = +1**
     - He hits the trap → **Penalty = -1**
     - He moves normally → **Small cost = -0.01 per step**
4. **Exploration Rule:**
   - If Jerry has no prior data for a state, he explores randomly.

---

## Stage 3: Fixed vs. Random Spawns
- **Current Approach:** Fixed spawn points for all entities.
- **Future Work:** Randomize positions to improve generalization.

---

## Stage 4: Episode Looping
- Add multiple episode runs for training and evaluation.
- Store Q-values for states and actions after each episode.

---

## Summary
**Core Features:**
- Jerry spawns in a maze.
- Cheese and traps are placed.
- Jerry learns to reach cheese (+1) while avoiding traps (–1).
- Each step costs a small negative reward (–0.01).
- Runs multiple episodes to learn optimal paths.

---

### Future Extensions
- Implement Q-learning.
- Add exploration–exploitation balance (ε-greedy).
- Introduce multiple traps/treats per episode.
- Visualize reward progression over time.
