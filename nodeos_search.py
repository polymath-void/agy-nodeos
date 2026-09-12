#!/usr/bin/env python3
import sqlite3
import sys
import math
import json
import os

def calculate_distance(x1, y1, x2, y2):
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

def search_nodes(query, db_path=None):
    if db_path is None:
        db_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "agy_nodeos.db")

    if not os.path.exists(db_path):
        print(json.dumps({"error": f"Database not found at {db_path}. Is the daemon running?"}))
        return


    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. Exact or Partial Match Search
    cursor.execute("SELECT node_id, node_type, name, x_coord, y_coord FROM nodes WHERE name LIKE ?", (f"%{query}%",))
    matches = cursor.fetchall()
    
    if not matches:
        print(json.dumps({"query": query, "results": [], "message": "No nodes found."}))
        conn.close()
        return

    results = []
    
    # 2. Fetch all nodes for spatial KNN (K-Nearest Neighbors) math
    all_nodes = cursor.execute("SELECT node_id, name, x_coord, y_coord, node_type FROM nodes").fetchall()

    for match in matches:
        node_id, node_type, name, x, y = match
        
        node_data = {
            "id": node_id,
            "name": name,
            "type": node_type,
            "coordinates": {"x": round(x, 2), "y": round(y, 2)},
            "direct_dependencies": [],
            "spatial_neighbors": []
        }
        
        # A. Find Direct Graph Dependencies (Edges)
        cursor.execute("SELECT target_id FROM edges WHERE source_id = ?", (node_id,))
        outgoing = [row[0] for row in cursor.fetchall()]
        
        cursor.execute("SELECT source_id FROM edges WHERE target_id = ?", (node_id,))
        incoming = [row[0] for row in cursor.fetchall()]
        
        for dep_id in outgoing + incoming:
            dep_name = next((n[1] for n in all_nodes if n[0] == dep_id), dep_id)
            node_data["direct_dependencies"].append(dep_name)
            
        # B. Perform Spatial KNN Algorithm (Blast Radius Context)
        distances = []
        for other in all_nodes:
            other_id, other_name, ox, oy, otype = other
            if other_id == node_id:
                continue
            dist = calculate_distance(x, y, ox, oy)
            distances.append({"name": other_name, "distance": round(dist, 2), "type": otype})
            
        # Sort by closest physical proximity (Hooke's Law result)
        distances.sort(key=lambda d: d["distance"])
        
        # Return top 3 nearest spatial neighbors
        node_data["spatial_neighbors"] = distances[:3]
        
        results.append(node_data)

    conn.close()
    
    # Output natively as JSON so AGY Sub-Agents can parse it without doing math
    print(json.dumps({"query": query, "results": results}, indent=2))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: python nodeos_search.py <node_name>"}))
    else:
        search_nodes(sys.argv[1])
