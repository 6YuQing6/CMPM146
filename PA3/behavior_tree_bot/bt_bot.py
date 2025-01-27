#!/usr/bin/env python
#

"""
// There is already a basic strategy in place here. You can use it as a
// starting point, or you can throw it out entirely and replace it with your
// own.
"""
import logging, traceback, sys, os, inspect
logging.basicConfig(filename=__file__[:-3] +'.log', filemode='w', level=logging.DEBUG)
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

from behavior_tree_bot.behaviors import *
from behavior_tree_bot.checks import *
from behavior_tree_bot.bt_nodes import Selector, Sequence, Action, Check

from planet_wars import PlanetWars, finish_turn


# You have to improve this tree or create an entire new one that is capable
# of winning against all the 5 opponent bots
def setup_behavior_tree():

    # Top-down construction of behavior tree
    root = Selector(name='High Level Ordering of Strategies')

    defensive_plan = Sequence(name='Defensive Strategy')
    planet_under_attack_check = Check(is_friendly_planet_under_attack)
    defend = Action(send_reinforcements_to_weakest_planet_under_attack)
    defensive_plan.child_nodes = [planet_under_attack_check, defend]

    offensive_plan = Sequence(name='Offensive Strategy')
    # Sniper Strategy - only works if I have a larger planet
    largest_fleet_check = Check(if_enemy_planet_snipable)
    attack = Action(attack_weakest_enemy_planet)
    offensive_plan.child_nodes = [largest_fleet_check, attack]
    # Add Crowding Strategy - only works if I have a larger number

    spread_sequence = Sequence(name='Spread Strategy')
    neutral_planet_check = Check(if_neutral_planet_available)
    spread_action = Action(spread_many_to_closest_planet)
    spread_sequence.child_nodes = [neutral_planet_check, spread_action]
    '''
    conquest_sequence = Sequence(name='Conquest')
    fleet_check = Check(have_largest_fleet)
    conquer = Action(all_out_attack)
    conquest_sequence.child_nodes = [fleet_check, conquer]
    '''
    root.child_nodes = [defensive_plan, offensive_plan, spread_sequence, attack.copy()]

    logging.info('\n' + root.tree_to_string())
    return root

# You don't need to change this function
def do_turn(state):
    behavior_tree.execute(planet_wars)

if __name__ == '__main__':
    logging.basicConfig(filename=__file__[:-3] + '.log', filemode='w', level=logging.DEBUG)

    behavior_tree = setup_behavior_tree()
    try:
        map_data = ''
        while True:
            current_line = input()
            if len(current_line) >= 2 and current_line.startswith("go"):
                planet_wars = PlanetWars(map_data)
                do_turn(planet_wars)
                finish_turn()
                map_data = ''
            else:
                map_data += current_line + '\n'

    except KeyboardInterrupt:
        print('ctrl-c, leaving ...')
    except Exception:
        traceback.print_exc(file=sys.stdout)
        logging.exception("Error in bot.")
