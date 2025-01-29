import sys
sys.path.insert(0, '../')
from planet_wars import issue_order
import logging

def attack_weakest_enemy_planet(state):
    strongest_planet = max(state.my_planets(), key=lambda t: t.num_ships, default=None)
    weakest_planet = min(state.enemy_planets(), key=lambda t: t.num_ships, default=None)

    if not strongest_planet or not weakest_planet:
        return False
    enemy_support = sum([fleet.num_ships for fleet in state.enemy_fleets()
        if fleet.destination_planet == weakest_planet.ID
    ])

    min_amount = weakest_planet.num_ships + enemy_support + (state.distance(strongest_planet.ID, weakest_planet.ID) * weakest_planet.growth_rate) + 1
    
    # If already sniping don't snipe
    if any(weakest_planet.ID == fleet.destination_planet for fleet in state.my_fleets()):
        return False
    
    return issue_order(state, strongest_planet.ID, weakest_planet.ID, min_amount)


def spread_to_weakest_neutral_planet(state):
    # Find the weakest neutral planet that isn't already being conquered
    weakest_neutral = min(
        (
            neutral for neutral in state.neutral_planets()
            if sum(fleet.num_ships for fleet in state.my_fleets() if fleet.destination_planet == neutral.ID) <= neutral.num_ships
        ),
        key=lambda neutral: neutral.num_ships,  # Target the planet with the fewest ships
        default=None
    )
    
    if not weakest_neutral:
        # No neutral planets available
        return False

    # Find the strongest allied planet to send ships from
    strongest_planet = max(state.my_planets(), key=lambda p: p.num_ships, default=None)

    if not strongest_planet or strongest_planet.num_ships <= 1:
        # No friendly planet with enough ships to send
        return False

    # Issue the order to send ships to the weakest neutral planet
    result = issue_order(state, strongest_planet.ID, weakest_neutral.ID, weakest_neutral.num_ships +  (state.distance(strongest_planet.ID, weakest_neutral.ID) * weakest_neutral.growth_rate) + 1)
    return result


def spread_to_most_growth_neutral_planet(state):
    # (2) Find my strongest planet.
    strongest_planet = max(state.my_planets(), key=lambda p: p.num_ships, default=None)

    # (3) Find the weakest neutral planet.
    growth_planet = min(state.neutral_planets(), key=lambda p: p.growth_rate, default=None)

    if not strongest_planet or not growth_planet or strongest_planet.num_ships < growth_planet.num_ships + 1:
        # No legal source or destination
        return False
    else:
        # (4) Send half the ships from my strongest planet to the weakest enemy planet.
        return issue_order(state, strongest_planet.ID, growth_planet.ID, growth_planet.num_ships)


# replacement bc it sometimes crashes
# def spread_many_to_closest_planet(state):
#     # Sort my planets from strongest to weakest
#     my_planets = sorted(state.my_planets(), key=lambda p: p.num_ships, reverse=True)
    
#     # Get neutral planets that are not already being targeted
#     neutral_planets = [
#         planet for planet in state.neutral_planets()
#         if not any(fleet.destination_planet == planet.ID for fleet in state.my_fleets())
#     ]

#     if not neutral_planets:
#         return False  # No neutral planets available

#     # Iterate through my planets and try to spread to the closest neutral planet
#     for my_planet in my_planets:
#         if my_planet.num_ships <= 1:
#             continue  # Skip planets with too few ships

#         # Sort neutral planets by distance to the current my_planet
#         neutral_planets_sorted = sorted(
#             neutral_planets,
#             key=lambda p: state.distance(my_planet.ID, p.ID)
#         )

#         # Try to find a neutral planet to attack
#         for neutral_planet in neutral_planets_sorted:
#             required_ships = neutral_planet.num_ships + 1

#             if my_planet.num_ships > required_ships:
#                 # Issue the order to spread to the neutral planet
#                 issue_order(state, my_planet.ID, neutral_planet.ID, required_ships)
#                 break  # Move to the next my_planet after issuing an order

#     return True

def spread_many_to_closest_planet(state):
    # Iterates through all my.planets() and spread to the closest values it can take. Similar to spread.bot, but focuses on distance.
    strong_to_weak_planet = iter(sorted(state.my_planets(), key=lambda p: p.num_ships))

    if not strong_to_weak_planet:
        return False
    try:
        curr_strong = next(strong_to_weak_planet)
    except StopIteration:
        return False
    
    neutral_planets = [planet for planet in state.neutral_planets()
                      if not any(fleet.destination_planet == planet.ID for fleet in state.my_fleets())]
    
    if not neutral_planets:
        return False
    
    neutral_planets.sort(key=lambda p: state.distance(p.ID, curr_strong.ID))
    target = iter(neutral_planets)
    count = 0

    try:
        target_planet = next(target)
        while True:
            required_ships = target_planet.num_ships + 1
            
            if curr_strong.num_ships > required_ships:
                issue_order(state, curr_strong.ID, target_planet.ID, required_ships)
                curr_strong = next(strong_to_weak_planet)
                target_planet = next(target)
                count = 0
            elif required_ships > curr_strong.num_ships and count < 3:
                #This is a general check of the other 3 closest nodes. 
                target_planet = next(target)    
                count += 1
            else:
                curr_strong = next(strong_to_weak_planet)
                count = 0            
                neutral_planets = [planet for planet in state.neutral_planets()
                                if not any(fleet.destination_planet == planet.ID for fleet in state.my_fleets())]
                
                if not neutral_planets:
                    return False
    
                neutral_planets.sort(key=lambda p: state.distance(p.ID, curr_strong.ID))
                target = iter(neutral_planets)

    except StopIteration:
        return False
    


def spread_to_closest_netural_planet(state):
    # Find the closest neutral planet to any of my planets that isn't already being conquered
    closest_neutral = min(
        (
            neutral for neutral in state.neutral_planets()
            if sum(fleet.num_ships for fleet in state.my_fleets() if fleet.destination_planet == neutral.ID) <= neutral.num_ships
        ),
        key=lambda neutral: min(state.distance(neutral.ID, my_planet.ID) for my_planet in state.my_planets()),
        default=None
    )
    
    if not closest_neutral:
        # No neutral planets available
        return False

    # Find the strongest allied planet to neutral planet
    strongest_planet = max(state.my_planets(), key=lambda p: p.num_ships, default=None)


    if not strongest_planet or strongest_planet.num_ships <= 1:
        # No friendly planet with enough ships to send
        return False

    # Issue the order to send ships to the closest neutral planet
    result = issue_order(state, strongest_planet.ID, closest_neutral.ID, closest_neutral.num_ships + 1)
    return result

# needs to check if already defending the attacked planet
# could also change weakest planet to be the planet that is about to be taken over by a fleet
def send_reinforcements_to_weakest_planet_under_attack(state):
    # Find all planets under attack
    # *** fleet.destination_planet is the planet ID NOT the planet itself...
    planets_under_attack = [
        fleet.destination_planet for fleet in state.enemy_fleets()
        if state.planets[fleet.destination_planet].owner == 1  # Only consider your planets
        and (
            # Case 1: No incoming friendly fleets
            sum(ally_fleet.num_ships for ally_fleet in state.my_fleets()
                if ally_fleet.destination_planet == fleet.destination_planet) == 0
            or
            # Case 2: Incoming friendly fleets are insufficient
            sum(ally_fleet.num_ships for ally_fleet in state.my_fleets()
                if ally_fleet.destination_planet == fleet.destination_planet)
            < sum(enemy_fleet.num_ships for enemy_fleet in state.enemy_fleets()
                if enemy_fleet.destination_planet == fleet.destination_planet)
        )
    ]

    if not planets_under_attack:
        return False
    
    # Find my weakest_planet under attack
    weakest_planet = min(
        (planet for planet in state.my_planets() if planet.ID in planets_under_attack),
        key=lambda p: p.num_ships,
        default=None
    )
    
    logging.info('\n' + "WEAKEST PLANET")
    logging.info(weakest_planet)
    
    # Find all fleets that are attacking weakest_planet
    attacking_fleets = [fleet for fleet in state.enemy_fleets()
         if fleet.destination_planet in [planet.ID for planet in state.my_planets()]
    ]
    
    logging.info('\n' + "ATTACKING FLEETS")
    logging.info(attacking_fleets)

    # Find the max fleet size
    min_req = sum([fleet.num_ships for fleet in attacking_fleets]) + 1
    
    # Find the closest planet that can send out reinforcements
    closest_ally_planet = min(
        (planet for planet in state.my_planets() if planet.ID != weakest_planet.ID and planet.num_ships > min_req * (state.distance(planet.ID, weakest_planet.ID) * weakest_planet.growth_rate)),
        key=lambda p: state.distance(p.ID, weakest_planet.ID),
        default=None
    )

    # If cannot defend abandon the planet
    if not closest_ally_planet:
        return False
    else:
        min_req += (state.distance(closest_ally_planet.ID, weakest_planet.ID) * weakest_planet.growth_rate)
        return issue_order(state, closest_ally_planet.ID, weakest_planet.ID, min_req)

def send_many_reinforcements_to_planets_under_attack(state):
    #does the same as above, but tries to defend with many planets
    planets_under_attack = [
        state.planets[fleet.destination_planet] for fleet in state.enemy_fleets()
        if state.planets[fleet.destination_planet].owner == 1  # Only consider your planets
        and (
            # Case 1: No incoming friendly fleets
            sum(ally_fleet.num_ships for ally_fleet in state.my_fleets()
                if ally_fleet.destination_planet == fleet.destination_planet) == 0
            or
            # Case 2: Incoming friendly fleets are insufficient
            sum(ally_fleet.num_ships for ally_fleet in state.my_fleets()
                if ally_fleet.destination_planet == fleet.destination_planet)
            < sum(enemy_fleet.num_ships for enemy_fleet in state.enemy_fleets()
                if enemy_fleet.destination_planet == fleet.destination_planet)
        )
    ]    
    if not planets_under_attack:
        return False
    logging.info('enemy time')
    planets_under_attack.sort(key=lambda p: p.num_ships)
    under_attack = iter(planets_under_attack)
    count = 0
    try:
        attacked = next(under_attack)
        while True:
            
            enemy_support = sum([fleet.num_ships for fleet in state.enemy_fleets()
                if fleet.destination_planet == attacked.ID
            ])
            
            enemy_time = max([fleet.total_trip_length for fleet in state.enemy_fleets()
                if fleet.destination_planet == attacked.ID
            ])
            
            closest_allies = [planet for planet in state.my_planets()
                if (state.distance(attacked.ID, planet.ID) <= enemy_time)]  
            if not closest_allies:
                return False
            
            closest_allies.sort(key=lambda p: p.num_ships, reverse=True)
            
            check = sum(allies.num_ships for allies in closest_allies) / 2
            if(check < enemy_support):
                issue_order(state, attacked.ID, closest_allies[0].ID, attacked.num_ships)
                return False
            
            ally_support = sum([fleet.num_ships for fleet in state.my_fleets()
                if fleet.destination_planet == attacked.ID
            ])
            for allies in closest_allies:
                count = ally_support
                if count > enemy_support:
                    return True
                elif enemy_support > count:
                    issue_order(state, allies.ID, attacked.ID, allies.num_ships / 2)
            return False

            
    except StopIteration:
        return False
    

# first find the netural planets that are going to be taken over by enemy
    # neutral_planet.num_ships - enemy_fleets size > 0
# calculate the distance it takes for the enemy fleet to arrive
# calculate the distance it takes for your planets with 
    #  neutral_planet.num_ships - enemy_fleets size + 1 num_ships to arrive
# send fleets from the planets that are enough distance away that the enemy's fleet will get to the neutral planet first
    # fleet size =  neutral_planet.num_ships - enemy_fleets size + 1 + (distance_from_enemy_fleet_to_neutral - distance_from_my_fleet_to_neutral) * neutral_growth_rate
def send_reinforcements_to_neutral_planet_under_attack(state):
    # Find all neutral planets that are about to be taken over by enemy fleets
    planets_under_attack = [
        fleet.destination_planet for fleet in state.enemy_fleets()
        if state.planets[fleet.destination_planet].owner == 0  # Neutral planets
        and sum(f.num_ships for f in state.enemy_fleets() if f.destination_planet == fleet.destination_planet) >= state.planets[fleet.destination_planet].num_ships
    ]

    if not planets_under_attack:
        return False

    # Find the planet that has the most growth rate
    neutral_planet = max(
        (state.planets[planet_id] for planet_id in planets_under_attack),
        key=lambda p: p.growth_rate,
        default=None
    )

    # Calculate the time for the enemy fleet to arrive
    enemy_arrival_time = max(
        fleet.turns_remaining for fleet in state.enemy_fleets() if fleet.destination_planet == neutral_planet.ID
    )

    # Find the friendly planets thats have enough ships and arrival time is > enemy_arrival_time
    strongest_planet = max(
        (planet for planet in state.my_planets() 
         if state.distance(planet.ID, neutral_planet.ID) > enemy_arrival_time
         and planet.num_ships > (state.distance(planet.ID, neutral_planet.ID) - enemy_arrival_time) * neutral_planet.growth_rate),
        key=lambda p: p.num_ships,
        default=None
    )

    if not strongest_planet:
        return False
    
    # Calculate distance / turns it takes between my planet and neutral
    friendly_arrival_time = state.distance(strongest_planet.ID, neutral_planet.ID)

    # Calculate the number of ships to send
    ships_to_send = ((friendly_arrival_time - enemy_arrival_time) * neutral_planet.growth_rate + 2)

    # Send the fleet
    if(friendly_arrival_time > 20):
        #tries not to send fleets too far away or too expensive.
        return False
    else:
        return issue_order(state, strongest_planet.ID, neutral_planet.ID, ships_to_send)


def take_small_enemy_planets(state):
    
    weakest_planet = min(state.enemy_planets(), key=lambda t: t.num_ships, default=None)
    closest_planet = min(
        (
            closest for closest in state.my_planets()
            if sum(fleet.num_ships for fleet in state.my_fleets() if fleet.destination_planet == weakest_planet.ID) > weakest_planet.num_ships
        ),
        key=lambda p: state.distance(p.ID, weakest_planet.ID),
        default=None
    )

    if not closest_planet():
        return False
    
    if closest_planet.num_ships > weakest_planet:
        return issue_order(state, closest_planet.ID, weakest_planet.ID, closest_planet.num_ships - 1)
    
def all_out_attack(state):
    #sends 5 ships constantly from many different planets to one until conquered, and moves to the next one.
    strong_to_weak_planet = iter(sorted(state.my_planets(), key=lambda p: p.num_ships, reverse=True))

    if not strong_to_weak_planet:
        return False

    enemy_planets = [planet for planet in state.enemy_planets()]

    if not enemy_planets:
        return False

    enemy_planets.sort(key=lambda p: p.num_ships)
    target = iter(enemy_planets)
    
    try:
        curr_strong = next(strong_to_weak_planet)
        target_planet = next(target)
        while True:
            required_ships = 3
            enemy_support = sum([fleet.num_ships for fleet in state.enemy_fleets()
                if fleet.destination_planet == target_planet.ID
            ])
            ally_support = sum([fleet.num_ships for fleet in state.my_fleets()
                if fleet.destination_planet == target_planet.ID
            ])
            planet_gone = target_planet.num_ships + enemy_support - ally_support
            if(target_planet.num_ships > 0 or planet_gone >= 0):
                issue_order(state, curr_strong.ID, target_planet.ID, required_ships)
                curr_strong = next(strong_to_weak_planet)
            else:
                target_planet = next(target)
    except StopIteration:
        return False