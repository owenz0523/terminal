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
        self.opponent_points = 0
        self.random_forest = RandomForestClassifier(n_estimators=100)
        self.attacked_locations = {}
        self.scored_on_locations = []
        self.game_state_history = []
        self.opponent_move_history = []
        self.attack_flag = False # determines if attack happens

        # board with 0 = wall, 1 = turret, 2 = structure
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
    
    # keep track of opponents moves and their corresponding points remaining
    def update_opponent_move_history(self, game_state):
        # change self.opponent_points and self.opponent_move_history
        pass

    # update the board and dictionary with the new game state
    def update_game_state(self, game_state):
        pass
    
    # strategy
    def dynamic_defense_strategy(self, game_state):
        defend_needed = []
        self.update_attacked_locations(game_state)
        self.update_scored_on_locations(game_state)
        self.defend_attacked_locations(game_state)
        self.defend_vulnerable_locations(game_state)
        self.predict_opponent_moves(game_state)
        self.defend_likely_moves(game_state)

    # check attacked locations - use github code from other guy
    def update_attacked_locations(self, game_state):
        pass

    # check scored locations - use template code
    def update_scored_on_locations(self, game_state):
        pass

    # defend attacked locations - return list of locations to defend structures that have been attacked
    def defend_attacked_locations(self, game_state):
        pass

    # defend scored locations - return list of locations that have been scored on or have a direct path
    def defend_vulnerable_locations(self, game_state):
        pass

    # predict opponent moves - use random forest
    def predict_opponent_moves(self, game_state):
        pass

    # based on what the opponent is likely to do, create an algo to prioritize where to defend either by upgrading or deploying more structures - also consider creating a funnel 
    def defend_likely_moves(self, game_state):
        pass

if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
