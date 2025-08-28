from random import shuffle
from agent_interface import AgentInterface
from envs.konquest import Universe
from random_agent import RandomAgent
from game import Game


class MarkovAgent(AgentInterface):
    """
    Evaluate each action by taking it, followed by
    random plays. The action with most wins is chosen.
    """
    def __init__(self):
        self.__simulator = Game([RandomAgent(), RandomAgent()])

    def info(self):
        return {"agent name": "Markov"}

    def decide(self, state: Universe):
        successors = state.successors()
        shuffle(successors)
        win_counter = [0] * len(successors)
        while True:
            for i, (_, next_state) in enumerate(successors):
                result = self.__simulator.play(output=False, 
                                               starting_state=next_state)
                win_counter[i] += 1 if result == [state.current_player] else 0
            yield successors[win_counter.index(max(win_counter))][0]