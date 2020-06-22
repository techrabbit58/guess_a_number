"""
Mastermind Game Play: Code Maker
"""
import sys
from argparse import ArgumentParser
from random import choice
from itertools import product, permutations
from typing import Iterable, Tuple, List
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

    def init() -> Tuple[Tuple, List[Tuple]]:
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

    def get_guess():
        try:
            guess = tuple(
                int(ch) for ch in input('Make a guess: ').split() if 0 <= int(ch) < 10)
        except KeyboardInterrupt:
            print('\nBye!')
            sys.exit(12)
        except ValueError:
            print(f'Your input must be: a series of {pins} single digits, separated by blanks.')
            guess = None
        if len(guess) != pins:
            print(f'Please give {pins} digits, separated by blanks.')
            guess = None
        return guess

    secret_code, possible_codes = init()
    print(f'The secret code is one of {len(possible_codes)} possible combinations.')
    
    rounds = 0
    feedback = ''
    while feedback != '+' * pins:
        guess = get_guess()
        if not guess:
            continue
        rounds += 1
        feedback = compare_codes(secret_code, guess)
        remaining_codes = len([
            code for code in possible_codes if compare_codes(code, guess) == feedback])
        print(f'{rounds}: {guess} -> {feedback:4} | other codes like this: {remaining_codes}')
        
    print(f'Code {secret_code} cracked in {rounds} rounds.')


def parse_args():
    parser = ArgumentParser(description='Make an unbreakable code like a mastermind!', usage='%(prog)s [options]')
    parser.add_argument('--colors', dest='num_colors', default=6, type=int,
                        help='set the number of different colors (default = 6)')
    parser.add_argument('--pins', dest='num_pins', default=4, type=int,
                        help='set the number of code pins (default = 4)')
    parser.add_argument('--no_repeats', action='store_true', help='do not repeat colors in code')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    run(
        colors=args.num_colors,
        pins=args.num_pins,
        variant=NO_REPEATS if args.no_repeats else STANDARD
    )

# last line of code
