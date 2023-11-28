# -*- coding: ascii -*-
from colorama import Fore
import random


def create_data_map(remote, map_size=7, name_player1, name_player2, clear=False):
    """ Create a dictionary that the game will use as database with units at their initial places.

    Parameters:
    ----------
    map_size : the length of the board game, every unit add one unit to vertical axis and horizontal axis (int, optional).
    name_player1: name of the first player (str)
    name_player2: name of the second player (str)
    clear: if you want to activate the clear screen (bool)

    Returns:
    -------
    data_map : dictionary that contain information's of every cells of the board (dict).
    data_ui : list with data to display the ui (list of str).

    Notes:
    -----
    The game board is a square, the size must be a positive integer, minimum 7 and maximum 30 units,
    or the game will be stopped after 20 turns if nobody attack.

    Version:
    -------
    specification: Maroit Jonathan & Bienvenu Joffrey v.2 (04/03/16)
    implementation: Maroit Jonathan & Bienvenu Joffrey & Laurent Emilie v.5 (23/03/16)
    """
    # Initialisation of variables
    data_map = {'player1': {},
                'player1info': [],
                'player2': {},
                'player2info': [],
                'main_turn': 1,
                'attack_turn': 0,
                'map_size': map_size,
                'remote': remote}

    # Place units to their initial positions.
    player_data = [Fore.BLUE, Fore.RED, name_player1, name_player2]
    for i in range(2):
        for line in range(1, 4):
            for column in range(1, 4):
                unit = 'E'
                life = 4

                if line >= 2 and column >= 2:
                    unit = 'D'
                    life = 10

                if line + column != 6:
                    x_pos = abs(i * map_size - line + i)
                    y_pos = abs(i * map_size - column + i)

                    data_map['player' + str(i + 1)][(x_pos, y_pos)] = [unit, player_data[i], life]
        data_map['player' + str(i + 1) + 'info'].extend([player_data[i], player_data[i + 2]])

    if not remote:
        # Randomize which player will start the game.
        number = random.randint(1, 2)
        if number == 1:
            data_map['player1info'][1] = name_player1
            data_map['player2info'][1] = name_player2
        else:
            data_map['player1info'][1] = name_player2
            data_map['player2info'][1] = name_player1

    data_map['data_ui'] = create_data_ui(data_map, clear)

    return data_map
