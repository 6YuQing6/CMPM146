from mcts_node import MCTSNode
from p2_t3 import Board
from random import choice, sample
from math import sqrt, log

num_nodes = 75
explore_faction = 2.

def traverse_nodes(node: MCTSNode, board: Board, state, bot_identity: int):
    """ Traverses the tree until the end criterion are met.
    e.g. find the best expandable node (node with untried action) if it exist,
    or else a terminal node

    Args:
        node:       A tree node from which the search is traversing.
        board:      The game setup.
        state:      The state of the game.
        identity:   The bot's identity, either 1 or 2

    Returns:
        node: A node from which the next stage of the search can proceed.
        state: The state associated with that node

    """
    while not node.untried_actions and node.child_nodes:
        node = get_best_node(node, board, state, bot_identity)
        state = board.next_state(state, node.parent_action)
    
    return node, state

def get_best_node(node, board, state, bot_identity):
    best_score = float('-inf')
    best_nodes = []
    for child in node.child_nodes.values():
        is_opponent = board.current_player(state) != bot_identity
        ucb_score = ucb(child, is_opponent)
        if ucb_score > best_score:
            best_score = ucb_score
            best_nodes = [child]
        elif ucb_score == best_score:
            best_nodes.append(child)
    node = choice(best_nodes)
    return node

def expand_leaf(node: MCTSNode, board: Board, state):
    """ Adds a new leaf to the tree by creating a new child node for the given node (if it is non-terminal).

    Args:
        node:   The node for which a child will be added.
        board:  The game setup.
        state:  The state of the game.

    Returns:
        node: The added child node
        state: The state associated with that node

    """
    if not node.untried_actions:
        return node, state
    
    # chooses a random action from untried actions
    action = choice(node.untried_actions)
    node.untried_actions.remove(action)

    # finds new node and state
    newstate = board.next_state(state, action)
    newnode = MCTSNode(node, action, action_list=board.legal_actions(newstate))

    # sets newnode as child of node
    node.child_nodes[action] = newnode

    return newnode, newstate

def heuristic_rollout(board: Board, state, bot_identity):
    """
    Simulates the remainder of the game using a heuristic strategy that prioritizes winning local boxes.
    
    Args:
        board: The game setup.
        state: The current state of the game.
        bot_identity: The bot's identity (1 or 2).
        
    Returns:
        The terminal state after the game ends.
    """
    while not board.is_ended(state):
        action = select_heuristic_action(board, state, bot_identity)
        state = board.next_state(state, action)
    return state


def select_heuristic_action(board: Board, state, bot_identity):
    """
    Selects the best action during rollout based on a heuristic evaluation of the resulting state.
    
    Args:
        board: The game setup.
        state: The current state of the game.
        bot_identity: The bot's identity (1 or 2).
        
    Returns:
        The action with the best heuristic score.
    """
    best_action = None
    best_score = float('-inf')
    
    # Evaluate a sample of legal actions (up to 9 for efficiency)
    legal_actions = sample(board.legal_actions(state), min(9, len(board.legal_actions(state))))
    
    for action in legal_actions:
        next_state = board.next_state(state, action)
        score = evaluate_state_change(board, state, next_state, bot_identity, action)
        if score > best_score:
            best_score = score
            best_action = action
    
    return best_action


def evaluate_state_change(board: Board, prev_state, next_state, bot_identity, action):
    """
    Evaluates the heuristic score of a state transition from prev_state to next_state.
    
    Args:
        board: The game setup.
        prev_state: The state before taking the action.
        next_state: The state after taking the action.
        bot_identity: The bot's identity (1 or 2).
        
    Returns:
        A heuristic score indicating the desirability of the state change.
    """
    score = 0
    owner = local_win(board, prev_state, next_state)
    if owner == bot_identity:
        score += 100  # Reward winning a local box
    elif owner == 0:
        score += 50
    
    if action_targets_middle(action):
        score += 30
    
    return score

def action_targets_middle(action):
    """
    Determines if the action targets the middle box in the outer or inner grid.
    
    Args:
        action: The action being evaluated (tuple).
        
    Returns:
        True if the action targets the middle box, otherwise False.
    """
    outer_box, inner_box = action[:2], action[2:]
    return outer_box == (1, 1) or inner_box == (1, 1)

def local_win(board: Board, prev_state, next_state):
    """
    Determines if a local box has been won by the bot in the transition from prev_state to next_state.
    
    Args:
        board: The game setup.
        prev_state: The state before taking the action.
        next_state: The state after taking the action.
        bot_identity: The bot's identity (1 or 2).
        
    Returns:
        0 or 1 if a box was won a local box in this transition, otherwise 0.
    """
    prev_boxes = board.owned_boxes(prev_state)
    curr_boxes = board.owned_boxes(next_state)
    
    # Check if any box changed ownership to the bot
    for (row, col), prev_owner in prev_boxes.items():
        curr_owner = curr_boxes.get((row, col), 0)
        if prev_owner == 0 and curr_owner != 0:
            return curr_owner  # A box was won by the bot
    
    return False

def backpropagate(node: MCTSNode|None, won: bool):
    """ Navigates the tree from a leaf node to the root, updating the win and visit count of each node along the path.

    Args:
        node:   A leaf node.
        won:    An indicator of whether the bot won or lost the game.

    """
    while node != None:
        node.visits += 1
        node.wins += won
        node = node.parent

def ucb(node: MCTSNode, is_opponent: bool):
    """ Calcualtes the UCB value for the given node from the perspective of the bot

    Args:
        node:   A node.
        is_opponent: A boolean indicating whether or not the last action was performed by the MCTS bot
    Returns:
        The value of the UCB function for the given node
    """

    exploitation = node.wins / node.visits # win rate percentage
    exploration = explore_faction * sqrt(log(node.parent.visits) / node.visits) 

    if is_opponent:
        exploitation = 1 - exploitation # reverses win rate
    
    ucb = exploitation + exploration
    return ucb


def get_best_action(root_node: MCTSNode):
    """ Selects the best action from the root node in the MCTS tree

    Args:
        root_node:   The root node
    Returns:
        action: The best action from the root node
    
    """
    bestaction = []
    winrate = float('-inf')

    for action, child in root_node.child_nodes.items():
        childwinrate = child.wins / child.visits
        if childwinrate > winrate:
            bestaction = [action]
            winrate = childwinrate
        elif childwinrate == winrate:
            bestaction.append(action)
    return choice(bestaction)

def is_win(board: Board, state, identity_of_bot: int):
    # checks if state is a win state for identity_of_bot
    outcome = board.points_values(state)
    assert outcome is not None, "is_win was called on a non-terminal state"
    return outcome[identity_of_bot] == 1

def think(board: Board, current_state):
    """ Performs MCTS by sampling games and calling the appropriate functions to construct the game tree.

    Args:
        board:  The game setup.
        current_state:  The current state of the game.

    Returns:    The action to be taken from the current state

    """
    bot_identity = board.current_player(current_state) # 1 or 2
    root_node = MCTSNode(parent=None, parent_action=None, action_list=board.legal_actions(current_state))

    for _ in range(num_nodes):
        state = current_state
        node = root_node
        node, state = traverse_nodes(node, board, state, bot_identity)
        node, state = expand_leaf(node, board, state)
        state = heuristic_rollout(board, state, bot_identity)
        backpropagate(node, is_win(board, state, bot_identity))

    # Return an action, typically the most frequently used action (from the root) or the action with the best
    # estimated win rate.
    best_action = get_best_action(root_node)
    
    # print(f"Action chosen: {best_action}")
    return best_action
