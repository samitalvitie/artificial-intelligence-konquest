from envs.konquest import Universe
from agent_interface import AgentInterface
import random

"""
What I have done:
- used minimax_agent.py as a template
- added alpha-beta pruning
- added iterative deepening
- tuned the heuristic function

Results:
- can now find solutions way past the original 4 depth bound
- does not have to visit every node thanks to alpha-beta pruning
- beats the basic mimimax algorithm consistently
"""


class Agent(AgentInterface):

    @staticmethod
    def info():
        return {"agent name": "kari_grandi",  # COMPLETE HERE
                "student name": ["Sami Talvitie"],  # COMPLETE HERE
                "student number": ["729624"]}  # COMPLETE HERE

    # Initialize start_depth and max_depth
    def __init__(self, start_depth: int = 1, max_depth: int = 100):
        # Initialize variables
        self.start_depth = start_depth
        self.max_depth = max_depth
        self.__player = None

    def heuristic(self, state: Universe):
        # Initialize variables
        id = state.current_player_id
        my_ships = 0
        my_fleets = 0
        my_production = 0
        my_planets = 0
        penalty = 0

        # Calculate values for the heuristic
        for planet in state.planets:
            if planet.owner == id:
                my_ships += planet.ships
                my_production += planet.info.production
                my_planets += 1
                if planet.info.capacity == planet.ships:
                    penalty += 1

        for fleet in state.fleets:
            if fleet.owner == id:
                my_fleets += 1

        return my_ships + my_fleets/2 + my_production*6 + my_planets*5 - penalty*10

    # Modified with alpha-beta pruning and iterative deepening
    def decide(self, state: Universe):
        # Initialize variables
        best_action = None
        max_value = float('-inf')
        alpha = float('-inf')
        beta = float('inf')

        # Iterative deepening loop
        for depth in range(self.start_depth, self.max_depth + 1):
            successors = state.successors()
            random.shuffle(successors)

            # Apply alpha-beta pruning to minimize the number of nodes visited
            for action, next_state in successors:
                action_value = self.min_value(next_state, depth - 1, alpha, beta)
                if action_value > max_value:
                    max_value = action_value
                    best_action = action
                alpha = max(alpha, max_value)
                if beta <= alpha:
                    break

            print("Depth:", depth, "Best action: ", best_action) # Uncomment to print best moves
            # Yield the best action found at the current depth
            yield best_action

    # This function now takes alpha and beta values as inputs
    def max_value(self, state: Universe, depth: int, alpha: float, beta: float):
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
            value = max(value, self.min_value(next_state, depth - 1, alpha, beta))
            alpha = max(alpha, value)
            if beta <= alpha:
                break
        return value

    # This function now takes alpha and beta values as inputs
    def min_value(self, state: Universe, depth: int, alpha: float, beta: float):
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
            value = min(value, self.max_value(next_state, depth - 1, alpha, beta))
            if value <= alpha:
                return value
            beta = min(beta, value)
        return value
