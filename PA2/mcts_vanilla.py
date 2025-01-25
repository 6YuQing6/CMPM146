from mcts_node import MCTSNode
from p2_t3 import Board
from random import choice
from math import sqrt, log

num_nodes = 1000
explore_faction = 2.

def traverse_nodes(node: MCTSNode, board: Board, state, bot_identity: int):
    """ Traverses the tree until the end criterion are met.

    Args:
        node:       A tree node from which the search is traversing.
        board:      The game setup.
        state:      The state of the game.
        identity:   The bot's identity, either 1 or 2.

    Returns:
        A node from which the next stage of the search can proceed.

    """
    while not node.untried_actions and node.child_nodes:
        node = get_best_child(node, board, state, bot_identity)
        state = board.next_state(state, node.parent_action)
    return node, state

def expand_leaf(node: MCTSNode, board: Board, state):
    """ Adds a new leaf to the tree by creating a new child node for the given node.

    Args:
        node:   The node for which a child will be added.
        board:  The game setup.
        state:  The state of the game.

    Returns:
        The added child node and the new state.

    """
    if node.untried_actions:
        action = choice(node.untried_actions)
        node.untried_actions.remove(action)
        new_state = board.next_state(state, action)
        child_node = MCTSNode(parent=node, parent_action=action, action_list=board.legal_actions(new_state))
        node.child_nodes[action] = child_node
        return child_node, new_state
    return node, state

def rollout(board: Board, state):
    """ Given the state of the game, the rollout plays out the remainder randomly.

    Args:
        board:  The game setup.
        state:  The state of the game.

    Returns:
        The terminal state of the game.

    """
    while not board.is_ended(state):
        action = choice(board.legal_actions(state))
        state = board.next_state(state, action)
    return state

def backpropagate(node: MCTSNode, won: bool):
    """ Navigates the tree from a leaf node to the root, updating the win and visit count of each node along the path.

    Args:
        node:   A leaf node.
        won:    An indicator of whether the bot won or lost the game.

    """
    while node:
        node.visits += 1
        node.wins += won
        node = node.parent

def get_best_child(node: MCTSNode, board: Board, state, bot_identity: int):
    """ Selects the best child node based on the UCT formula.

    Args:
        node:       The parent node.
        board:      The game setup.
        state:      The state of the game.
        identity:   The bot's identity, either 1 or 2.

    Returns:
        The child node with the highest UCT value.

    """
    enemy = 3 - bot_identity
    best_score = float('-inf')
    best_children = []

    for child in node.child_nodes.values():
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
    """ Selects the best action from the root node based on the highest win rate.

    Args:
        root_node:   The root node.

    Returns:
        The best action from the root node.

    """
    best_win_rate = float('-inf')
    best_actions = []
    
    for action, child in root_node.child_nodes.items():
        win_rate = child.wins / child.visits
        if win_rate > best_win_rate:
            best_win_rate = win_rate
            best_actions = [action]
        elif win_rate == best_win_rate:
            best_actions.append(action)
    
    return choice(best_actions)

def think(board: Board, current_state):
    """ Performs MCTS by sampling games and calling the appropriate functions to construct the game tree.

    Args:
        board:  The game setup.
        state:  The current state of the game.

    Returns:    The action to be taken.

    """
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