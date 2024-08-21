import gamelib
import random
import math
import warnings
from sys import maxsize
import json
from sklearn.ensemble import RandomForestClassifier
import numpy as np
from collections import deque

class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write('Random seed: {}'.format(seed))
        self.turn_number = 0
        self.myMP= 0
        self.opponentMP = 0
        self.mySP = 0
        self.opponentSP = 0
        self.myHealth = 0
        self.opponentHealth = 0
        self.random_forest = RandomForestClassifier(n_estimators=100)
        self.attacked_locations = []
        self.game_state_history = []
        self.opponent_move_history = []
        self.attack_flag = False # determines if attack happens

        # board with 1 = wall, 2 = turret, 3 = structure, add 3 if its an enemy structure
        self.structure_board = np.zeros((28, 28), dtype=np.int8)

        # (x, y) => (unit_health, is_unit_upgraded)
        self.board_dict = {}

    def on_game_start(self, config):
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
        game_state = gamelib.GameState(self.config, turn_state)
        game_state.suppress_warnings(True)
        self.turn_number += 1

        if self.turn_number <= 5:
            self.early_game_strategy(game_state)
        else:
            self.dynamic_defense_strategy(game_state)
            self.aggressive_offense_strategy(game_state)
    
        self.update_opponent_move_history(game_state)
        self.update_game_state(game_state)
        
        game_state.submit_turn()

    # first defend short corners with turrets and walls, then add upgraded structures, then push on turn 5 with demolishers
    def early_game_strategy(self, game_state):
        # hard code this
        if self.turn_number == 1:
            pass
        elif self.turn_number == 2:
            pass
        elif self.turn_number == 3:
            pass
        elif self.turn_number == 4:
            pass
        else:
            pass

    # update the board and dictionary with the new game state
    def update_game_state(self, game_state):
        for location in game_state.game_map:
            if game_state.contains_stationary_unit(location):
                for unit in game_state.game_map[location]:
                    if unit.unit_type == "F":
                        self.structure_board[location[0], location[1]] = 1
                    elif unit.unit_type == "E":
                        self.structure_board[location[0], location[1]] = 2
                    elif unit.unit_type == "D":
                        self.structure_board[location[0], location[1]] = 3
                    if unit.player_index == 1:
                        self.structure_board += 3
                    self.board_dict[location] = [unit.player_index, unit.unit_type, unit.health, unit.upgraded]

        self.myHealth = game_state.my_health
        self.opponentHealth = game_state.enemy_health
        self.mySP, self.myMP = game_state.get_resources(0)
        self.opponentSP, self.opponentMP = game_state.get_resources(1)
        self.game_state_history.append(game_state)
    
    # defense strategy
    def dynamic_defense_strategy(self, game_state):
        defend_needed = []
        self.update_attacked_locations(game_state)
        self.defend_attacked_locations(game_state, defend_needed)
        self.defend_vulnerable_locations(game_state, defend_needed)
        self.predict_opponent_moves(game_state)
        self.defend_likely_moves(game_state, defend_needed)

    # check attacked locations - use github code from other guy
    def update_attacked_locations(self, game_state):
        pass

    # check scored locations - use template code
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
            else:
                gamelib.debug_write("Opponent got scored on at: {}".format(location))
                self.scored_locations.append(location)
                gamelib.debug_write("All locations: {}".format(self.scored_locations))

        # keep track of opponent moves
        spawns = events["spawn"]
        for spawn in spawns:
            if spawn[3] == 2:
                location = spawn[0]
                unit_type = spawn[1]
                self.opponent_move_history.append([location, unit_type])

    # defend attacked locations - return list of locations to defend structures that have been attacked
    def defend_attacked_locations(self, game_state, defend_needed):
        pass

    # defend scored locations - return list of locations that have been scored on or have a direct path
    def defend_vulnerable_locations(self, game_state, defend_needed):
        pass

    # predict opponent moves - use random forest
    def predict_opponent_moves(self, game_state):
        pass

    # based on what the opponent is likely to do, create an algo to prioritize where to defend either by upgrading or deploying more structures - also consider creating a funnel 
    def defend_likely_moves(self, game_state, defend_needed):
        pass

    # attack strategy
    def aggressive_offense_strategy(self, game_state):
        if self.turn_number < 15:
            self.monte_carlo_search_tree(game_state)
        else:
            self.minimax(game_state)

    # implement monte carlo search tree with an emphasis on attacking short corners or weak points with demolishers in one major push
    def monte_carlo_search_tree(game_state):
        pass
    
    # implement minimax with an emphasis on attacking short corners or weak points with demolishers in one major push
    def minimax(game_state):
        pass

if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
