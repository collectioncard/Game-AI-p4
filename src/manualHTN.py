import pyhop

'''begin operators'''


def op_punch_for_wood(state, ID):
    if state.time[ID] >= 4:
        state.wood[ID] += 1
        state.time[ID] -= 4
        return state
    return False


def op_craft_wooden_axe_at_bench(state, ID):
    if state.time[ID] >= 1 and state.bench[ID] >= 1 and state.plank[ID] >= 3 and state.stick[ID] >= 2:
        state.made_wooden_axe[ID] = True
        state.wooden_axe[ID] += 1
        state.plank[ID] -= 3
        state.stick[ID] -= 2
        state.time[ID] -= 1
        return state
    return False


# your code here
def op_craft_plank(state, ID):
    if state.time[ID] >= 1 and state.wood[ID] >= 1:
        state.plank[ID] += 4
        state.wood[ID] -= 1
        state.time[ID] -= 1
        return state
    return False


def op_craft_stick(state, ID):
    if state.time[ID] >= 1 and state.plank[ID] >= 2:
        state.stick[ID] += 4
        state.plank[ID] -= 2
        state.time[ID] -= 1
        return state
    return False


def op_craft_bench(state, ID):
    if state.time[ID] >= 1 and state.plank[ID] >= 4:
        state.made_bench[ID] = True
        state.bench[ID] += 1
        state.plank[ID] -= 4
        state.time[ID] -= 1
        return state
    return False


def op_wooden_axe_for_wood(state, ID):
    if state.time[ID] >= 2 and state.wooden_axe[ID] >= 1:
        state.wood[ID] += 1
        state.time[ID] -= 2
        return state
    return False


pyhop.declare_operators(op_punch_for_wood, op_craft_wooden_axe_at_bench, op_craft_plank, op_craft_stick, op_craft_bench,
                        op_wooden_axe_for_wood)

'''end operators'''


def check_enough(state, ID, item, num):
    if getattr(state, item)[ID] >= num: return []
    return False


def produce_enough(state, ID, item, num):
    return [('produce', ID, item), ('have_enough', ID, item, num)]


def produce(state, ID, item):
    if item == 'wood':
        if state.made_wooden_axe[ID]:
            return [('produce_wood_wooden_axe', ID)]
        else:
            # If we don't have an axe we should try to get stuff and make one
            return [('produce_wood_hand', ID)] + produce(state, ID, 'plank') + produce(state, ID, 'stick') + produce(
                state, ID, 'bench') + produce(state, ID, 'wooden_axe')
    elif item == 'wooden_axe':
        if state.made_wooden_axe[ID]:
            return False
        else:
            return [('produce_plank', ID), ('produce_stick', ID), ('produce_bench', ID),
                    ('produce_wooden_axe', ID)]
    elif item == 'plank':
        if state.wood[ID] >= 1:
            return [('produce_plank', ID)]
        else:
            if state.made_wooden_axe[ID]:
                return [('produce_wood_wooden_axe', ID)]
            else:
                return [('produce_wood_hand', ID)]
    elif item == 'stick':
        if state.plank[ID] >= 2:
            return [('produce_plank', ID), ('produce_stick', ID)]
        else:
            if state.made_wooden_axe[ID]:
                return [('produce_wood_wooden_axe', ID), ('produce_plank', ID)]
            return [('produce_wood_hand', ID), ('produce_plank', ID)]
    elif item == 'bench':
        if state.made_bench[ID]:
            return False

        if state.plank[ID] >= 4:
            return [('produce_plank', ID), ('produce_bench', ID)]
        else:
            return [('produce_wood_hand', ID), ('produce_plank', ID)]
    else:
        return False


pyhop.declare_methods('have_enough', check_enough, produce_enough)
pyhop.declare_methods('produce', produce)

'''begin recipe methods'''


def punch_for_wood(state, ID):
    return [('op_punch_for_wood', ID)]


def craft_wooden_axe_at_bench(state, ID):
    return [('have_enough', ID, 'bench', 1), ('have_enough', ID, 'stick', 2), ('have_enough', ID, 'plank', 3),
            ('op_craft_wooden_axe_at_bench', ID)]


def craft_plank(state, ID):
    return [('have_enough', ID, 'wood', 1), ('op_craft_plank', ID)]


def craft_stick(state, ID):
    return [('have_enough', ID, 'plank', 2), ('op_craft_stick', ID)]


def craft_bench(state, ID):
    return [('have_enough', ID, 'plank', 4), ('op_craft_bench', ID)]


def wooden_axe_for_wood(state, ID):
    return [('have_enough', ID, 'wooden_axe', 1), ('op_wooden_axe_for_wood', ID)]


# your code here

pyhop.declare_methods('produce_wood_hand', punch_for_wood)
pyhop.declare_methods('produce_wooden_axe', craft_wooden_axe_at_bench)
pyhop.declare_methods('produce_plank', craft_plank)
pyhop.declare_methods('produce_stick', craft_stick)
pyhop.declare_methods('produce_bench', craft_bench)
pyhop.declare_methods('produce_wood_wooden_axe', wooden_axe_for_wood)

'''end recipe methods'''

# declare state
state = pyhop.State('state')
state.wood = {'agent': 0}
state.time = {'agent': 46}
state.wooden_axe = {'agent': 0}
state.made_wooden_axe = {'agent': False}
# your code here
state.plank = {'agent': 0}
state.stick = {'agent': 0}
state.bench = {'agent': 0}
state.made_bench = {'agent': False}

pyhop.print_operators()
pyhop.print_methods()

# Execute the plan with the revised goal
# pyhop.pyhop(state, goal, verbose=3)
pyhop.pyhop(state, [('have_enough', 'agent', 'wood', 12)], verbose=3)
