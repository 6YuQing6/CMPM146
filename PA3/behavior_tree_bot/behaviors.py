import sys
sys.path.insert(0, '../')
from planet_wars import issue_order


def attack_weakest_enemy_planet(state):
    # # (1) If we currently have a fleet in flight, abort plan.
    if len(state.my_fleets()) >= 1:
        return False

    # (2) Find my strongest planet.
    strongest_planet = max(state.my_planets(), key=lambda t: t.num_ships, default=None)

    # (3) Find the weakest enemy planet.
    weakest_planet = min(state.enemy_planets(), key=lambda t: t.num_ships, default=None)

    if not strongest_planet or not weakest_planet:
        # No legal source or destination
        return False
    else:
        # (4) Send half the ships from my strongest planet to the weakest enemy planet.
        return issue_order(state, strongest_planet.ID, weakest_planet.ID, strongest_planet.num_ships / 2)


def spread_to_weakest_neutral_planet(state):
    # # (1) If we currently have a fleet in flight, just do nothing.
    if len(state.my_fleets()) >= 1:
        return False

    # (2) Find my strongest planet.
    strongest_planet = max(state.my_planets(), key=lambda p: p.num_ships, default=None)

    # (3) Find the weakest neutral planet.
    weakest_planet = min(state.neutral_planets(), key=lambda p: p.num_ships, default=None)

    if not strongest_planet or not weakest_planet:
        # No legal source or destination
        return False
    else:
        # (4) Send half the ships from my strongest planet to the weakest enemy planet.
        return issue_order(state, strongest_planet.ID, weakest_planet.ID, strongest_planet.num_ships / 2)


# could also change weakest planet to be the planet that is about to be taken over by a fleet
def send_reinforcements_to_weakest_planet_under_attack(state):
    # Find all planets under attack
    planets_under_attack = [
        fleet.destination_planet for fleet in state.enemy_fleets()
        if state.planets[fleet.destination_planet].owner == 1  # Check if the destination planet is mine
    ]
    
    # Find my weakest_planet under attack
    weakest_planet = min(planets_under_attack, key=lambda p: p.num_ships, default=None)

    # Find all fleets that are attacking weakest_planet
    attacking_fleets = [fleet for fleet in state.enemy_fleets()
        if state.planets[fleet.destination_planet] == weakest_planet]
    
    # Find the closest enemy fleet to that planet
    closest_attacking_fleet = min(attacking_fleets, key=lambda fleet: fleet.turns_remaining, default=None)

    # Find the closest planet that can send out reinforcements
    closest_ally_planet = max(
        (planet for planet in state.my_planets() \
         if planet not in planets_under_attack and \
         planet.num_ships > closest_attacking_fleet.size + 1),
        key=lambda p: state.distance(p, weakest_planet),
        default=None
    )

    # If cannot defend abandon the planet
    if not closest_ally_planet:
        return False
    else:
        return issue_order(state, closest_ally_planet.ID, weakest_planet.ID, closest_attacking_fleet.size + 1)
