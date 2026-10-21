"""Grid pathfinding helpers used by the ghost agents."""
from collections import deque
from heapq import heappop, heappush
from itertools import count
from typing import Dict, Iterator, List, Tuple

from maze import Maze

Tile = Tuple[int, int]


def _neighbors(tile: Tile, maze: Maze) -> Iterator[Tile]:
    col, row = tile
    for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
        neighbor = (col + dx, row + dy)
        if maze.is_walkable(*neighbor):
            yield neighbor


def _reconstruct_path(came_from: Dict[Tile, Tile], goal: Tile) -> List[Tile]:
    path = [goal]
    while path[-1] in came_from:
        path.append(came_from[path[-1]])
    path.reverse()
    return path


def breadth_first_search(maze: Maze, start: Tile, goal: Tile) -> List[Tile]:
    """Return a shortest walkable path (including start and goal), or an empty list."""
    if not maze.is_walkable(*start) or not maze.is_walkable(*goal):
        return []
    if start == goal:
        return [start]

    frontier = deque([start])
    came_from: Dict[Tile, Tile] = {}
    visited = {start}
    while frontier:
        current = frontier.popleft()
        for neighbor in _neighbors(current, maze):
            if neighbor in visited:
                continue
            visited.add(neighbor)
            came_from[neighbor] = current
            if neighbor == goal:
                return _reconstruct_path(came_from, goal)
            frontier.append(neighbor)
    return []


def a_star_search(maze: Maze, start: Tile, goal: Tile) -> List[Tile]:
    """Return a shortest Manhattan-heuristic A* path, including both endpoints."""
    if not maze.is_walkable(*start) or not maze.is_walkable(*goal):
        return []
    if start == goal:
        return [start]

    def heuristic(tile: Tile) -> int:
        return abs(tile[0] - goal[0]) + abs(tile[1] - goal[1])

    sequence = count()
    frontier = [(heuristic(start), next(sequence), start)]
    came_from: Dict[Tile, Tile] = {}
    cost_so_far = {start: 0}
    while frontier:
        _, _, current = heappop(frontier)
        if current == goal:
            return _reconstruct_path(came_from, goal)
        for neighbor in _neighbors(current, maze):
            new_cost = cost_so_far[current] + 1
            if new_cost >= cost_so_far.get(neighbor, float("inf")):
                continue
            cost_so_far[neighbor] = new_cost
            came_from[neighbor] = current
            heappush(
                frontier,
                (new_cost + heuristic(neighbor), next(sequence), neighbor),
            )
    return []


def distances_from(maze: Maze, start: Tile) -> Dict[Tile, int]:
    """Return shortest-path distances from a walkable start tile."""
    if not maze.is_walkable(*start):
        return {}
    distances = {start: 0}
    frontier = deque([start])
    while frontier:
        current = frontier.popleft()
        for neighbor in _neighbors(current, maze):
            if neighbor not in distances:
                distances[neighbor] = distances[current] + 1
                frontier.append(neighbor)
    return distances
