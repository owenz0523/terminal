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

"""
There are some overlap
Upgrade priority is by placement priority (since turrets all have same HP, rather have an unupgraded turret take damage)
"""
left_corner_turret = [[4, 13], [3, 13], [2, 13]]
left_mid_turret = [[13, 13], [13,12], [6, 13], [5, 13]]
right_mid_turret = [[14, 13], [14, 12], [21, 13], [22, 13]]
right_corner_turret = [[23, 13], [24, 13], [25, 13]]


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

        return num

    def build_reinforced_defence(self, game_state):
        """
        run once, don't need to loop
        if enough time we can check enemy MP to determine if were safe
        """
        did_upgrade = True

        while(self.SP(game_state) > 2 and did_upgrade):
            did_upgrade = False
            left_corner = self.calc_block_defence(game_state, left_corner_turret)
            left_mid = self.calc_block_defence(game_state, left_mid_turret)
            right_mid = self.calc_block_defence(game_state, right_mid_turret)
            right_corner = self.calc_block_defence(game_state, right_corner_turret)

            defenses = [
                ('left_corner', left_corner),
                ('left_mid', left_mid),
                ('right_mid', right_mid),
                ('right_corner', right_corner)
            ]

            # Sort defenses by value (ascending order) so we always start with the lowest
            defenses.sort(key=lambda x: x[1])

            for key, _ in defenses:
                if key == 'left_corner':
                    if self.upgrade_defence(game_state, left_corner_turret) or self.build_defence(game_state, left_corner_turret):
                        did_upgrade[key] = True
                        break  # Exit the loop to restart after successful upgrade
                elif key == 'left_mid':
                    if self.upgrade_defence(game_state, left_mid_turret) or self.build_defence(game_state, left_mid_turret):
                        did_upgrade[key] = True
                        break  # Exit the loop to restart after successful upgrade
                elif key == 'right_mid':
                    if self.upgrade_defence(game_state, right_mid_turret) or self.build_defence(game_state, right_mid_turret):
                        did_upgrade[key] = True
                        break  # Exit the loop to restart after successful upgrade
                elif key == 'right_corner':
                    if self.upgrade_defence(game_state, right_corner_turret) or self.build_defence(game_state, right_corner_turret):
                        did_upgrade[key] = True
                        break  # Exit the loop to restart after successful upgrade
        
        

    def build_defence(self, game_state, turrets):
        """
        only places one turret
        """
        for turret in turrets:
            if game_state.attempt_spawn(TURRET, turret):
                break
        
    def upgrade_defence(self, game_state, turrets):
        for turret in turrets:
            if game_state.attempt_upgrade(turret):
                break


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

    def check_all_spawn_locations(self, game_state):
        locations = [[0, 13], [27, 13], [13, 0], [14, 0], [4, 9], [23, 9], [7, 6], [20, 6], [10, 3], [17,3]]
        return self.least_damage_spawn_location(game_state, locations)

    def place_turret_count(self, game_state):
        """
        returns how many turrets we can place
        [normal, upgraded from scratch, upgraded]
        """
        current_SP = self.SP(game_state)
        return {
            "place": current_SP//3,
            "upgrade": current_SP//5,
            "full": current_SP//8
        }

    def is_upgraded(self, game_state, turret):
        for unit in game_state.game_map[turret[0], turret[1]]:
            if unit.stationary and unit.upgraded:
                return True
        return False
    
    def get_turret_health_percentage(self, game_state, turret):
        for unit in game_state.game_map[turret[0], turret[1]]:
            if unit.stationary:
                return unit.health / unit.max_health

    def calc_block_defence(self, game_state, turrets):
        defense_point = 0
        for turret in turrets:
            turret_point = 0
            if game_state.contains_stationary_unit(turret):
                turret_point = 6
                turret_health = self.get_turret_health_percentage(game_state, turret)
                if self.is_upgraded(game_state, turret):
                    turret_point = 14
                defense_point += turret_health * turret_point
        
        return defense_point



if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()


"""
goal of defense, we want to score the defense, check how much SP and spread it out
"""