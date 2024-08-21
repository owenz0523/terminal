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


#Order by priority in array
foundation_turret_locations = [[4, 12], [10, 12], [17, 12], [23, 12]]
foundation_wall_locations = [[4, 13], [10, 13], [17, 13], [23, 13]]
secondary_wall_locations = [[3, 13], [24, 13], [11, 13], [16, 13]]
secondary_turret_locations = [[3, 12], [24, 12], [11, 12], [16, 12]]

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
        self.eunchae_strategy(game_state)

        game_state.submit_turn()


    def eunchae_strategy(self, game_state):
        """
        We implement a three-step strategy.
        1. Build opening defences (four turret locations with upgraded walls)
        2. Save up for a launched attack either on the left or right short corner
        3. Check whether our foundation needs to be upgraded or replaced
        4. Upgrade our defenses on Rank 12/13 with any leftover SP
        """

        # First, place basic defenses
        if game_state.turn_number == 1:
            self.build_opening_defence(game_state)
        
        # Launch attack, or check for its feasibility
        self.launch_attack(game_state)
        
        # Reinforce defences once we've tried to attack
        self.build_reinforced_defence(game_state)
        
        
        # Now build reactive defenses based on where the enemy scored
        # self.build_reactive_defense(game_state)

        # # If the turn is less than 5, stall with interceptors and wait to see enemy's base
        # if game_state.turn_number < 5:
        #     self.stall_with_interceptors(game_state)
        # else:
        #     # Now let's analyze the enemy base to see where their defenses are concentrated.
        #     # If they have many units in the front we can build a line for our demolishers to attack them at long range.
        #     if self.detect_enemy_unit(game_state, unit_type=None, valid_x=None, valid_y=[14, 15]) > 10:
        #         self.demolisher_line_strategy(game_state)
        #     else:
        #         # They don't have many units in the front so lets figure out their least defended area and send Scouts there.

        #         # Only spawn Scouts every other turn
        #         # Sending more at once is better since attacks can only hit a single scout at a time
        #         if game_state.turn_number % 2 == 1:
        #             # To simplify we will just check sending them from back left and right
        #             scout_spawn_location_options = [[13, 0], [14, 0]]
        #             best_location = self.least_damage_spawn_location(game_state, scout_spawn_location_options)
        #             game_state.attempt_spawn(SCOUT, best_location, 1000)

        #         # Lastly, if we have spare SP, let's build some supports
        #         support_locations = [[13, 2], [14, 2], [13, 3], [14, 3]]
        #         game_state.attempt_spawn(SUPPORT, support_locations)

    def build_opening_defence(self, game_state):
        """
        Build basic defenses using hardcoded locations.
        Remember to defend corners and avoid placing units in the front where enemy demolishers can attack them.
        """
        # Useful tool for setting up your base locations: https://www.kevinbai.design/terminal-map-maker
        # More community tools available at: https://terminal.c1games.com/rules#Download

        # Place turrets that attack enemy units
        turret_locations = [[4, 12], [10, 12], [17, 12], [23, 12]]
        
        # Spawn and upgrade turrets, using up all money from Round 1
        for location in turret_locations:
            game_state.attempt_spawn(TURRET, location)
            game_state.attempt_upgrade(location)
        
        # Place walls in front of turrets to soak up damage for them
        wall_locations = [[4, 13], [10, 13], [17, 13], [23, 13]]
        for location in wall_locations:
            game_state.attempt_spawn(WALL, location)
           
        # This concludes the building of our "foundation"
    
    def is_foundation_up(self, game_state):
        """
        If no foundation is broken, it will return None
        If yes, then it will return the coordinates of all broken walls and turrets
        """
        broken_walls = []
        broken_turrets = []
        for wall in foundation_wall_locations:
            if not game_state.contains_stationary_unit(wall):
                broken_walls.append(wall)
        
        for turret in foundation_turret_locations:
            if not game_state.contains_stationary_unit(turret):
                broken_turrets.append(turret)
        
        return {
            "walls": broken_walls,
            "turrets": broken_turrets,
        } if len(broken_turrets) and len(broken_walls) else None

    def SP(self, game_state):
        return game_state.get_resource(SP)
    
    def MP(self, game_state):
        return game_state.get_resource(MP)
        
    def upgrade_build_foundation(self, game_state):
        broken_foundation = self.is_foundation_up(game_state)
        if broken_foundation:
            for turret in broken_foundation["turrets"]:
                if not game_state.attempt_spawn(TURRET, turret):
                    break
            for turret in broken_foundation["turrets"]:
                if not game_state.attempt_upgrade(turret):
                    break
                
            for wall in broken_foundation["walls"]:
                if not game_state.attempt_spawn(WALL, wall):
                    break

            for wall in broken_foundation["walls"]:
                if not game_state.attempt_upgrade(wall):
                    break

    def launch_attack(self, game_state):
        """
        We should always prioritize attack over defense. 
        Thus, we first try spending structure points on a (deleted) support to "support" our rush with Scouts
        """
        
        # We will, in the future, base support spawn locations on our opponent's defenses
        # For now, we will randomise to either one of the corners:
        possible_support_locations = [[14, 2], [13, 2]]
        support_location = random.choice(possible_support_locations)
       
        # Determine Scout spawn location
        if support_location == [14, 2]:
            scout_location = [13, 0]
        elif support_location == [13, 2]:
            scout_location = [14, 0]
        
        # Check if we have enough Structure Points and Mobile Points to launch attacks
        # 4 SP is enough to spawn a Support, which shields our 10 Scouts
        if self.SP(game_state) >= 4 and self.MP(game_state) >= 10:
            game_state.attempt_spawn(SUPPORT, support_location)
            game_state.attempt_spawn(SCOUT, scout_location, int(self.MP(game_state))) # Use up all the MP we have, truncating MP to the closest integer
            game_state.attempt_remove(support_location)
            
    def build_reinforced_defence(self, game_state):
        """
        We build reinforced defenses once we've attacked
        Priority queue:
        1. Build/Upgrade foundation walls/turrets
        2. Upgrade walls
        2. Place down and upgrade turrets (turrets are not placed down if we cannot afford this)
        3. Place down walls (which can only be placed if there is a turret behind it)
        """

        # Build/upgrade any foundation walls/turrets
        self.upgrade_build_foundation(game_state)

        # Define potential turret and wall locations
        possible_turret_locations = [[x, 12] for x in range(3, 25) if [x, 12] not in foundation_turret_locations]
        possible_wall_locations = [[x, 13] for x in range(3, 25) if [x, 13] not in foundation_wall_locations]

        random.shuffle(possible_turret_locations)
        random.shuffle(possible_wall_locations)

        # Upgrade as many existing walls as possible
        for wall_location in possible_wall_locations:
            if game_state.contains_stationary_unit(wall_location): 
                if self.SP(game_state) >= 2:
                    game_state.attempt_upgrade(wall_location) 

        # Next, build and upgrade as many turrets as possible 
        for turret_location in possible_turret_locations:
            if not game_state.contains_stationary_unit(turret_location):
                if game_state.get_resource(SP) >= 8:
                    game_state.attempt_spawn(TURRET, turret_location)
                    game_state.attempt_upgrade(turret_location)

        # Next, build as many walls as possible
        for wall_location in possible_wall_locations:
            turret_location = [wall_location[0], wall_location[1] - 1]  
            if game_state.contains_stationary_unit(turret_location):
                if not game_state.contains_stationary_unit(wall_location): 
                    if game_state.get_resource(SP) >= 2:
                        game_state.attempt_spawn(WALL, wall_location)  
        

    # def build_reactive_defense(self, game_state):
    #     """
    #     This function builds reactive defenses based on where the enemy scored on us from.
    #     We can track where the opponent scored by looking at events in action frames 
    #     as shown in the on_action_frame function
    #     """
    #     for location in self.scored_on_locations:
    #         # Build turret one space above so that it doesn't block our own edge spawn locations
    #         build_location = [location[0], location[1]+1]
    #         game_state.attempt_spawn(TURRET, build_location)

    # def stall_with_interceptors(self, game_state):
    #     """
    #     Send out interceptors at random locations to defend our base from enemy moving units.
    #     """
    #     # We can spawn moving units on our edges so a list of all our edge locations
    #     friendly_edges = game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_LEFT) + game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_RIGHT)
        
    #     # Remove locations that are blocked by our own structures 
    #     # since we can't deploy units there.
    #     deploy_locations = self.filter_blocked_locations(friendly_edges, game_state)
        
    #     # While we have remaining MP to spend lets send out interceptors randomly.
    #     while game_state.get_resource(MP) >= game_state.type_cost(INTERCEPTOR)[MP] and len(deploy_locations) > 0:
    #         # Choose a random deploy location.
    #         deploy_index = random.randint(0, len(deploy_locations) - 1)
    #         deploy_location = deploy_locations[deploy_index]
            
    #         game_state.attempt_spawn(INTERCEPTOR, deploy_location)
    #         """
    #         We don't have to remove the location since multiple mobile 
    #         units can occupy the same space.
    #         """

    # def demolisher_line_strategy(self, game_state):
    #     """
    #     Build a line of the cheapest stationary unit so our demolisher can attack from long range.
    #     """
    #     # First let's figure out the cheapest unit
    #     # We could just check the game rules, but this demonstrates how to use the GameUnit class
    #     stationary_units = [WALL, TURRET, SUPPORT]
    #     cheapest_unit = WALL
    #     for unit in stationary_units:
    #         unit_class = gamelib.GameUnit(unit, game_state.config)
    #         if unit_class.cost[game_state.MP] < gamelib.GameUnit(cheapest_unit, game_state.config).cost[game_state.MP]:
    #             cheapest_unit = unit

    #     # Now let's build out a line of stationary units. This will prevent our demolisher from running into the enemy base.
    #     # Instead they will stay at the perfect distance to attack the front two rows of the enemy base.
    #     for x in range(27, 5, -1):
    #         game_state.attempt_spawn(cheapest_unit, [x, 11])

    #     # Now spawn demolishers next to the line
    #     # By asking attempt_spawn to spawn 1000 units, it will essentially spawn as many as we have resources for
    #     game_state.attempt_spawn(DEMOLISHER, [24, 10], 1000)

    # def least_damage_spawn_location(self, game_state, location_options):
    #     """
    #     This function will help us guess which location is the safest to spawn moving units from.
    #     It gets the path the unit will take then checks locations on that path to 
    #     estimate the path's damage risk.
    #     """
    #     damages = []
    #     # Get the damage estimate each path will take
    #     for location in location_options:
    #         path = game_state.find_path_to_edge(location)
    #         damage = 0
    #         for path_location in path:
    #             # Get number of enemy turrets that can attack each location and multiply by turret damage
    #             damage += len(game_state.get_attackers(path_location, 0)) * gamelib.GameUnit(TURRET, game_state.config).damage_i
    #         damages.append(damage)
        
    #     # Now just return the location that takes the least damage
    #     return location_options[damages.index(min(damages))]

    # def detect_enemy_unit(self, game_state, unit_type=None, valid_x = None, valid_y = None):
    #     total_units = 0
    #     for location in game_state.game_map:
    #         if game_state.contains_stationary_unit(location):
    #             for unit in game_state.game_map[location]:
    #                 if unit.player_index == 1 and (unit_type is None or unit.unit_type == unit_type) and (valid_x is None or location[0] in valid_x) and (valid_y is None or location[1] in valid_y):
    #                     total_units += 1
    #     return total_units
        
    # def filter_blocked_locations(self, locations, game_state):
    #     filtered = []
    #     for location in locations:
    #         if not game_state.contains_stationary_unit(location):
    #             filtered.append(location)
    #     return filtered

    # def on_action_frame(self, turn_string):
    #     """
    #     This is the action frame of the game. This function could be called 
    #     hundreds of times per turn and could slow the algo down so avoid putting slow code here.
    #     Processing the action frames is complicated so we only suggest it if you have time and experience.
    #     Full doc on format of a game frame at in json-docs.html in the root of the Starterkit.
    #     """
    #     # Let's record at what position we get scored on
    #     state = json.loads(turn_string)
    #     events = state["events"]
    #     breaches = events["breach"]
    #     for breach in breaches:
    #         location = breach[0]
    #         unit_owner_self = True if breach[4] == 1 else False
    #         # When parsing the frame data directly, 
    #         # 1 is integer for yourself, 2 is opponent (StarterKit code uses 0, 1 as player_index instead)
    #         if not unit_owner_self:
    #             gamelib.debug_write("Got scored on at: {}".format(location))
    #             self.scored_on_locations.append(location)
    #             gamelib.debug_write("All locations: {}".format(self.scored_on_locations))

if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
