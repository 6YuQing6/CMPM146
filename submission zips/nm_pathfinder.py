from queue import PriorityQueue
import math

def find_box(point, mesh):
    """Find the box that contains the given point."""
    x, y = point
    for box in mesh['boxes']:
        x1, x2, y1, y2 = box
        if x1 <= x <= x2 and y1 <= y <= y2:
            return box
    return None

def euclidean_distance(point1, point2):
    """Calculate the Euclidean distance between two points."""
    return math.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)

def closest_point(point, neighbor_box):
    """Find the closest point in the neighbor box to the current point."""
    x1, x2, y1, y2 = neighbor_box
    return (
        min(max(point[0], x1), x2),
        min(max(point[1], y1), y2)
    )

def reconstruct_path(forward_prev, backward_prev, meeting_box, forward_points, backward_points, destination_point):
    """Reconstruct the path by combining forward and backward paths."""
    path = []

    # Forward path: from source to meeting box
    current_box = meeting_box
    while current_box:
        path.append(forward_points[current_box])
        current_box = forward_prev[current_box]
    path.reverse()

    # Backward path: from meeting box to destination
    current_box = meeting_box
    while current_box:
        path.append(backward_points[current_box])
        current_box = backward_prev[current_box]
    path.append(destination_point)

    return path

def find_path(source_point, destination_point, mesh):
    """
    Searches for a path from source_point to destination_point through the mesh.
    """
    source_box = find_box(source_point, mesh)
    destination_box = find_box(destination_point, mesh)

    if not source_box or not destination_box:
        print("No path! Points are outside the navigable area.")
        return [], []

    if source_box == destination_box:
        return [source_point, destination_point], [source_box]

    # Initialization
    forward_prev, backward_prev = {source_box: None}, {destination_box: None}
    forward_points, backward_points = {source_box: source_point}, {destination_box: destination_point}
    forward_distances, backward_distances = {source_box: 0}, {destination_box: 0}

    visited_forward, visited_backward = set(), set()
    priority_queue = PriorityQueue()
    priority_queue.put((0, source_box, "forward"))
    priority_queue.put((0, destination_box, "backward"))

    # Search loop
    while not priority_queue.empty():
        current_distance, current_box, direction = priority_queue.get()

        if direction == "forward":
            visited_forward.add(current_box)
        else:
            visited_backward.add(current_box)

        # Check for meeting point
        if current_box in visited_forward and current_box in visited_backward:
            path = reconstruct_path(forward_prev, backward_prev, current_box, forward_points, backward_points, destination_point)
            return path, list(visited_forward | visited_backward)

        # Expand neighbors
        for neighbor_box in mesh['adj'].get(current_box, []):
            if direction == "forward":
                if neighbor_box in visited_forward:
                    continue
                neighbor_point = closest_point(forward_points[current_box], neighbor_box)
                new_distance = forward_distances[current_box] + euclidean_distance(forward_points[current_box], neighbor_point)

                if neighbor_box not in forward_distances or new_distance < forward_distances[neighbor_box]:
                    forward_distances[neighbor_box] = new_distance
                    forward_prev[neighbor_box] = current_box
                    forward_points[neighbor_box] = neighbor_point
                    heuristic = euclidean_distance(neighbor_point, destination_point)
                    priority_queue.put((new_distance + heuristic, neighbor_box, "forward"))

            elif direction == "backward":
                if neighbor_box in visited_backward:
                    continue
                neighbor_point = closest_point(backward_points[current_box], neighbor_box)
                new_distance = backward_distances[current_box] + euclidean_distance(backward_points[current_box], neighbor_point)

                if neighbor_box not in backward_distances or new_distance < backward_distances[neighbor_box]:
                    backward_distances[neighbor_box] = new_distance
                    backward_prev[neighbor_box] = current_box
                    backward_points[neighbor_box] = neighbor_point
                    heuristic = euclidean_distance(neighbor_point, source_point)
                    priority_queue.put((new_distance + heuristic, neighbor_box, "backward"))

    print("No path found!")
    return [], list(visited_forward | visited_backward)
