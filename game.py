import time
from typing import List, Optional
from copy import deepcopy
from random import choice

from agent_interface import AgentInterface
from envs.environment import AbstractState
from time_limit import time_limit
from envs.visualizer import Visualizer


class Game:
    def __init__(self, players: List[AgentInterface]):
        self.__players = players

    def play(self,
             starting_state: AbstractState,
             output=False,
             visualizer: Optional[Visualizer]=None,
             timeout_per_turn=[None, None]):
        winners = self.__play(starting_state,
                              output,
                              visualizer,
                              timeout_per_turn)
        if output:
            print("Game is over!")
            if len(winners) != 1:
                print("The game ended in a draw!")
            else:
                print(f"Player {winners[0]}, {self.__players[winners[0]]} WON!")
        if visualizer:
            visualizer.game_over(winners)
        return winners

    def __play(self, state: AbstractState, output, visualizer, timeout_per_turn):
        duration = None
        action = None
        if output:
            print(state)
            print("Branching factor:", len(state.successors()))
        while True:
            is_winner = state.is_winner()
            if is_winner is not None:
                if is_winner == 0:
                    return []
                if is_winner == 1:
                    return [state.current_player]
                return [1 - state.current_player]
            successors = state.successors()
            start_time = time.time()
            action = self.__get_action(self.__players[state.current_player],
                                       state,
                                       timeout_per_turn[state.current_player])
            duration = time.time() - start_time
            for action_, successor in successors:
                if action_ == action:
                    state = successor
                    break
            else:
                if action is None:
                    print ("Time out!")
                else:
                    print("Illegal move!")
                print("Choosing a random action!")
                action, state = choice(successors)
            if visualizer and state.current_player == 0:
                visualizer.update_state(state)
            if output:
                print(f"Decision time: {duration:0.3f}")
                print("Action:", action)
                print("===================================================")
                print(state)
                print("Branching factor:", len(state.successors()))

    def __get_action(self, player: AgentInterface, state, timeout):
        action = None
        try:
            with time_limit(timeout):
                for decision in player.decide(deepcopy(state)):
                    action = decision
        except TimeoutError:
            pass
        # NOTE: The following lines will be uncommented during tournament
        # except Exception as e:
        #     print("Got an EXCEPTION:", e)
        #     print()
        #     import traceback
        #     traceback.print_exc()
        return action
