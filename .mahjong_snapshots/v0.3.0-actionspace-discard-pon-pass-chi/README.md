# Mahjong CFR Agent

This project is focused on building a full 4-player Mahjong game environment and training an AI agent to play using Counterfactual Regret Minimization (CFR).

We are using the full 144-tile Mahjong set and simulating standard game rules. The goal is to train one CFR-based agent against three rule-based opponents. In future versions, this can be expanded to include multiple learning agents.

## Project Goals

- Build a complete Mahjong engine from scratch
- Design a CFR-compatible environment with hidden information
- Implement a single learning agent (Player 0)
- Integrate oracle-guided rollouts using real game data
- Analyze and evaluate learned strategies

## Current Progress

- Tile system implemented (`Tile` class)
- CFR planning and design in progress
- Game state and info set structure defined
- Testing framework in place
- Wall and action system to be implemented next
