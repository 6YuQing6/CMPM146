import copy
import heapq
import metrics
import multiprocessing.pool as mpool
import os
import random
import shutil
import time
import math

width = 200   # Standard Mario level width
height = 16   # Standard Mario level height

options = [
    "-",  # an empty space
    "X",  # a solid wall
    "?",  # a question mark block with a coin
    "M",  # a question mark block with a mushroom
    "B",  # a breakable block
    "o",  # a coin
    "|",  # a pipe segment
    "T",  # a pipe top
    "E",  # an enemy
    #"f",  # a flag, do not generate
    #"v",  # a flagpole, do not generate
    #"m"  # mario's start position, do not generate
]

# The level as a grid of tiles


class Individual_Grid(object):
    __slots__ = ["genome", "_fitness"]

    def __init__(self, genome):
        self.genome = copy.deepcopy(genome)
        self._fitness = None
    
    def __str__(self):
        return f"Fitness: {self._fitness if self._fitness is not None else 'Not Evaluated'}, Genome: {self.genome[:3]}..."  

    def __repr__(self):
        return f"Individual_Grid(Fitness={self._fitness if self._fitness is not None else 'Not Evaluated'})"
    # Update this individual's estimate of its fitness.
    # This can be expensive so we do it once and then cache the result.
    def calculate_fitness(self):
        measurements = metrics.metrics(self.to_level())
        # Print out the possible measurements or look at the implementation of metrics.py for other keys:
        # print(measurements.keys())
            # dict_keys(['length', 'negativeSpace', 'pathPercentage', 'emptyPercentage', 'decorationPercentage', 'leniency',
            # 'meaningfulJumps', 'jumps', 'meaningfulJumpVariance', 'jumpVariance', 'linearity', 'solvability'])
        # Default fitness function: Just some arbitrary combination of a few criteria.  Is it good?  Who knows?
        # STUDENT Modify this, and possibly add more metrics.  You can replace this with whatever code you like.
        # coefficients = dict(
        #     meaningfulJumpVariance=0.5,
        #     negativeSpace=0.3,
        #     pathPercentage=0.5,
        #     emptyPercentage=0.8,
        #     decorationPercentage=0.2,
        #     linearity=0.7,
        #     leniency=0.5,
        #     meaningfulJumps=1.5,
        #     jumps=0.5,
        #     solvability=2.0
        # )
        coefficients = dict(
            meaningfulJumpVariance=0.5,    # Ensure varied but manageable jumps
            negativeSpace=0.4,             # Reduce to avoid too many gaps
            pathPercentage=0.8,            # Increase to ensure traversable paths
            emptyPercentage=0.4,           # Balance between empty space and platforms
            linearity=-0.3,                # Slight negative to avoid flat levels
            solvability=3.0,               # Heavily weight solvable levels
            decorationPercentage=0.2,      # Add some visual interest
            leniency=0.6                   # Make levels more forgiving
        )
        penalties = 0
        
        # Penalize long gaps
        max_gap = 0
        current_gap = 0
        for x in range(width):
            if self.genome[height-1][x] == '-':
                current_gap += 1
                max_gap = max(max_gap, current_gap)
            else:
                current_gap = 0
        if max_gap > 4:
            penalties -= (max_gap - 4) * 0.5
        
        # Penalize too many enemies
        enemy_count = sum(row.count('E') for row in self.genome)
        if enemy_count > width/10:
            penalties -= (enemy_count - width/10) * 0.3
        
        # Penalize floating platforms
        for y in range(height-2):
            for x in range(1, width-1):
                if self.genome[y][x] in ['X', 'B', '?', 'M']:
                    if self.genome[y+1][x] == '-':
                        penalties -= 0.2
        
        self._fitness = sum(map(lambda m: coefficients[m] * measurements[m],
                                coefficients)) + penalties
        return self

    # Return the cached fitness value or calculate it as needed.
    def fitness(self):
        if self._fitness is None:
            self.calculate_fitness()
        return self._fitness

    # Mutate a genome into a new genome.  Note that this is a _genome_, not an individual!
    def mutate(self, genome):
        mutation_rate = 0.02
        tile_weights = {
            "-": 0.35,   # Empty space (common)
            "X": 0.15,   # Solid blocks
            "?": 0.1,    # Question blocks
            "M": 0.05,   # Mushroom blocks (rare)
            "B": 0.15,   # Breakable blocks
            "o": 0.1,    # Coins
            "|": 0.05,   # Pipe body (rare)
            "T": 0.03,   # Pipe top (rare)
            "E": 0.02    # Enemies (very rare)
        }
        
        for y in range(height):
            for x in range(1, width-1):  # Skip first/last columns
                if random.random() < mutation_rate:
                    # Don't modify ground level except for pipes
                    if y == height-1:
                        if genome[y][x] not in ['|', 'T']:
                            continue
                            
                    # Ensure platforms are supported
                    if y < height-1:
                        if genome[y+1][x] == '-':  # If no support below
                            valid_tiles = ['-', 'o']  # Only allow air or coins
                        else:
                            valid_tiles = list(tile_weights.keys())
                            
                    # Prevent floating pipes
                    if genome[y][x] in ['|', 'T']:
                        if y < height-1 and genome[y+1][x] not in ['|', 'X']:
                            valid_tiles.remove('|')
                            valid_tiles.remove('T')
                            
                    # Ensure enemies have ground
                    if genome[y][x] == 'E':
                        if y < height-1 and genome[y+1][x] == '-':
                            continue
                            
                    weights = [tile_weights[t] for t in valid_tiles]
                    genome[y][x] = random.choices(valid_tiles, weights=weights)[0]
        
        return genome

    # Create zero or more children from self and other
    def generate_children(self, other):
        new_genome = copy.deepcopy(self.genome)
        
        # Do crossover with constraints
        left = 1
        right = width - 1
        for y in range(height):
            # Keep ground level mostly intact
            if y == height-1:
                continue
            
            # Crossover in chunks to maintain coherent structures
            chunk_size = random.randint(3, 8)
            for x in range(left, right, chunk_size):
                if random.random() > 0.5:
                    end_x = min(x + chunk_size, right)
                    # Copy chunk while maintaining structural integrity
                    for cx in range(x, end_x):
                        for cy in range(y, min(y+3, height)):
                            new_genome[cy][cx] = other.genome[cy][cx]
                            
                    # Ensure platform connectivity
                    if y < height-1:
                        for cx in range(x, end_x):
                            if new_genome[y][cx] in ['X', 'B', '?', 'M']:
                                if new_genome[y+1][cx] == '-':
                                    new_genome[y][cx] = '-'
        
        return (Individual_Grid(new_genome),)

    # Turn the genome into a level string (easy for this genome)
    def to_level(self):
        return self.genome

    # These both start with every floor tile filled with Xs
    # STUDENT Feel free to change these
    @classmethod
    def empty_individual(cls):
        g = [["-" for col in range(width)] for row in range(height)]
        g[15][:] = ["X"] * width
        g[14][0] = "m"
        g[7][-1] = "v"
        for col in range(8, 14):
            g[col][-1] = "f"
        for col in range(14, 16):
            g[col][-1] = "X"
        return cls(g)

    @classmethod
    def random_individual(cls):
        # Initialize with ground and empty space
        g = [["-" for col in range(width)] for row in range(height)]
        
        # Create solid ground at bottom
        for x in range(width):
            g[height-1][x] = "X"
        
        # Add required elements
        g[height-2][0] = "m"  # Mario start
        g[7][width-1] = "v"  # Flag pole
        for y in range(8, 14):
            g[y][width-1] = "f"  # Flag
        g[height-2][width-1] = "X"  # Flag base
        g[height-1][width-1] = "X"  # Flag base
        
        # Add platforms and challenges
        last_platform_y = height - 3  # Track last platform height
        
        for x in range(5, width-10, random.randint(4, 8)):
            if random.random() < 0.75:  # 75% chance of platform
                # Vary platform height based on last platform
                max_height_diff = 3  # Maximum height difference between platforms
                min_y = max(height-7, last_platform_y - max_height_diff)
                max_y = min(height-3, last_platform_y + max_height_diff)
                platform_y = random.randint(min_y, max_y)
                
                # Ensure accessibility with stepping stones if platform is higher
                if platform_y < last_platform_y - 2:
                    # Create stepping stones
                    step_x = x - 3
                    step_y = last_platform_y - 1
                    while step_y > platform_y + 1 and step_x < x:
                        g[step_y][step_x] = "X"
                        step_x += 1
                        step_y -= 1
                
                last_platform_y = platform_y
                platform_length = random.randint(4, 8)
                
                # Create main platform
                for px in range(x, min(x + platform_length, width-2)):
                    g[platform_y][px] = "X"
                    
                    # Add accessible decorations above platform
                    if random.random() < 0.6:
                        if random.random() < 0.4:
                            g[platform_y-1][px] = "?"
                        else:
                            g[platform_y-1][px] = "B"
                    
                    # Add second layer that's reachable
                    if random.random() < 0.3 and platform_y > height-6:
                        if g[platform_y-1][px] in ["?", "B"]:
                            # Ensure there's a way to reach higher blocks
                            if px > x and g[platform_y-1][px-1] == "-":
                                g[platform_y-1][px-1] = "X"  # Add stepping block
                            if random.random() < 0.5:
                                g[platform_y-2][px] = "B"
                            else:
                                g[platform_y-2][px] = "o"
                
                # Add enemies on platforms
                if platform_length > 4 and random.random() < 0.5:
                    enemy_x = x + random.randint(1, platform_length-2)
                    if g[platform_y-1][enemy_x] == "-":
                        g[platform_y-1][enemy_x] = "E"
        
        # Add ground variation and pipes
        for x in range(1, width-2, random.randint(10, 15)):
            if random.random() < 0.5:
                pipe_height = random.randint(2, 4)
                if x < width-4:
                    # Add stepping blocks near tall pipes
                    if pipe_height > 2:
                        g[height-2][x-1] = "X"  # Stepping block
                    
                    for y in range(height-pipe_height-1, height-1):
                        g[y][x] = "|"
                        g[y][x+1] = "|"
                    g[height-pipe_height-1][x] = "T"
                    g[height-pipe_height-1][x+1] = "T"
                    
                    if random.random() < 0.4:
                        if x > 2 and g[height-2][x-2] == "-":
                            g[height-2][x-2] = "E"
                    x += 1
        
        # Add floating blocks with access paths
        for x in range(5, width-5, random.randint(4, 7)):
            for y in range(height-6, height-2):
                if g[y][x] == "-" and g[y+1][x] == "-":
                    if random.random() < 0.4:
                        # Create access path
                        if y < height-3:  # If block is high up
                            # Add stepping stone below
                            g[y+1][x-1] = "X"
                        
                        if random.random() < 0.6:
                            g[y][x] = "?"
                        elif random.random() < 0.7:
                            g[y][x] = "B"
                        else:
                            g[y][x] = "o"
        
        # Add ground decorations and enemies
        for x in range(1, width-2):
            if g[height-2][x] == "-":
                if random.random() < 0.15:
                    if random.random() < 0.6:
                        g[height-2][x] = "B"
                    else:
                        g[height-2][x] = "?"
                elif random.random() < 0.1:
                    g[height-2][x] = "E"
        
        # Add mushroom power-ups with access
        for x in range(5, width-5, random.randint(20, 30)):
            if random.random() < 0.3:
                y = random.randint(height-5, height-3)
                if g[y][x] == "?":
                    g[y][x] = "M"
                    # Ensure mushroom is accessible
                    if y < height-3 and g[y+1][x] == "-":
                        g[y+1][x-1] = "X"  # Add stepping block
        
        return cls(g)


def offset_by_upto(val, variance, min=None, max=None):
    val += random.normalvariate(0, variance**0.5)
    if min is not None and val < min:
        val = min
    if max is not None and val > max:
        val = max
    return int(val)


def clip(lo, val, hi):
    if val < lo:
        return lo
    if val > hi:
        return hi
    return val

# Inspired by https://www.researchgate.net/profile/Philippe_Pasquier/publication/220867545_Towards_a_Generic_Framework_for_Automated_Video_Game_Level_Creation/links/0912f510ac2bed57d1000000.pdf


class Individual_DE(object):
    # Calculating the level isn't cheap either so we cache it too.
    __slots__ = ["genome", "_fitness", "_level"]

    # Genome is a heapq of design elements sorted by X, then type, then other parameters
    def __init__(self, genome):
        self.genome = list(genome)
        heapq.heapify(self.genome)
        self._fitness = None
        self._level = None

    # Calculate and cache fitness
    def calculate_fitness(self):
        measurements = metrics.metrics(self.to_level())
        # Default fitness function: Just some arbitrary combination of a few criteria.  Is it good?  Who knows?
        # STUDENT Add more metrics?
        # STUDENT Improve this with any code you like
        coefficients = dict(
            meaningfulJumpVariance=0.5,
            negativeSpace=0.4,
            pathPercentage=0.8,
            emptyPercentage=0.4,
            linearity=-0.3,
            solvability=3.0,
            decorationPercentage=0.2,
            leniency=0.6
        )
        penalties = 0
        # STUDENT For example, too many stairs are unaesthetic.  Let's penalize that
        if len(list(filter(lambda de: de[1] == "6_stairs", self.genome))) > 5:
            penalties -= 2
        # STUDENT If you go for the FI-2POP extra credit, you can put constraint calculation in here too and cache it in a new entry in __slots__.
        self._fitness = sum(map(lambda m: coefficients[m] * measurements[m],
                                coefficients)) + penalties
        return self

    def fitness(self):
        if self._fitness is None:
            self.calculate_fitness()
        return self._fitness

    def mutate(self, new_genome):
        # STUDENT How does this work?  Explain it in your writeup.
        # STUDENT consider putting more constraints on this, to prevent generating weird things
        if random.random() < 0.1 and len(new_genome) > 0:
            to_change = random.randint(0, len(new_genome) - 1)
            de = new_genome[to_change]
            new_de = de
            x = de[0]
            de_type = de[1]
            choice = random.random()
            if de_type == "4_block":
                y = de[2]
                breakable = de[3]
                if choice < 0.33:
                    x = offset_by_upto(x, width / 8, min=1, max=width - 2)
                elif choice < 0.66:
                    y = offset_by_upto(y, height / 2, min=0, max=height - 1)
                else:
                    breakable = not de[3]
                new_de = (x, de_type, y, breakable)
            elif de_type == "5_qblock":
                y = de[2]
                has_powerup = de[3]  # boolean
                if choice < 0.33:
                    x = offset_by_upto(x, width / 8, min=1, max=width - 2)
                elif choice < 0.66:
                    y = offset_by_upto(y, height / 2, min=0, max=height - 1)
                else:
                    has_powerup = not de[3]
                new_de = (x, de_type, y, has_powerup)
            elif de_type == "3_coin":
                y = de[2]
                if choice < 0.5:
                    x = offset_by_upto(x, width / 8, min=1, max=width - 2)
                else:
                    y = offset_by_upto(y, height / 2, min=0, max=height - 1)
                new_de = (x, de_type, y)
            elif de_type == "7_pipe":
                h = de[2]
                if choice < 0.5:
                    x = offset_by_upto(x, width / 8, min=1, max=width - 2)
                else:
                    h = offset_by_upto(h, 2, min=2, max=height - 4)
                new_de = (x, de_type, h)
            elif de_type == "0_hole":
                w = de[2]
                if choice < 0.5:
                    x = offset_by_upto(x, width / 8, min=1, max=width - 2)
                else:
                    w = offset_by_upto(w, 4, min=1, max=width - 2)
                new_de = (x, de_type, w)
            elif de_type == "6_stairs":
                h = de[2]
                dx = de[3]  # -1 or 1
                if choice < 0.33:
                    x = offset_by_upto(x, width / 8, min=1, max=width - 2)
                elif choice < 0.66:
                    h = offset_by_upto(h, 8, min=1, max=height - 4)
                else:
                    dx = -dx
                new_de = (x, de_type, h, dx)
            elif de_type == "1_platform":
                w = de[2]
                y = de[3]
                madeof = de[4]  # from "?", "X", "B"
                if choice < 0.25:
                    x = offset_by_upto(x, width / 8, min=1, max=width - 2)
                elif choice < 0.5:
                    w = offset_by_upto(w, 8, min=1, max=width - 2)
                elif choice < 0.75:
                    y = offset_by_upto(y, height, min=0, max=height - 1)
                else:
                    madeof = random.choice(["?", "X", "B"])
                new_de = (x, de_type, w, y, madeof)
            elif de_type == "2_enemy":
                pass
            new_genome.pop(to_change)
            heapq.heappush(new_genome, new_de)
        return new_genome

    def generate_children(self, other):
        # STUDENT How does this work?  Explain it in your writeup.
        pa = random.randint(0, len(self.genome) - 1)
        pb = random.randint(0, len(other.genome) - 1)
        a_part = self.genome[:pa] if len(self.genome) > 0 else []
        b_part = other.genome[pb:] if len(other.genome) > 0 else []
        ga = a_part + b_part
        b_part = other.genome[:pb] if len(other.genome) > 0 else []
        a_part = self.genome[pa:] if len(self.genome) > 0 else []
        gb = b_part + a_part
        # do mutation
        return Individual_DE(self.mutate(ga)), Individual_DE(self.mutate(gb))

    # Apply the DEs to a base level.
    def to_level(self):
        if self._level is None:
            base = Individual_Grid.empty_individual().to_level()
            for de in sorted(self.genome, key=lambda de: (de[1], de[0], de)):
                # de: x, type, ...
                x = de[0]
                de_type = de[1]
                if de_type == "4_block":
                    y = de[2]
                    breakable = de[3]
                    base[y][x] = "B" if breakable else "X"
                elif de_type == "5_qblock":
                    y = de[2]
                    has_powerup = de[3]  # boolean
                    base[y][x] = "M" if has_powerup else "?"
                elif de_type == "3_coin":
                    y = de[2]
                    base[y][x] = "o"
                elif de_type == "7_pipe":
                    h = de[2]
                    base[height - h - 1][x] = "T"
                    for y in range(height - h, height):
                        base[y][x] = "|"
                elif de_type == "0_hole":
                    w = de[2]
                    for x2 in range(w):
                        base[height - 1][clip(1, x + x2, width - 2)] = "-"
                elif de_type == "6_stairs":
                    h = de[2]
                    dx = de[3]  # -1 or 1
                    for x2 in range(1, h + 1):
                        for y in range(x2 if dx == 1 else h - x2):
                            base[clip(0, height - y - 1, height - 1)][clip(1, x + x2, width - 2)] = "X"
                elif de_type == "1_platform":
                    w = de[2]
                    h = de[3]
                    madeof = de[4]  # from "?", "X", "B"
                    for x2 in range(w):
                        base[clip(0, height - h - 1, height - 1)][clip(1, x + x2, width - 2)] = madeof
                elif de_type == "2_enemy":
                    base[height - 2][x] = "E"
            self._level = base
        return self._level

    @classmethod
    def empty_individual(_cls):
        # STUDENT Maybe enhance this
        g = []
        return Individual_DE(g)

    @classmethod
    def random_individual(_cls):
        # STUDENT Maybe enhance this
        elt_count = random.randint(8, 128)
        g = [random.choice([
            (random.randint(1, width - 2), "0_hole", random.randint(1, 8)),
            (random.randint(1, width - 2), "1_platform", random.randint(1, 8), random.randint(0, height - 1), random.choice(["?", "X", "B"])),
            (random.randint(1, width - 2), "2_enemy"),
            (random.randint(1, width - 2), "3_coin", random.randint(0, height - 1)),
            (random.randint(1, width - 2), "4_block", random.randint(0, height - 1), random.choice([True, False])),
            (random.randint(1, width - 2), "5_qblock", random.randint(0, height - 1), random.choice([True, False])),
            (random.randint(1, width - 2), "6_stairs", random.randint(1, height - 4), random.choice([-1, 1])),
            (random.randint(1, width - 2), "7_pipe", random.randint(2, height - 4))
        ]) for i in range(elt_count)]
        return Individual_DE(g)


Individual = Individual_Grid


def generate_successors(population):
    results = []
    # print("POPULATION ", population)
    # creates children from population
    roulette = roulette_selection(population, int(len(population) * 0.99))
    results.extend(roulette)
    # print("roulette", roulette)
    # chooses top % of indiviudals in current pop to stay
    elite = elitist_selection(population, 0.01)
    results.extend(elite)
    # print("elitist", elite)

    # STUDENT Design and implement this
    # Hint: Call generate_children() on some individuals and fill up results.
    return results

# Selection Method for generate_successors
# Roulette Selection: Chooses based on probabilty of (individual fitness / total population fitness)
# Reference: https://cratecode.com/info/roulette-wheel-selection
def roulette_selection(population, size: int):
    # print(population)
    results = []
    total_fitness = sum(i.fitness() for i in population)
    
    # make cummulative probability distribution (to choose based on probability range)
    selection_probs = [i.fitness() / total_fitness for i in population]
    cumm_probs = []
    cumm_sum = 0
    for prob in selection_probs:
        cumm_sum += prob
        cumm_probs.append(cumm_sum)

    def select_parent():
        r = random.random() # random number between 0 and 1
        for i, p in enumerate(cumm_probs):
            if r <= p:
                return population[i]
            
    for i in range(size):
        parent1 = select_parent()
        parent2 = select_parent()
        # gene = random.randint(0, 1)
        # print("PARENTS ", parent1, parent2)
        child = parent1.generate_children(parent2)[0]
        # print("ROULETTE CHILD", child)
        results.append(child)

    return results

# Selection Method for generate_successors
# Elitist Selection: Chooses based on top fitness individuals and does not mutate them
# Reference: https://algorithmafternoon.com/genetic/elitist_genetic_algorithm/
'''
Parameters: 
    elite_percent (what percent of population is chosen to stay)
'''
def elitist_selection(population, elite_percent: float):
    if not (0 < elite_percent <= 1):
        raise ValueError("elite_percent must be between 0 and 1")
    results = []
    pop_limit = len(population)
    
    sorted_population = sorted(population, key=Individual.fitness, reverse=True)
    
    # keeps the best fitness individuals
    elite_count = max(1, int(pop_limit * elite_percent))
    results.extend(sorted_population[:elite_count])
    # for e in results:
    #     print("ELITE", e)
    
    return results

def ga():
    # Full path to Unity project's level file
    level_path = "levels/last.txt"
    
    # Create levels directory if it doesn't exist
    if not os.path.exists("levels"):
        os.makedirs("levels")
        
    # STUDENT Feel free to play with this parameter
    pop_limit = 480
    # Code to parallelize some computations
    batches = os.cpu_count()
    if pop_limit % batches != 0:
        print("It's ideal if pop_limit divides evenly into " + str(batches) + " batches.")
    batch_size = int(math.ceil(pop_limit / batches))
    with mpool.Pool(processes=os.cpu_count()) as pool:
        init_time = time.time()
        # STUDENT (Optional) change population initialization
        population = [Individual.random_individual() if random.random() < 0.9
                      else Individual.empty_individual()
                      for _g in range(pop_limit)]
        # But leave this line alone; we have to reassign to population because we get a new population that has more cached stuff in it.
        population = pool.map(Individual.calculate_fitness,
                              population,
                              batch_size)
        init_done = time.time()
        print("Created and calculated initial population statistics in:", init_done - init_time, "seconds")
        generation = 0
        start = time.time()
        now = start
        print("Use ctrl-c to terminate this loop manually.")
        try:
            while True:
                now = time.time()
                # Print out statistics
                best = max(population, key=Individual.fitness)
                print("Generation:", str(generation))
                print("Max fitness:", str(best.fitness()))
                print("Average generation time:", (now - start) / generation if generation > 0 else 0)
                print("Net time:", now - start)
                
                # Randomly select a level from top 25% of population
                sorted_population = sorted(population, key=Individual.fitness, reverse=True)
                top_quarter = sorted_population[:len(sorted_population)//4]
                selected_level = random.choice(top_quarter)
                
                # Write directly to Unity project path
                try:
                    with open(level_path, 'w') as f:
                        level_data = selected_level.to_level()
                        for row in level_data:
                            f.write("".join(row) + "\n")
                    print(f"Wrote level to {level_path}")
                except Exception as e:
                    print(f"Error writing to {level_path}: {e}")
                
                generation += 1
                # STUDENT Determine stopping condition
                stop_condition = False
                if stop_condition:
                    break
                
                # STUDENT Also consider using FI-2POP as in the Sorenson & Pasquier paper
                gentime = time.time()
                next_population = generate_successors(population)
                gendone = time.time()
                print("Generated successors in:", gendone - gentime, "seconds")
                
                # Calculate fitness in batches in parallel
                next_population = pool.map(Individual.calculate_fitness,
                                           next_population,
                                           batch_size)
                popdone = time.time()
                print("Calculated fitnesses in:", popdone - gendone, "seconds")
                population = next_population
                
        except KeyboardInterrupt:
            pass
    return population


if __name__ == "__main__":
    final_gen = sorted(ga(), key=Individual.fitness, reverse=True)
    best = final_gen[0]
    print("Best fitness: " + str(best.fitness()))
    now = time.strftime("%m_%d_%H_%M_%S")
    # STUDENT You can change this if you want to blast out the whole generation, or ten random samples, or...
    for k in range(0, 10):
        with open("levels/" + now + "_" + str(k) + ".txt", 'w') as f:
            for row in final_gen[k].to_level():
                f.write("".join(row) + "\n")
