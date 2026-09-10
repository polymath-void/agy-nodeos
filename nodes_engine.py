import math
import sqlite3

class Point:
    def __init__(self, x, y, node_id, node_type, mass=1.0, name="unknown", calls=None):
        self.x = x
        self.y = y
        self.vx = 0.0
        self.vy = 0.0
        self.fx = 0.0
        self.fy = 0.0
        self.mass = mass
        self.node_id = node_id
        self.node_type = node_type
        self.name = name
        self.calls = calls if calls else []
        self.edges = []

class Rectangle:
    def __init__(self, x, y, w, h):
        self.x = x
        self.y = y
        self.w = w
        self.h = h

    def contains(self, point):
        return (self.x - self.w <= point.x <= self.x + self.w and
                self.y - self.h <= point.y <= self.y + self.h)

    def intersects(self, range_rect):
        return not (range_rect.x - range_rect.w > self.x + self.w or
                    range_rect.x + range_rect.w < self.x - self.w or
                    range_rect.y - range_rect.h > self.y + self.h or
                    range_rect.y + range_rect.h < self.y - self.h)

class QuadTree:
    def __init__(self, boundary, capacity):
        self.boundary = boundary
        self.capacity = capacity
        self.points = []
        self.divided = False

    def subdivide(self):
        x, y, w, h = self.boundary.x, self.boundary.y, self.boundary.w / 2, self.boundary.h / 2
        self.northeast = QuadTree(Rectangle(x + w, y - h, w, h), self.capacity)
        self.northwest = QuadTree(Rectangle(x - w, y - h, w, h), self.capacity)
        self.southeast = QuadTree(Rectangle(x + w, y + h, w, h), self.capacity)
        self.southwest = QuadTree(Rectangle(x - w, y + h, w, h), self.capacity)
        self.divided = True

    def insert(self, point):
        if not self.boundary.contains(point):
            return False
        if len(self.points) < self.capacity:
            self.points.append(point)
            return True
        if not self.divided:
            self.subdivide()
        return (self.northeast.insert(point) or self.northwest.insert(point) or 
                self.southeast.insert(point) or self.southwest.insert(point))

    def query(self, range_rect, found=None):
        if found is None: found = []
        if not self.boundary.intersects(range_rect): return found
        for p in self.points:
            if range_rect.contains(p): found.append(p)
        if self.divided:
            self.northwest.query(range_rect, found)
            self.northeast.query(range_rect, found)
            self.southwest.query(range_rect, found)
            self.southeast.query(range_rect, found)
        return found

class NativeNodesEngine:
    """
    NATIVE SPATIAL CLUSTERING & PHYSICS ENGINE
    Implements Force-Directed Graph physics (Repulsion + Gravity + Hooke's Law Springs) and batch SQLite sync.
    """
    def __init__(self, db_path='agy_nodeos.db'):
        self.db_path = db_path
        self.boundary = Rectangle(500, 500, 500, 500)
        self.qtree = QuadTree(self.boundary, 4)
        self.all_nodes = []
        self.hydrate_from_db()

    def hydrate_from_db(self):
        print("[Physics Engine] Hydrating spatial matrix from SQLite Database...")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT node_id, node_type, x_coord, y_coord, name FROM nodes")
            rows = cursor.fetchall()
            for row in rows:
                if row[2] is not None and row[3] is not None:
                    name = row[4] if len(row) > 4 else "unknown"
                    p = Point(row[2], row[3], row[0], row[1], name=name)
                    self.all_nodes.append(p)
                    self.qtree.insert(p)
            print(f"[Physics Engine] Hydrated {len(self.all_nodes)} kinetic nodes.")
        except sqlite3.OperationalError:
            print("[Physics Engine] Table not initialized. Skipping hydration.")
        conn.close()

    def rebuild_qtree(self):
        self.qtree = QuadTree(self.boundary, 4)
        for p in self.all_nodes:
            self.qtree.insert(p)

    def resolve_edges(self):
        """Resolves the string AST calls into physical Point references for Spring Physics."""
        print("[Physics Engine] Resolving execution call graph into physical edges...")
        name_to_node = {p.name: p for p in self.all_nodes}
        edge_count = 0
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for p in self.all_nodes:
            for call_name in p.calls:
                target = name_to_node.get(call_name)
                if target and target not in p.edges:
                    p.edges.append(target)
                    edge_count += 1
                    try:
                        cursor.execute('''
                            INSERT INTO edges (source_id, target_id, relation_type) 
                            VALUES (?, ?, "CALL")
                        ''', (p.node_id, target.node_id))
                    except sqlite3.OperationalError:
                        pass # Ignore if edges table missing/already exists
                        
        conn.commit()
        conn.close()
        print(f"[Physics Engine] Bonded {edge_count} structural connections. Simulating graph clustering...")
        if edge_count > 0:
            self.simulate_physics(ticks=100)
            self.sync_to_sqlite()

    def simulate_physics(self, ticks=50):
        """Euler Integration of Coulomb Repulsion, Central Gravity, and Hooke's Law Springs."""
        damping = 0.85
        time_step = 1.0
        k_repulse = 5000.0
        k_gravity = 0.05
        k_spring = 0.1  # Hooke's Law spring constant
        ideal_length = 50.0  # Ideal distance between connected nodes
        center_x, center_y = 500.0, 500.0
        
        for _ in range(ticks):
            # Reset forces and apply central gravity
            for node in self.all_nodes:
                node.fx = (center_x - node.x) * k_gravity
                node.fy = (center_y - node.y) * k_gravity
                
            # Coulomb Repulsion between ALL nodes
            for i in range(len(self.all_nodes)):
                for j in range(i + 1, len(self.all_nodes)):
                    n1, n2 = self.all_nodes[i], self.all_nodes[j]
                    dx, dy = n1.x - n2.x, n1.y - n2.y
                    dist_sq = dx**2 + dy**2
                    if dist_sq > 0:
                        force = k_repulse / dist_sq
                        dist = math.sqrt(dist_sq)
                        fx = force * (dx / dist)
                        fy = force * (dy / dist)
                        n1.fx += fx
                        n1.fy += fy
                        n2.fx -= fx
                        n2.fy -= fy
                        
            # Hooke's Law Spring Attraction between CONNECTED nodes
            for n1 in self.all_nodes:
                for n2 in n1.edges:
                    dx, dy = n2.x - n1.x, n2.y - n1.y
                    dist = math.sqrt(dx**2 + dy**2)
                    if dist > 0:
                        force = k_spring * (dist - ideal_length)
                        fx = force * (dx / dist)
                        fy = force * (dy / dist)
                        n1.fx += fx
                        n1.fy += fy
                        n2.fx -= fx
                        n2.fy -= fy

            # Euler Integration
            for node in self.all_nodes:
                ax = node.fx / node.mass
                ay = node.fy / node.mass
                node.vx = (node.vx + ax * time_step) * damping
                node.vy = (node.vy + ay * time_step) * damping
                node.x += node.vx * time_step
                node.y += node.vy * time_step
                
        self.rebuild_qtree()

    def sync_to_sqlite(self):
        """Batch update physical positions to SQLite to save I/O overhead."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        for p in self.all_nodes:
            cursor.execute('''
                INSERT INTO nodes (node_id, node_type, name, x_coord, y_coord, last_updated)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(node_id) DO UPDATE SET 
                    name=excluded.name, 
                    x_coord=excluded.x_coord, 
                    y_coord=excluded.y_coord, 
                    last_updated=excluded.last_updated
            ''', (p.node_id, p.node_type, p.name, p.x, p.y))
        conn.commit()
        conn.close()

    def add_node(self, node_id, node_type, name="unknown", calls=None, parent_x=500, parent_y=500):
        import random
        drop_x = parent_x + random.uniform(-10, 10)
        drop_y = parent_y + random.uniform(-10, 10)
        
        existing = next((n for n in self.all_nodes if n.node_id == node_id), None)
        if not existing:
            p = Point(drop_x, drop_y, node_id, node_type, name=name, calls=calls)
            self.all_nodes.append(p)
            print(f"[Physics Engine] Dropped {node_type} '{name}' into kinetic simulation.")
            return p
        else:
            existing.name = name
            if calls:
                existing.calls = calls
            return existing
