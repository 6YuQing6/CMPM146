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


    sourcebox, destbox = None, None
    # checks if source / dest point exists
    for box in mesh['boxes']:
        if find_point_in_box(source_point, box):
            sourcebox = box
        if find_point_in_box(destination_point, box):
            destbox = box

    if not (sourcebox and destbox):
        print("No path!")
        return [],[]
    
    print('sourcebox', sourcebox)
    print('destbox', destbox)
    
    path = [] # shortest path
    boxes = {} 
    queue = [sourcebox]
    boxes[sourcebox] = None
    visited = set() # visited boxes
    visitedpath = set() # visited path, prevents circular bfs

    while queue:
        currentbox = queue.pop(0)
        visited.add(currentbox)

        if currentbox == destbox:
            while currentbox != None: # gets path of boxes from dest to source
                if (currentbox in visitedpath):
                    print("No Path!")
                    return [],[]
                else:
                    path.append(currentbox)
                    visitedpath.add(currentbox)
                    currentbox = boxes[currentbox]
            path.reverse() # reverses so its source to box instead
            print('boxes', boxes)
            print('path', path, "\n")
            return path, boxes.keys()
        else:
            for neighbor in mesh['adj'].get(currentbox,[]): # gets value of adjacent boxes for currentbox
                if neighbor not in visited:
                    queue.append(neighbor)
                    boxes[neighbor] = currentbox
                    visited.add(neighbor)
    
    print("No path!")
    return [], []

# checks if point is within box's bounds
def find_point_in_box(point, box):
    x, y = point # point coordinates
    x1, x2, y1, y2 = box # box coordinates
    if (x1 <= x <= x2 and y1 <= y <= y2):
        return True
    else:
        return False