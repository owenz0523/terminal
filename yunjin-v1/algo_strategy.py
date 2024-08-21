import gamelib
import random
import math
import warnings
from sys import maxsize
import json


"""
Most of the algo code you write will be in this file unless you create new
modules yourself. Start by modifying the 'on_turn' function.

Advanced strategy tips: 

  - You can analyze action frames by modifying on_action_frame function

  - The GameState.map object can be manually manipulated to create hypothetical 
  board states. Though, we recommended making a copy of the map to preserve 
  the actual current map state.
"""

wall_axis = 13
turret_axis = 12

#layout is sorted by priority

first_turret = [
    [[4, 13], [3, 13], [2, 13]], #left
    [[4, 13], [5, 13], [6, 13]] #right
]

second_turret = [
    [[13, 13], [13,12], [6, 13]], #left
    [[14, 13], [14, 12], [21, 13]] #right
]

third_turret = [
    [[23, 13], [22, 13], [21, 13]],  # left
    [[23, 13], [24, 13], [25, 13]]   # right
]


class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write('Random seed: {}'.format(seed))

    def on_game_start(self, config):
        """ 
        Read in config and perform any initial setup here 
        """
        gamelib.debug_write('Configuring your custom algo strategy...')
        self.config = config
        global WALL, SUPPORT, TURRET, SCOUT, DEMOLISHER, INTERCEPTOR, MP, SP
        WALL = config["unitInformation"][0]["shorthand"]
        SUPPORT = config["unitInformation"][1]["shorthand"]
        TURRET = config["unitInformation"][2]["shorthand"]
        SCOUT = config["unitInformation"][3]["shorthand"]
        DEMOLISHER = config["unitInformation"][4]["shorthand"]
        INTERCEPTOR = config["unitInformation"][5]["shorthand"]
        MP = 1
        SP = 0
        self.scored_on_locations = []
        self.scored_locations = []

    def on_turn(self, turn_state):
        """
        This function is called every turn with the game state wrapper as
        an argument. The wrapper stores the state of the arena and has methods
        for querying its state, allocating your current resources as planned
        unit deployments, and transmitting your intended deployments to the
        game engine.
        """
        game_state = gamelib.GameState(self.config, turn_state)
        gamelib.debug_write('Performing turn {} of your custom algo strategy'.format(game_state.turn_number))
        #game_state.suppress_warnings(True)  #Comment or remove this line to enable warnings.
        self.sakura_strategy(game_state)

        game_state.submit_turn()


    def sakura_strategy(self, game_state):
        """
        We implement a three-step strategy.
        1. Build opening defences (four turret locations with upgraded walls)
        2. Save up for a launched attack either on the left or right short corner
        3. Check whether our foundation needs to be upgraded or replaced
        4. Upgrade our defenses on Rank 12/13 with any leftover SP
        """

        # First, place basic defenses
        if game_state.turn_number == 0:
            self.build_opening_defence(game_state)
        
        # Launch attack, or check for its feasibility
        self.launch_attack(game_state)
        
        # Reinforce defences once we've tried to attack
        self.build_reinforced_defence(game_state)

    def build_opening_defence(self, game_state):
        """
        Build basic defenses using hardcoded locations.
        Remember to defend corners and avoid placing units in the front where enemy demolishers can attack them.
        """
        # Useful tool for setting up your base locations: https://www.kevinbai.design/terminal-map-maker
        # More community tools available at: https://terminal.c1games.com/rules#Download

        # Place turrets that attack enemy units
        turret_locations = [[4, 13], [5, 13], [13, 13], [22, 13], [23, 13]]
        
        # Spawn and upgrade turrets, using up all money from Round 1
        for location in turret_locations:
            game_state.attempt_spawn(TURRET, location)
            game_state.attempt_upgrade(location)
    

    def SP(self, game_state):
        return game_state.get_resource(SP)
    
    def MP(self, game_state):
        return game_state.get_resource(MP)

    def launch_attack(self, game_state):
        """
        We should always prioritize attack over defense. 
        Thus, we first try spending structure points on a (deleted) support to "support" our rush with Scouts
        """
        # Determine Scout spawn location
        scout_location = self.check_all_spawn_locations(game_state)
        left = scout_location[0] + scout_location[1] < 14
        if left:
            if scout_location[1] == 0:
                support_location = [scout_location[0], 1]
            elif scout_location[1] == 13:
                support_location = [scout_location[0] + 1, scout_location[1]]
            elif not game_state.contains_stationary_unit([scout_location[0] + 2, scout_location[1]]):
                support_location = [scout_location[0] + 2, scout_location[1]]
            else:
                support_location = [scout_location[0] + 1, scout_location[1] - 1]
        else:
            if scout_location[1] == 0:
                support_location = [scout_location[0], 1]
            elif scout_location[1] == 13:
                support_location = [scout_location[0] - 1, scout_location[1]]
            elif not game_state.contains_stationary_unit([scout_location[0] - 2, scout_location[1]]):
                support_location = [scout_location[0] - 2, scout_location[1]]
            else:
                support_location = [scout_location[0] - 1, scout_location[1] - 1]

        # # panic feature
        # opponent_mp = game_state.get_resource(MP, 1)
        # if opponent_mp >= 1.5 * game_state.my_health:
        #     # launch aggressive attack
        #     if self.SP(game_state) >= 4 and self.MP(game_state) >= 10:
        #         if game_state.attempt_spawn(SUPPORT, support_location):
        #             if game_state.attempt_spawn(SCOUT, scout_location, int(self.MP(game_state))):  # Use up all the MP we have, truncating MP to the closest integer
        #                 game_state.attempt_remove(support_location)
        #     return

        # Check if we have enough Structure Points and Mobile Points to launch attacks
        # 4 SP is enough to spawn a Support, which shields our 10 Scouts
        if game_state.turn_number < 10:
            if self.SP(game_state) >= 4 and self.MP(game_state) >= 10:
                if game_state.attempt_spawn(SUPPORT, support_location):
                    if game_state.attempt_spawn(SCOUT, scout_location, int(self.MP(game_state))): # Use up all the MP we have, truncating MP to the closest integer
                        game_state.attempt_remove(support_location)
        elif game_state.turn_number < 20:
            if self.SP(game_state) >= 4 and self.MP(game_state) >= 15:
                if game_state.attempt_spawn(SUPPORT, support_location):
                    if game_state.attempt_spawn(SCOUT, scout_location, int(self.MP(game_state))): # Use up all the MP we have, truncating MP to the closest integer
                        game_state.attempt_remove(support_location)
        else:
            if self.SP(game_state) >= 4 and self.MP(game_state) >= 20:
                if game_state.attempt_spawn(SUPPORT, support_location):
                    if game_state.attempt_spawn(SCOUT, scout_location, int(self.MP(game_state))): # Use up all the MP we have, truncating MP to the closest integer
                        game_state.attempt_remove(support_location)

    def num_turrets(self, game_state, turrets):
        num = 0
        for turret in turrets:
            if game_state.contains_stationary_unit(turret):
                num += 1

    def where_to_upgrade(self, game_state):
        """
        Our defense is made up of four places, (2 corners and 2 middles)
        but we need to know which side to upgrade on
        [1, 2, 3, 4] for each four places
        left = 0
        right = 1
        so return value will be: [1, 1] for first place right side
        """
        first_left = self.num_turrets(game_state, first_turret[0])
        first_right = self.num_turrets(game_state, first_turret[1])
        second_left = self.num_turrets(game_state, second_turret[0])
        second_right = self.num_turrets(game_state, second_turret[1])
        third_left = self.num_turrets(game_state, third_turret[0])
        third_right = self.num_turrets(game_state, third_turret[1])

        left = first_left + first_right
        mid = second_left + second_right
        right = third_left + third_right

        if (mid < left and mid < right):
            #build middle
            if (second_left < second_right):
                #add on left side
                self.build_next_defence(game_state, second_turret[0])
                self.upgrade_defence(game_state, second_turret[1])
            else:
                #add on right side
                self.build_next_defence(game_state, second_turret[1])
                self.upgrade_defence(game_state, second_turret[0])
        elif (left < right):
            if (first_left < first_right):
                #add on left side
                self.build_next_defence(game_state, first_turret[0])
                self.upgrade_defence(game_state, first_turret[1])
            else:
                #add on right side
                self.build_next_defence(game_state, first_turret[1])
                self.upgrade_defence(game_state, first_turret[0])
        else:
            if (second_left < second_right):
                #add on left side
                self.build_next_defence(game_state, second_turret[0])
                self.upgrade_defence(game_state, second_turret[1])
            else:
                #add on right side
                self.build_next_defence(game_state, second_turret[1])
                self.upgrade_defence(game_state, second_turret[0])
        

    def build_next_defence(self, game_state, turrets):
        """
        only places one turret + upgrade and wall + upgrade (in that priority)
        """
        for turret in turrets:
            game_state.attempt_upgrade(turret)
            if game_state.attempt_spawn(TURRET, turret):
                game_state.attempt_upgrade(turret)
                break
        
    def upgrade_defence(self, game_state, turrets):
        for turret in turrets:
            game_state.attempt_upgrade(turret)
            
    def build_reinforced_defence(self, game_state):
        """
        We build reinforced defenses once we've attacked
        Priority queue:
        1. Build/Upgrade foundation walls/turrets
        2. Upgrade walls
        2. Place down and upgrade turrets (turrets are not placed down if we cannot afford this)
        3. Place down walls (which can only be placed if there is a turret behind it)
        """
        
        limit = 6

        while self.SP(game_state) > 1 and limit > 0:
            limit += -1
            self.where_to_upgrade(game_state)


    def least_damage_spawn_location(self, game_state, location_options):
        """
        This function will help us guess which location is the safest to spawn moving units from.
        It gets the path the unit will take then checks locations on that path to 
        estimate the path's damage risk.
        """
        damages = []
        # Get the damage estimate each path will take
        for location in location_options:
            path = game_state.find_path_to_edge(location)
            damage = 0
            for path_location in path:
                # Get number of enemy turrets that can attack each location and multiply by turret damage
                damage += len(game_state.get_attackers(path_location, 0)) * gamelib.GameUnit(TURRET, game_state.config).damage_i
            damages.append(damage)
        
        # Now just return the location that takes the least damage
        return location_options[damages.index(min(damages))]

    def next_anticipated_attack(self, game_state):
        """
        Finds the weakest points in our defense
        can run this function up to 3 times
        """
        location_options = [[13, 27], [14, 27], [8, 22], [19, 22], [5, 19], [22, 19], [0, 14], [27, 14]]
        paths = []
        damages = []
        # Get the damage estimate each path will take
        for location in location_options:
            path = game_state.find_path_to_edge(location)
            if path is None:
                continue  # Skip this location if no valid path is found
            paths.append(path)
            damage = 0
            for path_location in path:
                # Get number of enemy turrets that can attack each location and multiply by turret damage
                damage += len(game_state.get_attackers(path_location, 1)) * gamelib.GameUnit(TURRET, game_state.config).damage_i
            damages.append(damage)
        
        # Now just return the location that takes the max damage
        return paths[damages.index(min(damages))][-1]

    def check_all_spawn_locations(self, game_state):
        locations = [[0, 13], [27, 13], [13, 0], [14, 0]]
        return self.least_damage_spawn_location(game_state, locations)

    def on_action_frame(self, turn_string):
        """
        This is the action frame of the game. This function could be called 
        hundreds of times per turn and could slow the algo down so avoid putting slow code here.
        Processing the action frames is complicated so we only suggest it if you have time and experience.
        Full doc on format of a game frame at in json-docs.html in the root of the Starterkit.
        """
        # Let's record at what position we get scored on
        state = json.loads(turn_string)
        events = state["events"]
        breaches = events["breach"]
        for breach in breaches:
            location = breach[0]
            unit_owner_self = True if breach[4] == 1 else False
            # When parsing the frame data directly, 
            # 1 is integer for yourself, 2 is opponent (StarterKit code uses 0, 1 as player_index instead)
            if not unit_owner_self:
                gamelib.debug_write("Got scored on at: {}".format(location))
                self.scored_on_locations.append(location)
                gamelib.debug_write("All locations: {}".format(self.scored_on_locations))

if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()