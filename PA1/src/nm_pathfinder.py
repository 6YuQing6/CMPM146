from queue import PriorityQueue
import math

def find_path (source_point, destination_point, mesh):

    """
    Searches for a path from source_point to destination_point through the mesh

    Args:
        source_point: starting point of the pathfinder
        destination_point: the ultimate goal the pathfinder must reach
        mesh: pathway constraints the path adheres to

    Returns:

        A path (list of points) from source_point to destination_point if exists
        A list of boxes explored by the algorithm
    """
    # checks if point is within box's bounds
    def find_box(point):
        x, y = point # point coordinates
        for box in mesh['boxes']:
            x1, x2, y1, y2 = box # box coordinates
            if (x1 <= x <= x2 and y1 <= y <= y2):
                return box
        return None

    sourcebox = find_box(source_point)
    destbox = find_box(destination_point)

    if not (sourcebox and destbox):
        print("No path!")
        return [],[]
    
    camefrom = {} 
    camefrom[sourcebox] = None
    point = {}
    point[sourcebox] = source_point

    queue = PriorityQueue()
    queue.put((0,sourcebox))
    cost = {}

    visitedboxes = set() # visited boxes


    while queue:
        currentcost, currentbox = queue.get()
        visitedboxes.add(currentbox)

        if currentbox == destbox:
            visitedpath = set() # visited path, prevents circular bfs
            path = [] # shortest path
            path.append(destination_point)
            while currentbox != None: # gets path of boxes from dest to source
                if (currentbox in visitedpath):
                    print("No Path!")
                    return [],[]
                else:
                    path.append(point[currentbox])
                    visitedpath.add(currentbox)
                    currentbox = camefrom[currentbox]
            path.reverse() # reverses so its source to box instead
            print('boxes', camefrom)
            print('path', path)
            print('detailpoints', point)
            print("\n")
            return path, list(visitedboxes)
        else:
            for neighbor in mesh['adj'].get(currentbox,[]): # gets value of adjacent boxes for currentbox
                if neighbor in visitedboxes:
                    continue
                # finds neighboring closest point 
                neighborpoint = closest_point(point[currentbox], currentbox, neighbor)
                newcost = currentcost + distance(neighborpoint, point[currentbox])
                # update dist and queue if shorter path found
                if (neighbor not in cost or newcost < cost[neighbor]):
                    cost[neighbor] = newcost
                    camefrom[neighbor] = currentbox
                    point[neighbor] = neighborpoint
                    queue.put((newcost, neighbor))
    
    print("No path!")
    return [], []


# finds the closest point's distance
def closest_point(point, box1, box2):
    b1x1,b1x2,b1y1,b1y2 = box1
    b2x1,b2x2,b2y1,b2y2 = box2
    px,py = point
    xrange = [max(b1x1, b2x1), min(b1x2, b2x2)]
    yrange = [max(b1y1, b2y1), min(b1y2, b2y2)]
    px = min(max(px, xrange[0]), xrange[1])
    py = min(max(py, yrange[0]), yrange[1])
    return [px, py]

# finds distance between two points
def distance(point1, point2):
    x1, y1 = point1
    x2, y2 = point2
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)