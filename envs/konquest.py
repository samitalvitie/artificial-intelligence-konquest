from typing import List, Tuple, Optional
from string import ascii_uppercase as alphabet
from copy import deepcopy
from dataclasses import dataclass
from enum import Enum
from random import randrange, shuffle
from itertools import product, combinations
from math import sqrt, ceil, isclose

from envs.environment import AbstractPlayer, AbstractState, AbstractAction


EPSILON = 1e-7


class ID(Enum):
    """ Player ID """

    RED = "red"
    BLUE = "blue"
    NEUTRAL = "wheat"


@dataclass
class Player(AbstractPlayer):
    name: str                        # Player name
    id_: ID                          # Player id


@dataclass
class Action(AbstractAction):
    ships: int                       # Number of ships
    source_id: int                   # Index of source planet
    destination_id: int              # Index of destination planet

    def __str__(self):
        if self.ships == 0:
            return "(No move!)"
        return (f"({alphabet[self.source_id]} == {self.ships} ships ==>"
                f" {alphabet[self.destination_id]})")


@dataclass
class Fleet:
    fleet_id: int                    # The id of current fleet
    owner: ID                        # Fleet owner
    ships: int                       # Number of ships
    distance: int                    # Number of turns to reach the destination
    source_id: int                   # Index of source planet
    destination_id: int              # Index of destination planet

    def __hash__(self) -> int:
        return hash(self.fleet_id)

    def __eq__(self, __o: 'Fleet') -> bool:
        return self.fleet_id == __o.fleet_id


class PlanetInfo:
    def __init__(self,
                 name: str,
                 position: Tuple[int, int],
                 capacity: int,
                 production: int) -> None:
        self.name = name
        self.position = position
        self.capacity = capacity
        self._production = production

    def __str__(self):
        output = "<Info: "
        output += f"name = {self.name}, "
        output += f"position = {self.position}, "
        output += f"capacity = {self.capacity}, "
        output += f"production = {self.production}>"
        return output

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, __o: 'PlanetInfo'):
        return self.name == __o.name

    @property
    def production(self):
        return self._production / 100


class Planet:
    def __init__(self, info: PlanetInfo, owner: ID, ships: int) -> None:
        self.info = info
        self.owner = owner
        self.__ships = ships * 100

    def __str__(self):
        output = "<Planet: "
        output += f"owner: {self.owner}, "
        output += f"ships: {self.ships}, "
        output += f"{str(self.info)}>"
        return output

    def __hash__(self) -> int:
        return hash((self.info, self.owner, self.__ships))

    def __eq__(self, __o: 'Planet') -> bool:
        return (    self.info == __o.info
                and self.owner == __o.owner
                and self.__ships == __o.ships)

    def __deepcopy__(self, memo):
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        for k, v in self.__dict__.items():
            if k == 'info':
                # Do not need to deepcopy `info`
                setattr(result, k, v)
            else:
                setattr(result, k, deepcopy(v, memo))
        return result

    @property
    def ships(self):
        return round(self.__ships / 100, ndigits=2)

    @ships.setter
    def ships(self, value: int):
        self.__ships = value * 100
        return self

    def produce_ships(self):
        if self.owner != ID.NEUTRAL:
            self.__ships = min(self.info.capacity * 100,
                               self.info._production + self.__ships)
        return self

    def calculate_distance(self, position: Tuple[int, int]):
        d_x = self.info.position[0] - position[0]
        d_y = self.info.position[1] - position[1]
        return ceil(sqrt(d_x ** 2 + d_y ** 2))

    def arrival(self, fleet: Fleet):
        if fleet.owner == self.owner:
            # Reinforce the defense
            self.__ships = min(self.info.capacity * 100,
                               self.__ships + fleet.ships * 100)
            return self
        return self.__combat(fleet)

    def __combat(self, fleet: Fleet):
        KILL_RATE = 70 # percent 
        remaining_defender = self.__ships - KILL_RATE * fleet.ships
        if remaining_defender < 0:
            self.owner = fleet.owner
            alive_ships = int(100 * fleet.ships - 100 * self.__ships / 70)
            self.__ships = min(self.info.capacity * 100, alive_ships)
            return self
        self.__ships = remaining_defender
        return self


class Universe(AbstractState):
    __SIZE = (4, 3)
    __CAPACITY = (4, 12)
    __PRODUCTION_RANGE = (40, 130)  # percent
    __MIN_PLAYER_DISTANCE = 4
    __MAX_TURN = 200

    def __init__(self, player_names: List[str], neutrals_count: int):
        assert len(player_names) < len(ID),  f"We support {len(ID) - 1} players"
        self.__players = [Player(p, i) for p, i in zip(player_names, ID)]
        self.__current_player = 0
        self.planets: List[Planet] = []
        self.fleets: List[Fleet] = []
        self.__fleet_counter = 0
        self.remaining_turns = self.__MAX_TURN
        self.__big_bang(neutrals_count)

    @property
    def current_player(self) -> int:
        return self.__current_player

    @property
    def current_player_id(self) -> ID:
        return self.__players[self.__current_player].id_
    
    @property
    def players(self) -> List[Player]:
        return self.__players.copy()

    def __hash__(self):
        return hash((self.__current_player,
                     tuple(self.planets),
                     tuple(self.fleets),
                     self.remaining_turns))

    def __eq__(self, __o: 'Universe') -> bool:
        return (    self.__current_player == __o.__current_player
                and self.planets == __o.planets
                and self.fleets == __o.fleets
                and self.remaining_turns == __o.remaining_turns)

    def __str__(self) -> str:
        out  = "****************************************************\n"
        out += "{: ^45}\n".format("Planets")
        out += "{:-^45}\n".format("")
        planets = "|{: <4}|{: <10}|{: ^7}|{: ^8}|{: ^10}|\n"
        out += planets.format("Name", "Owner", "Ships", "Capacity", "Production")
        out += planets.format("=" * 4, "=" * 10, "=" * 7, "=" * 8, "=" * 10)
        for planet in self.planets:
            info = planet.info
            out += planets.format(info.name,
                                  planet.owner.name,
                                  planet.ships,
                                  info.capacity,
                                  info.production)
        out += "{:=^45}\n".format("")

        out += "\n"
        out += "{: ^33}\n".format("Fleets")
        out += "{:-^33}\n".format("")
        fleets = "|{: <7}|{: ^5}|{: ^7}|{: ^9}|\n"
        out += fleets.format("Owner", "Ships", "Target", "Distance")
        out += fleets.format("=" * 7, "=" * 5, "=" * 7, "=" * 9)
        for fleet in sorted(self.fleets, key=lambda f: f.distance):
            out += fleets.format(fleet.owner.name,
                                 fleet.ships,
                                 self.planets[fleet.destination_id].info.name,
                                 fleet.distance)
        out += "{:=^33}\n".format("")

        player = self.__players[self.current_player]
        out += f"Current Player: {player.id_.name} ({player.name})\n"
        return out

    def initialize(self):
        for planet in self.planets:
            planet.ships = planet.info.capacity
        for planet, player in zip(self.planets, self.__players):
            planet.owner = player.id_
        return self

    def rotate_players(self):
        self.__players.append(self.__players.pop(0))
        return self

    def successors(self) -> List[Tuple[Action, 'Universe']]:
        applicable_actions = self.__applicable_actions()
        successors = []
        for action in applicable_actions:
            successors.append((action, self.__apply(action)))
        shuffle(successors) 
        return successors

    def is_winner(self) -> Optional[int]:
        ships = {}
        for planet in self.planets:
            ships[planet.owner] = ships.get(planet.owner, 0) + planet.ships
        for fleet in self.fleets:
            ships[fleet.owner] = ships.get(fleet.owner, 0) + fleet.ships
        ships.pop(ID.NEUTRAL, None)
        # Following condition is not possible
        # if len(ships) == 0:
        #     return 0
        if len(ships) == 1:
            current_player_id = self.__players[self.__current_player].id_
            return 1 if ships.popitem()[0] == current_player_id else -1
        if self.remaining_turns == 0:
            ships = sorted(ships.items(), key=lambda i: i[1], reverse=True)
            if isclose(ships[0][1], ships[1][1]):
                return 0
            current_player_id = self.__players[self.__current_player].id_
            return 1 if ships[0][0] == current_player_id else -1
        return None

    def clone(self):
        # Returns a shallow copy of the current universe
        cls = self.__class__
        cloned = cls.__new__(cls)
        cloned.__players = self.__players
        cloned.__current_player = self.__current_player
        cloned.__fleet_counter = self.__fleet_counter
        cloned.remaining_turns = self.remaining_turns
        cloned.planets = deepcopy(self.planets)
        cloned.fleets = deepcopy(self.fleets)
        return cloned

    def __big_bang(self, neutral_count):
        while True:
            names = list(alphabet)
            self.planets = []
            for i in range(len(self.__players)):
                position = (randrange(self.__SIZE[0]),
                            randrange(self.__SIZE[1]))
                planet_info = PlanetInfo(names.pop(0),
                                         position,
                                         self.__CAPACITY[1] - 2,
                                         100)
                self.planets.append(Planet(planet_info, ID.NEUTRAL, 0))
            for planet1, planet2 in combinations(self.planets, r=2):
                distance = planet1.calculate_distance(planet2.info.position)
                if distance < self.__MIN_PLAYER_DISTANCE:
                    # Too close! we should rearrange them
                    break
            else:
                # Everything is fine, we can place the neutral planets
                break
        for i in range(neutral_count):
            while True:
                position = (randrange(self.__SIZE[0]),
                            randrange(self.__SIZE[1]))
                for planet in self.planets:
                    # Two planets cannot be placed on the exact same locaiton
                    if position == planet.info.position:
                        break
                else:
                    break

            capacity = randrange(*self.__CAPACITY)
            production = randrange(*self.__PRODUCTION_RANGE)
            planet_info = PlanetInfo(names[i], position, capacity, production)
            self.planets.append(Planet(planet_info, ID.NEUTRAL, 0))

        print("#{:#^72}#".format(""))
        print("#{: ^72}#".format("Big Bang!"))
        print("#{:#^72}#".format(""))
        for planet in self.planets:
            print("#{: <72}#".format(" " + str(planet.info)))
        print("#{:#^72}#".format(""))
        print()
        return self

    def __applicable_actions(self):
        player_id = self.__players[self.__current_player].id_
        sources = [i
                   for i, p in enumerate(self.planets)
                   if p.owner == player_id]
        # planets_ships = [int(self.planets[s].ships) for s in sources]
        # counts = range(1, max(planets_ships + [0]) + 1)
        counts = [2, 4, 8]
        attacks = [Action(c, s, d)
                   for c, s, d in product(counts,
                                          sources,
                                          range(len(self.planets)))
                   if s != d and c <= self.planets[s].ships]
        fortified = Action(0, -1, -1)
        attacks.append(fortified)
        return attacks

    def __apply(self, attack: Action):
        successor = self.clone()
        if attack.ships > 0:
            distance = (successor
                        .planets[attack.destination_id]
                        .calculate_distance(successor
                                            .planets[attack.source_id]
                                            .info
                                            .position))
            new_fleet = Fleet(self.__fleet_counter,
                              successor.planets[attack.source_id].owner,
                              attack.ships,
                              distance,
                              attack.source_id,
                              attack.destination_id)
            successor.__fleet_counter += 1
            successor.planets[attack.source_id].ships -= attack.ships
            successor.fleets.append(new_fleet)
        successor.__current_player += 1
        successor.remaining_turns -= 1

        if successor.__current_player == len(successor.__players):
            # End of turn; we should update planets and fleets
            for planet in successor.planets:
                planet.produce_ships()
            new_fleets = []
            for fleet in successor.fleets:
                if fleet.distance == 0:
                    successor.planets[fleet.destination_id].arrival(fleet)
                else:
                    fleet.distance -= 1
                    new_fleets.append(fleet)
            successor.fleets = new_fleets
            successor.__current_player = 0
        return successor