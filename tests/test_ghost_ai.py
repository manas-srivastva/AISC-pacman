"""Tests for ghost pathfinding, fuzzy aggression, and power-pellet behavior."""
import os

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame

pygame.init()

from fuzzy_controller import FuzzyController
from game_state import GameState
from ghost import Ghost
from maze import Maze
from pathfinding import a_star_search, breadth_first_search
from settings import (
    COLOR_GHOST_FLEE,
    GHOST_POINTS,
    GhostState,
    GhostType,
    INITIAL_LIVES,
)
from pacman import Pacman


TEST_MAZE = Maze(
    [
        "#####",
        "#...#",
        "#.#.#",
        "#...#",
        "#####",
    ]
)


def test_bfs_and_a_star_return_shortest_walkable_paths():
    start = (1, 1)
    goal = (3, 3)

    bfs_path = breadth_first_search(TEST_MAZE, start, goal)
    a_star_path = a_star_search(TEST_MAZE, start, goal)

    assert bfs_path[0] == start and bfs_path[-1] == goal
    assert a_star_path[0] == start and a_star_path[-1] == goal
    assert len(a_star_path) == len(bfs_path)
    assert all(TEST_MAZE.is_walkable(*tile) for tile in a_star_path)
    assert a_star_search(TEST_MAZE, start, (0, 0)) == []


def test_fuzzy_aggression_responds_to_distance_and_pellet_protection():
    close_critical = FuzzyController.aggression(1, 0, 1)
    far_healthy = FuzzyController.aggression(12, 0, 3)
    protected = FuzzyController.aggression(1, 1, 1)

    assert close_critical > far_healthy
    assert protected < close_critical


def test_hunter_chases_player_and_powered_ghost_flees():
    maze = Maze(["#####", "#...#", "#####"])
    pacman = Pacman(3, 1)
    ghost = Ghost(2, 1, ghost_type=GhostType.HUNTER)

    ghost.update(maze, pacman)
    assert ghost.current_dir == (1, 0)

    ghost.reset_position()
    ghost.update(maze, pacman, protection=1.0)
    assert ghost.state == GhostState.FLEE
    assert ghost.color == COLOR_GHOST_FLEE
    assert ghost.current_dir == (-1, 0)


def test_powered_collision_scores_ghost_without_losing_life():
    maze = Maze(["#####", "#P.G#", "#...#", "#####"])
    state = GameState(maze)
    ghost = state.ghosts[0]
    state.power_ticks_remaining = 10
    state.pacman.x = ghost.x
    state.pacman.y = ghost.y
    state.pacman.col = ghost.col
    state.pacman.row = ghost.row
    score_before = state.score

    state.update()

    assert state.score == score_before + GHOST_POINTS
    assert state.lives == INITIAL_LIVES
    assert (ghost.col, ghost.row) == (ghost.spawn_col, ghost.spawn_row)
