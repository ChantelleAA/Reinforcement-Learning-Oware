import numpy as np

class GameState:
    """
    Manages the state of the game, including tracking the current board, stores, territory counts,
    and the history of actions taken throughout the game.

    This class is essential for maintaining a record of the game's progress and status, allowing
    for state retrieval at any point, which is critical for both game logic and potential UI rendering
    or game replays.

    Attributes:
        B (Board): An instance of the Board class which represents the current state of the game board.
        total_games_played (int): The total number of games played during this session.
        games_won (np.ndarray): Array tracking the number of games won by each player.
        current_board_state (np.ndarray): Snapshot of the current state of the game board.
        current_store_state (np.ndarray): Snapshot of the current seeds stored by each player.
        current_territory_count (np.ndarray): Snapshot of the current territories held by each player.
        rounds_completed (int): The number of rounds completed in the current game.
        turns_completed (int): The number of turns completed in the current round.
        win_list (list): A list of players who have won each round.
        round_winner (int): The player who won the most recent round.
        current_player (int): The player who is currently taking their turn.
        other_player (int): The player who is not currently taking their turn.
        actions (np.ndarray): Array of possible actions players can take (typically pit indices).
        game_actions (list): A comprehensive list of all actions taken in the game.
        player_1_actions (list): A list of actions specifically taken by player 1.
        player_2_actions (list): A list of actions specifically taken by player 2.
        max_turns (int): The maximum allowed turns per game to prevent infinite loops.
        max_rounds (int): The maximum allowed rounds per game.
        game_states (np.ndarray): A matrix to store detailed game state after each turn for analysis or replay.

    Methods:
        __init__(board, max_turns=2000, max_rounds=7): Initializes a new game state with a reference to the game board.
        update_win_list(player): Adds the winning player of a round to the win list.
        possible_moves(player): Returns a list of possible moves for the specified player based on the current board state.
        save_actions(player, action): Records an action taken by a player for historical tracking.
        save_game_state(): Stores the detailed current state of the game in the game_states matrix for later retrieval or analysis.
    """

    def __init__(self, board, max_turns=2000, max_rounds=7):
        """
        Initializes the game state with a reference to the board and sets up initial tracking variables.

        Parameters:
            board (Board): The game board instance.
            max_turns (int): Maximum number of turns to prevent infinite game loops.
            max_rounds (int): Maximum number of rounds in a game session.
        """   
        self.B = board
        self.total_games_played = 0
        self.games_won = np.array([0, 0])
        self.current_board_state = self.B.board
        self.current_store_state = self.B.stores
        self.current_territory_count = self.B.territory_count
        self.rounds_completed = 0
        self.turns_completed = 0
        self.win_list = []
        self.round_winner = 0
        self.actions = np.arange(12)
        self.game_actions = []
        self.player_1_actions = []
        self.player_2_actions = []      
        self.max_turns = max_turns
        self.max_rounds = max_rounds
        self.game_state = []
        self.all_states = []
        self.all_states_np = np.zeros((16, 1))
        self.stores_list = []
        self.game_winner_list = []

    def update_win_list(self, player):
        if player == self.round_winner:
            self.win_list += [player]

    def possible_moves(self, player):
        player_id = player-1
        open_moves = []
        for i in self.actions:
            pit_index = self.B.action2pit(i)
            if pit_index in self.B.player_territories[player_id]:
                if self.B.board[pit_index] != 0 :
                    open_moves.append(i)
        return open_moves

    def save_actions(self, player, action):
        if player == 1:
            self.player_1_actions.append(action)
            self.game_actions.append(action)
        elif player == 2:
            self.player_2_actions.append(action)
            self.game_actions.append(action)

    def save_stores(self):
        self.stores_list.append(self.current_store_state)
        return self.stores_list
    
    def save_actions_stores(self, action):
        self.game_actions.append(action)
        actions_stores = self.game_actions + self.stores_list
        return actions_stores

    def save_game_state(self):
        """
        Saves the game state to the game_states matrix after each turn.
        Each row is padded or truncated to length 'k'.
        Each row format: [board state, store state, territory count, ...] for each round.
        """

        a = np.reshape(self.current_board_state, (2, -1))
        b = np.reshape(self.current_store_state, (2, 1))
        c = np.reshape(self.current_territory_count, (2, 1))

        current_state = np.hstack([a, b, c])

        self.game_state.append(current_state)

    def save_all_states(self):
        if np.sum(self.current_board_state)>0:
            a = np.reshape(self.current_board_state, (-1, 1))
            b = np.reshape(self.current_store_state, (-1, 1))
            c = np.reshape(self.current_territory_count, (-1, 1))

            current_state = np.concatenate([a, b, c])
            self.all_states_np = np.concatenate([self.all_states_np, current_state], axis=1)
            self.all_states.append(current_state)


    def game_winner(self):
        
        if self.current_territory_count[0] > self.current_territory_count[1]:
            winner = 1
        elif self.current_territory_count[0] < self.current_territory_count[1]:
            winner = 2
        else:
            winner = 0
        return winner

    def save_winner(self):
        winner = self.game_winner()
        self.game_winner_list.append(winner)


    def switch_player(self, current_player, other_player):
        current_player, other_player = other_player, current_player

    def distribute_seeds(self, action: int, current_player, other_player):
        """
        Distributes seeds from a selected pit and captures seeds according to the game rules.
        """
        pit_index = self.B.action2pit(action)
        seeds = int(self.B.board[pit_index])  # pick seeds from the selected pit
        self.B.board[pit_index] = 0  # empty the selected pit

        for _ in range(seeds):  # iterate over the number of seeds picked
            global next_index
            action = (action + 1) % 12  # move to the next pit cyclically
            next_index = self.B.board_format[action]
            self.B.board[next_index] += 1  # drop one seed in the next pit

            # After all seeds are distributed, check if it's time to capture seeds
            if self.B.turns_completed > 1:
                self.capture_seeds(action,  current_player, other_player)

                if np.sum(self.B.board) < 4:
                    self.B.board = np.zeros((self.B.nrows, self.B.ncols))
                    break

            if seeds == 0:    
                self.capture_seeds(action,  current_player, other_player,during_game=False)

        self.B.turns_completed += 1  # increment the turn counter
        return next_index

    def capture_seeds(self, action: int, current_player, other_player, during_game=True):
        """
        Handles seed capture based on game rules when seeds are placed into pits.
        """
        pit_index = self.B.action2pit(action)
        player_idx = current_player - 1  # Adjust index for zero-based list access

        # Check for exactly 4 seeds in the pit after a move and that total seeds exceed a threshold.
        if self.B.get_seeds(action) == 4:
            if np.sum(self.B.board) > 8:  # More than 8 seeds on board allows for normal capture
                # Check whether the pit is in the current player's territory
                if pit_index in self.B.player_territories[player_idx]:
                    self.B.stores[player_idx] += 4  # Add seeds to the current player's store
                else:
                    self.B.stores[other_player - 1] += 4  # Add seeds to the other player's store
                self.B.board[pit_index] = 0  # Clear the pit after capture
            elif np.sum(self.B.board) <= 8:  # Special rule when total seeds on board is 8 or less
                print("Special condition triggered with 8 seeds on the board.")
                self.B.stores[player_idx] += np.sum(self.B.board)  # Transfer all seeds to the player's store
                self.B.board[:] = 0  # Clear the board

    def calculate_reward(self, player_id):
        # Initialize reward
        reward = 0
        
        # Reward for capturing more seeds than the opponent
        seeds_captured = self.current_store_state[player_id - 1] - self.current_store_state[1 - (player_id - 1)]
        if seeds_captured > 0:
            reward += seeds_captured * 10  # example: 10 points per seed advantage
        
        # Additional reward for winning the game
        if player_id == self.game_winner():
            reward += 100  # significant points for winning the game
        
        return reward
