"""
Mastermind Game Play: Code Breaker
"""
import sys
from argparse import ArgumentParser
from collections import Counter
from itertools import product, permutations
from random import choice
from typing import List, Tuple, Iterable

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


def run(code, *, variant: int = STANDARD, colors: int = BASIC, pins: int = NORMAL) -> None:
    def init() -> Tuple[Tuple, List[Tuple]]:
        possible_codes = {
            STANDARD: lambda c, p: list(product(range(c), repeat=p)),
            NO_REPEATS: lambda c, p: list(permutations(range(c), p)),
        }[variant](colors, pins)
        return possible_codes

    def compare_codes(a: Iterable, b: Iterable) -> str:
        if len(a) != len(b):
            raise ValueError('Can not compare iterables of different length.')
        result = RIGHT_COLOR * sum((Counter(a) & Counter(b)).values())
        for x, y in zip(a, b):
            if x == y:
                result = result[1:] + RIGHT_COLOR_AND_POSITION
        return result

    def reduce_choices() -> List[Tuple]:
        return [
            code
            for code in remaining_codes
            if compare_codes(code, guess) == feedback and code != guess
        ]

    secret_code = code
    possible_codes = init()
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
        remaining_codes = reduce_choices()
        print(f'{rounds}: {guess} -> {feedback:4} | remaining choices: {len(remaining_codes)}')

    print(f'You cracked the secret code {secret_code} with {rounds} tries.')


def parse_args():
    parser = ArgumentParser(description='Break the code like a mastermind!', usage='%(prog)s [options]')
    parser.add_argument('digits', type=int, nargs='+', help='your code digits')
    parser.add_argument('--colors', dest='num_colors', default=6, type=int,
                        help='set the number of different colors (default = 6)')
    parser.add_argument('--pins', dest='num_pins', default=4, type=int,
                        help='set the number of code pins (default = 4)')
    parser.add_argument('--no_repeats', action='store_true', help='do not repeat colors in code')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    if len(args.digits) != args.num_pins:
        print(f'Bad code: {args.digits}.')
        print(f'Please give {args.num_pins} digits, separated by blanks.')
        sys.exit(4)
    for d in args.digits:
        if not 0 <= d < 10:
            print(f'Bad color: {d}.')
            print(f'All color codes must be single digits 0 <= d < 10.')
            sys.exit(4)
    run(
        args.digits,
        colors=args.num_colors,
        pins=args.num_pins,
        variant=NO_REPEATS if args.no_repeats else STANDARD
    )

# last line of code
