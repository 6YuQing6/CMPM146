Modified Monte Carlo Tree Search Algorithm

Members: Anson Fong, Sunny Han

Contributions: We collaborated equally on all aspects of the program, sharing responsibility for its design, implementation, and testing.

Modifications Overview
Heuristic Rollout Strategy
	·Implemented a signal to identify winning moves that result in immediate victories.
	·Added functionality to block opponents from winning on their next turn.
Enhanced the algorithm to prioritize moves that maximize the number of owned boxes.
	·Defaulted to random choice when none of the above strategies are applicable.

Additional Improvements
	·get_best_child: Now prioritizes unexplored nodes, striking a better balance between exploration and exploitation within the tree search.
	·get_best_action: Skips exploration and unvisited nodes when determining the final action.

Results
·Improved decision-making hierarchy that prioritizes winning moves and prevents opponent wins, with random actions as a last resort.

·Enhanced exploration of the game tree during simulations.

·Achieved a higher overall win rate regardless of node values.