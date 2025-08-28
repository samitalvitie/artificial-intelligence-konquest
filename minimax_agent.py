import random
from agent_interface import AgentInterface
from envs.konquest import Universe, ID


class MinimaxAgent(AgentInterface):
    """
    An agent who plays the Konquest game using Minimax algorithm
    """

    def __init__(self, depth: int = 4):
        self.depth = depth
        self.__player = None

    def info(self):
        return {"agent name": f"Minimax-simple"}

    def heuristic(self, state: Universe):
        id = state.current_player_id
        my_ships = 0
        for planet in state.planets:
            if planet.owner == id:
                my_ships += planet.ships
        for fleet in state.fleets:
            if fleet.owner == id:
                my_ships += fleet.ships
        return my_ships

    def decide(self, state: Universe):
        """
        Get the value of each action by passing its successor to min_value
        function.
        """
        successors = state.successors()
        random.shuffle(successors)
        best_action, _ = successors[0]
        max_value = float('-inf')
        for action, next_state in successors:
            action_value = self.min_value(next_state, self.depth - 1)
            if action_value > max_value:
                max_value = action_value
                best_action = action
        yield best_action

    def max_value(self, state: Universe, depth: int):
        """
        Get the value of each action by passing its successor to min_value
        function. Return the maximum value of successors.

        `max_value()` function sees the game from players's perspective, trying
        to maximize the value of next state.

        NOTE: when passing the successor to min_value, `depth` must be
        reduced by 1, as we go down the Minimax tree.

        NOTE: the player must check if it is the winner (or loser)
        of the game, in which case, a large value (or a negative value) must
        be assigned to the state. Additionally, if the game is not over yet,
        but we have `depth == 0`, then we should return the heuristic value
        of the current state.
        """

        # Termination conditions
        is_winner = state.is_winner()
        if is_winner is not None:
            return is_winner * float('inf')
        if depth == 0:
            return self.heuristic(state)

        # If it is not terminated
        successors = state.successors()
        value = float('-inf')
        for _, next_state in successors:
            value = max(value, self.min_value(next_state, depth - 1))
        return value

    def min_value(self, state: Universe, depth):
        """
        Get the value of each action by passing its successor to max_value
        function. Return the minimum value of successors.
        
        `min_value()` function sees the game from opponent's perspective, trying
        to minimize the value of next state.
        
        NOTE: when passing the successor to max_value, `depth` must be
        reduced by 1, as we go down the Minimax tree.

        NOTE: the opponent must check if it is the winner (or loser)
        of the game, in which case, a negative value (or a large value) must
        be assigned to the state. Additionally, if the game is not over yet,
        but we have `depth == 0`, then we should return the heuristic value
        of the current state.
        """

        # Termination conditions
        is_winner = state.is_winner()
        if is_winner is not None:
            return is_winner * float('-inf')
        if depth == 0:
            return -1 * self.heuristic(state)

        # If it is not terminated
        successors = state.successors()
        value = float('inf')
        for _, next_state in successors:
            value = min(value, self.max_value(next_state, depth - 1))
        return value