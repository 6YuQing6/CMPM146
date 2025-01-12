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
    if sourcebox == destbox:
        return [source_point, destination_point], [sourcebox]
    
    forward_prev = {sourcebox: None} 
    backward_prev = {destbox: None} 
    forward_points = {sourcebox: source_point}
    backward_points = {destbox: destination_point}

    forward_dist = {sourcebox: 0}
    backward_dist = {destbox: 0}

    visitedforward = set() # visited boxes
    visitedbackward = set() 
    
    queue = PriorityQueue()
    queue.put((0,sourcebox, "forward"))
    queue.put((0,destbox, "backward"))

    def construct_path(meetingbox):
        forwardpath = [] # shortest path
        currentbox = meetingbox
        while currentbox != None: # gets path of boxes from dest to source
            forwardpath.append(forward_points[currentbox])
            currentbox = forward_prev[currentbox]
        forwardpath.reverse() # reverses so its source to box instead

        backwardpath = []
        currentbox = meetingbox
        while currentbox != None: # gets path of boxes from dest to source
            backwardpath.append(backward_points[currentbox])
            currentbox = backward_prev[currentbox]
        backwardpath.append(destination_point)

        return forwardpath + backwardpath[1:]
    

    while not queue.empty():
        currentdist, currentbox, currentdirection = queue.get()
        if (currentdirection == "forward"):
            visitedforward.add(currentbox)
        else:
            visitedbackward.add(currentbox)

        if currentbox in visitedbackward and currentbox in visitedforward:
            path = construct_path(currentbox)
            return path, list(visitedforward | visitedbackward)
        else:
            for neighbor in mesh['adj'].get(currentbox,[]): # gets value of adjacent boxes for currentbox
                if (currentdirection == "forward"):
                    if neighbor in visitedforward:
                        continue
                    # finds neighboring closest point 
                    neighborpoint = closest_point(forward_points[currentbox], currentbox, neighbor)
                    newdist = currentdist + distance(neighborpoint, destination_point)
                    # update dist and queue if shorter path found
                    if (neighbor not in forward_dist or newdist < forward_dist[neighbor]):
                        forward_dist[neighbor] = newdist
                        forward_prev[neighbor] = currentbox
                        forward_points[neighbor] = neighborpoint
                        queue.put((newdist, neighbor, "forward"))
                elif (currentdirection == "backward"):
                    if neighbor in visitedbackward:
                        continue
                    # finds neighboring closest point 
                    neighborpoint = closest_point(backward_points[currentbox], currentbox, neighbor)
                    newdist = currentdist + distance(neighborpoint, source_point)
                    # update dist and queue if shorter path found
                    if (neighbor not in backward_dist or newdist < backward_dist[neighbor]):
                        backward_dist[neighbor] = newdist
                        backward_prev[neighbor] = currentbox
                        backward_points[neighbor] = neighborpoint
                        queue.put((newdist, neighbor, "backward"))
    
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