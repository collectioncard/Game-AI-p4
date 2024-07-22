import random

import pyhop
import json


def check_enough(state, ID, item, num):
    if getattr(state, item)[ID] >= num: return []
    return False


def produce_enough(state, ID, item, num):
    return [('produce', ID, item), ('have_enough', ID, item, num)]


pyhop.declare_methods('have_enough', check_enough, produce_enough)


def produce(state, ID, item):
    return [('produce_{}'.format(item), ID)]


pyhop.declare_methods('produce', produce)


def make_method(name, rule):
    def method(state, ID):
        method_list = []
        # Loop though the requirements and verify with check_enough
        for req_name, req_quant in rule['Requires'].items():
            method_list.append(('check_enough', ID, req_name, req_quant))

        # loop though produces and call the op for it
        for output_name, output_quant in rule['Produces'].items():
            op_name = 'op_' + name.replace(' ', '_')
            method_list.append((op_name, ID))

        return method_list

    return method


def declare_methods(data):
    # some recipes are faster than others for the same product even though they might require extra tools
    # sort the recipes so that faster recipes go first
    # sort the recipes based on the time it takes to complete the recipe
    #TODO: Fix that
    sorted_recipes = {k: v for k, v in sorted(data['Recipes'].items(), key=lambda item: item[1]['Time'])}

    for recipe_name, recipe_data in sorted_recipes.items():
        temp = make_method(str(recipe_name).replace(" ", "_"), recipe_data)
        pyhop.declare_methods(str(recipe_name).replace(" ", "_"), temp)


def make_operator(rule):
    def operator(state, ID):
        print("Breakpoint")
        # Loop though the requirements and verify
        for req_name, req_quant in rule['Requires'].items():
            if getattr(state, req_name)[ID] < req_quant:
                return False

        # Decrement anything in the consumes list
        for consumable_name, consumable_quant in rule['Consumes'].items():
            # if getattr(state, consumable_name)[ID] < consumable_quant:
            # 	return False
            curr_val = getattr(state, consumable_name)[ID]
            new_val = curr_val - consumable_quant
            setattr(state, consumable_name, {ID: new_val})

        # increment state by the output of the recipe
        for out_name, out_quant in rule['Produces'].items():
            # get the current value of the item we are going to change
            curr_val = getattr(state, out_name)[ID]
            new_val = curr_val + out_quant
            setattr(state, out_name, {ID: new_val})

        # Modify the state to reflect the time taken to complete the recipe
        getattr(state, 'time')[ID] -= rule['Time']
        return state

    return operator


def declare_operators(data):
    recipes = data['Recipes']
    final_recipes = []
    for key, recipe in recipes.items():
        temp = make_operator(recipe)
        temp.__name__ = 'op_' + str(key).replace(" ", "_")
        final_recipes.append(temp)
    pyhop.declare_operators(*final_recipes)


def add_heuristic(data, ID):
    # prune search branch if heuristic() returns True
    # do not change parameters to heuristic(), but can add more heuristic functions with the same parameters:
    # e.g. def heuristic2(...); pyhop.add_check(heuristic2)
    def heuristic(state, curr_task, tasks, plan, depth, calling_stack):
        # your code here
        task = curr_task[0]
        if task.startswith('op_'):
            rule = task[3:].replace('_', ' ')
            if rule in data["Recipes"]:
                duration = data["Recipes"][rule].get("Time", 0)
                if state.time[ID] < duration:
                    return True
        if depth > 10 or (len(plan) > 1 and curr_task == plan[-1]):
            return True
        if len(calling_stack) != len(set(calling_stack)):
            return True
        if tasks:
            if getattr(state, tasks[0][2])[ID] >= tasks[0][3] or len(tasks):
                return True
        return False  # if True, prune this branch

    pyhop.add_check(heuristic)


def set_up_state(data, ID, time=0):
    state = pyhop.State('state')
    state.time = {ID: time}

    for item in data['Items']:
        setattr(state, item, {ID: 0})

    for item in data['Tools']:
        setattr(state, item, {ID: 0})

    for item, num in data['Initial'].items():
        setattr(state, item, {ID: num})

    return state


def set_up_goals(data, ID):
    goals = []
    for item, num in data['Goal'].items():
        goals.append(('have_enough', ID, item, num))

    return goals


if __name__ == '__main__':
    rules_filename = 'crafting.json'

    with open(rules_filename) as f:
        data = json.load(f)

    state = set_up_state(data, 'agent', time=239)  # allot time here
    goals = set_up_goals(data, 'agent')

    declare_operators(data)
    declare_methods(data)
    # add_heuristic(data, 'agent')

    # pyhop.print_operators()
    # pyhop.print_methods()

    # Hint: verbose output can take a long time even if the solution is correct;
    # try verbose=1 if it is taking too long
    pyhop.pyhop(state, goals, verbose=3)
    # pyhop.pyhop(state, [('have_enough', 'agent', 'cart', 1),('have_enough', 'agent', 'rail', 20)], verbose=3)
