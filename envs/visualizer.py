from time import sleep
import tkinter as tk
import multiprocessing as mp
from multiprocessing.connection import Connection
from envs.konquest import Universe


class Visualizer:
    __UPDATE_STATE_COMMAND = "update state"
    __GAME_OVER_COMMAND = "game over"

    def __init__(self, initial_state: Universe, timeouts: int):
        other_end, self.__connection = mp.Pipe()
        self.__process = mp.Process(target=self.start,
                                    args=(initial_state, timeouts, other_end))
        self.__process.start()
    
    def start(self, initial_state: Universe, timeout, connection: Connection):
        from envs.konquest_visualizer import KonquestVisualizer

        try:
            visualizer = KonquestVisualizer(initial_state, timeout)
            commands = {self.__UPDATE_STATE_COMMAND: visualizer.update_state,
                        self.__GAME_OVER_COMMAND: visualizer.game_over}
            need_result = set()
            while not KonquestVisualizer.is_closed:
                if not connection.poll():
                    visualizer.refresh(1 / KonquestVisualizer.REFRESH_FREQUENCY)
                    continue
                command, args, kw = connection.recv()
                result = commands[command](*args, **kw)
                if command in need_result:
                    connection.send(result)

            connection.close()
        except tk.TclError:
            pass
        except EOFError:
            pass

    def update_state(self, state: Universe):
        self.__connection.send((self.__UPDATE_STATE_COMMAND, (state,), {}))

    def game_over(self, winners):
        self.__connection.send((self.__GAME_OVER_COMMAND, (winners,), {}))
        self.__process.join()