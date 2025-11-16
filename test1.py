import itertools
from collections import defaultdict

# Actions agent can choose to take
ACTIONS = ['UP', 'DOWN', 'LEFT', 'RIGHT']

def get_q_value(state, action):

    """Return Q(s,a), defaulting to 0.0 if unseen."""
    return q_table_dict[state].get(action, 0.0)

q_table_dict = defaultdict(dict)

q_table_dict[(1,1)]["UP"] = 1
q_table_dict[(1,1)]["DOWN"] = 2
q_table_dict[(1,1)]["RIGHT"] = 1
q_table_dict[(1,1)]["LEFT"] = 3

print(get_q_value((1,1), "UP"))
print(get_q_value((1,1), "DOWN"))
print(get_q_value((1,2), "RIGHT"))

print(q_table_dict)

q_values = [(get_q_value((1,1), a), a) for a in ACTIONS]

max_q = max(q_values, key=lambda x: x[0])[0]

# if multiple actions tie, choose among the best randomly
best_actions = [a for (q, a) in q_values if q == max_q]

print(q_values)
print(best_actions)

# def bitGen(n):
#     return list(itertools.product([0, 1], repeat=n))

# bits_3 = bitGen(3)

# print(bits_3)

# index = bits_3.index((1,0,0))

# print(index)

# bits_1 = bitGen(1)

# print(bits_1)

# list_to_tuple = tuple([1])
# print(list_to_tuple)

# list_to_tuple = [1,2]
# print(list_to_tuple)

# list_to_tuple = tuple(list_to_tuple)
# print(list_to_tuple)

# num_treats = 3

# treat_list = list()

# for i in range(num_treats):
#     treat_list.append("treat" + str(i))

# print(treat_list)