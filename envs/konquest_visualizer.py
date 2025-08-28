from typing import Tuple, List, Dict
import os
from time import sleep, time
import math
import random
import tkinter as tk
from tkinter.font import Font as tkFont
from PIL import Image, ImageTk
import numpy as np

from envs.konquest import Universe, ID, Player


class KonquestVisualizer:
    ROOT: tk.Tk = tk.Tk()
    ROOT.title("Konquest (CS-E4800 Tournament)")
    ROOT.iconphoto(True, tk.PhotoImage(file="images/AI.png"))
    is_closed = False

    BACKGROUND = Image.open("images/background.png")
    LOGO = Image.open("images/logo.png")
    GAME_OVER = Image.open("images/game_over.png")
    # BOARD_SIZE = (2560, 1440)
    BOARD_SIZE = (1920, 1440)
    REFRESH_FREQUENCY = 10

    PLANETS = [os.path.join("images", "planets", planet)
               for planet in os.listdir("images/planets")]

    def __init__(self, initial_state: Universe, turn_timeout: float):
        #refresh Canvas
        for old_items in self.ROOT.winfo_children():
            old_items.destroy()
        self.canvas = ResizableCanvas(self.ROOT,
                                      width=self.BOARD_SIZE[0],
                                      height=self.BOARD_SIZE[1])
        width = self.ROOT.winfo_screenwidth() - 110
        width = min(width // 1.5, int(self.BOARD_SIZE[0] * 0.75))
        self.canvas.resize(width=width, height=None)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.config(bg='black')
        self.ROOT.eval('tk::PlaceWindow . center')
        self.canvas.create_image(0,
                                 self.BOARD_SIZE[1] - self.BACKGROUND.size[1],
                                 anchor=tk.NW,
                                 image=self.BACKGROUND)

        # Create planets
        positions = [p.info.position for p in initial_state.planets]
        planets = random.sample(self.PLANETS, k=len(initial_state.planets))
        capacities = [p.info.capacity for p in initial_state.planets]
        productions = [p.info.production for p in initial_state.planets]
        names = [p.info.name for p in initial_state.planets]
        self.__planets = [Planet(n, pos, c, pr, pl, self.canvas)
                          for n, pos, c, pr, pl, in zip(names,
                                                        positions,
                                                        capacities,
                                                        productions,
                                                        planets)]
        self.__players = initial_state.players
        self.__info = Info(self.__players, self.__planets, self.canvas)

        self.__fleets: Dict[int, Fleet] = {}

        self.__refresh_per_turn = turn_timeout * self.REFRESH_FREQUENCY
        self.__refresh_counter = self.__refresh_per_turn
        self.__last_refresh_time = 0
        self.__game_over = False

        # Add AI logo
        self.canvas.create_image(self.BOARD_SIZE[0] - 5,
                                 self.BOARD_SIZE[1] - 5,
                                 anchor=tk.SE,
                                 image=self.LOGO)

        self.update_state(initial_state)

    def refresh(self, after=0):
        sleeping_time = after - (time() - self.__last_refresh_time)
        if sleeping_time > 0:
            self.__last_refresh_time = self.__last_refresh_time + after
            sleep(sleeping_time)
        else:
            self.__last_refresh_time = time()
        if self.is_closed:
            exit()
        if not self.__game_over:
            for planet in self.__planets:
                planet.next_frame()
            for fleet in self.__fleets.values():
                fleet.move()
        self.ROOT.update_idletasks()
        self.ROOT.update()
        self.__refresh_counter += 1

    def update_state(self, state: Universe):
        # We need to refresh the screen at least for `self.__refresh_per_turn`
        while self.__refresh_counter < self.__refresh_per_turn:
            self.refresh(0.01)
        self.__refresh_counter = 0

        def get_player(player_id: ID):
            if player_id == ID.RED:
                return 0
            if player_id == ID.BLUE:
                return 1
            return None

        for my_planet, planet in zip(self.__planets, state.planets):
            my_planet.update_info(get_player(planet.owner), planet.ships)
        inactive_fleets = {fleet_id for fleet_id in self.__fleets}
        for fleet in state.fleets:
            if fleet.fleet_id not in self.__fleets:
                source = self.__planets[fleet.source_id].position
                destination = self.__planets[fleet.destination_id].position
                number_of_moves = (fleet.distance + 1) * self.__refresh_per_turn
                self.__fleets[fleet.fleet_id] = Fleet(source,
                                                      destination,
                                                      number_of_moves,
                                                      get_player(fleet.owner),
                                                      fleet.ships,
                                                      self.canvas)
            else:
                inactive_fleets.remove(fleet.fleet_id)
        for fleet_id in inactive_fleets:
            assert self.__fleets[fleet_id].reached, "A fleet has not reached!"
            self.__fleets[fleet_id].delete()
            del self.__fleets[fleet_id]

        self.__info.update_info()

    def game_over(self, winners: List[int]):
        x, y = (self.BOARD_SIZE[0] / 2, self.BOARD_SIZE[1] / 2)
        self.__game_over = True
        self.canvas.create_image(x, y, image=self.GAME_OVER, anchor=tk.CENTER)
        style = {"size": 42, "fill": "#6e2600"}
        if len(winners) != 1:
            winner = "The game ended in a draw!"
        else:
            player_name = self.__players[winners[0]].name
            winner = f"Player {winners[0]}, {player_name}, WON!"
        self.canvas.create_text(x, y, text="Game is over", anchor=tk.S, **style)
        self.canvas.create_text(x, y, text=winner, anchor=tk.N, **style)
        self.refresh(0.1)
        self.refresh(5)
        self.is_closed = True


class Planet:
    OFFSET = (100, 100)
    LENGTH = 200
    FULL_LENGTH = 1.8 * LENGTH   # With margin
    CAPTURED = ["images/captured_red.png", "images/captured_blue.png"]
    BACKGROUND = "images/planet_background.png"

    def __create_circle_mask(length):
        return np.array([[True if (  ((2 * i - length) / length) ** 2
                                   + ((2 * j - length) / length) ** 2)
                                   > 1.2
                          else False
                          for j in range(length)]
                         for i in range(length)])
    CIRCLE_MASK = __create_circle_mask(LENGTH)

    def __init__(self,
                 name: str,
                 position: Tuple[int, int],
                 capacity: int,
                 production: float,
                 image_path: str,
                 canvas: tk.Canvas):
        self.__name = name
        self.__position = tuple(self.OFFSET[i] + self.FULL_LENGTH * position[i]
                                for i in range(2))
        self.__handlers = []
        self.__frames = self.__normalize_image(image_path)
        for frame in self.__frames:
            handler = canvas.create_image(*self.__position,
                                          image=frame,
                                          anchor=tk.NW,
                                          state='hidden')
            self.__handlers.append(handler)
        self.__background = Image.open(self.BACKGROUND)
        self.__background_h = canvas.create_image(*self.__position,
                                                  image=self.__background,
                                                  anchor=tk.NW)
        self.__current_frame = 0
        self.__canvas = canvas
        self.__captured = None
        self.__cp_handle = None
        self.__owner = None
        self.__ships = 0
        self.__capacity = capacity
        self.__production = production
        self.next_frame()

    @property
    def icon(self):
        return self.__frames[0].copy()
    
    @property
    def name(self):
        return self.__name

    @property
    def position(self):
        return [self.__position[0] + self.LENGTH / 2,
                self.__position[1] + self.LENGTH / 2]

    @property
    def owner(self):
        return self.__owner

    @property
    def ships(self):
        return self.__ships
    
    @property
    def capacity(self):
        return self.__capacity
    
    @property
    def production(self):
        return self.__production

    def update_info(self, owner: int, ships: int):
        if self.__owner != owner:
            if self.__cp_handle is not None:
                self.__canvas.delete(self.__cp_handle)
            self.__owner = owner
            self.__captured = Image.open(self.CAPTURED[owner])
            self.__cp_handle = self.__canvas.create_image(self.position[0] - 2,
                                                          self.position[1] - 1,
                                                          anchor=tk.CENTER,
                                                          image=self.__captured)
        self.__ships = ships

    def next_frame(self):
        self.__canvas.itemconfigure(self.__handlers[self.__current_frame],
                                    state='hidden')
        self.__current_frame += 1
        self.__current_frame %= len(self.__handlers)
        self.__canvas.itemconfigure(self.__handlers[self.__current_frame],
                                    state='normal')
        self.__canvas.tag_raise(self.__background_h)
        self.__canvas.tag_raise(self.__handlers[self.__current_frame])

    @staticmethod
    def __normalize_image(image_path: str):
        image = Image.open(image_path)
        frames = []
        for frame_index in range(image.n_frames):
            image.seek(frame_index)
            frames.append(image.convert('RGBA'))
        if os.path.basename(image_path).startswith("normalized_"):
            return frames
        frames = Planet.__transparent_background(frames)
        frames = Planet.__crop(frames)
        frames = Planet.__resize(frames)
        frames = Planet.__apply_circle_mask(frames)
        assert len(frames) > 1,  "A gif with more than one frame expected!"
        normalized_name = f"normalized_{os.path.basename(image_path)}"
        output_path = os.path.join(os.path.dirname(image_path), normalized_name)
        frames[0].save(output_path,
                       format='PNG',
                       save_all=True,
                       append_images=frames[1:],
                       exact=True,
                       lossless=True,
                       optimize=False,
                       quality=100)
        return frames

    @staticmethod
    def __transparent_background(frames: List[Image.Image]):
        new_frames = []
        for frame in frames:
            rgba = np.array(frame)
            rgb = rgba[:, :, :3]
            background = rgb[0, 0]
            threshold = np.array([50, 50, 50])
            diff = rgb - background
            mask1 = np.all(diff < threshold, axis=-1)
            mask2 = np.all(diff > -threshold, axis=-1)
            mask = np.logical_and(mask1, mask2)
            rgba[mask] = [0, 0, 0, 0]
            new_frames.append(Image.fromarray(rgba))
        return new_frames
    
    @staticmethod
    def __crop(frames: List[Image.Image]):
        bounding_box = [float('inf'), float('inf'), 0, 0]
        criteria = [min, min, max, max]
        for frame in frames:
            new_bounding_box = frame.getbbox()
            bounding_box = [c(n, o) for c, n, o in zip(criteria,
                                                       new_bounding_box,
                                                       bounding_box)]
        new_frames = []
        for frame in frames:
            new_frames.append(frame.crop(bounding_box))
        return new_frames

    @staticmethod
    def __resize(frames: List[Image.Image]):
        return [f.resize((Planet.LENGTH, Planet.LENGTH), Image.LANCZOS)
                for f in frames]

    @staticmethod
    def __apply_circle_mask(frames: List[Image.Image]) -> List[Image.Image]:
        new_frames = []
        for frame in frames:
            frame = frame.convert('RGBA')
            rgba = np.array(frame)
            rgba[Planet.CIRCLE_MASK] = [0, 0, 0, 0]
            new_frames.append(Image.fromarray(rgba))
        return new_frames


class Fleet:
    __PLAYERS = ["images/fleet_red.png", "images/fleet_blue.png"]
    def __init__(self,
                 source: Tuple[int, int],
                 destination: Tuple[int, int],
                 number_of_moves: int,
                 player: int,
                 number_of_ships: int,
                 canvas: 'ResizableCanvas'):
        self.__position = source
        self.__destination = destination
        self.__delta = [(destination[0] - source[0]) / number_of_moves,
                        (destination[1] - source[1]) / number_of_moves]
        self.__remaining = [0, 0]
        self.__canvas = canvas
        self.__handler = self.__create_image(player, number_of_ships)
        self.__number_of_moves = number_of_moves

    @property
    def reached(self):
        return self.__number_of_moves <= 0

    def move(self):
        if self.reached:
            return self
        move_x = self.__remaining[0] + self.__delta[0]
        move_y = self.__remaining[1] + self.__delta[1]
        self.__position = [self.__position[0] + int(move_x), self.__position[1] + int(move_y)]
        self.__canvas.image_move(self.__handler, int(move_x), int(move_y))
        self.__remaining = [move_x - int(move_x), move_y - int(move_y)]
        self.__number_of_moves -= 1
        return self
    
    def delete(self):
        self.__canvas.delete(self.__handler)

    def __find_angle(self):
        opposite = self.__destination[1] - self.__position[1]
        opposite *= -1
        adjacent = self.__destination[0] - self.__position[0]
        if math.isclose(adjacent, 0):
            angle = math.pi / 2
            if opposite < 0:
                angle *= -1
        else:
            angle = math.atan(opposite / adjacent)
        if not math.isclose(adjacent, 0) and adjacent < 0:
            angle += math.pi
        return angle / math.pi * 180
        
    def __create_image(self, player: int, number_of_ships: int):
        image = Image.open(self.__PLAYERS[player])
        if number_of_ships != 4:
            size = image.size
            size = [size[0], int(size[1] * number_of_ships / 4)]
            image = image.resize(size, Image.LANCZOS)
        angle = self.__find_angle()
        image = image.rotate(angle, expand=True)
        handler = self.__canvas.create_image(self.__position[0],
                                             self.__position[1],
                                             anchor=tk.CENTER,
                                             image=image)
        return handler
    

class Info:
    LENGTH = 300
    X_OFFSET = KonquestVisualizer.BOARD_SIZE[0] - LENGTH
    __PLANET_LENGTH = 100
    __BAR_WIDTH = 3
    __MARGIN = 40

    def __init__(self,
                 players: List[Player],
                 planets: List[Planet],
                 canvas: 'ResizableCanvas'):
        self.__planets = planets
        self.__bg = canvas.create_rectangle(self.X_OFFSET,
                                            0,
                                            KonquestVisualizer.BOARD_SIZE[0],
                                            KonquestVisualizer.BOARD_SIZE[1],
                                            outline='black',
                                            fill='black')
        canvas.tag_raise(self.__bg)
        self.__bar = canvas.create_rectangle(self.X_OFFSET,
                                             0,
                                             self.X_OFFSET + self.__BAR_WIDTH,
                                             KonquestVisualizer.BOARD_SIZE[1],
                                             outline='white',
                                             fill="white")
        canvas.tag_raise(self.__bar)
        self.__canvas = canvas

        self.__add_names(players)

        self.__icons: List[Image.Image] = []
        self.__text_handlers = []
        self.__create_icons()

    def update_info(self):
        margin = self.__MARGIN
        x_offset = self.X_OFFSET + margin / 2 + self.__PLANET_LENGTH + margin
        y_offset = 4 * margin
        style = {"size": 15}
        for handler in self.__text_handlers:
            self.__canvas.delete(handler)
        for planet in self.__planets:
            text = "{: ^11}\n".format(planet.name)
            alignment = "{: <11}\n"
            text += alignment.format(f"ships: {planet.ships}")
            text += alignment.format(f"cap.: {planet.capacity}")
            text += alignment.format(f"prod.: {planet.production}")

            fill = "white"
            if planet.owner == 0:
                fill = "violet red"
            elif planet.owner == 1:
                fill = "deep sky blue"

            self.__text_handlers.append(self.__canvas.create_text(x_offset,
                                                                  y_offset,
                                                                  text=text,
                                                                  anchor=tk.NW,
                                                                  fill=fill,
                                                                  **style))
            y_offset += self.__PLANET_LENGTH + margin

    def __add_names(self, players: List[Player]):
        player0 = f"Player 0:\n{players[0].name}"
        player1 = f"Player 1: \n{players[1].name}"
        colors = {ID.RED: "violet red", ID.BLUE:"deep sky blue"}
        
        x_offset = self.X_OFFSET + self.__MARGIN
        y_offset = self.__MARGIN / 2
        self.__canvas.create_text(x_offset,
                                  y_offset,
                                  text=player0,
                                  anchor=tk.NW,
                                  fill=colors[players[0].id_],
                                  size=15)

        y_offset += 1.5 * self.__MARGIN
        self.__canvas.create_text(x_offset,
                                  y_offset,
                                  text=player1,
                                  anchor=tk.NW,
                                  fill=colors[players[1].id_],
                                  size=15)

    def __create_icons(self):
        self.__icons = []
        for planet in self.__planets:
            icon = planet.icon
            icon = icon.resize((self.__PLANET_LENGTH, self.__PLANET_LENGTH),
                               Image.LANCZOS)
            self.__icons.append(icon)

        margin = self.__MARGIN
        x_offset = self.X_OFFSET + margin
        y_offset = 4 * margin
        for icon in self.__icons:
            self.__canvas.create_image(x_offset,
                                       y_offset,
                                       image=icon,
                                       anchor=tk.NW)
            y_offset += self.__PLANET_LENGTH + margin

class ResizableCanvas(tk.Canvas):
    def __init__(self, parent, **kwargs):
        super().__init__(parent,**kwargs)
        self.config(highlightthickness=0)
        self.bind("<Configure>", self.on_resize)
        self.height = self.winfo_reqheight()
        self.width = self.winfo_reqwidth()
        self.x_scale = 1
        self.y_scale = 1
        self.images = {}
        self.texts = {}
        self.rectangles = {}

    def create_image(self, x, y, *args, **kw):
        new_x, new_y = self.__new_position(x, y)
        image = kw.pop('image')
        new_image = image.copy().resize(self.__new_position(*image.size))
        tk_image = ImageTk.PhotoImage(new_image)
        image_id = super().create_image(new_x, new_y, *args, image=tk_image, **kw)
        self.images[image_id] = [x, y, image, tk_image]
        return image_id

    def image_move(self, image_id, x, y):
        self.images[image_id][0] += x
        self.images[image_id][1] += y
        self.coords(image_id, *self.__new_position(*self.images[image_id][:2]))

    def image_move_to(self, image_id, x, y):
        self.images[image_id][0] = x
        self.images[image_id][1] = y
        self.coords(image_id, *self.__new_position(x, y))

    def get_image_coordinate(self, image_id):
        return self.images[image_id][:2]

    def get_style(self, size: int):
        return {"font": tkFont(family="Cooper Black", size=int(size * self.y_scale), weight='bold')}

    def create_rectangle(self, x0, y0, x1, y1, *args, **kw):
        xx0, yy0 = self.__new_position(x0, y0)
        xx1, yy1 = self.__new_position(x1, y1)
        rectangle_id = super().create_rectangle(xx0, yy0, xx1, yy1, *args, **kw)
        self.rectangles[rectangle_id] = [x0, y0, x1, y1]
        return rectangle_id

    def create_text(self, x, y, *args, **kw):
        size = kw.pop('size')
        kw.update(self.get_style(size))
        text_id = super().create_text(*self.__new_position(x, y), *args, **kw)
        self.texts[text_id] = [x, y, size]
        return text_id

    def on_resize(self, event):
        self.resize(event.width, event.height)

    def resize(self, width, height):
        # determine the ratio of old width/height to new width/height
        if width == None:
            width = self.width * (height / self.height)
        if height == None:
            height = self.height * (width / self.width)
        self.x_scale = width / self.width
        self.y_scale = height / self.height
        # resize the canvas 
        self.config(width=width, height=height)
        # resize all images
        for image_id, (x, y, image, _) in self.images.items():
            new_image = image.copy()
            new_size = (int(new_image.size[0] * self.x_scale), int(new_image.size[1] * self.y_scale))
            new_image = new_image.resize(new_size, Image.LANCZOS)
            tk_image = ImageTk.PhotoImage(new_image)
            self.images[image_id][3] = tk_image
            self.itemconfigure(image_id, image=tk_image)
            self.coords(image_id, *self.__new_position(x, y))

        # reposition all texts
        for text_id, (x, y, size) in self.texts.items():
            self.coords(text_id, *self.__new_position(x, y))
            self.itemconfigure(text_id, self.get_style(size))

        # reposition all rectangles
        for rectangle_id, (x0, y0, x1, y1) in self.rectangles.items():
            x0, y0 = self.__new_position(x0, y0)
            x1, y1 = self.__new_position(x1, y1)
            self.coords(rectangle_id, x0, y0, x1, y1)

    def __new_position(self, x, y):
        return (int(self.x_scale * x), int(self.y_scale * y))


if __name__ == "__main__":
    visualizer = KonquestVisualizer(Universe(["p1", "p2"], 6), 5)
    while not visualizer.is_closed:
        visualizer.refresh(1 / KonquestVisualizer.REFRESH_FREQUENCY)
        
    
