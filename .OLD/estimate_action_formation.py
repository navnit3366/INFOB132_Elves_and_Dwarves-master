# -*- coding: ascii -*-
import pickle


def estimate_action_formation(data_ia, are_enemy, where_enemies, is_formation):
    """Estimate which action may the group of units doing and compute amount of points to allow the action.

    Parameters:
    -----------
    data_ia: the whole database (dict)
    are_enemy: tells whether there are enemy in the surroundings (bool)
    where_enemies: position of the enemy's units (list)
    is_formation: tells where the units are in strategic formation (bool)

    Returns:
    --------
    action_type: actions with amount of points for each one (dict)

    Versions:
    ---------
    specification: Laurent Emilie v1 (19/04/16)
    implementation: Laurent Emilie v1 (25/04/16)
    """
    formation_scheme = pickle.load(open("formation_scheme.pkl", "rb"))
    if is_formation:
        #number of point

    #compute the range of action of ia and of enemy
    player_range={'ia':{}, 'enemy':{}}
    unit_type = ['D','E']
    player = ['ia','enemy']
    for player_id in player:
        for units in data_ia['ia']:
            for type in range(len(unit_type)):
                #check coordinates
                for i in range (1, (data_ia['map_size'])+1):
                    for j in range (1, (data_ia['map_size'])+1):
                        #save coordinates
                        if ((units[0] - (type+1)) <= i <= (units[0]+ (type+1))) and ((units[1]-(type+1)) <= j <= (units[1]+(type+1))):
                            if (i,j) not in player_range[type]:
                                player_range[player_id][(i,j)]=[]
                            player_range[player_id][(i,j)].append([type])

    #Remove our units from our range (and reciprocal for enemy)
    for player_id in player_range:
        for coord in player_id:
            if coord in data_ia[player_id]:
                del player_range[player_id][coord]

    #beginning diagram
    for adverse_coord in where_enemies:
        #check whether there is enemy in the action range
        if adverse_coord in player_range['ia']:
            damage = 0
            for unit in player_range['ia'][adverse_coord]:
                if unit == 'E':
                    damage += 1
                if unit == 'D':
                    damage += 3
            #check whether the enemy can die whether ia's units attacks
            if data_ia['enemy'][adverse_coord] <= damage:
                #ATTAQUER !!!
            else:
                #enemy looses damage HP

            #check if an ia unit can die whether enemy's unit attacks
            damage = 0
            ia_unit_dead = []
            for ia_coord in data_ia['ia']:
                if ia_coord in where_enemies:
                    for unit_id in player_range['enemy'][ia_coord]:
                        if unit_id == 'E':
                            damage += 1
                        if unit_id == 'D':
                            damage += 3
                    if ia_coord[0] <= damage:
                        #list of deaths
                        ia_unit_dead.append(ia_coord)
            if ia_unit_dead != []:
                #DEATH !!
            else:
            #Can ia's unit kill one enemy unit at the next turn ?
                for adverse_coord in where_enemies:
                    if adverse_coord in player_range['ia']:
                        damage = 0
                        for unit in player_range['ia'][adverse_coord]:
                            if unit == 'E':
                                damage += 1
                            if unit == 'D':
                                damage += 3
                        if data_ia['enemy'][adverse_coord] <= damage:
                            #ATTAQUER !!!
                        else:
                            #enemy looses damage HP
                    damage = 0
                    ia_unit_dead = []
                    for ia_coord in data_ia['ia']:
                        if ia_coord in where_enemies:
                            for unit_id in player_range['enemy'][ia_coord]:
                                if unit_id == 'E':
                                    damage += 1
                                if unit_id == 'D':
                                    damage += 3
                            if ia_coord[0] <= damage:
                                #list of deaths
                                ia_unit_dead.append(ia_coord)
                        if ia_unit_dead == []:
                            #DEATH !!
                        else:
                            #ATTACK !!!


        else:
            #Check whether there are enemy in my extended range (+1)

            #Compute the extended range (range +1)
            player_extended_range={'ia':{}, 'enemy':{}}
            unit_type = ['D','E']
            player = ['ia','enemy']
            for player_id in player:
                for units in data_ia['ia']:
                    for type in range(len(unit_type)):
                        #check coordinates
                        for i in range (1, (data_ia['map_size'])+1):
                            for j in range (1, (data_ia['map_size'])+1):
                                #save coordinates
                                if ((units[0] - (type+2)) <= i <= (units[0]+ (type+2))) and ((units[1]-(type+2)) <= j <= (units[1]+(type+2))):
                                    if (i,j) not in player_range[type]:
                                        player_extended_range[player_id][(i,j)]=[]
                                    player_extended_range[player_id][(i,j)].append([type])

            #May I dead whether I move to the enemy
            for adverse_coord in where_enemies:
                if adverse_coord in player_extended_range['ia']:
                    damage = 0
                    ia_unit_dead = []
                    for ia_coord in data_ia['ia']:
                        if ia_coord in where_enemies:
                            for unit_id in player_extended_range['enemy'][ia_coord]:
                                if unit_id == 'E':
                                    damage += 1
                                if unit_id == 'D':
                                    damage += 3
                            if ia_coord[0] <= damage:
                                #list of deaths
                                ia_unit_dead.append(ia_coord)
                    if ia_unit_dead != []:
                        # MOVE !!
                        # Can ia's unit kill one enemy unit at the next turn ?
                        for adverse_coord in where_enemies:
                            if adverse_coord in player_range['ia']:
                                damage = 0
                                for unit in player_range['ia'][adverse_coord]:
                                    if unit == 'E':
                                        damage += 1
                                    if unit == 'D':
                                        damage += 3
                                if data_ia['enemy'][adverse_coord] <= damage:
                                    #ATTAQUER !!!
                                else:
                                    #enemy looses damage HP
                            damage = 0
                            ia_unit_dead = []
                            for ia_coord in data_ia['ia']:
                                if ia_coord in where_enemies:
                                    for unit_id in player_range['enemy'][ia_coord]:
                                        if unit_id == 'E':
                                            damage += 1
                                        if unit_id == 'D':
                                            damage += 3
                                    if ia_coord[0] <= damage:
                                        #list of deaths
                                        ia_unit_dead.append(ia_coord)
                                if ia_unit_dead == []:
                                    #DEATH !!
                                elif ia_unit_dead != []:
                                    #ATTACK
                else:
                    #MOVE !! (to the enemy)

    return action_type
