# -*- coding: ascii -*-


def attack_unit(data_map, attacker_coord, target_coord, player, enemy, data_ia):
    """Attack an adverse cell and check whether it is a legal attack.

    Parameters:
    -----------
    data_map: the whole database (dict)
    attacker_coord: coordinates of the attacker's pawn (tuple)
    target_coord: coordinates of the attacked's pawn (tuple)
    player: the player who is attacking (str)
    enemy: the other player (str)

    Returns:
    --------
    data_map: the database modified by the attack (dict)

    Notes:
    ------
    The database will only change by decrement unit's life and, eventually, decrementing the unit's number of the player.
    attacker_coord and attacked_coord will be tuple of int.

    Version:
    -------
    specification: Laurent Emilie & Bienvenu Joffrey v.2 (17/03/16)
    implementation: Bienvenu Joffrey v.1 (17/03/16)
    """
    damage = {'E': 1, 'D': 3}
    attacked = 0

    # Check if there's a unit on the attacker cell, and if the attacked cell is occupied.
    if attacker_coord in data_map[player] and target_coord in data_map[enemy]:

        # Check if the attack is rightful and save it.
        if attacker_coord[0] - 2 <= target_coord[0] <= attacker_coord[0] + 2 and attacker_coord[1] - 2 <= target_coord[1] <= attacker_coord[1] + 2:
            attacker_type = data_map[player][attacker_coord][0]
            if attacker_type == 'E' or (attacker_coord[0] - 1 <= target_coord[0] <= attacker_coord[0] + 1 and attacker_coord[1] - 1 <= target_coord[1] <= attacker_coord[1] + 1):

                # Decrement the heal point and delete the unit if their hp are equal or less than 0.
                data_map[enemy][target_coord][2] -= damage[attacker_type]
                if data_map[enemy][target_coord][2] <= 0:
                    del data_map[enemy][target_coord]

                data_ia[enemy][target_coord][1] -= damage[attacker_type]
                if data_ia[enemy][target_coord][1] <= 0:
                    del data_ia[enemy][target_coord]

                attacked = 1

    return data_map, attacked, data_ia
