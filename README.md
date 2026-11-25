# rtree-str-spatial-indexing

R-tree construction with the sort-tile-recursive (STR) method in main memory, and range and nearest neighbour queries on spatial restaurant data (Beijing).

Assignment 2, Data Management (Διαχείριση Σύνθετων Δεδομένων), University of Ioannina, 2025-26.


## Contents
- `build_rtree.py`: builds an R-tree with the STR method from `Beijing_restaurants.txt` and writes it to a file (`rtree.csv`).
- `query_rtree.py`: runs window range, distance range and k-nearest neighbour queries on the R-tree.
- `Beijing_restaurants.txt`: coordinates of 51,970 restaurants.
- `NNQueries.txt`, `distanceRangeQueries.txt`, `windowRangeQueries.txt`: query files.
- `rtree.csv`: the R-tree produced by `build_rtree.py`.
- `report_diaxeirisi_2_5206_5182.pdf`: project report.

## Requirements
- Python 3 (standard library only)

## How to Run
1. Clone the repository: `git clone https://github.com/dafermoudanae/rtree-str-spatial-indexing.git`
2. Build the R-tree:
   `python build_rtree.py Beijing_restaurants.txt rtree.csv`
3. Run the queries (the file name of the R-tree is the second argument):
   - Window range: `python query_rtree.py window rtree.csv windowRangeQueries.txt`
   - Distance range: `python query_rtree.py distance rtree.csv distanceRangeQueries.txt`
   - k nearest neighbours: `python query_rtree.py knn rtree.csv NNQueries.txt <k>`
