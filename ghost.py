"""Ghost agents with distinct strategies, finite-state modes, and maze navigation."""
import random
from typing import List, Optional, Tuple






import pygame

from fuzzy_controller import FuzzyController
from maze import Maze
from pacman import Pacman
from pathfinding import a_star_search, distances_from
from settings import (
    COLOR_GHOST_CYAN,
    COLOR_GHOST_FLEE,
    COLOR_GHOST_ORANGE,
    COLOR_GHOST_PINK,
    COLOR_GHOST_RED,
    GHOST_SPEED,
    TILE_SIZE,
    Direction,
    GhostState,
    GhostType,
)


GHOST_COLORS = {
    GhostType.HUNTER: COLOR_GHOST_RED,
    GhostType.AMBUSHER: COLOR_GHOST_PINK,
    GhostType.PATROL: COLOR_GHOST_CYAN,
    GhostType.GUARD: COLOR_GHOST_ORANGE,
}


class Ghost:
    """A ghost that pursues, patrols, searches, or flees based on game state."""

    def __init__(
        self,
        col: int,
        row: int,
        color: Optional[Tuple[int, int, int]] = None,
        ghost_type: GhostType = GhostType.HUNTER,
    ):
        self.spawn_col = col
        self.spawn_row = row
        self.col = col
        self.row = row
        self.spawn_col = col
        self.spawn_row = row
        self.col = col
        self.row = row
        self.x = (col + 0.5) * TILE_SIZE
        self.y = (row + 0.5) * TILE_SIZE
        self.current_dir: Tuple[int, int] = Direction.LEFT
        self.ghost_type = ghost_type
        self.base_color = color if color is not None else GHOST_COLORS[ghost_type]
        self.color = self.base_color
        self.speed = GHOST_SPEED
        self.radius = int(TILE_SIZE * 0.45)
        self.state = GhostState.PATROL if ghost_type in (
            GhostType.PATROL,
            GhostType.GUARD,
        ) else GhostState.CHASE
        self.patrol_targets: List[Tuple[int, int]] = []
        self.patrol_index = 0
        self.last_seen_player: Optional[Tuple[int, int]] = None

    def get_legal_directions(
        self, current_col: int, current_row: int, maze: Maze
    ) -> List[Tuple[int, int]]:
        """Return all walkable cardinal directions from the given tile."""
        legal = []
        for direction in (
            Direction.UP,
            Direction.DOWN,
            Direction.LEFT,
            Direction.RIGHT,
        ):

            dx, dy = direction
            if maze.is_walkable(current_col + dx, current_row + dy):
                legal.append(direction)
        return legal

    def _get_patrol_targets(self, maze: Maze) -> List[Tuple[int, int]]:
        walkable = [
            (col, row)
            for row in range(maze.rows)
            for col in range(maze.cols)
            if maze.is_walkable(col, row)
        ]
        if not walkable:
            return [(self.spawn_col, self.spawn_row)]

        corners = (
            (1, 1),
            (maze.cols - 2, 1),
            (maze.cols - 2, maze.rows - 2),
            (1, maze.rows - 2),
        )
        targets = []
        for corner in corners:
            nearest = min(
                walkable,
                key=lambda tile: abs(tile[0] - corner[0]) + abs(tile[1] - corner[1]),
            )
            if nearest not in targets:
                targets.append(nearest)
        return targets or [walkable[0]]

    def _target_for_state(
        self,
        maze: Maze,
        pacman: Pacman,
        aggression: float,
        distance_tiles: float,
    ) -> Tuple[int, int]:
        player_tile = (pacman.col, pacman.row)
        self.last_seen_player = player_tile

        if self.ghost_type == GhostType.HUNTER:
            self.state = GhostState.CHASE
            return player_tile

        if self.ghost_type == GhostType.AMBUSHER:
            self.state = GhostState.CHASE
            dx, dy = pacman.current_dir
            for lead in range(4, 0, -1):
                target = (pacman.col + dx * lead, pacman.row + dy * lead)
                if maze.is_walkable(*target):
                    return target
            return player_tile

        if not self.patrol_targets:
            self.patrol_targets = self._get_patrol_targets(maze)
        patrol_target = self.patrol_targets[self.patrol_index]

        if self.ghost_type == GhostType.GUARD:
            if distance_tiles <= 5.0 or aggression >= 65.0:
                self.state = GhostState.CHASE
                return player_tile
            self.state = GhostState.PATROL
            return patrol_target

        if distance_tiles <= 7.0 and aggression >= 35.0:
            self.state = GhostState.SEARCH
            return self.last_seen_player
        self.state = GhostState.PATROL
        return patrol_target

    def _choose_direction(
        self,
        maze: Maze,
        pacman: Pacman,
        frightened: bool,
        target: Tuple[int, int],
    ) -> None:
        legal = self.get_legal_directions(self.col, self.row, maze)
        if not legal:
            self.current_dir = Direction.NONE
            return

        opposite = Direction.OPPOSITES.get(self.current_dir)
        choices = [direction for direction in legal if direction != opposite]
        if not choices:
            choices = legal

        if frightened:
            distances = distances_from(maze, (pacman.col, pacman.row))
            self.current_dir = max(
                choices,
                key=lambda direction: distances.get(
                    (self.col + direction[0], self.row + direction[1]), -1
                ),
            )
            self.state = GhostState.FLEE
            return

        path = a_star_search(maze, (self.col, self.row), target)
        if len(path) > 1:
            next_tile = path[1]
            direction = (next_tile[0] - self.col, next_tile[1] - self.row)
            if direction in legal:
                self.current_dir = direction
                return
        self.current_dir = random.choice(choices)

    def update(
        self,
        maze: Maze,
        pacman: Optional[Pacman] = None,
        player_lives: int = 3,
        protection: float = 0.0,
    ) -> None:
        """Update ghost strategy and movement; protection is normalized to 0-1."""
        current_col = int(self.x // TILE_SIZE)
        current_row = int(self.y // TILE_SIZE)
        tile_center_x = (current_col + 0.5) * TILE_SIZE
        tile_center_y = (current_row + 0.5) * TILE_SIZE
        at_center = (
            abs(self.x - tile_center_x) <= self.speed / 2.0
            and abs(self.y - tile_center_y) <= self.speed / 2.0
        )

        if at_center:
            # Snap to center
            self.x = tile_center_x
            self.y = tile_center_y
            self.col = current_col
            self.row = current_row

            self.x = tile_center_x
            self.y = tile_center_y
            self.col = current_col
            self.row = current_row

            if pacman is None:
                target = (self.col, self.row)
                frightened = False
                aggression = 0.0
                distance_tiles = 0.0
            else:
                distance_tiles = (
                    abs(self.col - pacman.col) + abs(self.row - pacman.row)
                )
                aggression = FuzzyController.aggression(
                    distance_tiles, protection, player_lives
                )
                frightened = protection > 0.0
                target = self._target_for_state(
                    maze, pacman, aggression, distance_tiles
                )

            if (
                self.ghost_type in (GhostType.PATROL, GhostType.GUARD)
                and self.state == GhostState.PATROL
                and self.patrol_targets
                and (self.col, self.row) == self.patrol_targets[self.patrol_index]
            ):
                self.patrol_index = (self.patrol_index + 1) % len(self.patrol_targets)
                target = self.patrol_targets[self.patrol_index]

            self.speed = GHOST_SPEED * (0.75 + aggression / 200.0)
            self.color = COLOR_GHOST_FLEE if frightened else self.base_color
            if pacman is not None:
                self._choose_direction(maze, pacman, frightened, target)
            else:
                legal = self.get_legal_directions(self.col, self.row, maze)
                reverse = Direction.OPPOSITES.get(self.current_dir)
                choices = [direction for direction in legal if direction != reverse]
                self.current_dir = random.choice(choices or legal) if legal else Direction.NONE

            legal_dirs = self.get_legal_directions(self.col, self.row, maze)
            opposite = Direction.OPPOSITES.get(self.current_dir)
            forward_dirs = [direction for direction in legal_dirs if direction != opposite]

            if forward_dirs:
                if self.current_dir in forward_dirs and random.random() < 0.65:
                    pass
                else:
                    self.current_dir = random.choice(forward_dirs)
            elif legal_dirs:
                self.current_dir = legal_dirs[0]
            else:
                self.current_dir = Direction.NONE

        dx, dy = self.current_dir
        if dx or dy:
            target_x = self.x + dx * self.speed
            target_y = self.y + dy * self.speed
            next_col = int(target_x // TILE_SIZE)
            next_row = int(target_y // TILE_SIZE)
            if maze.is_walkable(next_col, next_row):
                self.x = target_x
                self.y = target_y
            else:
                self.current_dir = Direction.NONE

                self.x = target_x
                self.y = target_y
            else:
                self.x = tile_center_x
                self.y = tile_center_y

        self.col = int(self.x // TILE_SIZE)
        self.row = int(self.y // TILE_SIZE)

    def get_rect(self) -> pygame.Rect:
        """Return the bounding rectangle used for ghost collisions."""
        return pygame.Rect(
            int(self.x - self.radius),
            int(self.y - self.radius),
            self.radius * 2,
            self.radius * 2,
        )

    def reset_position(self) -> None:
        """Reset the ghost to its spawn tile and initial state."""
        self.col = self.spawn_col
        self.row = self.spawn_row
        self.x = (self.col + 0.5) * TILE_SIZE
        self.y = (self.row + 0.5) * TILE_SIZE
        self.current_dir = Direction.LEFT
        self.state = GhostState.PATROL if self.ghost_type in (
            GhostType.PATROL,
            GhostType.GUARD,
        ) else GhostState.CHASE
        self.color = self.base_color
        self.speed = GHOST_SPEED
        self.patrol_index = 0
        self.last_seen_player = None

