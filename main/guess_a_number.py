"""
An interactive set of helpers for a more successful operation of the board game "Mastermind" (Hasbro).

Reference:
- https://en.wikipedia.org/wiki/Mastermind_(board_game)
"""
import json
import sys
from cmd import Cmd
from collections import Counter
from itertools import product, permutations
from random import choice
from typing import Tuple, List


class SuperHirn(Cmd):
    intro = """
    Welcome to the interactive collection of helpers for the
    well known code-breaking game.
    """
    prompt = '(Mastermind) '

    STOP, CONTINUE = True, False

    session_mode = None

    settings = {
        'colors': 8,
        'pins': 4,
        'limit': 12,
        'repeat': True,
    }
    defaults = {k: v for k, v in settings.items()}

    secret_code = None
    possible_codes = None
    remaining_codes = None
    guesses = 0
    board = []
    game_over = False
    cracked = False

    def emptyline(self) -> bool:
        return False

    def precmd(self, line: str) -> str:
        return line.lower()

    # noinspection PyUnusedLocal
    def do_EOF(self, arg: str) -> bool:
        """Press ^D (^Z+<ENTER> on Windows) to quit the mastermind prompt."""
        print('Bye!')
        return self.STOP

    def do_eof(self, arg: str) -> bool:
        """Same as quit."""
        return self.do_EOF(arg)

    def do_quit(self, arg: str) -> bool:
        """Quit the mastemind prompt."""
        return self.do_EOF(arg)

    def help_show(self) -> None:
        for line in [
            'Show current session status or session settings: "show help|session|settings|[all]".',
            '"show help" or "help" show a list of all help topics.',
            'Default: "show [all]".',
        ]: print(line)

    def do_show(self, arg: str) -> bool:
        _, args = self.split_args(arg)
        if len(args) > 1:
            print(f'*** {self.lastcmd}: expected a single keyword but got {len(args)}.')
            return self.CONTINUE
        item = (args + ['all'])[0]
        try:
            {
                'session': self.show_session,
                'settings': self.show_settings,
                'all': self.show_all,
                'help': lambda: self.onecmd('help')
            }[item]()
        except KeyError:
            print(f'*** {self.lastcmd}: can not show unknown property.')
        return self.CONTINUE

    def help_set(self) -> None:
        for line in [
            'Set the game parameters: "set colors|pins|limit|repeat <value>", where ...',
            '- "colors" is the permitted number of code colors: 6 <= value <= 9, default 8',
            '- "pins" is the permitted number of code pins: value in {4, 5}, default 4',
            '- "limit" is the maximum number of guesses: value in {10, 12}, default 12',
            '- "repeat" says if clors may be repeated in codes or not: value is true or false, default true',
        ]: print(line)

    def do_set(self, arg: str) -> bool:
        if self.session_mode:
            print(f'*** {self.session_mode.capitalize()} session running, settings locked.')
            print('*** Settings can be changed after reset.')
            return self.CONTINUE
        _, args = self.split_args(arg)
        if len(args) != 2:
            print(f'*** {self.lastcmd}: expected a key and a value but got {len(args)} arguments.')
            return self.CONTINUE
        key, value = args
        if key not in self.settings:
            print(f'*** {self.lastcmd}: key not recognized.')
        try:
            if {
                'colors': lambda v: 4 <= int(v) <= 9,
                'pins': lambda v: int(v) in (4, 5),
                'limit': lambda v: int(v) in (10, 12),
                'repeat': lambda v: isinstance(json.loads(v), bool),
            }[key](value):
                self.settings[key] = {
                    'colors': lambda v: int(v),
                    'pins': lambda v: int(v),
                    'limit': lambda v: int(v),
                    'repeat': lambda v: json.loads(v),
                }[key](value)
            else:
                raise ValueError()
        except ValueError:
            print(f'*** {self.lastcmd}: value not recognized.')
        finally:
            return self.CONTINUE

    def do_reset(self, arg):
        """Reset session status and set game defaults."""
        argc, _ = self.split_args(arg)
        if argc:
            print(f'*** {self.lastcmd}: expected no arguments but got {argc}.')
        else:
            self.session_mode = None
            self.settings = {k: v for k, v in self.defaults.items()}
            self.possible_codes = None
            self.remaining_codes = None
            self.secret_code = None
            self.guesses = 0
            self.board.clear()
            self.game_over = False
            self.cracked = False
            print('+ Session ended. Mastermind set to defaults.')
        return self.CONTINUE

    def show_session(self) -> None:
        if self.session_mode:
            print(f'+ Mastermind is running in {self.session_mode} mode.')
            if self.session_mode == 'codemaker':
                print(f'+ Guesses so far: {self.guesses}')
                print(f'+ Remaining guesses: {self.settings["limit"] - self.guesses}')
                if self.game_over:
                    self.reveal()
                return
            if self.session_mode == 'codebreaker':
                print(f'+ Guesses so far: {self.guesses}')
                print(f'+ Remaining guesses: {self.settings["limit"] - self.guesses}')
                if self.game_over:
                    self.reveal()
                return
        else:
            print('+ Session not running.')

    def show_settings(self) -> None:
        for setting, value in self.settings.items():
            if setting in {'colors', 'pins'}:
                print(f'+ The number of code {setting} is {value}.')
            elif setting == 'limit':
                print(f'+ Maximum allowed guesses for codebreaking are {value}.')
            elif setting == 'repeat':
                print(f'+ Code colors may{" " if value else " not "}be repeated.')

    def show_all(self) -> None:
        self.show_settings()
        self.show_session()

    # noinspection PyUnusedLocal
    def do_board(self, arg: str) -> bool:
        """Show the current game board."""
        argc, _ = self.split_args(arg)
        if argc > 0:
            print(f'{self.lastcmd}: expected no further arguments, but got {argc}.')
            return self.CONTINUE
        code_width = 1 + self.settings['pins'] * 2
        print("  ." + "-" * (14 + code_width) + ".")
        heading = 'c o d e'.center(code_width)
        print(f'  | pos |{heading}| score |')
        print('  |' + "-" * (14 + code_width) + '|')
        for n in range(self.settings['limit']):
            if n < len(self.board):
                num = self.board[n][0]
                code = ' '.join(
                    [str(self.board[n][1][d]) for d in range(self.settings['pins'])]
                ).center(code_width)
                score = self.board[n][2][:self.settings['pins']]
                print(f'  | {num:3} |{code}| {score:5} |')
            else:
                print('  |     |' + ' ' * code_width + '|       |')
        print("  '" + "-" * (14 + code_width) + "'")
        return self.CONTINUE

    def do_guess(self, arg: str) -> bool:
        """Enter guess as a codebreaker in a codemaker session: "guess 1 2 3 4 [5]"."""
        if self.game_over:
            print('*** The game is over. Will not accept another guess.')
            return self.CONTINUE
        try:
            if self.session_mode != 'codemaker':
                raise AttributeError('not in session')
            if self.guesses >= self.settings['limit']:
                raise AttributeError('too many guesses')
            if self.cracked:
                raise AttributeError('already cracked')
            args = [int(a) for a in arg.split()]
            if len(args) != self.settings['pins']:
                raise ValueError('arg count')
            if any([a < 0 or a >= self.settings['colors'] for a in args]):
                raise ValueError('unknown color')
            if not self.settings['repeat'] and len(args) != len(set(args)):
                raise ValueError('repeats not allowed')
        except ValueError:
            print(f'*** Color codes must be in the range 0 ... {self.settings["colors"] - 1}.')
            print(f'*** Color codes may{" " if self.settings["repeat"] else " not "}be repeated.')
            print(f'*** Please enter exactly {self.settings["pins"]} single digits separated by blanks.')
        except AttributeError as e:
            if str(e) == 'not in session':
                print('+ You must be in a codemaker session for this to work.')
            elif str(e) == 'already cracked':
                self.reveal()
            else:
                print(f'+ Too many guesses. Secret code {self.secret_code} not broken. Game over.')
        else:
            self.guesses += 1
            score = self.score(tuple(args), self.secret_code)
            self.board.append((self.guesses, tuple(args), score))
            if self.guesses >= self.settings['limit'] and score != '+' * self.settings['pins']:
                self.game_over = True
                self.reveal()
            elif score == '+' * self.settings['pins']:
                self.game_over = True
                self.cracked = True
                self.reveal()
        return self.do_board(arg)

    def reveal(self) -> None:
        if self.cracked:
            print(f'+ Congratulations! The secret code {self.secret_code} has been cracked.')
        else:
            print(f'+ Game over. Secret code {self.secret_code} not broken.')

    def do_codemaker(self, arg: str) -> bool:
        """Switches mastermind to codemaker mode. Play a game against the machine, as a codebreaker."""
        if self.session_mode:
            print(f'*** Already in a {self.session_mode} session.')
            print('*** Reset first, then start a new session.')
            return self.CONTINUE
        argc, _ = self.split_args(arg)
        if argc:
            print(f'*** {self.lastcmd}: Expected single word but got {argc} additional item{"s" if argc > 1 else ""}.')
            return self.CONTINUE
        self.possible_codes = self.calculate_possible_codes()
        self.secret_code = choice(self.possible_codes)
        self.session_mode = 'codemaker'
        print(f'+ {self.session_mode.capitalize()} did '
              f'choose one secret code out of {len(self.possible_codes)}.')
        return self.CONTINUE

    def help_feedback(self) -> None:
        for line in [
            'Enter guess as a codemaker in a codebreaker session: "feedback <guess> <answer>", where ...',
            '- "guess" is the secret code, represented by four or five, as the current settings are',
            '- "answer" is the codemaker\'s response to the guess, with "-" meaning "no score",',
            '  and "o" meaning right color, and "+" meaning right color and place.',
        ]: print(line)

    def do_feedback(self, arg: str):
        if self.game_over:
            print('*** Game already over. Will not accept another feedback.')
            return self.CONTINUE
        argc, argv = self.split_args(arg)
        if argc != 1:
            print(f'{self.lastcmd}: expected one single argument, but got {argc}.')
            return self.CONTINUE
        try:
            if self.session_mode != 'codebreaker':
                raise AttributeError('not in session')
            if self.guesses >= self.settings['limit']:
                raise AttributeError('too many guesses')
            if self.cracked:
                raise AttributeError('already cracked')
            answer = argv[0]
            if len(answer) > self.settings['pins']:
                raise ValueError('too many feedback chars')
            if len(answer) == 1 and answer[0] == '-':
                answer = ''
            if [ch not in 'o+' for ch in answer].count(True):
                raise ValueError('unknown feedback symbol')
            answer_pins = Counter(answer)
            answer = 'o' * answer_pins['o'] + '+' * answer_pins['+']
        except ValueError:
            print(f'*** The answer of the codemaker can be a string of "o" and "+", or a single "-".')
        except AttributeError as e:
            if str(e) == 'not in session':
                print('+ You must be in a codebreaker session for this to work.')
            elif str(e) == 'already cracked':
                self.reveal()
            else:
                print('+ Too many guesses. Secret code not broken. Game over.')
        else:
            self.guesses += 1
            self.remaining_codes = self.calculate_remaining_codes(self.secret_code, answer)
            self.board.append((self.guesses, self.secret_code, answer))
            self.do_board('')
            if answer == '+' * self.settings['pins']:
                self.cracked = True
                self.game_over = True
                self.reveal()
            elif self.guesses >= self.settings['limit'] and answer != '+' * self.settings['pins']:
                self.game_over = True
                print('+ Too many guesses. Secret code not cracked. Game over.')
            else:
                self.secret_code = choice(self.remaining_codes)
                print(f'+ Next guess: {self.secret_code}.')
        return self.CONTINUE

    def do_codebreaker(self, arg: str) -> bool:
        """Switches mastermind to codebreaker mode. Let the machine crack the code based on codemaker feedbacks."""
        if self.session_mode:
            print(f'*** Already in a {self.session_mode} session.')
            print('*** Reset first, then start a new session.')
            return self.CONTINUE
        argc, _ = self.split_args(arg)
        if argc:
            print(f'*** {self.lastcmd}: Expected single word but got {argc} additional item{"s" if argc > 1 else ""}.')
            return self.CONTINUE
        self.remaining_codes = self.calculate_possible_codes()
        self.session_mode = 'codebreaker'
        print(f'+ Now in {self.session_mode} mode.')
        self.secret_code = choice(self.remaining_codes)
        print(f'+ First guess: {self.secret_code}. Ready for feedbacks.')
        return self.do_show('settings')

    def calculate_possible_codes(self) -> List[Tuple[int, ...]]:
        return {
            True: lambda c, p: list(product(range(c), repeat=p)),
            False: lambda c, p: list(permutations(range(c), p)),
        }[self.settings['repeat']](self.settings['colors'], self.settings['pins'])

    def calculate_remaining_codes(self, guess: Tuple[int, ...], feedback: str) -> List[Tuple[int, ...]]:
        return [
            code
            for code in self.remaining_codes
            if self.score(code, guess) == feedback and code != guess
        ]

    @staticmethod
    def score(a: Tuple[int, ...], b: Tuple[int, ...]) -> str:
        if len(a) != len(b):
            raise ValueError('*** Can not compare iterables of different length.')
        result = 'o' * sum((Counter(a) & Counter(b)).values())
        for x, y in zip(a, b):
            if x == y:
                result = result[1:] + '+'
        return result

    @staticmethod
    def split_args(arg: str) -> Tuple[int, List[str]]:
        argv = arg.split()
        argc = len(argv)
        return argc, argv


if __name__ == '__main__':
    app = SuperHirn()
    try:
        app.cmdloop()
    except KeyboardInterrupt:
        print('^C')
        app.onecmd('quit')
    sys.exit(0)

# last line of code
