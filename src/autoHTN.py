import itertools

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


# Creates a method for each recipe in the json file given the name and the rule. The method will be called the name of the recipe.
# The method will return a list of tasks that need to be done to complete the recipe. NO OPS HERE
def make_method(name, rule):
    def method(state, ID):
        # Create a list of tasks that need to be done to complete the recipe
        tasks = []

        # I JUST REALIZED THAT WE CAN MAKE THIS SO MUCH BETTER
        crafting_order = ['ingot', 'coal', 'ore', 'cobble', 'stick', 'plank', 'wood']

        # Loop through any of the "Requires" items and call check_enough on them
        if 'Requires' in rule:
            # Loop through any of the "Requires" items and call have_enough on them
            for item, num in rule['Requires'].items():
                tasks.append(('have_enough', ID, item, num))

        # Check the consumed items in the order in which they are crafted
        if 'Consumes' in rule:
            for item in crafting_order:
                if item in rule['Consumes']:
                    tasks.append(('have_enough', ID, item, rule['Consumes'][item]))

        # Call the op method for the recipe name if it all checks out
        tasks.append(('op_' + str(name).replace(" ", "_"), ID))

        return tasks

    # Tag the function with the item it produces
    method.produces = next(iter(rule['Produces']))

    # Tag the function with the time it takes to produce the item
    method.time = rule['Time']

    # And now give it a cool name so I can debug without going crazy
    method.__name__ = str(name).replace(" ", "_")

    return method


def declare_methods(data):
    method_list = []

    #Create a method for each recipe in the json file
    for recipe_name, recipe_data in data['Recipes'].items():
        method_list.append(make_method(recipe_name, recipe_data))

    # Sort the methods by the item they produce and then by the time it takes to produce
    method_list.sort(key=lambda method: (method.produces, method.time))

    # Declare the methods to pyhop. Any methods that produce the same item should be declared together. Apparently
    # groupby is just a thing that exists? Awesome. https://www.geeksforgeeks.org/itertools-groupby-in-python/
    for key, group in itertools.groupby(method_list, key=lambda recipe: recipe.produces):
        pyhop.declare_methods("produce_" + key, *group)


def make_operator(rule):
    def operator(state, ID):
        # Check if the state has enough of the required items
        if 'Requires' in rule:
            for item, num in rule['Requires'].items():
                if getattr(state, item)[ID] < num:
                    return False

        # Check if the state has enough of the consumed items
        if 'Consumes' in rule:
            for item, num in rule['Consumes'].items():
                if getattr(state, item)[ID] < num:
                    return False

        # Check if the state has enough time
        if state.time[ID] < rule['Time']:
            return False

        # Remove the consumed items from the state
        if 'Consumes' in rule:
            for item, num in rule['Consumes'].items():
                getattr(state, item)[ID] -= num

        # Add the produced items to the state
        for item, num in rule['Produces'].items():
            getattr(state, item)[ID] += num

        # Subtract the time it took to produce the items
        state.time[ID] -= rule['Time']

        return state

    # Tag it just like the methods for easy debugging
    operator.produces = next(iter(rule['Produces']))
    operator.time = rule['Time']

    return operator


def declare_operators(data):
    operator_list = []

    # Create an operator for each recipe in the json file
    for recipe_name, recipe_data in data['Recipes'].items():
        temp_operator = make_operator(recipe_data)

        #I can't pass the name without changing the sig, so....
        temp_operator.__name__ = 'op_' + str(recipe_name).replace(" ", "_")
        operator_list.append(temp_operator)

    # Declare the operators to pyhop
    pyhop.declare_operators(*operator_list)


def add_heuristic(data, ID):
    # prune search branch if heuristic() returns True
    # do not change parameters to heuristic(), but can add more heuristic functions with the same parameters:
    # e.g. def heuristic2(...); pyhop.add_check(heuristic2)
    def heuristic(state, curr_task, tasks, plan, depth, calling_stack):

        # Trim if we are about to hit the recursion limit because that keeps happening
        if depth > 900:
            return True

        # This thing loves to make tools so lets make sure we only actually make them if they are useful.
        # I had chatGPT help me come up with how I should check these and the values for them. I could probably have done the math but they seem to work?
        # https://chatgpt.com/share/28db628e-4fed-4701-b15c-025bf079b80c
        # I've changed this a lot since then but the core idea is still the same
        if curr_task[0] == 'produce':
            item_produced = curr_task[2]
            goals = data['Goal'].keys()

            # Ensure that we only make one of each tool
            if item_produced in data['Tools']:
                if curr_task in calling_stack:
                    return True

            # Don't trim if the goal is a tool or it'll never make it
            if item_produced in goals:
                return False

            if item_produced == 'iron_pickaxe':

                time_saved = {
                    "coal": 1,
                    "ingot": 2,
                    "cobble": 1,
                }

                # run through everything and calculate the time saved
                time_saved_total = 0
                for task in filter(lambda task: task[0] == 'have_enough' and task[2] in time_saved.keys(), tasks):
                    time_saved_total += time_saved[task[2]] * task[3]

                # Check to see if we are gonna mine enough for it to matter
                if time_saved_total <= 18:  # Seems to be a good amount of time saved. idk
                    return True

            if item_produced == 'stone_pickaxe':
                # This one is a lot easier to make so we should almost always do it. Just make it if we need to mine more than a small amount
                required_mining = sum(
                    task[3] for task in filter(lambda task: task[0] == 'have_enough' and task[2] in {'cobble'}, tasks))
                if required_mining <= 7:  # If you have 7, then you are about to get a furnace. Just make a pick at that point
                    return True

            # We don't need one for the wooden pick because it is the only way to get cobble n stuff

            if item_produced in ('wooden_axe', 'stone_axe'):
                required_wood = sum(task[3] for task in
                                    filter(lambda task: task[0] == 'have_enough' and task[2] in {'wood', 'planks'},
                                           tasks))
                if required_wood <= 10 or (
                        required_wood <= 12 and item_produced == 'stone_axe'):  #  This was just a guess tbh
                    return True

            if item_produced == 'iron_axe':
                required_wood = sum(task[3] for task in
                                    filter(lambda task: task[0] == 'have_enough' and task[2] in {'wood', 'planks'},
                                           tasks))

                if required_wood <= 20:
                    return True

        # Don't try to do the same thing over and over again - doesn't work well
        max_repetitions = 10
        if len(calling_stack) > max_repetitions:
            last_tasks = calling_stack[-max_repetitions:]
            same_task_repeated = True
            for task in last_tasks:
                if task != curr_task:
                    same_task_repeated = False
                    break
            if same_task_repeated:
                return True

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

    state = set_up_state(data, 'agent', time=300)  # allot time here
    goals = set_up_goals(data, 'agent')

    declare_operators(data)
    declare_methods(data)
    add_heuristic(data, 'agent')

    # pyhop.print_operators()
    # pyhop.print_methods()

    # Hint: verbose output can take a long time even if the solution is correct;
    # try verbose=1 if it is taking too long
    pyhop.pyhop(state, goals, verbose=3)
    # pyhop.pyhop(state, [('have_enough', 'agent', 'cart', 1),('have_enough', 'agent', 'rail', 20)], verbose=1)
