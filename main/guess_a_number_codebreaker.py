"""
Mastermind Game Play
"""
from random import choice
from itertools import product, permutations
from typing import Iterable
from collections import Counter

# variants
STANDARD = 0
NO_REPEATS = 1

# number of colors for code
BASIC = 6
SUPER = 8

# number of code pins
NORMAL = 4

# feedback
RIGHT_COLOR = 'o'
RIGHT_COLOR_AND_POSITION = '+'


def run(*, variant: int = STANDARD, colors: int = BASIC, pins: int = NORMAL) -> None:

    def init() -> None:
        possible_codes = {
            STANDARD: lambda c, p: list(product(range(c), repeat=p)),
            NO_REPEATS: lambda c, p: list(permutations(range(c), p)),
        }[variant](colors, pins)
        secret_code = choice(possible_codes)
        return secret_code, possible_codes
        
    def compare_codes(a: Iterable, b: Iterable) -> str:
        if len(a) != len(b):
            raise ValueError('Can not compare iterables of different length.')
        result = RIGHT_COLOR * sum((Counter(a) & Counter(b)).values())
        for x, y in zip(a, b):
            if x == y:
                result = result[1:] + RIGHT_COLOR_AND_POSITION
        return result

    secret_code, possible_codes = init()
    print(f'The secret code is one of {len(possible_codes)} possible combinations.')
    
    rounds = 0
    feedback = ''
    remaining_codes = possible_codes.copy()
    while feedback != '+' * pins:
        guess = choice(remaining_codes)
        if len(guess) != pins:
            print(f'Please give {pins} digits, separated by blanks.')
            continue
        rounds += 1
        feedback = compare_codes(secret_code, guess)
        remaining_codes = [
            code for code in remaining_codes if compare_codes(code, guess) == feedback]
        print(f'{rounds}: {guess} -> {feedback:4} | remaining choices: {len(remaining_codes)}')
        
    print(f'Code {secret_code} cracked in {rounds} rounds.')


if __name__ == '__main__':
    run()

# last line of code
