import itertools

def bitGen(n):
    return list(itertools.product([0, 1], repeat=n))

bits_3 = bitGen(3)

print(bits_3)

index = bits_3.index((1,0,0))

print(index)

bits_1 = bitGen(1)

print(bits_1)

list_to_tuple = tuple([1])
print(list_to_tuple)

list_to_tuple = [1,2]
print(list_to_tuple)

list_to_tuple = tuple(list_to_tuple)
print(list_to_tuple)

num_treats = 3

treat_list = list()

for i in range(num_treats):
    treat_list.append("treat" + str(i))

print(treat_list)