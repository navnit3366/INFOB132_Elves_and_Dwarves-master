def ia_reflexion(data_ia, data_map, player):
    """Brain of the Artificial Intelligence.

    Parameters:
    -----------
    ia_data: the whole database (dict)

    Returns:
    --------
    data_ia: database for the ia (dict)
    data_map: database of the whole game (dict)
    player: tells which player is the ia (int)

    Versions:
    ---------
    specification: Bienvenu Joffrey & Laurent Emilie v.2 (28/04/16)
    implementation: Bienvenu Joffrey & Laurent Emilie v.3 (01/0516)
    """
    ia = 'player' + str(data_map['remote'])
    enemy = 'player' + str(3 - data_map['remote'])
    commands = {}

    new_positions = []
    moved_units = []

    for ia_unit in data_ia[ia]:
        unit_has_attacked = False
        unit_targets = []

        for enemy_unit in data_ia[enemy]:
            # Find each possible target for the Dwarves.
            if data_ia[ia][ia_unit][0] == 'D':
                if (ia_unit[0] - 1) <= enemy_unit[0] <= (ia_unit[0] + 1) and (ia_unit[1] - 1) <= enemy_unit[1] <= (ia_unit[1] + 1):
                    # Add the unit to the target list.
                    unit_targets.append(enemy_unit)

            # Find each possible target for the Elves - ATTACK
            else:
                for i in range(2):
                    if (ia_unit[0] - (1 + i)) <= enemy_unit[0] <= (ia_unit[0] + (1 + i)) and (ia_unit[1] - (1 + i)) <= enemy_unit[1] <= (ia_unit[1] + (1 + i)):
                        # Add the unit to the target list.
                        unit_targets.append(enemy_unit)

        # Find the weakest units.
        if unit_targets:
            target = unit_targets[0]
            for enemy_unit in unit_targets:
                if data_ia[enemy][enemy_unit][0] == 'D' or data_ia[enemy][enemy_unit][1] < data_ia[enemy][target][1]:
                    target = enemy_unit

            # Write the attack.
            commands[data_ia[ia][ia_unit][2]] = [ia_unit, ' -a-> ', target]
            unit_has_attacked = True

        # Find the weakest of all enemy's units - MOVE
        if not unit_has_attacked:
            target_list = data_ia[enemy].keys()
            target = target_list[0]

            for enemy_unit in data_ia[enemy]:
                if data_ia[enemy][enemy_unit][0] == 'D' or data_ia[enemy][enemy_unit][1] < data_ia[enemy][target][1]:
                    target = enemy_unit

            target_cell = [ia_unit[0], ia_unit[1]]
            # Move on Y axis
            if target and abs(ia_unit[1] - target[1]) > abs(ia_unit[0] - target[0]) and 1 <= ia_unit[0] <= data_map['map_size'] and 1 <= ia_unit[1] <= data_map['map_size']:
                if ia_unit[1] > target[1]:
                    target_cell[1] -= 1
                else:
                    target_cell[1] += 1
            # Move on X axis
            elif target and 1 <= ia_unit[0] <= data_map['map_size'] and 1 <= ia_unit[1] <= data_map['map_size']:
                if ia_unit[0] > target[0]:
                    target_cell[0] -= 1
                else:
                    target_cell[0] += 1

            new_target = False
            # Check if he can move on the targeted position.
            enemy_positions = data_ia[enemy].keys()
            ia_positions = data_ia[ia].keys()
            for units in moved_units:
                del ia_positions[ia_positions.index(units)]

            # If the units can't move, find another free cell.
            if target_cell in (new_positions or enemy_positions or ia_positions):
                new_target_cells = []
                for line in range(target_cell[0] - 1, target_cell[0] + 2):
                    for column in range(target_cell[1] - 1, target_cell[1] + 2):

                        # Append the possible free cell to the list.
                        if (line, column) not in (new_positions or enemy_positions or ia_positions):
                            new_target_cells.append((line, column))

                # Choose the nearest free cell.
                if new_target_cells:
                    new_target = new_target_cells[0]
                    for cell in new_target_cells:
                        if abs(ia_unit[0] - cell[0]) + abs(ia_unit[1] - cell[1]) < abs(ia_unit[0] - new_target[0]) + abs(ia_unit[1] - new_target[1]):
                            new_target = new_target_cells[new_target_cells.index(cell)]

            # Save the new target in the correct variable.
            if new_target:
                target_cell = new_target

            # Write the move
            if target_cell != ia_unit:
                commands[data_ia[ia][ia_unit][2]] = [ia_unit, ' -m-> ', target_cell]
                new_positions.append(target_cell)
                moved_units.append(ia_unit)

    return commands