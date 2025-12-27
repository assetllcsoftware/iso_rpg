"""A* Pathfinding implementation."""

import heapq
from typing import List, Tuple, Optional, Set
from dataclasses import dataclass, field


@dataclass(order=True)
class Node:
    """Pathfinding node."""
    f_cost: float
    g_cost: float = field(compare=False)
    x: int = field(compare=False)
    y: int = field(compare=False)
    parent: Optional['Node'] = field(compare=False, default=None)


class Pathfinder:
    """A* pathfinding for the dungeon."""
    
    DIRECTIONS = [
        (0, -1),   # Up
        (0, 1),    # Down
        (-1, 0),   # Left
        (1, 0),    # Right
        (-1, -1),  # Up-left
        (1, -1),   # Up-right
        (-1, 1),   # Down-left
        (1, 1),    # Down-right
    ]
    
    def __init__(self, dungeon):
        self.dungeon = dungeon
    
    def find_path(
        self,
        start_x: float,
        start_y: float,
        goal_x: float,
        goal_y: float,
        max_iterations: int = 1000
    ) -> List[Tuple[float, float]]:
        """Find path from start to goal.
        
        Args:
            start_x, start_y: Starting position (float)
            goal_x, goal_y: Goal position (float)
            max_iterations: Maximum search iterations
        
        Returns:
            List of waypoints as (x, y) tuples, or empty if no path
        """
        # Convert to tile coordinates
        sx, sy = int(start_x), int(start_y)
        gx, gy = int(goal_x), int(goal_y)
        
        # Check bounds and walkability
        if not self.dungeon.is_walkable(gx, gy):
            return []
        
        if sx == gx and sy == gy:
            return [(goal_x, goal_y)]
        
        # A* algorithm
        open_set = []
        closed_set: Set[Tuple[int, int]] = set()
        
        start_node = Node(
            f_cost=self._heuristic(sx, sy, gx, gy),
            g_cost=0,
            x=sx,
            y=sy
        )
        heapq.heappush(open_set, start_node)
        
        # Track best g_cost to each position
        g_costs = {(sx, sy): 0}
        
        iterations = 0
        
        while open_set and iterations < max_iterations:
            iterations += 1
            
            current = heapq.heappop(open_set)
            
            if current.x == gx and current.y == gy:
                # Found path!
                return self._reconstruct_path(current, goal_x, goal_y)
            
            if (current.x, current.y) in closed_set:
                continue
            
            closed_set.add((current.x, current.y))
            
            # Check neighbors
            for dx, dy in self.DIRECTIONS:
                nx, ny = current.x + dx, current.y + dy
                
                if (nx, ny) in closed_set:
                    continue
                
                if not self.dungeon.is_walkable(nx, ny):
                    continue
                
                # Diagonal movement check - make sure we can cut corner
                if dx != 0 and dy != 0:
                    if not self.dungeon.is_walkable(current.x + dx, current.y):
                        continue
                    if not self.dungeon.is_walkable(current.x, current.y + dy):
                        continue
                
                # Calculate costs
                move_cost = 1.414 if (dx != 0 and dy != 0) else 1.0
                new_g = current.g_cost + move_cost
                
                # Check if this is a better path
                if (nx, ny) in g_costs and new_g >= g_costs[(nx, ny)]:
                    continue
                
                g_costs[(nx, ny)] = new_g
                f_cost = new_g + self._heuristic(nx, ny, gx, gy)
                
                neighbor = Node(
                    f_cost=f_cost,
                    g_cost=new_g,
                    x=nx,
                    y=ny,
                    parent=current
                )
                heapq.heappush(open_set, neighbor)
        
        # No path found
        return []
    
    def _heuristic(self, x1: int, y1: int, x2: int, y2: int) -> float:
        """Euclidean distance heuristic."""
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        return ((dx ** 2) + (dy ** 2)) ** 0.5
    
    def _reconstruct_path(
        self,
        end_node: Node,
        goal_x: float,
        goal_y: float
    ) -> List[Tuple[float, float]]:
        """Reconstruct path from end node."""
        path = []
        current = end_node
        
        while current is not None:
            # Center of tile
            path.append((float(current.x) + 0.5, float(current.y) + 0.5))
            current = current.parent
        
        path.reverse()
        
        # Replace last point with exact goal
        if path:
            path[-1] = (goal_x, goal_y)
        
        # Simplify path (remove unnecessary waypoints)
        return self._simplify_path(path)
    
    def _simplify_path(self, path: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """Remove intermediate waypoints when direct line is possible."""
        if len(path) <= 2:
            return path
        
        simplified = [path[0]]
        
        i = 0
        while i < len(path) - 1:
            # Try to skip ahead
            j = len(path) - 1
            while j > i + 1:
                if self._has_line_of_sight(path[i], path[j]):
                    break
                j -= 1
            
            simplified.append(path[j])
            i = j
        
        return simplified
    
    def _has_line_of_sight(self, p1: Tuple[float, float], p2: Tuple[float, float]) -> bool:
        """Check if two points have line of sight (Bresenham's line)."""
        x1, y1 = int(p1[0]), int(p1[1])
        x2, y2 = int(p2[0]), int(p2[1])
        
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        x, y = x1, y1
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        
        if dx > dy:
            err = dx / 2
            while x != x2:
                if not self.dungeon.is_walkable(x, y):
                    return False
                err -= dy
                if err < 0:
                    y += sy
                    err += dx
                x += sx
        else:
            err = dy / 2
            while y != y2:
                if not self.dungeon.is_walkable(x, y):
                    return False
                err -= dx
                if err < 0:
                    x += sx
                    err += dy
                y += sy
        
        return self.dungeon.is_walkable(x2, y2)

