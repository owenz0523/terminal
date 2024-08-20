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
        self.update_evaluation_board(game_state)
        
        game_state.submit_turn()

    def early_game_strategy(self, game_state):
        if self.turn_number == 1:
            
        

if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
