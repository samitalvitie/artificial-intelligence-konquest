from typing import List, Tuple, Optional
from dataclasses import MISSING


class AbstractPlayer:
    pass


class AbstractAction:
    pass


class AbstractState:
    def __str__(self) -> str:
        raise NotImplementedError

    def successors(self) -> List[Tuple[AbstractAction, 'AbstractState']] :
        raise NotImplementedError

    def is_winner(self) -> Optional[int]:
        """
        Determines if there is a winner in the current state or not

        This function can be used to determine if the game has ended or not, and
        if it is over, who is the winner.

        The return value is:
            `None`  => if the game is not over yet,
            `1`     => if the current player is the winner,
            `0`     => if the game ended in a draw, or,
            `-1`    => if the opponent won the game.
        """
        raise NotImplementedError

    @property
    def current_player(self) -> int:
        raise NotImplementedError