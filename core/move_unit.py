# -*- coding: ascii -*-


def move_unit(data_map, start_coord, end_coord, player, enemy, data_ia):
    """Move an unit from a cell to another cell. And check if the move is legal.

    Parameters:
    -----------
    data_map: the whole database (dict)
    start_coord: coordinates at the origin of the movement (tuple)
    end_coord: coordinates at the destination of the movement (tuple)
    player: the player who is moving the unit (str)
    enemy: the other player (str)

    Returns:
    --------
    data_map: the database modified by the move (dict)

    Notes:
    ------
    The database will only change the coordinate of the units concerned.
    start_coord and end_coord will be tuple of int

    Version:
    --------
    specification: Laurent Emilie & Bienvenu Joffrey v.2 (17/02/16)
    implementation: Laurent Emilie & Bienvenu Joffrey v.2 (17/03/16)
    """

    # Check if there's a unit on the starting cell, and if the destination cell is free.
    if start_coord in data_map[player] and end_coord not in data_map[player]and end_coord not in data_map[enemy]:

        # Check if the move is rightful and save it.
        if start_coord[0] - 1 <= end_coord[0] <= start_coord[0] + 1 and start_coord[1] - 1 <= end_coord[1] <= start_coord[1] + 1:
            if data_map[player][start_coord][0] == 'E' or (sum(start_coord) - 1 <= sum(end_coord) <= sum(start_coord) + 1):
                data_map[player][end_coord] = data_map[player].pop(start_coord)
                data_ia[player][end_coord] = data_ia[player].pop(start_coord)
    return data_map, data_ia
