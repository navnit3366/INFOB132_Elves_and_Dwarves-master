# -*- coding: ascii -*-


def create_data_ia(map_size, id):
    """Create the ia database

    Parameters:
    -----------
    map_size: the length of the board game, every unit add one unit to vertical axis and horizontal axis (int, optional)
    id: tells which player is the ia (int)

    Returns:
    --------
    data_ia: the ia database (dict).

    Versions:
    ---------
    specifications: Laurent Emilie v.1 (24/04/16)
    implementation: Laurent Emilie v.1 (24/04/16)
    """
    data_ia = {'player1': {},
               'player2': {},
               'main_turn': 1,
               'attack_turn': 0,
               'map_size': map_size,
               'id': id}


    order_unit = {}
    order_unit['if_left'] = [(2,3), (3,2), (1,3), (2,2), (3,1), (1,2), (2,1), (1,1)]
    order_unit['if_right'] = [(map_size -1, map_size -2), (map_size -2, map_size -1), (map_size, map_size -2), (map_size -1, map_size -1), (map_size -1, map_size -1), (map_size -2, map_size), (map_size, map_size-1), (map_size -1, map_size), (map_size, map_size)]

    print order_unit

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

                    if i == 0:
                        unit_id = (order_unit['if_left'].index((x_pos,y_pos))) + 1
                        data_ia['player1'][(x_pos, y_pos)] = [unit, life, unit_id]
                    else:
                        unit_id = (order_unit['if_right'].index((x_pos,y_pos))) + 1
                        data_ia['player2'][(x_pos, y_pos)] = [unit, life, unit_id]

    return data_ia
