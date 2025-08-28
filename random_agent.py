import random
from envs.environment import AbstractState
from agent_interface import AgentInterface


class RandomAgent(AgentInterface):
    @staticmethod
    def info():
        return {"agent name": "Random"}

    def decide(self, state: AbstractState):
        actions = [action for action, _ in state.successors()]
        yield random.choice(actions)
