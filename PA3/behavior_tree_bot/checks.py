

import logging


def if_neutral_planet_available(state):
    return any(state.neutral_planets())


def have_largest_fleet(state):
    return sum(planet.num_ships for planet in state.my_planets()) \
             + sum(fleet.num_ships for fleet in state.my_fleets()) \
           > sum(planet.num_ships for planet in state.enemy_planets()) \
             + sum(fleet.num_ships for fleet in state.enemy_fleets())

def is_friendly_planet_under_attack(state):
  # Checks if any friendly planet is being targeted by enemy fleets.
  planets_under_attack = [
      fleet.destination_planet for fleet in state.enemy_fleets()
      if fleet.destination_planet in [planet.ID for planet in state.my_planets()]  # Compare IDs
  ]
  logging.info('\n' + "PLANETS UNDER ATTACK")
  logging.info(planets_under_attack)
  
  if not planets_under_attack:
      return False
  else:
    return True

def is_neutral_planet_under_attack(state):
    # Determines if enemy fleets are targeting a neutral planet.
    planets_under_attack = [
      fleet.destination_planet for fleet in state.enemy_fleets()
      if fleet.destination_planet in state.neutral_planets()  # Check if the destination planet is mine
    ]
    if not planets_under_attack:
       return False
    else:
       return True

