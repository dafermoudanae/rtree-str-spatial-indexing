# DAFERMOU CHRISTINA DANAE - 5206
# VALERAS CHRISTOS - 5182

import sys
import math
import heapq
import re

# ===========================================================================================
# Program Description and Usage
# This file processes queries using an R-tree (from rtree.csv).
# It supports three types of queries:
# - Window Range Queries
# - Distance Range Queries
# - k-Nearest Neighbors (kNN) Queries
# The program reads the R-tree and the query file as input.
# It then executes the queries and returns the results.
# The program runs from the command line with the query type,
# the R-tree file, the query file, and (for kNN) the value of k.
# ===========================================================================================


# ===========================================================================================
# R-tree Loading from CSV File
# The code reads the rtree.csv file and builds the R-tree structure in memory.
# Each node is stored as a dictionary.
# A node contains:
# - node_id: the id of the node
# - is_leaf: shows if it is a leaf node
# - entries: a list of (pointer, geometry)
# ===========================================================================================

def load_rtree(filename):
    nodes = []
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split(' , ', 3)
            node_id = int(parts[0])
            n = int(parts[1])
            flag = int(parts[2])
            is_leaf = (flag == 0)

            entries = []
            entries_str = parts[3]

            if is_leaf:
                #leaf: (record_id,(x, y))
                pattern = r'\((\d+),\(([^)]+)\)\)'
                for m in re.finditer(pattern, entries_str):
                    rid = int(m.group(1))
                    coords = [float(x) for x in m.group(2).split(',')]
                    entries.append((rid, (coords[0], coords[1])))
            else:
                #internal node: (node_id,[x_low, y_low, x_high, y_high])
                pattern = r'\((\d+),\[([^\]]+)\]\)'
                for m in re.finditer(pattern, entries_str):
                    nid = int(m.group(1))
                    coords = [float(x) for x in m.group(2).split(',')]
                    entries.append((nid, (coords[0], coords[1], coords[2], coords[3])))

            nodes.append({
                'node_id': node_id,
                'is_leaf': is_leaf,
                'entries': entries
            })

    #The root is the last node
    root_id = len(nodes) - 1
    return nodes, root_id

# ===========================================================================================
# Geometry Helper Functions
# These functions are used for geometric calculations in the R-tree queries.
# They help check overlaps, distances, and point positions.

# mbr_overlaps_window:
# Checks if an MBR overlaps with a query window.
# Two rectangles overlap if they are not completely separated.

# point_in_window:
# Checks if a point (x, y) is inside a query window.
# The borders are included.

# euclidean_distance:
# Calculates the Euclidean distance between two points.

# min_distance_point_to_mbr:
# Calculates the minimum distance from a point to an MBR.
# If the point is inside the MBR, the distance is 0.
# Otherwise, it calculates the distance to the closest edge.
# ===========================================================================================


def mbr_overlaps_window(mbr, window):
    if mbr[2] < window[0] or mbr[0] > window[2]:
        return False
    if mbr[3] < window[1] or mbr[1] > window[3]:
        return False
    return True

def point_in_window(point, window):
    x, y = point
    return (window[0] <= x <= window[2]) and (window[1] <= y <= window[3])

def euclidean_distance(p1, p2):
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)


def min_distance_point_to_mbr(point, mbr):
    px, py = point
    x_low, y_low, x_high, y_high = mbr

    # x-distance
    if px < x_low:
        dx = x_low - px
    elif px > x_high:
        dx = px - x_high
    else:
        dx = 0.0

    # y-distance
    if py < y_low:
        dy = y_low - py
    elif py > y_high:
        dy = py - y_high
    else:
        dy = 0.0
    return math.sqrt(dx * dx + dy * dy)


# ===========================================================================================
# Window Range Query
# This function finds all points inside a given window.
# The search starts from the root node.

# Algorithm:
# 1. Start from the root.
# 2. For internal nodes:
#    Check if each MBR overlaps with the window.
#    If yes, go to the child node.
# 3. For leaf nodes:
#    Check if each point is inside the window.

# The function returns a list of record_ids.
# A stack is used instead of recursion for the tree traversal.

# Leaf node:
# Check each point if it is inside the window.

# Internal node:
# Check each entry MBR if it overlaps with the window.
# ===========================================================================================

def window_range_query(nodes, root_id, window):
    results = []
    stack = [root_id]

    while stack:
        nid = stack.pop()
        node = nodes[nid]

        if node['is_leaf']:
            for record_id, point in node['entries']:
                if point_in_window(point, window):
                    results.append(record_id)
        else:
            for child_id, mbr in node['entries']:
                if mbr_overlaps_window(mbr, window):
                    stack.append(child_id)
    return results

# ===========================================================================================
# Distance Range Query
# This function finds all points with distance <= epsilon from a query point q.
# The search starts from the root node.

# Algorithm:
# 1. Start from the root.
# 2. For internal nodes:
#    Check the minimum distance from the MBR to point q.
#    If it is <= epsilon, go to the child node.
# 3. For leaf nodes:
#    Check the distance of each point from q.
#    If it is <= epsilon, add it to the results.

# Leaf node:
# Check the distance of each point from q.

# Internal node:
# Check the minimum distance from each MBR to q.
# ===========================================================================================

def distance_range_query(nodes, root_id, q, epsilon):
    results = []
    stack = [root_id]

    while stack:
        nid = stack.pop()
        node = nodes[nid]

        if node['is_leaf']:
            for record_id, point in node['entries']:
                if euclidean_distance(point, q) <= epsilon:
                    results.append(record_id)
        else:
            for child_id, mbr in node['entries']:
                if min_distance_point_to_mbr(q, mbr) <= epsilon:
                    stack.append(child_id)

    return results

# ===========================================================================================
# k-Nearest Neighbors (kNN) Query
# This function finds the k nearest neighbors of a query point q.
# It uses a best-first search algorithm.

# Algorithm:
# 1. Insert the root node into a priority queue.
# 2. At each step, remove the element with the smallest distance:
#    - If it is a point (from a leaf), it is the next nearest neighbor.
#    - If it is an MBR (from an internal node), expand the node
#      and add its entries to the queue.
# 3. Repeat until k points are found.

# The priority queue stores:
# (distance, type, id, geometry)
# - type: 'node' for internal nodes, 'point' for leaf points
# A min-heap (heapq) is used for the priority queue.
# The counter is used to break ties (FIFO order).

# Initialization:
# The root is inserted into the queue with distance 0.

# Leaf node:
# Add each point to the queue.

# When a point is removed:
# It is the next nearest neighbor.
# ===========================================================================================

def knn_query(nodes, root_id, q, k):
    results = []
    counter = 0
    heap = []

    heapq.heappush(heap, (0.0, counter, 'node', root_id, None))
    counter += 1

    while heap and len(results) < k:
        dist, _, entry_type, entry_id, entry_geo = heapq.heappop(heap)

        if entry_type == 'point':
            results.append(entry_id)
        elif entry_type == 'node':
            node = nodes[entry_id]
            if node['is_leaf']:
                for record_id, point in node['entries']:
                    d = euclidean_distance(q, point)
                    heapq.heappush(heap, (d, counter, 'point', record_id, point))
                    counter += 1
            else:
                for child_id, mbr in node['entries']:
                    d = min_distance_point_to_mbr(q, mbr)
                    heapq.heappush(heap, (d, counter, 'node', child_id, mbr))
                    counter += 1

    return results

# -------------------------- Query File Reading --------------------------------------

def read_window_queries(filename):
    queries = []

    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            parts = line.split()

            for i in range(0, len(parts), 4):
                try:
                    x_low = float(parts[i])
                    y_low = float(parts[i+1])
                    x_high = float(parts[i+2])
                    y_high = float(parts[i+3])

                    queries.append((x_low, y_low, x_high, y_high))
                except:
                    print("ERROR at:", parts[i:i+4])

    return queries

def read_distance_queries(filename):
    queries = []
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            line = line.replace('[', '').replace(']', '')
            line = line.replace(',', ' ')
            parts = line.split()
            x = float(parts[0])
            y = float(parts[1])
            eps = float(parts[2])
            queries.append(((x, y), eps))
    return queries


def read_nn_queries(filename):
    queries = []
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            line = line.replace('[', '').replace(']', '')
            line = line.replace(',', ' ')
            parts = line.split()
            x, y = float(parts[0]), float(parts[1])
            queries.append((x, y))
    return queries


# ------------------------------------- Main-----------------------------------------

def main():
    if len(sys.argv) < 4:
       # print("Usage:")
        print( "Usage: ...")
        print("  python query_rtree.py window <rtree_file> <queries_file>")
        print("  python query_rtree.py distance <rtree_file> <queries_file>")
        print("  python query_rtree.py knn <rtree_file> <queries_file> <k>")
        sys.exit(1)

    query_type = sys.argv[1]
    rtree_file = sys.argv[2]
    queries_file = sys.argv[3]

    nodes, root_id = load_rtree(rtree_file)

    if query_type == "window":
        queries = read_window_queries(queries_file)
        for i, window in enumerate(queries):
            results = window_range_query(nodes, root_id, window)
            rids_str = ",".join(str(r) for r in results)
            #print(f"{i} ({len(results)}): {rids_str}")
            print( "{} ({}): {}".format(i, len(results), rids_str))

    elif query_type == "distance":
        queries = read_distance_queries(queries_file)
        for i, (q, eps) in enumerate(queries):
            results = distance_range_query(nodes, root_id, q, eps)
            rids_str = ",".join(str(r) for r in results)
            #print(f"{i} ({len(results)}): {rids_str}")
            print( "{} ({}): {}".format(i, len(results), rids_str))

    elif query_type == "knn":
        if len(sys.argv) < 5:
            print( "Error: kNN requires k parameter")
            sys.exit(1)
        k = int(sys.argv[4])
        queries = read_nn_queries(queries_file)
        for i, q in enumerate(queries):
            results = knn_query(nodes, root_id, q, k)
            rids_str = ",".join(str(r) for r in results)
            print ("{}: {}".format(i, rids_str))

    else:

        print("Unknown query type: {}".format(query_type))
        sys.exit(1)


if __name__ == "__main__":
    main()
