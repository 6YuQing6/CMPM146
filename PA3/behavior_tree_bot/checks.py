

import logging


def if_neutral_planet_available(state):
    return any(state.neutral_planets())
    # needs to check if neutral planets already has fleets on the way and is able to conquer planet

def if_enemy_planet_snipable(state):
  # check if my strongest planet can conquer the weakest enemy planet
  strongest_planet = max(state.my_planets(), key=lambda p: p.num_ships, default=None)

  # Find the weakest enemy planet (one with the fewest ships)
  weakest_enemy_planet = min(state.enemy_planets(), key=lambda p: p.num_ships, default=None)

  if not strongest_planet or not weakest_enemy_planet:
      # If there are no valid strongest or weakest planets, return False
      return False

  # Check if the strongest planet can conquer the weakest enemy planet
  return strongest_planet.num_ships > weakest_enemy_planet.num_ships * 1.2

def have_largest_fleet(state):
    #do not use this when neutral planets exist.
    if(any(state.neutral_planets())):
       return False
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
    planets_under_attack = [
        fleet.destination_planet for fleet in state.enemy_fleets()
        if state.planets[fleet.destination_planet].owner == 0  # Only consider neutral planets
    ]
    if not planets_under_attack:
      return False
    else:
      return True