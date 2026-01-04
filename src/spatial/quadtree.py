from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Point:
    x: float
    y: float
    entity_id: int


@dataclass
class Rectangle:
    x: float
    y: float
    w: float
    h: float

    def contains(self, point: Point) -> bool:
        return (
            self.x - self.w <= point.x <= self.x + self.w
            and self.y - self.h <= point.y <= self.y + self.h
        )

    def intersects(self, other: "Rectangle") -> bool:
        return not (
            self.x + self.w < other.x - other.w
            or self.x - self.w > other.x + other.w
            or self.y + self.h < other.y - other.h
            or self.y - self.h > other.y + other.h
        )


class QuadTree:
    def __init__(self, boundary: Rectangle, capacity: int = 4):
        self.boundary = boundary
        self.capacity = capacity
        self.points: List[Point] = []
        self.divided = False

        self.northeast: Optional[QuadTree] = None
        self.northwest: Optional[QuadTree] = None
        self.southeast: Optional[QuadTree] = None
        self.southwest: Optional[QuadTree] = None

        self.children: List[Optional[QuadTree]] = []

    def subdivide(self) -> None:
        x, y, w, h = self.boundary.x, self.boundary.y, self.boundary.w, self.boundary.h
        hw, hh = w / 2, h / 2

        ne = Rectangle(x + hw, y + hh, hw, hh)
        nw = Rectangle(x - hw, y + hh, hw, hh)
        se = Rectangle(x + hw, y - hh, hw, hh)
        sw = Rectangle(x - hw, y - hh, hw, hh)

        self.northeast = QuadTree(ne, self.capacity)
        self.northwest = QuadTree(nw, self.capacity)
        self.southeast = QuadTree(se, self.capacity)
        self.southwest = QuadTree(sw, self.capacity)

        self.children = [self.northeast, self.northwest, self.southeast, self.southwest]

        self.divided = True

    def insert(self, point: Point) -> bool:
        if not self.boundary.contains(point):
            return False

        if len(self.points) < self.capacity and not self.divided:
            self.points.append(point)
            return True

        if not self.divided:
            self.subdivide()

            old_points = self.points
            self.points = []
            for p in old_points:
                self._insert_into_children(p)

        return self._insert_into_children(point)

    def _insert_into_children(self, point: Point) -> bool:
        for child in self.children:
            if child and child.insert(point):
                return True
        return False

    def query(self, range_rect: Rectangle) -> List[int]:
        found: List[int] = []

        if not self.boundary.intersects(range_rect):
            return found

        for point in self.points:
            if range_rect.contains(point):
                found.append(point.entity_id)

        if self.divided:
            for child in self.children:
                if not child:
                    continue

                found.extend(child.query(range_rect))

        return found

    def query_radius(
        self, center_x: float, center_y: float, radius: float
    ) -> List[int]:
        range_rect = Rectangle(center_x, center_y, radius, radius)
        result: List[int] = []
        radius_sq = radius * radius

        self._query_radius_recursive(range_rect, center_x, center_y, radius_sq, result)
        return result

    def _query_radius_recursive(
        self,
        range_rect: Rectangle,
        cx: float,
        cy: float,
        radius_sq: float,
        result: List[int],
    ) -> None:
        if not self.boundary.intersects(range_rect):
            return

        for point in self.points:
            dx = point.x - cx
            dy = point.y - cy
            if dx * dx + dy * dy <= radius_sq:
                result.append(point.entity_id)

        if self.divided:
            for child in self.children:
                if child:
                    child._query_radius_recursive(range_rect, cx, cy, radius_sq, result)

    def _find_point(self, entity_id: int) -> Optional[Point]:
        for point in self.points:
            if point.entity_id != entity_id:
                continue

            return point

        if not self.divided:
            return None

        for child in self.children:
            if not child:
                continue

            result = child._find_point(entity_id)
            if result:
                return result

        return None

    def remove(self, entity_id: int) -> bool:
        for i, point in enumerate(self.points):
            if point.entity_id == entity_id:
                self.points.pop(i)
                return True

        if not self.divided:
            return False

        for child in self.children:
            if not child:
                continue

            if child.remove(entity_id):
                return True

        return False

    def clear(self) -> None:
        self.points.clear()
        if self.divided:
            self.northeast = None
            self.northwest = None
            self.southeast = None
            self.southwest = None
            self.children = []
            self.divided = False

    def count(self) -> int:
        total = len(self.points)
        if self.divided:
            for child in self.children:
                if not child:
                    continue

                total += child.count()
        return total
