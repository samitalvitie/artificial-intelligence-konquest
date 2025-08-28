from typing import Type
from random import seed

from game import Game
from envs.konquest import Universe
from envs.visualizer import Visualizer

# Importing Agents
from agent_interface import AgentInterface
from random_agent import RandomAgent
from minimax_agent import MinimaxAgent
from id_minimax_agent import IDMinimaxAgent
from markov_agent import MarkovAgent
from kari_grandi import Agent    # After completing your agent, you can uncomment this line



# If you want the reproducibility uncomment the following line
# seed(13731367)
NEUTRAL_PLANETS_COUNT =  4


def main():
    ############### Set the players ###############
    # players = [RandomAgent, IDMinimaxAgent]
    # players = [MarkovAgent, RandomAgent]
    # players = [IDMinimaxAgent, MarkovAgent]

    players = [Agent, MarkovAgent]   #<-- Uncomment this to test your agent
    ###############################################

    RENDER = True

    # The rest of the file is not important; you can skip reading it. #
    ###################################################################

    results = [0, 0]
    for i in range(5):
        initial_state = Universe([player_name(p) for p in players],
                                 NEUTRAL_PLANETS_COUNT)
        for round in range(len(players)):
            print( "########################################################")
            print("#{: ^54}#".format(f"ROUND {round}"))
            print( "########################################################")
            players_instances = [p() for p in players]
            # Timeout for each move. Don't rely on the value of it. This
            # value might be changed during the tournament.
            timeouts = [5, 5]
            game = Game(players_instances)
            new_round = initial_state.clone().initialize()
            turn_duration_estimate = sum([t
                                          for p, t in zip(players, timeouts)
                                          if p != RandomAgent])
            if RENDER:
                visualizer = Visualizer(new_round, turn_duration_estimate)
            else:
                visualizer = None

            winners = game.play(new_round,
                                output=True,
                                visualizer=visualizer,
                                timeout_per_turn=timeouts)
            if len(winners) == 1:
                results[winners[0]] += 1

            print()
            print(f"{i}) Result) {player_name(players[0])}: {results[0]} - "
                f"{player_name(players[1])}: {results[1]}")
            print("########################################################")

            # Rotating players for the next rounds
            initial_state.rotate_players()
            players.append(players.pop(0))
            results.append(results.pop(0))


def player_name(player: Type[AgentInterface]):
    return player().info()['agent name']


if __name__ == "__main__":
    import platform
    if platform.system() == "Darwin":
        import multiprocessing
        multiprocessing.set_start_method('spawn')

    try:
        main()
    except BrokenPipeError as e:
        print("Broken Pipe Error:", e)
    except EOFError as e:
        print("EOF Error:", e)
