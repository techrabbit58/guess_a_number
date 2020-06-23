"""
An interactive set of helpers for a more successful operation of the board game "Mastermind" (Hasbro).

Reference:
- https://en.wikipedia.org/wiki/Mastermind_(board_game)
"""
import json
import sys
from cmd import Cmd
from itertools import product, permutations
from random import choice


class SuperHirn(Cmd):
    intro = """
    Welcome to the interactive collection of helpers for the
    well known code-breaking game.
    """
    prompt = '(Mastermind) '
    session_mode = None
    settings = {
        'colors': 8,
        'pins': 4,
        'limit': 12,
        'repeat': True,
    }
    defaults = {k: v for k, v in settings.items()}

    STOP, CONTINUE = True, False

    secret_code = None
    possible_codes = None
    guesses = 0

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
        args = arg.split()
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
        args = arg.split()
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
        argc = len(arg.split())
        if argc:
            print(f'*** {self.lastcmd}: expected no arguments but got {argc}.')
        else:
            self.session_mode = None
            self.settings = {k: v for k, v in self.defaults.items()}
            self.possible_codes = None
            self.secret_code = None
            self.guesses = 0
            print('+ Session ended. Mastermind set to defaults.')
        return self.CONTINUE

    def show_session(self) -> None:
        if self.session_mode:
            print(f'+ Mastermind is running in {self.session_mode} mode.')
            if self.session_mode == 'codemaker':
                print(f'+ Guesses so far: {self.guesses}')
                print(f'+ Remaining guesses: {self.settings["limit"] - self.guesses}')
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
    def do_codemaker(self, arg: str) -> bool:
        """Switches mastermind to codemaker mode. Play a game against the machine, as a codebreaker."""
        argc = len(arg.split())
        if argc:
            print(f'*** {self.lastcmd}: Expected single word but got {argc} additional item{"s" if argc > 1 else ""}.')
            return self.CONTINUE
        print('+ Codemaker session started.')
        self.possible_codes = {
            True: lambda c, p: list(product(range(c), repeat=p)),
            False: lambda c, p: list(permutations(range(c), p)),
        }[self.settings['repeat']](self.settings['colors'], self.settings['pins'])
        self.secret_code = choice(self.possible_codes)
        self.session_mode = 'codemaker'
        return self.CONTINUE


if __name__ == '__main__':
    app = SuperHirn()
    try:
        app.cmdloop()
    except KeyboardInterrupt:
        print('^C')
        app.onecmd('quit')
    sys.exit(0)

# last line of code