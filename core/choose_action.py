# -*- coding: ascii -*-


def choose_action(data_map, connection, data_ia):
    """Ask and execute the instruction given by the players to move or attack units.

    Parameters:
    ----------
    data_map: the whole database (dict)

    Returns:
    -------
    data_map: the database changed by moves or attacks (dict)

    Notes:
    -----
    Instructions must be in one line, with format xx_xx -a-> xx_xx for an attack and xx_xx -m-> xx_xx for a movement.
    Each instruction must be spaced by 3 characters.

    Version:
    -------
    specification: Laurent Emilie v.1 (11/02/16)
    implementation: Laurent Emilie v.3 (21/03/16)
    """
    player = 'player' + str((data_map['main_turn'] % 2) + 1)
    enemy = 'player' + str(2 - (data_map['main_turn'] % 2))
    if data_map['remote']:
        player = 'player' + str(data_map['remote'])
        enemy = 'player' + str(3 - data_map['remote'])

    # Tells whether IA or player's turn.
    # if (data_map['main_turn'] % 2) + 2 == data_map['remote'] or data_map['main_turn'] % 2 == data_map['remote'] or data_map[str(player + 'info')][1] == 'IA':
    if data_map['main_turn'] % 2 == data_map['remote'] % 2 or data_map[str(player + 'info')][1] == 'IA':
        game_instruction = ia_action(data_map, data_ia, player)
        if data_map['remote']:
            notify_remote_orders(connection, game_instruction)
    else:
        if data_map['remote']:
            player = 'player' + str(3 - data_map['remote'])
            enemy = 'player' + str(data_map['remote'])
            game_instruction = get_remote_orders(connection)
        else:
            game_instruction = raw_input('Enter your commands in format xx_xx -a-> xx_xx or xx_xx -m-> xx_xx')

    # Split commands string by string.
    list_action = game_instruction.split()

    # grouper instruction par instructions
    list_action2 = []
    for instruction in range(0, len(list_action), 3):
        list_action2.append((list_action[instruction], list_action[instruction + 1], list_action[instruction + 2]))

    # Call attack_unit or move_unit in function of instruction.
    attack_counter = 0
    for i in range(len(list_action2)):
        if '-a->' in list_action2[i]:
            data_map, attacked, data_ia = attack_unit(data_map, (int(list_action2[i][0][:2]), int(list_action2[i][0][3:])),
                        (int(list_action2[i][2][:2]), int(list_action2[i][2][3:])), player, enemy, data_ia)
            attack_counter += attacked
        elif '-m->' in list_action2[i]:
            data_map, data_ia = move_unit(data_map, (int(list_action2[i][0][:2]), int(list_action2[i][0][3:])),
                      (int(list_action2[i][2][:2]), int(list_action2[i][2][3:])), player, enemy, data_ia)

    # Save if a player have attacked.
    if attack_counter:
        data_map['attack_turn'] = 0
    else:
        data_map['attack_turn'] += 1
    data_map['main_turn'] += 1

    return data_map
