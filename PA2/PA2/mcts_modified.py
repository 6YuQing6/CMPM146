from mcts_node import MCTSNode
from p2_t3 import Board
from random import choice, random
from math import sqrt, log

num_nodes = 1000
explore_faction = 2.

def traverse_nodes(node: MCTSNode, board: Board, state, bot_identity: int):
    while not node.untried_actions and node.child_nodes:
        node = get_best_child(node, board, state, bot_identity)
        state = board.next_state(state, node.parent_action)
    return node, state

def expand_leaf(node: MCTSNode, board: Board, state):
    if node.untried_actions:
        action = choice(node.untried_actions)
        node.untried_actions.remove(action)
        new_state = board.next_state(state, action)
        child_node = MCTSNode(parent=node, parent_action=action, action_list=board.legal_actions(new_state))
        node.child_nodes[action] = child_node
        return child_node, new_state
    return node, state

def rollout(board: Board, state):
    while not board.is_ended(state):
        actions = board.legal_actions(state)
        action = choose_heuristic_action(board, state, actions)
        state = board.next_state(state, action)
    return state

def choose_heuristic_action(board: Board, state, actions):
    current_player = board.current_player(state)
    enemy_player = 3 - current_player
    
    for action in actions:
        next_state = board.next_state(state, action)
        if board.is_ended(next_state) and board.points_values(next_state)[current_player] == 1:
            return action
    
    for action in actions:
        next_state = board.next_state(state, action)
        opponent_actions = board.legal_actions(next_state)
        for opp_action in opponent_actions:
            opp_state = board.next_state(next_state, opp_action)
            if board.is_ended(opp_state) and board.points_values(opp_state)[enemy_player] == 1:
                return action
    
    best_action = None
    max_owned_boxes = -1
    for action in actions:
        next_state = board.next_state(state, action)
        owned_boxes = sum(1 for owner in board.owned_boxes(next_state).values() if owner == current_player)
        if owned_boxes > max_owned_boxes:
            max_owned_boxes = owned_boxes
            best_action = action
    
    return best_action if best_action else choice(actions)

def backpropagate(node: MCTSNode, won: bool):
    while node:
        node.visits += 1
        node.wins += won
        node = node.parent

def get_best_child(node: MCTSNode, board: Board, state, bot_identity: int):
    enemy = 3 - bot_identity
    best_score = float('-inf')
    best_children = []

    for child in node.child_nodes.values():
        if child.visits == 0:
            return child
        
        win_rate = child.wins / child.visits
        if board.current_player(state) == enemy:
            win_rate = 1 - win_rate
        
        exploration = explore_faction * sqrt(log(node.visits) / child.visits)
        uct_score = win_rate + exploration
        
        if uct_score > best_score:
            best_score = uct_score
            best_children = [child]
        elif uct_score == best_score:
            best_children.append(child)
    
    return choice(best_children)

def get_best_action(root_node: MCTSNode):
    best_win_rate = float('-inf')
    best_actions = []
    
    for action, child in root_node.child_nodes.items():
        if child.visits == 0:
            continue
        win_rate = child.wins / child.visits
        if win_rate > best_win_rate:
            best_win_rate = win_rate
            best_actions = [action]
        elif win_rate == best_win_rate:
            best_actions.append(action)
    
    return choice(best_actions) if best_actions else choice(list(root_node.child_nodes.keys()))

def think(board: Board, current_state):
    identity_of_bot = board.current_player(current_state)
    root_node = MCTSNode(parent=None, parent_action=None, action_list=board.legal_actions(current_state))

    for _ in range(num_nodes):
        state = current_state
        node = root_node
        node, state = traverse_nodes(node, board, state, identity_of_bot)
        node, state = expand_leaf(node, board, state)
        state = rollout(board, state)
        backpropagate(node, board.points_values(state)[identity_of_bot])

    return get_best_action(root_node)