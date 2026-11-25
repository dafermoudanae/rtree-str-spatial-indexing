# DAFERMOU CHRISTINA DANAE - 5206
# VALERAS CHRISTOS - 5182

import sys
import math

# ===========================================================================================
# Program Description and Usage
# This file builds an R-tree using the STR method.
# The program reads spatial data from an input file.
# Then, it creates the R-tree and saves it to an output file.
# The program is executed from the command line
# by giving the input file and the output file as arguments.
# ===========================================================================================


NODE_SIZE = 1024
LEAF_ENTRY_SIZE = 20
ML = NODE_SIZE // LEAF_ENTRY_SIZE
INTERNAL_ENTRY_SIZE = 36
MINT = NODE_SIZE // INTERNAL_ENTRY_SIZE  # = 28
MIN_FILL_FACTOR = 0.4

mL = int(math.floor(MIN_FILL_FACTOR * ML))  # = 20
mINT = int(math.floor(MIN_FILL_FACTOR * MINT))  # = 11

nodes = []


def compute_mbr(entries, is_leaf):
    if is_leaf:
        # entries: (record_id, (x, y))
        first_point = entries[0][1]
        xmin = xmax = first_point[0]
        ymin = ymax = first_point[1]
    else:
        # entries: (node_id, [x_low, y_low, x_high, y_high])
        first_mbr = entries[0][1]
        xmin, ymin, xmax, ymax = first_mbr[0], first_mbr[1], first_mbr[2], first_mbr[3]

    for i in range(1, len(entries)):
        geometry = entries[i][1]

        if is_leaf:
            x = geometry[0]
            y = geometry[1]
            if x < xmin: xmin = x
            if x > xmax: xmax = x
            if y < ymin: ymin = y
            if y > ymax: ymax = y
        else:
            x_low, y_low, x_high, y_high = geometry[0], geometry[1], geometry[2], geometry[3]
            if x_low < xmin:   xmin = x_low
            if y_low < ymin:   ymin = y_low
            if x_high > xmax:  xmax = x_high
            if y_high > ymax:  ymax = y_high

    return xmin, ymin, xmax, ymax


def mbr_area(mbr):
    return (mbr[2] - mbr[0]) * (mbr[3] - mbr[1])


def create_node(entries, is_leaf):
    node_id = len(nodes)
    nodes.append({
        'node_id': node_id,
        'is_leaf': is_leaf,
        'entries': entries
    })
    return node_id


# ===========================================================================================
# Minimum Fill Check
# The code checks if the last node has fewer than m entries.
# If yes, it moves or merges entries from the previous node.
# The last node will end up with exactly m entries.
# This helps keep the tree balanced.
# The root node is not included in this rule.
# ===========================================================================================


def enforce_min_fill(raw_groups, m):
    if len(raw_groups) > 1 and len(raw_groups[-1]) < m:
        merged = raw_groups[-2] + raw_groups[-1]
        raw_groups[-2] = merged[:-m]
        raw_groups[-1] = merged[-m:]
    return raw_groups


# ===========================================================================================
# STR Leaf-Level Sorting and Grouping
# The code organizes the points into leaf nodes using the STR method.
# First, it sorts all points by their x value.
# Then, it splits them into vertical groups (stripes).
# Inside each stripe, the points are sorted by their y value.
# After that, the points are divided into groups of size M,
# where each group becomes one leaf node.
# The function returns a list of these groups.
# ===========================================================================================


def get_x(entry):
    return entry[1][0]


def str_grouping(items, m):
    n = len(items)
    if n == 0:
        return []

    # num_nodes = math.ceil(n / m)
    num_nodes = int(math.ceil(float(n) / m))
    # num_stripes = math.ceil(math.sqrt(num_nodes)) #num of stripes
    num_stripes = int(math.ceil(math.sqrt(num_nodes)))
    items_per_stripe = num_stripes * m

    items_sorted_x = sorted(items, key=get_x)

    all_sorted = []
    for i in range(num_stripes):
        start = i * items_per_stripe
        end = min(start + items_per_stripe, n)
        stripe = items_sorted_x[start:end]

        stripe.sort(key=lambda e: e[1][1])
        all_sorted.extend(stripe)

    raw_groups = []

    for i in range(0, n, m):
        raw_groups.append(all_sorted[i:i + m])

    return raw_groups


# ===========================================================================================
# Grouping for Internal Nodes
# The code groups items into sets of size M.
# It is used for internal levels of the R-tree.
# The items are already sorted from the previous STR step.
# Each group becomes one internal node.
# ===========================================================================================


def sequential_group(items, m):
    raw_groups = []
    n = len(items)
    for i in range(0, n, m):
        raw_groups.append(items[i:i + m])
    return raw_groups


# ===========================================================================================
# R-tree Construction using STR
# The code builds the R-tree step by step using the STR method.
# First, it groups the points to create leaf nodes.
# Then, it groups the MBRs of these nodes to create higher levels.
# This process repeats until only one node is left (the root).
# ===========================================================================================


def build_str_rtree(points):
    # -----------------------------Leaf Nodes Construction----------------------------------------

    leaf_items = [(rid, (x, y)) for rid, x, y in points]
    raw_groups = str_grouping(leaf_items, ML)
    raw_groups = enforce_min_fill(raw_groups, mL)
    level_node_ids = []
    for group in raw_groups:
        nid = create_node(group, is_leaf=True)
        level_node_ids.append(nid)

    level = 0
    level_info = []

    # ---------------------------Leaf Level Statistics-------------------------------------------

    level_info.append((level, len(level_node_ids), 0))

    # -------------------------- Higher Levels Construction--------------------------------------

    while len(level_node_ids) > 1:
        level += 1

        internal_items = []
        for nid in level_node_ids:
            node = nodes[nid]
            child_mbr = compute_mbr(node['entries'], node['is_leaf'])
            internal_items.append((nid, child_mbr))

        raw_groups = sequential_group(internal_items, MINT)

        if len(raw_groups) > 1:
            raw_groups = enforce_min_fill(raw_groups, mINT)

        # --Internal Nodes---
        level_node_ids = []
        for group in raw_groups:
            nid = create_node(group, is_leaf=False)
            level_node_ids.append(nid)

        # --------------------------Average MBR Area Calculation------------------------------
        total_area = 0
        for nid in level_node_ids:
            node = nodes[nid]
            node_mbr = compute_mbr(node['entries'], is_leaf=False)
            total_area += mbr_area(node_mbr)
        # avg_area = total_area / len(level_node_ids)
        avg_area = float(total_area) / len(level_node_ids)
        level_info.append((level, len(level_node_ids), avg_area))

    root_id = level_node_ids[0]

    for lvl, cnt, avg in level_info:
        print("{} nodes at level {} with average MBR area {}".format(cnt, lvl, avg))

    return root_id


# ===========================================================================================
# R-tree Output to CSV
# The code writes the R-tree into a CSV file.
# The nodes are written from bottom to top.
# The last line of the file is the root node.
# ===========================================================================================


def write_rtree_csv(output_file):
    with open(output_file, 'w') as f:
        for node in nodes:
            nid = node['node_id']
            n = len(node['entries'])
            flag = 0 if node['is_leaf'] else 1

            parts = []
            for ptr, geo in node['entries']:
                if node['is_leaf']:
                    # format: (record_id,(x, y))
                    parts.append("({},({}, {}))".format(ptr, geo[0], geo[1]))
                else:
                    # format: (node_id,[xmin, ymin, xmax, ymax])
                    # parts.append(f"({ptr},[{geo[0]}, {geo[1]}, {geo[2]}, {geo[3]}])")
                    mbr_str = "[{}, {}, {}, {}]".format(geo[0], geo[1], geo[2], geo[3])
                    parts.append("({},{})".format(ptr, mbr_str))

            entries_str = " , ".join(parts)+ " , "
            f.write("{} , {} , {} , {}\n".format(nid, n, flag, entries_str))

# -----------------------------------------Main--------------------------------------------------------#

def main():
    if len(sys.argv) != 3:
        print("Usage: python build_rtree.py <data_file> <output_file>")
        sys.exit(1)

    data_file = sys.argv[1]
    output_file = sys.argv[2]

    with open(data_file, 'r') as f:
        lines = f.readlines()

    num_points = int(lines[0].strip())
    points = []
    for i in range(1, num_points + 1):
        parts = lines[i].strip().split()
        x = float(parts[0])
        y = float(parts[1])
        record_id = i  # 1-based (grammi 1 = record_id 1)
        points.append((record_id, x, y))

    print("Read {} points.".format(len(points)))

    root_id = build_str_rtree(points)
    print("Root node id: {}".format(root_id))
    print("Total nodes: {}".format(len(nodes)))

    write_rtree_csv(output_file)
    print("R-tree written to {}".format(output_file))


if __name__ == "__main__":
    main()
