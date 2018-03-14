import random
import re
import sys


ASCII_COLORS = [
    '\u001b[0m',      # Reset

    '\u001b[31;1m', # Bright Red
    '\u001b[32;1m', # Bright Green
    '\u001b[33;1m', # Bright Yellow
    '\u001b[36;1m', # Bright Cyan
    '\u001b[35;1m', # Bright Magenta
    '\u001b[30;1m', # Bright Black
    '\u001b[34;1m', # Bright Blue
    '\u001b[37;1m', # Bright White

    '\u001b[40;1m', # Background Bright Black
    '\u001b[41;1m', # Background Bright Red
    '\u001b[42;1m', # Background Bright Green
    '\u001b[43;1m', # Background Bright Yellow
    '\u001b[44;1m', # Background Bright Blue
    '\u001b[45;1m', # Background Bright Magenta
    '\u001b[46;1m', # Background Bright Cyan
    '\u001b[47;1m', # Background Bright White
]

class Tile:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.is_mine = False
        self.neighbors = []
        self.is_revealed = False
        self.is_flagged = False

    def dangerous_neighbor_count(self):
        return len( [t for t in self.neighbors if t.is_mine] )

    def str_as_revealed(self):
        if self.is_mine:
            return "[*]"
        num_dangerous_neighbors = self.dangerous_neighbor_count()
        if num_dangerous_neighbors > 0:
            return "[{}]".format(num_dangerous_neighbors)
        return "[ ]"

    def __str__(self):

        if self.is_revealed:
            return self.str_as_revealed()
        if self.is_flagged:
            return "[F]"
        return "[?]"


class Board:

    neighbor_offsets = [
        # Clockwise from upper left
        (-1, 1),
        ( 0, 1),
        ( 1, 1),
        (-1, 0),
        ( 1, 0),
        (-1, -1),
        ( 0, -1),
        ( 1, -1),
    ]



    def __init__(self, difficulty=0.2, width=20, height=20):
        """
        Sets up a new board
        :param difficulty: On a range from 0.01 to 1, how difficult the level is. A value of 1 means about half the tiles are mines.
        :param width: Board width
        :param height: Board height
        """
        self.difficulty = difficulty
        self.width = width
        self.height = height

        self.board_layout = self.generate_board()

    def is_valid_coordinate(self, x, y):
        if x < 0 or y < 0:
            return False
        if x > self.width - 1 or y > self.height - 1:
            return False
        return True

    def generate_board(self):
        new_board = []

        for y in range(self.height):
            new_row = []
            for x in range(self.width):
                new_tile = Tile(x, y)
                new_tile.is_mine = ( random.random() < (self.difficulty * 0.5) )
                new_tile.x = x
                new_tile.y = y
                new_row.append(
                    new_tile
                )
            new_board.append(new_row)

        for y, row in enumerate(new_board):
            for x, tile in enumerate(row):
                for offset in self.neighbor_offsets:
                    if self.is_valid_coordinate(tile.x + offset[0], tile.y + offset[1]):
                        tile.neighbors.append(
                            new_board[tile.y + offset[1]][tile.x + offset[0]]
                        )

        return new_board

    def print_board(self, cheat=False):
        top_coordinates = " " * 4
        for i in range(len(self.board_layout)):
            top_coordinates += str("{:>3}").format(i)
        print(top_coordinates)

        for y_idx, row in enumerate(self.board_layout):
            row_indicator = "{:>3} ".format(y_idx)
            row_map =  "".join([t.str_as_revealed() if cheat else str(t) for t in row])

            sys.stdout.write(row_indicator)

            for char in list(row_map):
                if char in ['1', '2', '3', '4', '5', '6']:
                    sys.stdout.write(ASCII_COLORS[int(char)])
                    sys.stdout.write(char)
                    sys.stdout.write(ASCII_COLORS[0])
                elif char in ['[', ']']:
                    sys.stdout.write(ASCII_COLORS[7])
                    sys.stdout.write(char)
                    sys.stdout.write(ASCII_COLORS[0])
                else:
                    sys.stdout.write(char)
            print()

    def get_neighbors_of(self, x, y):
        neighbors = []
        for offset in self.neighbor_offsets:
            n_x = x + offset[0]
            n_y = y + offset[1]
            if self.is_valid_coordinate(n_x, n_y):
                neighbors.append(
                    self.board_layout[n_y][n_x]
                )
        return neighbors


    def get_plain_neighbors(self, x, y):
        all_neighbors = self.get_neighbors_of(x, y)
        return [n for n in all_neighbors if not n.is_mine and n.dangerous_neighbor_count() == 0]


    def ripple_step(self, x, y, known_plains=None):

        if known_plains is None:
            known_plains = []

        tile_neighbors = self.get_neighbors_of(x, y)

        # Reveal any hints and tiles
        hint_tiles = [t for t in tile_neighbors if not t.is_mine]
        for hint in hint_tiles:
            hint.is_revealed = True

        # find neighbors
        plain_neighbors = self.get_plain_neighbors(x, y)

        # Reduce neighbors to only new neighbors
        [plain_neighbors.remove(kp) for kp in known_plains if kp in plain_neighbors]

        # Add all currently known plains to known_plains
        [known_plains.append(pn) for pn in plain_neighbors]

        # for every tile in the newly discovered list
        for plain_tile in plain_neighbors:
            # discover neighbors, excluding _all_ knowns
            self.ripple_step(plain_tile.x, plain_tile.y, known_plains)

    def flag(self, x, y):
        self.board_layout[y][x].is_flagged = (not self.board_layout[y][x].is_flagged)


    def step_on(self, x, y):
        # Accessing list of lists is reversed of standard notation
        if self.board_layout[y][x].is_flagged:
            return False

        if self.board_layout[y][x].is_mine:

            for y_idx, row in enumerate(self.board_layout):
                for tile in row:
                    if tile.is_mine:
                        tile.is_revealed = True

            return True

        self.board_layout[y][x].is_revealed = True

        if self.board_layout[y][x].dangerous_neighbor_count() == 0:
            self.ripple_step(x, y)

        return False


game = Board(0.8)

user_input = None
died = False
while(user_input != "exit"):

    if died:
        game = None
        print(ASCII_COLORS[1] + "# # # # # # BLAMO # # # # # #" + ASCII_COLORS[0])
        print(ASCII_COLORS[1] + "# # # # YOU HAVE DIED # # # #" + ASCII_COLORS[0])

    if game is None:
        print()
        print("To start a new game, enter <new>")

    user_input = input("> ")

    if user_input in ["new", "restart"]:
        died = False
        game = Board()

    if user_input == "help":
        print("<Help message here>")

    if "flag" in user_input:
        coordinate_match = re.match("(\w+)(\s+)(\d+),(\d+)", user_input)
        x_coord = int( coordinate_match.group(3) )
        y_coord = int( coordinate_match.group(4) )
        print("Toggling flag on {},{}".format(x_coord, y_coord))
        game.flag(x_coord, y_coord)

    if "step" in user_input:
        coordinate_match = re.match("(\w+)(\s+)(\d+),(\d+)", user_input)
        x_coord = int( coordinate_match.group(3) )
        y_coord = int( coordinate_match.group(4) )
        print("Stepping on {},{}".format(x_coord, y_coord))
        died = game.step_on(x_coord, y_coord)
        game.print_board()

    if user_input in ["cheat", "map"]:
        game.print_board(True)

    if "?" in user_input:
        game.print_board()

print("Goodbye!")
