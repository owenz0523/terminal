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

first_turret = [[4, 13], [3, 13], [2, 13], [5, 13], [6, 13]]
first_upgrade_turret = [[2, 13], [3, 13], [4, 13], [6, 13], [5, 13]]

second_turret = [[13, 13], [14, 13], [13,12], [14, 12]]

third_turret = [[23, 13], [24, 13], [25, 13], [22, 13], [21, 13]] 
third_upgrade_turret = [[25, 13], [24, 13], [23, 13], [21, 13], [22, 13]]


class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write('Random seed: {}'.format(seed))
        self.left_turrets = [0]
        self.left_middle_turrets = [0]
        self.right_middle_turrets = [0]
        self.right_turrets = [0]

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
    
    def opponent_SP(self, game_state):
        return game_state.get_resource(SP, 1)

    def opponent_MP(self, game_state):
        return game_state.get_resource(MP, 1)

    def health(self, game_state):
        return game_state.my_health
    
    def opponent_health(self, game_state):
        return game_state.enemy_health

    def num_turrets(self, game_state, turrets):
        num = 0
        for turret in turrets:
            if game_state.contains_stationary_unit(turret):
                num += 1

        return num

    def where_to_upgrade(self, game_state):
        """
        Our defense is made up of four places, (2 corners and 2 middles)
        but we need to know which side to upgrade on
        [1, 2, 3, 4] for each four places
        left = 0
        right = 1
        so return value will be: [1, 1] for first place right side
        """

        left = self.num_turrets(game_state, first_turret)
        mid = self.num_turrets(game_state, second_turret)
        right = self.num_turrets(game_state, third_turret)

        if (mid < left and mid < right):
            self.build_next_defence(game_state, second_turret, second_turret)
        elif (left < right):
            self.build_next_defence(game_state, first_turret, first_upgrade_turret)
        else:
            self.build_next_defence(game_state, third_turret, third_upgrade_turret)
        

    def build_next_defence(self, game_state, turrets, upgrade):
        """
        only places one turret + upgrade and wall + upgrade (in that priority)
        """
        for turret in turrets:
            if game_state.attempt_spawn(TURRET, turret):
                break
        for turret in upgrade:
            game_state.attempt_upgrade(turret)
        
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

    # 0 = left, 1 = left middle, 2 = right middle, 3 = right
    # 0 = quick, 1 = medium, 2 = heavy
    def launch_attack(self, game_state):
        self.track_turrets(game_state)

        mp = self.MP(game_state)
        opponentSP = self.opponent_SP(game_state)
        opponentMP = self.opponent_MP(game_state)

        health = self.health(game_state)
        opponent_health = self.opponent_health(game_state)

        turrets = [self.left_turrets, self.left_middle_turrets, self.right_middle_turrets, self.right_turrets]

        if opponent_health < mp * 0.75 and health > opponentMP:
            self.all_out_attack(game_state, mp)

        for i, turret_block in enumerate(turrets):
            if sum(turret_block) <= 1.25 and (i == 0 or i == 3) and opponentSP < 10 and mp >= 5:
                self.attack(game_state, i, mp)
                return
        
        for i, turret_block in enumerate(turrets):
            if sum(turret_block) <= 5 and mp >= 10:
                self.attack(game_state, i, mp) 
                return

        for i, turret_block in enumerate(turrets):
            if mp >= 15:
                    self.attack(game_state, i, mp)

    def is_upgraded(self, game_state, turret):
        for unit in game_state.game_map[turret[0], turret[1]]:
            if unit.stationary and unit.upgraded:
                return 1
        return 0
                
    def track_turrets(self, game_state):
        self.left_turrets = [0]
        self.left_middle_turrets = [0]
        self.right_middle_turrets = [0]
        self.right_turrets = [0]
        for location in game_state.game_map:
            if game_state.contains_stationary_unit(location):
                for unit in game_state.game_map[location]:
                    if unit.player_index == 1 and unit.unit_type[0] == "D":
                        point = unit.health / unit.max_health + self.is_upgraded(game_state, location)
                        gamelib.debug_write(point)
                        if location[0] < 7:
                            self.left_turrets.append(point)
                        elif location[0] < 14:
                            self.left_middle_turrets.append(point)
                        elif location[0] < 21:
                            self.right_middle_turrets.append(point)
                        else:
                            self.right_turrets.append(point)


    def attack(self, game_state, location, mp):
        if mp >= 5 and self.SP(game_state) >= 4:
            if location == 0:
                if game_state.attempt_spawn(SCOUT, [0, 13], int(mp)):
                    if game_state.attempt_spawn(SUPPORT, [1, 12]):
                        game_state.attempt_remove([1,12])
            elif location == 1:
                if game_state.attempt_spawn(SCOUT, [7, 6], int(mp)):
                    if game_state.attempt_spawn(SUPPORT, [8, 5]):
                        game_state.attempt_remove([8, 5])
            elif location == 2:
                if game_state.attempt_spawn(SCOUT, [20, 6], int(mp)):
                    if game_state.attempt_spawn(SUPPORT, [19, 5]):
                        game_state.attempt_remove([19, 5])
            else:
                if game_state.attempt_spawn(SCOUT, [27, 13], int(mp)):
                    if game_state.attempt_spawn(SUPPORT, [26, 12]):
                        game_state.attempt_remove([26, 12])

    def all_out_attack(self, game_state, mp):
        for location in game_state.game_map:
            if game_state.contains_stationary_unit(location):
                for unit in game_state.game_map[location]:
                    if unit.player_index == 0:
                        game_state.attempt_remove(location)

        game_state.attempt_spawn(SCOUT, [14, 0], int(mp))
        support_startX = 13
        support_startY = 1
        for i in range(13):
            game_state.attempt_spawn(SUPPORT, [support_startX + i, support_startY + i], 1)

    def on_action_frame(self, turn_string):
        """
        This is the action frame of the game. This function could be called 
        hundreds of times per turn and could slow the algo down so avoid putting slow code here.
        Processing the action frames is complicated so we only suggest it if you have time and experience.
        Full doc on format of a game frame at in json-docs.html in the root of the Starterkit.
        """
        # # Let's record at what position we get scored on
        # state = json.loads(turn_string)
        # events = state["events"]
        # breaches = events["breach"]
        # for breach in breaches:
        #     location = breach[0]
        #     unit_owner_self = True if breach[4] == 1 else False
        #     # When parsing the frame data directly, 
        #     # 1 is integer for yourself, 2 is opponent (StarterKit code uses 0, 1 as player_index instead)
        #     if not unit_owner_self:
        #         gamelib.debug_write("Got scored on at: {}".format(location))
        #         self.scored_on_locations.append(location)
        #         gamelib.debug_write("All locations: {}".format(self.scored_on_locations))

if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()