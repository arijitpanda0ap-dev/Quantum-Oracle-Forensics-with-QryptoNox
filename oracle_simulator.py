#first simple oracle

def constant_oracle(x, secret):
    return secret


#different inputs
print("Input 0:", constant_oracle(0, 1))
print("Input 5:", constant_oracle(5, 1))
print("Input 100:", constant_oracle(100, 1))
print("Input 255:", constant_oracle(255, 1))

print("Input 5:", constant_oracle(5, 0))


def linear_oracle(x, a, b):
    matching_bits = x & a
    parity = bin(matching_bits).count("1") % 2
    return parity ^ b


print("Linear test 1:", linear_oracle(5, 5, 0))
print("Linear test 2:", linear_oracle(5, 1, 0))
print("Linear test 3:", linear_oracle(5, 1, 1))


print("\nTesting the linear oracle:")

a = 5
b = 0

for x in range(8):
    result = linear_oracle(x, a, b)
    print("Input:", x, "| Output:", result)


def recover_a(oracle, b):
    for candidate in range(1, 8):
        matches = True

        for x in range(8):
            expected = linear_oracle(x, candidate, b)

            if oracle(x) != expected:
                matches = False
                break

        if matches:
            return candidate

    return None


#Pretend this oracle's hidden value is unknown to us.
hidden_a = 5
hidden_b = 0

def secret_oracle(x):
    return linear_oracle(x, hidden_a, hidden_b)


found_a = recover_a(secret_oracle, hidden_b)
print("Recovered a:", found_a)


def recover_a_and_b(oracle):
    for candidate_b in range(2):
        for candidate_a in range(1, 8):
            matches = True

            for x in range(8):
                expected = linear_oracle(
                    x, candidate_a, candidate_b
                )

                if oracle(x) != expected:
                    matches = False
                    break

            if matches:
                return candidate_a, candidate_b

    return None, None


# The oracle has hidden values.
'''hidden_a = 5
hidden_b = 1'''

'''hidden_a = 3
hidden_b = 0'''

hidden_a = 6
hidden_b = 1

def secret_oracle_2(x):
    return linear_oracle(x, hidden_a, hidden_b)


found_a, found_b = recover_a_and_b(secret_oracle_2)

print("Recovered a:", found_a)
print("Recovered b:", found_b)


def detect_constant(oracle):
    first_output = oracle(0)

    for x in range(1, 8):
        if oracle(x) != first_output:
            return False

    return True


def example_constant_oracle(x):
    return 1


print("Is constant:", detect_constant(example_constant_oracle))


def example_changing_oracle(x):
    return x % 2


print(
    "Is changing oracle constant:",
    detect_constant(example_changing_oracle)
)


def detect_balanced(oracle):
    zero_count = 0
    one_count = 0

    for x in range(8):
        result = oracle(x)

        if result == 0:
            zero_count += 1
        else:
            one_count += 1

    return zero_count == 4 and one_count == 4


def example_balanced_oracle(x):
    return x % 2


print("Is balanced:", detect_balanced(example_balanced_oracle))


def example_unbalanced_oracle(x):
    if x == 0:
        return 1
    return 0


print(
    "Is unbalanced oracle balanced:",
    detect_balanced(example_unbalanced_oracle)
)


def grover_oracle(x, marked_input):
    if x == marked_input:
        return 1
    return 0


marked_input = 5

print("Grover test:")
for x in range(8):
    print(x, "->", grover_oracle(x, marked_input))

def recover_marked_input(oracle):
    for x in range(8):
        if oracle(x) == 1:
            return x
    return None


hidden_input = 6

def secret_grover_oracle(x):
    return grover_oracle(x, hidden_input)


found_input = recover_marked_input(secret_grover_oracle)

print("Recovered marked input:", found_input)

def simon_oracle(x, secret):
    return min(x, x ^ secret)


hidden_secret = 3

print("Simon oracle test:")
for x in range(8):
    print(x, "->", simon_oracle(x, hidden_secret))

def recover_simon_secret(oracle):
    for secret in range(1, 8):
        matches = True

        for x in range(8):
            if oracle(x) != oracle(x ^ secret):
                matches = False
                break

        if matches:
            return secret

    return None


found_secret = recover_simon_secret(
    lambda x: simon_oracle(x, hidden_secret)
)

print("Recovered Simon secret:", found_secret)

import random

def randfun_oracle(x):
    return 1 if random.random() < 0.30 else 0


print("Random-function oracle test:")
for x in range(8):
    print(x, "->", randfun_oracle(x))