from config import *
from math import sqrt

def getNeighbors(cell: (int, int), size: (int, int)):
    col, row = cell
    colCount, rowCount = size

    ns = []
    if col > 0:
        ns.append((col - 1, row))
    if row > 0:
        ns.append((col, row - 1))
    if col < colCount - 1:
        ns.append((col + 1, row))
    if row < rowCount - 1:
        ns.append((col, row + 1))

    # diagonals
    if row > 0 and col > 0:
        ns.append((col - 1, row - 1))
    if row > 0 and col < colCount - 1:
        ns.append((col + 1, row - 1))
    if row < rowCount - 1 and col > 0:
        ns.append((col - 1, row + 1))
    if row < rowCount - 1 and col < colCount - 1:
        ns.append((col + 1, row + 1))

    return ns
def heuristic(a: (int, int), b: (int, int), cellsize: (int, int)):
    return abs(a[0] - b[0]) * cellsize[0] + abs(a[1] - b[1]) * cellsize[1]
def distance(a: (int, int), b: (int, int), cellsize: (int, int)):
    return sqrt(((a[0] - b[0]) * cellsize[0]) ** 2 + ((a[1] - b[1]) * cellsize[1]) ** 2)
def astar(walls, start: (int, int), target: (int, int), cellsize: (int, int)):
    # init intermediate data structures:
    # { key( (row_index, col_index) ): value( { 'F': f-value, 'C': cost, 'P': previous cell } )
    data = {}
    open = set()
    closed = set()

    # put start cell to data dict and to open set
    open.add(start)
    data[start] = {
        'F': heuristic(start, target, cellsize),
        'C': 0,
        'P': None
    }

    while open:  # is not empty
        # position tuple that has min f-value
        current = min(open, key=lambda k: data[k]['F'])

        # building path in reverse from target to start
        if current == target:
            path = [target]
            node = target
            while node != start:
                node = data[node]['P']
                path.append(node)
            path.append(start)
            return target, path, data[target]['F']

        # put (transfer) current cell to closed set
        open.remove(current)
        closed.add(current)

        # get cell neighbors list and filtering  wall cells
        mapsize = (CANVAS_WIDTH // cellsize[0], CANVAS_HEIGHT // cellsize[1])
        ns = getNeighbors(current, mapsize)
        neighbors = list(filter(lambda cell: cell not in walls, ns))

        # iterate over available neighbor cells
        for neighbor in neighbors:
            # cell has already been visited
            if neighbor in closed:
                continue

            # calculate new tentative cost
            newCost = data[current]['C'] + distance(current, neighbor, cellsize)

            # calculate/update neighbor's data
            if (neighbor not in open) or (newCost < data[neighbor]['C']):
                open.add(neighbor)
                data[neighbor] = {
                    'F': newCost + heuristic(neighbor, target, cellsize),
                    'C': newCost,
                    'P': current
                }

    return
