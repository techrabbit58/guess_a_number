"""
An interactive set of helpers for a more successful operation of the board game "Mastermind" (Hasbro).

Reference:
- https://en.wikipedia.org/wiki/Mastermind_(board_game)
"""
import sys
from cmd import Cmd
from collections import Counter
from itertools import product, permutations
from random import choice
from typing import Tuple, List, Union


class SuperHirn(Cmd):
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
    
    colormap = {
        0: 'white',
        1: 'red',
        2: 'green',
        3: 'cyan',
        4: 'purple',
        5: 'yellow',
        6: 'brown',
        7: 'orange',
        8: '(blank)',
    }
    reverse_colormap = {v, k for k, v in colormap}

    secret_code = None
    possible_codes = None
    remaining_codes = None
    guesses = 0
    board = []
    game_over = False
    cracked = False
    
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.possible_codes = self.calculate_possible_codes()

    def emptyline(self) -> bool:
        return False

    def precmd(self, line: str) -> str:
        return line.lower()

    def got_arguments(self, arg: str) -> bool:
        return bool(len(arg))

    def got_all_valid_digits(self, arg: str) -> Union[None, Tuple[int, ...]]:
        argc, argv = self.split_args(arg)
        if argc != self.settings['pins']:
            return None
        for d in argv:
            if d not in list('0123456789')[:self.settings['colors']]:
                return None
        if not self.settings['repeat'] and len(argv) == len(set(argv)):
            return None
        return tuple(int(d) for d in argv)

    def got_valid_feedback_string(self, arg: str) -> Union[None, str]:
        if arg == '':
            return None
        if arg == '-':
            return ''
        for ch in arg:
            if ch not in 'o+':
                return None
        answer_pins = Counter(arg)
        arg = 'o' * answer_pins['o'] + '+' * answer_pins['+']
        if len(arg) > self.settings['pins']:
            return None
        else:
            return arg

    def got_one_or_less_arguments(self, arg: str) -> Union[None, List[str]]:
        argc, argv = self.split_args(arg)
        return None if argc > 1 else argv

    def got_exactly_two_arguments(self, arg: str) -> Union[None, List[str]]:
        argc, argv = self.split_args(arg)
        return None if argc != 2 else argv

    # noinspection PyUnusedLocal
    def do_eof(self, arg: str) -> bool:
        """Press ^D (^Z+<ENTER> on Windows) to quit the mastermind prompt."""
        print()
        return self.exit_cmdloop()

    # noinspection PyUnusedLocal
    def do_quit(self, arg: str) -> bool:
        """Quit the mastemind prompt."""
        return self.exit_cmdloop()
        
    def exit_cmdloop(self) -> bool:
        print('Bye!')
        return self.STOP

    def help_show(self) -> None:
        for line in [
            'Show current session status or session settings: "show help|session|settings|[all]".',
            '"show help" or "help" show a list of all help topics.',
            'Default: "show [all]".',
        ]: print(line)

    def do_show(self, arg: str) -> bool:
        argv = self.got_one_or_less_arguments(arg)
        if arg is None:
            return self.wrong_number_of_arguments_help_hint()
        arg = (argv + ['all'])[0]
        try:
            {
                'session': self.show_session,
                'settings': self.show_settings,
                'all': self.show_all,
                'help': lambda: self.onecmd('help'),
            }[arg]()
        except KeyError:
            return self.settings_help_hint()
        finally:
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
        if self.in_session():
            return self.settings_locked_notification()
        argv = self.got_exactly_two_arguments(arg)
        if argv is None:
            return self.wrong_number_of_arguments_help_hint()
        key, value = self.argv_is_key_value_pair(argv)
        print(key, value)
        if key is None:
            return self.wrong_argument_type_hint()
        self.settings[key] = value
        self.possible_codes = self.calculate_possible_codes()
        return self.CONTINUE

    def do_reset(self, arg):
        """Reset session status and set game defaults."""
        if self.got_arguments(arg):
            return self.arguments_not_expected_help_hint()
        self.session_mode = None
        self.settings = {k: v for k, v in self.defaults.items()}
        self.possible_codes = self.calculate_possible_codes()
        self.remaining_codes = None
        self.secret_code = None
        self.guesses = 0
        self.board.clear()
        self.game_over = False
        self.cracked = False
        print('+ Session ended. Mastermind set to defaults.')
        return self.CONTINUE

    def show_session(self) -> None:
        if self.in_session():
            print(f'+ Mastermind is running in {self.session_mode} mode.')
            if self.session_mode == 'codemaker':
                print(f'+ Guesses so far: {self.guesses}')
                print(f'+ Remaining guesses: {self.settings["limit"] - self.guesses}')
                if self.game_over:
                    self.reveal()
                return None
            if self.session_mode == 'codebreaker':
                print(f'+ Guesses so far: {self.guesses}')
                print(f'+ Remaining guesses: {self.settings["limit"] - self.guesses}')
                if self.game_over:
                    self.reveal()
                else:
                    print(f'+ Last guess awaiting feedback: {self.secret_code}.')
                return None
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
        print(f'+ With this settings there are {len(self.possible_codes)} codes possible to make.')

    def show_all(self) -> None:
        self.show_settings()
        self.show_session()

    # noinspection PyUnusedLocal
    def do_board(self, arg: str) -> bool:
        """Show the current game board."""
        if self.got_arguments(arg):
            return self.arguments_not_expected_help_hint()
        else:
            return self.show_board()

    def show_board(self) -> bool:
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
        if not self.is_in_session('codemaker'):
            return self.wrong_session_mode_hint('codemaker')
        if self.is_game_over():
            return self.game_over_warning('guess')
        if self.is_guesses_limit_reached():
            return self.guesses_limit_reached()
        if self.is_already_cracked():
            return self.already_cracked_hint()
        argv = self.got_all_valid_digits(arg)
        if argv is None:
            return self.wrong_arguments_help_hint()
        self.guesses += 1
        score = self.score(argv, self.secret_code)
        self.board.append((self.guesses, argv, score))
        self.show_board()
        if self.guesses >= self.settings['limit'] and score != '+' * self.settings['pins']:
            self.game_over = True
            self.reveal()
        elif score == '+' * self.settings['pins']:
            self.game_over = True
            self.cracked = True
            self.reveal()
        return self.CONTINUE

    def reveal(self) -> None:
        if self.cracked:
            print(f'+ Congratulations! The secret code {self.secret_code} has been cracked.')
        else:
            print(f'+ Game over. Secret code {self.secret_code} not broken.')

    def do_codemaker(self, arg: str) -> bool:
        """Switches mastermind to codemaker mode. Play a game against the machine, as a codebreaker."""
        if self.in_session():
            return self.already_in_session_hint()
        if self.got_arguments(arg):
            return self.arguments_not_expected_help_hint()
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

    # noinspection PyUnusedLocal
    def do_done(self, arg: str) -> bool:
        """A shortcut for "feedback ++++[+]"."""
        return self.do_feedback('+' * self.settings['pins'])

    def do_feedback(self, arg: str):
        if not self.is_in_session('codebreaker'):
            return self.wrong_session_mode_hint('codebreaker')
        if self.is_game_over():
            return self.game_over_warning('feedback')
        if self.is_guesses_limit_reached():
            return self.guesses_limit_reached()
        if self.is_already_cracked():
            return self.already_cracked_hint()
        answer = self.got_valid_feedback_string(arg)
        if answer is None:
            return self.wrong_arguments_help_hint()
        self.guesses += 1
        self.remaining_codes = self.calculate_remaining_codes(self.secret_code, answer)
        self.board.append((self.guesses, self.secret_code, answer))
        self.show_board()
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
        if self.in_session():
            return self.already_in_session_hint()
        if self.got_arguments(arg):
            return self.arguments_not_expected_help_hint()
        self.remaining_codes = self.possible_codes[:]
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

    def settings_help_hint(self) -> bool:
        command = self.lastcmd.split()[0]
        print(f'*** {command}: unknown setting. Try "help {command}".')
        return self.CONTINUE

    def wrong_number_of_arguments_help_hint(self) -> bool:
        command = self.lastcmd.split()[0]
        print(f'*** {command}: wrong number of arguments. Try "help {command}".')
        return self.CONTINUE

    def wrong_arguments_help_hint(self) -> bool:
        command = self.lastcmd.split()[0]
        print(f'*** {command}: Something wrong with the arguments?. Try "help {command}".')
        return self.CONTINUE

    def arguments_not_expected_help_hint(self) -> bool:
        command = self.lastcmd.split()[0]
        print(f'*** {command}: did not expect an argument. Try "help {command}".')
        return self.CONTINUE

    def in_session(self) -> bool:
        return self.session_mode is not None

    def settings_locked_notification(self) -> bool:
        print(f'*** {self.session_mode.capitalize()} session running, settings locked.')
        return self.CONTINUE

    def argv_is_key_value_pair(self, argv: List[str]) -> Tuple[Union[None, str], Union[None, int, bool]]:
        if not (len(argv) == 2 and argv[0] in self.settings):
            return None, None
        k, v = argv
        if k == 'colors' and v in list('6789'):
            return k, int(v)
        elif k == 'pins' and v in list('45'):
            return k, int(v)
        elif k == 'limit' and v in ('10', '12'):
            return k, int(v)
        elif k == 'repeat' and v in ('true', 'false'):
            return k, v == 'true'
        else:
            return None, None

    def wrong_argument_type_hint(self) -> bool:
        command = self.lastcmd.split()[0]
        print(f'*** {command}: unknown arguments. Try "help {command}".')
        return self.CONTINUE

    def is_game_over(self) -> bool:
        return self.game_over is True

    def is_in_session(self, mode: str) -> bool:
        return self.session_mode == mode

    def wrong_session_mode_hint(self, mode: str) -> bool:
        if self.session_mode is None:
            print(f'*** Not in session. Start a session to use this command.')
        else:
            print(f'*** {self.session_mode.capitalize()} session running, but this requires a {mode} session.')
        return self.CONTINUE

    def game_over_warning(self, func: str) -> bool:
        print(f'*** The game is over. Will not accept another {func}.')
        return self.CONTINUE

    def is_guesses_limit_reached(self):
        return self.guesses >= self.settings['limit']

    def guesses_limit_reached(self) -> bool:
        print(f'+ Too many guesses. Secret code {self.secret_code} not broken. Game over.')
        return self.CONTINUE

    def is_already_cracked(self) -> bool:
        return self.cracked is True

    def already_cracked_hint(self) -> bool:
        self.reveal()
        return self.CONTINUE

    def already_in_session_hint(self):
        print(f'*** Already in a {self.session_mode} session. Starting another session requires reset.')
        return self.CONTINUE

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
    intro = """
    Welcome to the interactive collection of helpers for the
    well known code-breaking game.
    """
    app = SuperHirn()
    while True:
        try:
            app.cmdloop(intro)
            sys.exit(0)
        except KeyboardInterrupt:
            print('^C')
            intro = ''

# last line of code
