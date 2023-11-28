# coding=utf-8
import pyaudio
import wave
import time
import random

import pickle
import socket

# ======================================COLORAMA=============================================================

import re
import sys
import os
import atexit
import contextlib

orig_stdout = None
orig_stderr = None

wrapped_stdout = None
wrapped_stderr = None

atexit_done = False

class WinColor(object):
    BLACK   = 0
    BLUE    = 1
    GREEN   = 2
    CYAN    = 3
    RED     = 4
    MAGENTA = 5
    YELLOW  = 6
    GREY    = 7

# from wincon.h
class WinStyle(object):
    NORMAL              = 0x00 # dim text, dim background
    BRIGHT              = 0x08 # bright text, dim background
    BRIGHT_BACKGROUND   = 0x80 # dim text, bright background

class WinTerm(object):

    def __init__(self):
        self._default = GetConsoleScreenBufferInfo(STDOUT).wAttributes
        self.set_attrs(self._default)
        self._default_fore = self._fore
        self._default_back = self._back
        self._default_style = self._style
        # In order to emulate LIGHT_EX in windows, we borrow the BRIGHT style.
        # So that LIGHT_EX colors and BRIGHT style do not clobber each other,
        # we track them separately, since LIGHT_EX is overwritten by Fore/Back
        # and BRIGHT is overwritten by Style codes.
        self._light = 0

    def get_attrs(self):
        return self._fore + self._back * 16 + (self._style | self._light)

    def set_attrs(self, value):
        self._fore = value & 7
        self._back = (value >> 4) & 7
        self._style = value & (WinStyle.BRIGHT | WinStyle.BRIGHT_BACKGROUND)

    def reset_all(self, on_stderr=None):
        self.set_attrs(self._default)
        self.set_console(attrs=self._default)

    def fore(self, fore=None, light=False, on_stderr=False):
        if fore is None:
            fore = self._default_fore
        self._fore = fore
        # Emulate LIGHT_EX with BRIGHT Style
        if light:
            self._light |= WinStyle.BRIGHT
        else:
            self._light &= ~WinStyle.BRIGHT
        self.set_console(on_stderr=on_stderr)

    def back(self, back=None, light=False, on_stderr=False):
        if back is None:
            back = self._default_back
        self._back = back
        # Emulate LIGHT_EX with BRIGHT_BACKGROUND Style
        if light:
            self._light |= WinStyle.BRIGHT_BACKGROUND
        else:
            self._light &= ~WinStyle.BRIGHT_BACKGROUND
        self.set_console(on_stderr=on_stderr)

    def style(self, style=None, on_stderr=False):
        if style is None:
            style = self._default_style
        self._style = style
        self.set_console(on_stderr=on_stderr)

    def set_console(self, attrs=None, on_stderr=False):
        if attrs is None:
            attrs = self.get_attrs()
        handle = STDOUT
        if on_stderr:
            handle = STDERR
        SetConsoleTextAttribute(handle, attrs)

    def get_position(self, handle):
        position = GetConsoleScreenBufferInfo(handle).dwCursorPosition
        # Because Windows coordinates are 0-based,
        # and SetConsoleCursorPosition expects 1-based.
        position.X += 1
        position.Y += 1
        return position

    def set_cursor_position(self, position=None, on_stderr=False):
        if position is None:
            # I'm not currently tracking the position, so there is no default.
            # position = self.get_position()
            return
        handle = STDOUT
        if on_stderr:
            handle = STDERR
        SetConsoleCursorPosition(handle, position)

    def cursor_adjust(self, x, y, on_stderr=False):
        handle = STDOUT
        if on_stderr:
            handle = STDERR
        position = self.get_position(handle)
        adjusted_position = (position.Y + y, position.X + x)
        SetConsoleCursorPosition(handle, adjusted_position, adjust=False)

    def erase_screen(self, mode=0, on_stderr=False):
        # 0 should clear from the cursor to the end of the screen.
        # 1 should clear from the cursor to the beginning of the screen.
        # 2 should clear the entire screen, and move cursor to (1,1)
        handle = STDOUT
        if on_stderr:
            handle = STDERR
        csbi = GetConsoleScreenBufferInfo(handle)
        # get the number of character cells in the current buffer
        cells_in_screen = csbi.dwSize.X * csbi.dwSize.Y
        # get number of character cells before current cursor position
        cells_before_cursor = csbi.dwSize.X * csbi.dwCursorPosition.Y + csbi.dwCursorPosition.X
        if mode == 0:
            from_coord = csbi.dwCursorPosition
            cells_to_erase = cells_in_screen - cells_before_cursor
        if mode == 1:
            from_coord = COORD(0, 0)
            cells_to_erase = cells_before_cursor
        elif mode == 2:
            from_coord = COORD(0, 0)
            cells_to_erase = cells_in_screen
        # fill the entire screen with blanks
        FillConsoleOutputCharacter(handle, ' ', cells_to_erase, from_coord)
        # now set the buffer's attributes accordingly
        FillConsoleOutputAttribute(handle, self.get_attrs(), cells_to_erase, from_coord)
        if mode == 2:
            # put the cursor where needed
            SetConsoleCursorPosition(handle, (1, 1))

    def erase_line(self, mode=0, on_stderr=False):
        # 0 should clear from the cursor to the end of the line.
        # 1 should clear from the cursor to the beginning of the line.
        # 2 should clear the entire line.
        handle = STDOUT
        if on_stderr:
            handle = STDERR
        csbi = GetConsoleScreenBufferInfo(handle)
        if mode == 0:
            from_coord = csbi.dwCursorPosition
            cells_to_erase = csbi.dwSize.X - csbi.dwCursorPosition.X
        if mode == 1:
            from_coord = COORD(0, csbi.dwCursorPosition.Y)
            cells_to_erase = csbi.dwCursorPosition.X
        elif mode == 2:
            from_coord = COORD(0, csbi.dwCursorPosition.Y)
            cells_to_erase = csbi.dwSize.X
        # fill the entire screen with blanks
        FillConsoleOutputCharacter(handle, ' ', cells_to_erase, from_coord)
        # now set the buffer's attributes accordingly
        FillConsoleOutputAttribute(handle, self.get_attrs(), cells_to_erase, from_coord)

    def set_title(self, title):
        SetConsoleTitle(title)

def reset_all():
    if AnsiToWin32 is not None:    # Issue #74: objects might become None at exit
        AnsiToWin32(orig_stdout).reset_all()


def init(autoreset=False, convert=None, strip=None, wrap=True):

    if not wrap and any([autoreset, convert, strip]):
        raise ValueError('wrap=False conflicts with any other arg=True')

    global wrapped_stdout, wrapped_stderr
    global orig_stdout, orig_stderr

    orig_stdout = sys.stdout
    orig_stderr = sys.stderr

    if sys.stdout is None:
        wrapped_stdout = None
    else:
        sys.stdout = wrapped_stdout = \
            wrap_stream(orig_stdout, convert, strip, autoreset, wrap)
    if sys.stderr is None:
        wrapped_stderr = None
    else:
        sys.stderr = wrapped_stderr = \
            wrap_stream(orig_stderr, convert, strip, autoreset, wrap)

    global atexit_done
    if not atexit_done:
        atexit.register(reset_all)
        atexit_done = True


def deinit():
    if orig_stdout is not None:
        sys.stdout = orig_stdout
    if orig_stderr is not None:
        sys.stderr = orig_stderr


@contextlib.contextmanager
def colorama_text(*args, **kwargs):
    init(*args, **kwargs)
    try:
        yield
    finally:
        deinit()


def reinit():
    if wrapped_stdout is not None:
        sys.stdout = wrapped_stdout
    if wrapped_stderr is not None:
        sys.stderr = wrapped_stderr


def wrap_stream(stream, convert, strip, autoreset, wrap):
    if wrap:
        wrapper = AnsiToWin32(stream,
            convert=convert, strip=strip, autoreset=autoreset)
        if wrapper.should_wrap():
            stream = wrapper.stream
    return stream

winterm = None
if winterm is not None:
    winterm = WinTerm()


def is_stream_closed(stream):
    return not hasattr(stream, 'closed') or stream.closed


def is_a_tty(stream):
    return hasattr(stream, 'isatty') and stream.isatty()


class StreamWrapper(object):
    '''
    Wraps a stream (such as stdout), acting as a transparent proxy for all
    attribute access apart from method 'write()', which is delegated to our
    Converter instance.
    '''
    def __init__(self, wrapped, converter):
        # double-underscore everything to prevent clashes with names of
        # attributes on the wrapped stream object.
        self.__wrapped = wrapped
        self.__convertor = converter

    def __getattr__(self, name):
        return getattr(self.__wrapped, name)

    def write(self, text):
        self.__convertor.write(text)


class AnsiToWin32(object):
    '''
    Implements a 'write()' method which, on Windows, will strip ANSI character
    sequences from the text, and if outputting to a tty, will convert them into
    win32 function calls.
    '''
    ANSI_CSI_RE = re.compile('\001?\033\[((?:\d|;)*)([a-zA-Z])\002?')     # Control Sequence Introducer
    ANSI_OSC_RE = re.compile('\001?\033\]((?:.|;)*?)(\x07)\002?')         # Operating System Command

    def __init__(self, wrapped, convert=None, strip=None, autoreset=False):
        # The wrapped stream (normally sys.stdout or sys.stderr)
        self.wrapped = wrapped

        # should we reset colors to defaults after every .write()
        self.autoreset = autoreset

        # create the proxy wrapping our output stream
        self.stream = StreamWrapper(wrapped, self)

        on_windows = os.name == 'nt'
        # We test if the WinAPI works, because even if we are on Windows
        # we may be using a terminal that doesn't support the WinAPI
        # (e.g. Cygwin Terminal). In this case it's up to the terminal
        # to support the ANSI codes.
        conversion_supported = on_windows and winapi_test()

        # should we strip ANSI sequences from our output?
        if strip is None:
            strip = conversion_supported or (not is_stream_closed(wrapped) and not is_a_tty(wrapped))
        self.strip = strip

        # should we should convert ANSI sequences into win32 calls?
        if convert is None:
            convert = conversion_supported and not is_stream_closed(wrapped) and is_a_tty(wrapped)
        self.convert = convert

        # dict of ansi codes to win32 functions and parameters
        self.win32_calls = self.get_win32_calls()

        # are we wrapping stderr?
        self.on_stderr = self.wrapped is sys.stderr

    def should_wrap(self):
        '''
        True if this class is actually needed. If false, then the output
        stream will not be affected, nor will win32 calls be issued, so
        wrapping stdout is not actually required. This will generally be
        False on non-Windows platforms, unless optional functionality like
        autoreset has been requested using kwargs to init()
        '''
        return self.convert or self.strip or self.autoreset

    def get_win32_calls(self):
        if self.convert and winterm:
            return {
                AnsiStyle.RESET_ALL: (winterm.reset_all, ),
                AnsiStyle.BRIGHT: (winterm.style, WinStyle.BRIGHT),
                AnsiStyle.DIM: (winterm.style, WinStyle.NORMAL),
                AnsiStyle.NORMAL: (winterm.style, WinStyle.NORMAL),
                AnsiFore.BLACK: (winterm.fore, WinColor.BLACK),
                AnsiFore.RED: (winterm.fore, WinColor.RED),
                AnsiFore.GREEN: (winterm.fore, WinColor.GREEN),
                AnsiFore.YELLOW: (winterm.fore, WinColor.YELLOW),
                AnsiFore.BLUE: (winterm.fore, WinColor.BLUE),
                AnsiFore.MAGENTA: (winterm.fore, WinColor.MAGENTA),
                AnsiFore.CYAN: (winterm.fore, WinColor.CYAN),
                AnsiFore.WHITE: (winterm.fore, WinColor.GREY),
                AnsiFore.RESET: (winterm.fore, ),
                AnsiFore.LIGHTBLACK_EX: (winterm.fore, WinColor.BLACK, True),
                AnsiFore.LIGHTRED_EX: (winterm.fore, WinColor.RED, True),
                AnsiFore.LIGHTGREEN_EX: (winterm.fore, WinColor.GREEN, True),
                AnsiFore.LIGHTYELLOW_EX: (winterm.fore, WinColor.YELLOW, True),
                AnsiFore.LIGHTBLUE_EX: (winterm.fore, WinColor.BLUE, True),
                AnsiFore.LIGHTMAGENTA_EX: (winterm.fore, WinColor.MAGENTA, True),
                AnsiFore.LIGHTCYAN_EX: (winterm.fore, WinColor.CYAN, True),
                AnsiFore.LIGHTWHITE_EX: (winterm.fore, WinColor.GREY, True),
                AnsiBack.BLACK: (winterm.back, WinColor.BLACK),
                AnsiBack.RED: (winterm.back, WinColor.RED),
                AnsiBack.GREEN: (winterm.back, WinColor.GREEN),
                AnsiBack.YELLOW: (winterm.back, WinColor.YELLOW),
                AnsiBack.BLUE: (winterm.back, WinColor.BLUE),
                AnsiBack.MAGENTA: (winterm.back, WinColor.MAGENTA),
                AnsiBack.CYAN: (winterm.back, WinColor.CYAN),
                AnsiBack.WHITE: (winterm.back, WinColor.GREY),
                AnsiBack.RESET: (winterm.back, ),
                AnsiBack.LIGHTBLACK_EX: (winterm.back, WinColor.BLACK, True),
                AnsiBack.LIGHTRED_EX: (winterm.back, WinColor.RED, True),
                AnsiBack.LIGHTGREEN_EX: (winterm.back, WinColor.GREEN, True),
                AnsiBack.LIGHTYELLOW_EX: (winterm.back, WinColor.YELLOW, True),
                AnsiBack.LIGHTBLUE_EX: (winterm.back, WinColor.BLUE, True),
                AnsiBack.LIGHTMAGENTA_EX: (winterm.back, WinColor.MAGENTA, True),
                AnsiBack.LIGHTCYAN_EX: (winterm.back, WinColor.CYAN, True),
                AnsiBack.LIGHTWHITE_EX: (winterm.back, WinColor.GREY, True),
            }
        return dict()

    def write(self, text):
        if self.strip or self.convert:
            self.write_and_convert(text)
        else:
            self.wrapped.write(text)
            self.wrapped.flush()
        if self.autoreset:
            self.reset_all()


    def reset_all(self):
        if self.convert:
            self.call_win32('m', (0,))
        elif not self.strip and not is_stream_closed(self.wrapped):
            self.wrapped.write(Style.RESET_ALL)


    def write_and_convert(self, text):
        '''
        Write the given text to our wrapped stream, stripping any ANSI
        sequences from the text, and optionally converting them into win32
        calls.
        '''
        cursor = 0
        text = self.convert_osc(text)
        for match in self.ANSI_CSI_RE.finditer(text):
            start, end = match.span()
            self.write_plain_text(text, cursor, start)
            self.convert_ansi(*match.groups())
            cursor = end
        self.write_plain_text(text, cursor, len(text))


    def write_plain_text(self, text, start, end):
        if start < end:
            self.wrapped.write(text[start:end])
            self.wrapped.flush()


    def convert_ansi(self, paramstring, command):
        if self.convert:
            params = self.extract_params(command, paramstring)
            self.call_win32(command, params)


    def extract_params(self, command, paramstring):
        if command in 'Hf':
            params = tuple(int(p) if len(p) != 0 else 1 for p in paramstring.split(';'))
            while len(params) < 2:
                # defaults:
                params = params + (1,)
        else:
            params = tuple(int(p) for p in paramstring.split(';') if len(p) != 0)
            if len(params) == 0:
                # defaults:
                if command in 'JKm':
                    params = (0,)
                elif command in 'ABCD':
                    params = (1,)

        return params


    def call_win32(self, command, params):
        if command == 'm':
            for param in params:
                if param in self.win32_calls:
                    func_args = self.win32_calls[param]
                    func = func_args[0]
                    args = func_args[1:]
                    kwargs = dict(on_stderr=self.on_stderr)
                    func(*args, **kwargs)
        elif command in 'J':
            winterm.erase_screen(params[0], on_stderr=self.on_stderr)
        elif command in 'K':
            winterm.erase_line(params[0], on_stderr=self.on_stderr)
        elif command in 'Hf':     # cursor position - absolute
            winterm.set_cursor_position(params, on_stderr=self.on_stderr)
        elif command in 'ABCD':   # cursor position - relative
            n = params[0]
            # A - up, B - down, C - forward, D - back
            x, y = {'A': (0, -n), 'B': (0, n), 'C': (n, 0), 'D': (-n, 0)}[command]
            winterm.cursor_adjust(x, y, on_stderr=self.on_stderr)


    def convert_osc(self, text):
        for match in self.ANSI_OSC_RE.finditer(text):
            start, end = match.span()
            text = text[:start] + text[end:]
            paramstring, command = match.groups()
            if command in '\x07':       # \x07 = BEL
                params = paramstring.split(";")
                # 0 - change title and icon (we will only change title)
                # 1 - change icon (we don't support this)
                # 2 - change title
                if params[0] in '02':
                    winterm.set_title(params[1])
        return text

CSI = '\033['
OSC = '\033]'
BEL = '\007'


def code_to_chars(code):
    return CSI + str(code) + 'm'

def set_title(title):
    return OSC + '2;' + title + BEL

def clear_screen(mode=2):
    return CSI + str(mode) + 'J'

def clear_line(mode=2):
    return CSI + str(mode) + 'K'


class AnsiCodes(object):
    def __init__(self):
        # the subclasses declare class attributes which are numbers.
        # Upon instantiation we define instance attributes, which are the same
        # as the class attributes but wrapped with the ANSI escape sequence
        for name in dir(self):
            if not name.startswith('_'):
                value = getattr(self, name)
                setattr(self, name, code_to_chars(value))


class AnsiCursor(object):
    def UP(self, n=1):
        return CSI + str(n) + 'A'
    def DOWN(self, n=1):
        return CSI + str(n) + 'B'
    def FORWARD(self, n=1):
        return CSI + str(n) + 'C'
    def BACK(self, n=1):
        return CSI + str(n) + 'D'
    def POS(self, x=1, y=1):
        return CSI + str(y) + ';' + str(x) + 'H'


class AnsiFore(AnsiCodes):
    BLACK           = 30
    RED             = 31
    GREEN           = 32
    YELLOW          = 33
    BLUE            = 34
    MAGENTA         = 35
    CYAN            = 36
    WHITE           = 37
    RESET           = 39

    # These are fairly well supported, but not part of the standard.
    LIGHTBLACK_EX   = 90
    LIGHTRED_EX     = 91
    LIGHTGREEN_EX   = 92
    LIGHTYELLOW_EX  = 93
    LIGHTBLUE_EX    = 94
    LIGHTMAGENTA_EX = 95
    LIGHTCYAN_EX    = 96
    LIGHTWHITE_EX   = 97


class AnsiBack(AnsiCodes):
    BLACK           = 40
    RED             = 41
    GREEN           = 42
    YELLOW          = 43
    BLUE            = 44
    MAGENTA         = 45
    CYAN            = 46
    WHITE           = 47
    RESET           = 49

    # These are fairly well supported, but not part of the standard.
    LIGHTBLACK_EX   = 100
    LIGHTRED_EX     = 101
    LIGHTGREEN_EX   = 102
    LIGHTYELLOW_EX  = 103
    LIGHTBLUE_EX    = 104
    LIGHTMAGENTA_EX = 105
    LIGHTCYAN_EX    = 106
    LIGHTWHITE_EX   = 107


class AnsiStyle(AnsiCodes):
    BRIGHT    = 1
    DIM       = 2
    NORMAL    = 22
    RESET_ALL = 0

Fore   = AnsiFore()
Back   = AnsiBack()
Style  = AnsiStyle()
Cursor = AnsiCursor()

STDOUT = -11
STDERR = -12

try:
    import ctypes
    from ctypes import LibraryLoader
    windll = LibraryLoader(ctypes.WinDLL)
    from ctypes import wintypes
except (AttributeError, ImportError):
    windll = None
    SetConsoleTextAttribute = lambda *_: None
    winapi_test = lambda *_: None
else:
    from ctypes import byref, Structure, c_char, POINTER

    COORD = wintypes._COORD

    class CONSOLE_SCREEN_BUFFER_INFO(Structure):
        """struct in wincon.h."""
        _fields_ = [
            ("dwSize", COORD),
            ("dwCursorPosition", COORD),
            ("wAttributes", wintypes.WORD),
            ("srWindow", wintypes.SMALL_RECT),
            ("dwMaximumWindowSize", COORD),
        ]
        def __str__(self):
            return '(%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d)' % (
                self.dwSize.Y, self.dwSize.X
                , self.dwCursorPosition.Y, self.dwCursorPosition.X
                , self.wAttributes
                , self.srWindow.Top, self.srWindow.Left, self.srWindow.Bottom, self.srWindow.Right
                , self.dwMaximumWindowSize.Y, self.dwMaximumWindowSize.X
            )

    _GetStdHandle = windll.kernel32.GetStdHandle
    _GetStdHandle.argtypes = [
        wintypes.DWORD,
    ]
    _GetStdHandle.restype = wintypes.HANDLE

    _GetConsoleScreenBufferInfo = windll.kernel32.GetConsoleScreenBufferInfo
    _GetConsoleScreenBufferInfo.argtypes = [
        wintypes.HANDLE,
        POINTER(CONSOLE_SCREEN_BUFFER_INFO),
    ]
    _GetConsoleScreenBufferInfo.restype = wintypes.BOOL

    _SetConsoleTextAttribute = windll.kernel32.SetConsoleTextAttribute
    _SetConsoleTextAttribute.argtypes = [
        wintypes.HANDLE,
        wintypes.WORD,
    ]
    _SetConsoleTextAttribute.restype = wintypes.BOOL

    _SetConsoleCursorPosition = windll.kernel32.SetConsoleCursorPosition
    _SetConsoleCursorPosition.argtypes = [
        wintypes.HANDLE,
        COORD,
    ]
    _SetConsoleCursorPosition.restype = wintypes.BOOL

    _FillConsoleOutputCharacterA = windll.kernel32.FillConsoleOutputCharacterA
    _FillConsoleOutputCharacterA.argtypes = [
        wintypes.HANDLE,
        c_char,
        wintypes.DWORD,
        COORD,
        POINTER(wintypes.DWORD),
    ]
    _FillConsoleOutputCharacterA.restype = wintypes.BOOL

    _FillConsoleOutputAttribute = windll.kernel32.FillConsoleOutputAttribute
    _FillConsoleOutputAttribute.argtypes = [
        wintypes.HANDLE,
        wintypes.WORD,
        wintypes.DWORD,
        COORD,
        POINTER(wintypes.DWORD),
    ]
    _FillConsoleOutputAttribute.restype = wintypes.BOOL

    _SetConsoleTitleW = windll.kernel32.SetConsoleTitleA
    _SetConsoleTitleW.argtypes = [
        wintypes.LPCSTR
    ]
    _SetConsoleTitleW.restype = wintypes.BOOL

    handles = {
        STDOUT: _GetStdHandle(STDOUT),
        STDERR: _GetStdHandle(STDERR),
    }

    def winapi_test():
        handle = handles[STDOUT]
        csbi = CONSOLE_SCREEN_BUFFER_INFO()
        success = _GetConsoleScreenBufferInfo(
            handle, byref(csbi))
        return bool(success)

    def GetConsoleScreenBufferInfo(stream_id=STDOUT):
        handle = handles[stream_id]
        csbi = CONSOLE_SCREEN_BUFFER_INFO()
        success = _GetConsoleScreenBufferInfo(
            handle, byref(csbi))
        return csbi

    def SetConsoleTextAttribute(stream_id, attrs):
        handle = handles[stream_id]
        return _SetConsoleTextAttribute(handle, attrs)

    def SetConsoleCursorPosition(stream_id, position, adjust=True):
        position = COORD(*position)
        # If the position is out of range, do nothing.
        if position.Y <= 0 or position.X <= 0:
            return
        # Adjust for Windows' SetConsoleCursorPosition:
        #    1. being 0-based, while ANSI is 1-based.
        #    2. expecting (x,y), while ANSI uses (y,x).
        adjusted_position = COORD(position.Y - 1, position.X - 1)
        if adjust:
            # Adjust for viewport's scroll position
            sr = GetConsoleScreenBufferInfo(STDOUT).srWindow
            adjusted_position.Y += sr.Top
            adjusted_position.X += sr.Left
        # Resume normal processing
        handle = handles[stream_id]
        return _SetConsoleCursorPosition(handle, adjusted_position)

    def FillConsoleOutputCharacter(stream_id, char, length, start):
        handle = handles[stream_id]
        char = c_char(char.encode())
        length = wintypes.DWORD(length)
        num_written = wintypes.DWORD(0)
        # Note that this is hard-coded for ANSI (vs wide) bytes.
        success = _FillConsoleOutputCharacterA(
            handle, char, length, start, byref(num_written))
        return num_written.value

    def FillConsoleOutputAttribute(stream_id, attr, length, start):
        ''' FillConsoleOutputAttribute( hConsole, csbi.wAttributes, dwConSize, coordScreen, &cCharsWritten )'''
        handle = handles[stream_id]
        attribute = wintypes.WORD(attr)
        length = wintypes.DWORD(length)
        num_written = wintypes.DWORD(0)
        # Note that this is hard-coded for ANSI (vs wide) bytes.
        return _FillConsoleOutputAttribute(
            handle, attribute, length, start, byref(num_written))

    def SetConsoleTitle(title):
        return _SetConsoleTitleW(title)

# ===========================================REMOTE_IP========================================================

def get_IP():
    """Returns the IP of the computer where get_IP is called.

    Returns
    -------
    computer_IP: IP of the computer where get_IP is called (str)

    Notes
    -----
    If you have no internet connection, your IP will be 127.0.0.1.
    This IP address refers to the local host, i.e. your computer.

    """

    return socket.gethostbyname(socket.gethostname())


def connect_as_referee(remote_IP_1='127.0.0.1',  remote_IP_2='127.0.0.1', verbose=False, timeout=None):
    """Initialise communication to players as referee.

    Parameters
    ----------
    remote_IP_1: IP of the computer where remote player 1 is (str, optional)
    remote_IP_2: IP of the computer where remote player 2 is (str, optional)
    verbose: True only if connection progress must be displayed (bool, optional)
    timeout: maximum time given to remote players for each request (int, optional)

    Returns
    -------
    connection_1: sockets to receive/send orders from/to player 1 (tuple)
    connection_2: sockets to receive/send orders from/to player 2 (tuple)

    Notes
    -----
    Initialisation can take several seconds.  The function only
    returns after connection has been initialised by both players.

    Use the default value of remote_IP_1/2 if both players are running on
    the same machine.  Otherwise, indicate the IP where both players are
    running with remote_IP_1/2.  On most systems, the IP of a computer
    can be obtained by calling the get_IP function on that computer.

    """

    # init verbose display
    if verbose:
        print '\n----------------------------------------------------------------------------'

    # open sockets (as server) to receive orders
    socket_in = []
    for player_id in (1, 2):
        socket_in.append(socket.socket(socket.AF_INET, socket.SOCK_STREAM))
        socket_in[player_id-1].setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # deal with a socket in TIME_WAIT state

        if remote_IP_1 == '127.0.0.1' and remote_IP_2 == '127.0.0.1':
            local_IP = '127.0.0.1'
        else:
            local_IP = get_IP()
        local_port = 42000 + (3-player_id)

        if verbose:
            print 'referee binding on %s:%d to receive orders from player %d...' % (local_IP, local_port, player_id)
        socket_in[player_id-1].bind((local_IP, local_port))
        socket_in[player_id-1].listen(1)
        if verbose:
            print '   done -> referee is now waiting for player %d to connect on %s:%d' % (player_id, local_IP, local_port)

    if verbose:
        print

    # open sockets (as client) to send orders
    socket_out = []
    for player_id in (1, 2):
        socket_out.append(socket.socket(socket.AF_INET, socket.SOCK_STREAM))
        socket_out[player_id-1].setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # deal with a socket in TIME_WAIT state

        if player_id == 1:
            remote_IP = remote_IP_1
        else:
            remote_IP = remote_IP_2

        local_IP = get_IP()

        if remote_IP == '127.0.0.1' or remote_IP == local_IP:
            remote_port = 42000 + 100 + player_id
        else:
            remote_port = 42000 + player_id

        connected = False
        msg_shown = False
        while not connected:
            try:
                if verbose and not msg_shown:
                    print 'referee connecting on %s:%d to forward orders to player %d...' % (remote_IP, remote_port, player_id)
                socket_out[player_id-1].connect((remote_IP, remote_port))
                connected = True
                if verbose:
                    print '   done -> referee is now forwarding orders to player %d on %s:%d' % (player_id, remote_IP, remote_port)
            except:
                if verbose and not msg_shown:
                    print '   connection failed -> referee will try again every 100 msec...'
                time.sleep(.1)
                msg_shown = True

    if verbose:
        print

    # accept connection to the server sockets to the server socket to receive orders from remote player
    for player_id in (1, 2):
        socket_in[player_id-1], remote_address = socket_in[player_id-1].accept()
        if verbose:
            print 'now listening to orders from player %d' % (player_id)

    if verbose:
        print

    # setting timeout if necessary
    if timeout != None:
        socket_in[0].settimeout(timeout)
        socket_in[1].settimeout(timeout)
        socket_out[0].settimeout(timeout)
        socket_out[1].settimeout(timeout)

        if verbose:
            print 'warning: remote players are given %d sec. for each request' % timeout
    else:
        if verbose:
            print 'warning: remote players have no time limit to answer requests'

    # end verbose display
    if verbose:
        print '\nconnection to remote players successful\n----------------------------------------------------------------------------\n'

    # return sockets for further use
    return (socket_in[0], socket_out[0]), (socket_in[1], socket_out[1])


def connect_to_player(player_id, remote_IP='127.0.0.1', verbose=False):
    """Initialise communication with remote player.

    Parameters
    ----------
    player_id: player id of the remote player, 1 or 2 (int)
    remote_IP: IP of the computer where remote player is (str, optional)
    verbose: True only if connection progress must be displayed (bool, optional)

    Returns
    -------
    connection: sockets to receive/send orders (tuple)

    Notes
    -----
    Initialisation can take several seconds.  The function only
    returns after connection has been initialised by both players.

    Use the default value of remote_IP if the remote player is running on
    the same machine.  Otherwise, indicate the IP where the other player
    is running with remote_IP.  On most systems, the IP of a computer
    can be obtained by calling the get_IP function on that computer.

    """

    # init verbose display
    if verbose:
        print '\n-------------------------------------------------------------'

    # open socket (as server) to receive orders
    socket_in = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket_in.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # deal with a socket in TIME_WAIT state

    if remote_IP == '127.0.0.1':
        local_IP = '127.0.0.1'
    else:
        local_IP = get_IP()
    local_port = 42000 + (3-player_id)

    try:
        if verbose:
            print 'binding on %s:%d to receive orders from player %d...' % (local_IP, local_port, player_id)
        socket_in.bind((local_IP, local_port))
    except:
        local_port = 42000 + 100+ (3-player_id)
        if verbose:
            print '   referee detected, binding instead on %s:%d...' % (local_IP, local_port)
        socket_in.bind((local_IP, local_port))

    socket_in.listen(1)
    if verbose:
        print '   done -> now waiting for a connection on %s:%d\n' % (local_IP, local_port)

    # open client socket used to send orders
    socket_out = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket_out.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # deal with a socket in TIME_WAIT state

    remote_port = 42000 + player_id

    connected = False
    msg_shown = False
    while not connected:
        try:
            if verbose and not msg_shown:
                print 'connecting on %s:%d to send orders to player %d...' % (remote_IP, remote_port, player_id)
            socket_out.connect((remote_IP, remote_port))
            connected = True
            if verbose:
                print '   done -> now sending orders to player %d on %s:%d' % (player_id, remote_IP, remote_port)
        except:
            if verbose and not msg_shown:
                print '   connection failed -> will try again every 100 msec...'
            time.sleep(.1)

            msg_shown = True

    if verbose:
        print

    # accept connection to the server socket to receive orders from remote player
    print 'sutck on accept'
    socket_in, remote_address = socket_in.accept()
    if verbose:
        print 'now listening to orders from player %d' % (player_id)

    # end verbose display
    if verbose:
        print '\nconnection to remote player %d successful\n-------------------------------------------------------------\n' % player_id

    # return sockets for further use
    return (socket_in, socket_out)


def disconnect_from_player(connection):
    """End communication with remote player.

    Parameters
    ----------
    connection: sockets to receive/send orders (tuple)

    """

    # get sockets
    socket_in = connection[0]
    socket_out = connection[1]

    # shutdown sockets
    socket_in.shutdown(socket.SHUT_RDWR)
    socket_out.shutdown(socket.SHUT_RDWR)

    # close sockets
    socket_in.close()
    socket_out.close()


def notify_remote_orders(connection, orders):
    """Notifies orders of the local player to a remote player.

    Parameters
    ----------
    connection: sockets to receive/send orders (tuple)
    orders: orders of the local player (str)

    Raises
    ------
    IOError: if remote player cannot be reached

    """

    # get sockets
    socket_in = connection[0]
    socket_out = connection[1]

    # deal with null orders (empty string)
    if orders == '':
        orders = 'null'

    # send orders
    try:
        socket_out.sendall(orders)
    except:
        raise IOError, 'remote player cannot be reached'


def get_remote_orders(connection):
    """Returns orders from a remote player.

    Parameters
    ----------
    connection: sockets to receive/send orders (tuple)

    Returns
    ----------
    player_orders: orders given by remote player (str)

    Raises
    ------
    IOError: if remote player cannot be reached

    """

    # get sockets
    socket_in = connection[0]
    socket_out = connection[1]

    # receive orders
    try:
        orders = socket_in.recv(4096)
    except:
        raise IOError, 'remote player cannot be reached'

    # deal with null orders
    if orders == 'null':
        orders = ''

    return orders



#======================================================================================================================
#======================================================================================================================
#======================================================================================================================
#======================================================================================================================

def start_game(remote=1, pc_id = 1, player1='player 1', player2='player_2', map_size=7, file_name=None, sound=False, clear=False):
    """Start the entire game.
    Parameters:
    -----------
    player1: Name of the first player or IA (optional, str).
    player2: Name of the second player or IA (optional, str).
    map_size: Size of the map that players wanted to play with (optional, int).
    file_name: File of the name to load if necessary (optional, str).
    sound: Activate the sound or not (optional, bool).
    clear: Activate the "clear_output" of the notebook. Game looks more realistic, but do not work properly on each computer (optional, bool).
    Notes:
    ------
    It is the main function that gonna call the other functions.
    map_size must be contained between 7 and 30
    file_name load a game only if the game was saved earlier
    Version:
    -------
    specification: Laurent Emilie & Maroit Jonathan v.1 (10/03/16)
    implementation: Maroit Jonathan & Bienvenu Joffrey v.1(21/03/16)
    """
    enemy_id = remote
    ia_id =  3 - remote

    # Creation of the database or load it.
    data_map = create_data_map(remote, map_size, player1, player2, clear, enemy_id, ia_id, remote)
    data_ia = create_data_ia(map_size, enemy_id, ia_id)
    # If we play versus another ia, connect to her.
    if remote:
        IP = '138.48.160.1' + str(pc_id)
        connection = connect_to_player(enemy_id, IP)
        print 'connected'
    else:
        connection = None

    # Diplay introduction event and the map.
    play_event(sound,"","","intro")

    # Run de game turn by turn
    continue_game = True
    while continue_game:
        display_map(data_map, clear)
        data_map = choose_action(data_map, connection, data_ia)
        continue_game, loser, winner = is_not_game_ended(data_map)

    # Once the game is finished, disconnect from the other player.
    if remote:
        disconnect_from_player(connection)

    # Display the game-over event (versus IA).
    if player1 == 'IA' or player2 == 'IA':
        player = loser
        play_event(sound,player1,player, 'game_over')
    # Display the win event (versus real player).
    else:
        player = winner
        play_event(sound,player1,player, 'win')

def display_event(player,player_name,event,count_line):
    """Display screen which representst the actualy situation with the name of the concerned player
    Parameters:
    -----------
    player: tells if player 1 or player 2 concerned player (str)
    player_name: name of the user to display (str)
    event : the event who represent the situation ,introduction , game over, winner screen (str)

    Version:
    -------
    specification: Maroit Jonathan and Laurent Emilie (v.1 16/02/16)
    implementation: Maroit Jonathan (v.1 16/02/16)
    """
    player_name = 'you !'
    color_player= Back.RED
    if player == 'player1':
        color_player= Back.BLUE

    if event=='intro' :

        l0='█████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████'
        l1='██████████████████████████████████████████████████████++████████++███████████████████████████████████████████████████████'
        l2='███████+++█████████████████++██████████+++████████████++███++█████+++███████████████++███████████████++██████████++██████'
        l3='+++++++███++++++++++████;████:++██+++██+++██++++++++++++++++++++++███+++++++████████++███████+++██+++██+++++++█████+++██+'
        l4='+++++++***++*****+++++++++++++++++***+++++++**++++++++**+++++***++++++++++++++***++++++++++++***++:++++++***++***++++++++'
        l5='**+++██████**████*****+++*******************++*******;███*******++***████*++**+++*******+++*******+++**████:*******+++++*'
        l6='*****██:::**:::██********::*******;::************::**██:██******::***██*██*******************:::******██*:::*************'
        l7='*****██;,::,:::██:::*██**██**:████;:::█████;,,::;**::██:██:::***::***██::██:;██**;██::████:**██:*██::*██::::::█████:::,:*'
        l8='::;:;██::::::::██::::██::██::██::██::██:::::::::::::::███::::::::::::██::██::██:█:██:::::██::██:███:::██:::::██::;:::::::'
        l9=':::::█████:::::██::::██::██::██::██::██::::::::::::::██::::::::::::::██;:██::██:█:██:::::██::███:::::██████::██::::::::::'
        l10=':::::██::::::::██::::██::██::██████:::████:::::::::,,██:████:::::::::██,:██::██:█;██:;█████::██:::::::██::::::████:::::::'
        l11=':::::██:::::,,,██::::██,,██::██:,,:::::,,██:::,,,::,,██,,██::::::::::██::██,:██:█:██:██:,██::██:,,::::██:,,,:::::██,,,:::'
        l12=',,:::██:::,,,,,██:::.,████,,,██:,,,,,,,::██:::,,,,,,,██,,██,,,,,::,,,██,██,,,,██:██,:██,,██,,██,::,,,:██,,,,,,:::██,,,,,:'
        l13=',,,,,██████,,██████,,,,██,,,,,████,,,█████,,,,,,,,,,,,███,██,,,,,,,,,████,,,,,██,██,,,█████,,██,,,,,,,██,,,,,█████,,:,,,,'
        l14=',,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,'
        l15=',,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,'
        la1=Back.WHITE+Fore.BLACK+'                   GROUPE 42 : EMILIE LAURENT, JOFFREY BIENVENU, JONATHAN MAROIT ET SYLVAIN PIRLOT                       '




        line_list = [l0,l1,l2,l3,l4,l5,l6,l7,l8,l9,l10,l11,l12,l13,l14,l15,la1]
        if count_line < len(line_list):
            print Fore.RED+ Back.BLACK+line_list[count_line]



    elif event=='game_over':
        d0=(Fore.BLACK+Back.WHITE)+'                                                        '+('The loser is: '+player_name)+'                                                   '
        d1='██████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████'
        d2='███████████████████████████████████████        ████████████████████████████████████        ███████████████████████████████████████'
        d3='███████████████████████████████████████        ████████████████████████████████████        ███████████████████████████████████████'
        d4='███████████████████████████████████████████████    ████                    ████    ███████████████████████████████████████████████'
        d5='███████████████████████████████████████████████    ████                    ████    ███████████████████████████████████████████████'
        d6='███████████████████████████████████████████████████                            ███████████████████████████████████████████████████'
        d7='███████████████████████████████████████████████████    ████████    ████████    ███████████████████████████████████████████████████'
        d8='███████████████████████████████████████████████████    ████████    ████████    ███████████████████████████████████████████████████'
        d9='███████████████████████████████████████████████████    ████████    ████████    ███████████████████████████████████████████████████'
        d10='███████████████████████████████████████████████████    ████            ████    ███████████████████████████████████████████████████'
        d11='███████████████████████████████████████████████████    ████            ████    ███████████████████████████████████████████████████'
        d12='███████████████████████████████████████████████████            ████            ███████████████████████████████████████████████████'
        d13='███████████████████████████████████████████████████            ████            ███████████████████████████████████████████████████'
        d14='███████████████████████████████████████████████    ████                    ████    ███████████████████████████████████████████████'
        d15='███████████████████████████████████████████████    ████                    ████    ███████████████████████████████████████████████'
        d16='███████████████████████████████████████        ████████    ████    ████    ████████        ███████████████████████████████████████'
        d17='███████████████████████████████████████        ████████    ████    ████    ████████        ███████████████████████████████████████'
        d18='██████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████'
        d19=(Fore.BLACK+Back.WHITE)+'                                                                                                                                  '
        death_list=[d0,d1,d2,d3,d4,d5,d6,d7,d8,d9,d10,d11,d12,d13,d14,d15,d16,d17,d18]
        if count_line < len(death_list):
            print Fore.BLACK+color_player+death_list[count_line]


    elif event == 'win':

        w0=Back.BLACK+Fore.WHITE+'                                                               THE                                                                '
        wa='                                                                                                                                  '
        w1='               ██ █ ██       █           ██   ██  ████   ██   ██ ██   ██ ██████  █████                          █████             '
        w2='              █████████     ███          ██   ██   ██    ██   ██ ██   ██ ██      ██  ██         █            ███  █               '
        w3='              ███ █ ███      █           ██   ██   ██    ███  ██ ███  ██ ██      ██  ██        █ █         ██    █                '
        w4='               ██ █ ██       █           ██ █ ██   ██    ████ ██ ████ ██ ██      ██  ██       █ █ █      ██     █                 '
        w5='                █ █ █        █           ██ █ ██   ██    ██ ████ ██ ████ █████   █████          █       █      █                  '
        w6='                  █          █           ██ █ ██   ██    ██  ███ ██  ███ ██      ██ ██          █       █      █                  '
        w7='                  █          █            ██ ██    ██    ██   ██ ██   ██ ██      ██  ██         █       █     █                   '
        w8='                  █      █████████        ██ ██    ██    ██   ██ ██   ██ ██      ██  ██        ███       █    █                   '
        w9='                 ███     █████████        ██ ██   ████   ██   ██ ██   ██ ██████  ██  ██       ██ ██       ██ █                    '
        wb='                  █          █                                                                █   █         ████                  '
        wb1='                                                                                                                                  '
        w10=Back.BLACK+Fore.WHITE+'                                                               IS                                                                 '
        w11=Back.BLACK+Fore.WHITE+'                                                            '+player_name+'                                                             '
        win_list=[w0,wa,w1,w2,w3,w4,w5,w6,w7,w8,w9,wb,wb1,w10,w11]
        if count_line < len(win_list):
            print Fore.BLACK+color_player+win_list[count_line]



def play_event(sound,player,player_name,event):
    """Play a selected sound
    Parameters:
    -----------
    sound: argument who active or desactive the sound, true or false (bool)
    sound_name:the name of the sound file that will be played (str)
    Versions:
    ---------
    spécification: Maroit Jonathan (v.1 17/02/16)
    implémentation: Maroit Jonathan(v.1 17/02/16)
    """
    if sound:
        sound_name = event+'.wav'
        chunk = 1024
        wf = wave.open(sound_name, 'rb')
        p = pyaudio.PyAudio()


        stream = p.open(
            format = p.get_format_from_width(wf.getsampwidth()),
            channels = wf.getnchannels(),
            rate = wf.getframerate(),
            output = True)

        data = wf.readframes(chunk)
        written = False
        time_count = 0
        count_line = 0

        while data != '':
            time_count += 1
            if time_count == 18:
                time_count = 0
                display_event(player,player_name,event,count_line)
                count_line += 1
            stream.write(data)
            data = wf.readframes(chunk)

        stream.stop_stream()
        stream.close()
        wf.close()
        p.terminate()
    else :
        for count_line in range(20):
            display_event(player,player_name,event,count_line)
            time.sleep(0.5)
    time.sleep(2)

def display_map(data_map, clear):
    """Display the map of the game.

    Parameters:
    -----------
    data_map: the whole database of the game (dict)
    clear: Activate the "clear_output" of the notebook. Game looks more realistic (bool)

    Version:
    --------
    specification: Laurent Emilie v.1 (12/02/16)
    implementation: Bienvenu Joffrey v.3 (01/04/16)
    """
    # if clear:
        #clear_output()

    # Check which player have to play and define displaying constants.
    player = 'player' + str((data_map['main_turn'] % 2) + 1)
    ennemy = 'player' + str(2 - (data_map['main_turn'] % 2))
    ui_color = data_map[player + 'info'][0]

    data_cell = {'ui_color': ui_color}

    # Generate the units to be displayed.
    for i in range(1, data_map['map_size'] + 1):
        for j in range(1, data_map['map_size'] + 1):

            # Coloration black/white of the cells.
            background_cell = ''
            if (i + j) % 2 == 0:
                background_cell = Back.WHITE

            if (i, j) in data_map['player1']:
                data_cell['(' + str(i) + ',' + str(j) + ')'] = data_map['player1'][(i, j)][1] + background_cell + ' ☻' + str(data_map['player1'][(i, j)][0]) + (str(data_map['player1'][(i, j)][2]) + ' ')[:2]
            elif (i, j) in data_map['player2']:
                data_cell['(' + str(i) + ',' + str(j) + ')'] = data_map['player2'][(i, j)][1] + background_cell + ' ☻' + str(data_map['player2'][(i, j)][0]) + (str(data_map['player2'][(i, j)][2]) + ' ')[:2]
            else:
                data_cell['(' + str(i) + ',' + str(j) + ')'] = background_cell + (' ' * 5)

    # Generate the statistics to be displayed.
    player1_cell = data_map[player].keys()
    cell1_couter = 0
    player2_cell = data_map[ennemy].keys()
    cell2_couter = 0
    unit_name = {'E': 'Elf', 'D': 'Dwarf'}

    for i in range(1, 5):
        for j in range(1, 3):
            if len(player1_cell) > cell1_couter:
                data_cell['stat' + str(i) + str(j)] = (('0' + str(player1_cell[cell1_couter][0]))[-2:] + '-' + ('0' + str(player1_cell[cell1_couter][1]))[-2:] + ' ' + unit_name[data_map[player][player1_cell[cell1_couter]][0]] + ' hp: ' + str(data_map[player][player1_cell[cell1_couter]][2]) + ' ' * 20)[:20]
                cell1_couter += 1
            else:
                data_cell['stat' + str(i) + str(j)] = ' ' * 20
        for j in range(3, 5):
            if len(player2_cell) > cell2_couter:
                data_cell['stat' + str(i) + str(j)] = (('0' + str(player2_cell[cell2_couter][0]))[-2:] + '-' + ('0' + str(player2_cell[cell2_couter][1]))[-2:] + ' ' + unit_name[data_map[ennemy][player2_cell[cell2_couter]][0]] + ' hp: ' + str(data_map[ennemy][player2_cell[cell2_couter]][2]) + ' ' * 20)[:20]
                cell2_couter += 1
            else:
                data_cell['stat' + str(i) + str(j)] = ' ' * 20

    # Generate the title of the map to be displayed.
    data_cell['turn'] = str(data_map['main_turn']/2 + 1)
    data_cell['playername'] = data_map[player + 'info'][1]
    data_cell['blank'] = ((data_map['map_size'] * 5) - 19 - len(data_cell['turn']) - len(data_cell['playername'])) * ' '

    # Print the top of the UI.
    for line in data_map['data_ui']:
        print line % data_cell

def ia_reflexion(data_ia, data_map):
    """Brain of the Artificial Intelligence.

    Parameters:
    -----------
    ia_data: the whole database (dict)

    Returns:
    --------
    data_ia: database for the ia (dict)
    data_map: database of the whole game (dict)
    player: tells which player is the ia (int)

    Versions:
    ---------
    specification: Bienvenu Joffrey & Laurent Emilie v.2 (28/04/16)
    implementation: Bienvenu Joffrey & Laurent Emilie v.3 (01/0516)
    """
    ia = data_ia['ia_id']
    enemy = data_ia['enemy_id']
    commands = {}

    new_positions = []
    moved_units = []

    for ia_unit in data_ia[ia]:
        unit_has_attacked = False
        unit_targets = []

        for enemy_unit in data_ia[enemy]:
            # Find each possible target for the Dwarves.
            if data_ia[ia][ia_unit][0] == 'D':
                if (ia_unit[0] - 1) <= enemy_unit[0] <= (ia_unit[0] + 1) and (ia_unit[1] - 1) <= enemy_unit[1] <= (ia_unit[1] + 1):
                    # Add the unit to the target list.
                    unit_targets.append(enemy_unit)

            # Find each possible target for the Elves - ATTACK
            else:
                for i in range(2):
                    if (ia_unit[0] - (1 + i)) <= enemy_unit[0] <= (ia_unit[0] + (1 + i)) and (ia_unit[1] - (1 + i)) <= enemy_unit[1] <= (ia_unit[1] + (1 + i)):
                        # Add the unit to the target list.
                        unit_targets.append(enemy_unit)

        # Find the weakest units.
        if unit_targets:
            target = unit_targets[0]
            for enemy_unit in unit_targets:
                if data_ia[enemy][enemy_unit][0] == 'D' or data_ia[enemy][enemy_unit][1] < data_ia[enemy][target][1]:
                    target = enemy_unit

            # Write the attack.
            commands[data_ia[ia][ia_unit][2]] = [ia_unit, ' -a-> ', target]
            unit_has_attacked = True

        # Find the weakest of all enemy's units - MOVE
        if not unit_has_attacked:
            target_list = data_ia[enemy].keys()
            target = target_list[0]

            for enemy_unit in data_ia[enemy]:
                if data_ia[enemy][enemy_unit][0] == 'D' or data_ia[enemy][enemy_unit][1] < data_ia[enemy][target][1]:
                    target = enemy_unit

            target_cell = [ia_unit[0], ia_unit[1]]
            # Move on Y axis
            if target and abs(ia_unit[1] - target[1]) > abs(ia_unit[0] - target[0]) and 1 <= ia_unit[0] <= data_map['map_size'] and 1 <= ia_unit[1] <= data_map['map_size']:
                if ia_unit[1] > target[1]:
                    target_cell[1] -= 1
                else:
                    target_cell[1] += 1
            # Move on X axis
            elif target and 1 <= ia_unit[0] <= data_map['map_size'] and 1 <= ia_unit[1] <= data_map['map_size']:
                if ia_unit[0] > target[0]:
                    target_cell[0] -= 1
                else:
                    target_cell[0] += 1

            new_target = False
            # Check if he can move on the targeted position.
            enemy_positions = data_ia[enemy].keys()
            ia_positions = data_ia[ia].keys()
            for units in moved_units:
                del ia_positions[ia_positions.index(units)]

            # If the units can't move, find another free cell.
            if target_cell in (new_positions or enemy_positions or ia_positions):
                new_target_cells = []
                for line in range(target_cell[0] - 1, target_cell[0] + 2):
                    for column in range(target_cell[1] - 1, target_cell[1] + 2):

                        # Append the possible free cell to the list.
                        if (line, column) not in (new_positions or enemy_positions or ia_positions):
                            new_target_cells.append((line, column))

                # Choose the nearest free cell.
                if new_target_cells:
                    new_target = new_target_cells[0]
                    for cell in new_target_cells:
                        if abs(ia_unit[0] - cell[0]) + abs(ia_unit[1] - cell[1]) < abs(ia_unit[0] - new_target[0]) + abs(ia_unit[1] - new_target[1]):
                            new_target = new_target_cells[new_target_cells.index(cell)]

            # Save the new target in the correct variable.
            if new_target:
                target_cell = new_target

            # Write the move
            if target_cell != ia_unit:
                commands[data_ia[ia][ia_unit][2]] = [ia_unit, ' -m-> ', target_cell]
                new_positions.append(target_cell)
                moved_units.append(ia_unit)

    return commands

def ia_action(data_map, data_ia, player):
    """The artificial intelligence of the game. Generate an instruction and return it.

    Parameters:
    -----------
    data_map: the whole database of the game (dict).
    data_ia: the ia identifier ('player1' or 'player2', string).
    player: the player identifier ('player1' or 'player2', string).

    Return:
    -------
    command: the instruction of the ia (string).

    Version:
    --------
    specification: Laurent Emilie and Bienvenu Joffrey v. 1 (02/03/16)
    implementation: Bienvenu Joffrey and Jonathan Maroit & Laurent Emilie v.4 (01/05/16)
    """
    raw_commands = ia_reflexion(data_ia, data_map, player)

    # Rewrite the command into a single string.
    string_commands = ''
    for key in raw_commands:
        string_commands += ('0' + str(raw_commands[key][0][0]))[-2:] + '-' + ('0' + str(raw_commands[key][0][1]))[-2:] + raw_commands[key][1] + ('0' + str(raw_commands[key][2][0]))[-2:] + '-' + ('0' + str(raw_commands[key][2][1]))[-2:] + '   '
    return string_commands


def create_data_ia(map_size, enemy_id, ia_id):
    """Create the ia database.

    Parameters:
    -----------
    map_size: the length of the board game, every unit add one unit to vertical axis and horizontal axis (int, optional)
    id: tells which player is the ia (int)

    Returns:
    --------
    data_ia: the ia database (dict).

    Versions:
    ---------
    specifications: Laurent Emilie v.1 (24/04/16)
    implementation: Laurent Emilie v.1 (24/04/16)
    """
    data_ia = {'player1': {},
               'player2': {},
               'main_turn': 1,
               'attack_turn': 0,
               'map_size': map_size,
               'enemy_id': enemy_id,
               'ia_id': ia_id}


    order_unit = {}
    order_unit['if_left'] = [(2,3), (3,2), (1,3), (2,2), (3,1), (1,2), (2,1), (1,1)]
    order_unit['if_right'] = [(map_size -1, map_size -2), (map_size -2, map_size -1), (map_size, map_size -2), (map_size -1, map_size -1), (map_size -1, map_size -1), (map_size -2, map_size), (map_size, map_size-1), (map_size -1, map_size), (map_size, map_size)]

    for i in range(2):
        for line in range(1, 4):
            for column in range(1, 4):
                unit = 'E'
                life = 4

                if line >= 2 and column >= 2:
                    unit = 'D'
                    life = 10

                if line + column != 6:
                    x_pos = abs(i * map_size - line + i)
                    y_pos = abs(i * map_size - column + i)

                    if i == 0:
                        unit_id = (order_unit['if_left'].index((x_pos,y_pos))) + 1
                        data_ia['player1'][(x_pos, y_pos)] = [unit, life, unit_id]
                    else:
                        unit_id = (order_unit['if_right'].index((x_pos,y_pos))) + 1
                        data_ia['player2'][(x_pos, y_pos)] = [unit, life, unit_id]

    return data_ia


def save_apap(data_map):
    """Load a saved game.

    Parameters:
    -----------
    data_map_saved: name of the file to load (str)

    Version:
    --------
    specification: Laurent Emilie v.1 (11/02/16)
    implementation: Pirlot Sylvain v.1 & Bienvenu Joffrey (21/03/16)
    """
    pickle.dump(data_map, open("save.p", "wb"))



def load_data_map():
    """Save the game.

    Parameters:
    -----------
    data_map: the whole database of the game (dict)

    Version:
    --------
    specification: Laurent Emilie v.1 (11/02/16)
    implementation: Pirlot Sylvain v.1 & Bienvenu Joffrey (21/03/16)
    """

    return pickle.load(open("save.p", "rb"))

def move_unit(data_map, start_coord, end_coord, player, enemy, data_ia):
    """Move an unit from a cell to another cell. And check if the move is legal.

    Parameters:
    -----------
    data_map: the whole database (dict)
    start_coord: coordinates at the origin of the movement (tuple)
    end_coord: coordinates at the destination of the movement (tuple)
    player: the player who is moving the unit (str)
    enemy: the other player (str)

    Returns:
    --------
    data_map: the database modified by the move (dict)

    Notes:
    ------
    The database will only change the coordinate of the units concerned.
    start_coord and end_coord will be tuple of int

    Version:
    --------
    specification: Laurent Emilie & Bienvenu Joffrey v.2 (17/02/16)
    implementation: Laurent Emilie & Bienvenu Joffrey v.2 (17/03/16)
    """

    # Check if there's a unit on the starting cell, and if the destination cell is free.
    if start_coord in data_map[player] and end_coord not in data_map[player]and end_coord not in data_map[enemy]:

        # Check if the move is rightful and save it.
        if start_coord[0] - 1 <= end_coord[0] <= start_coord[0] + 1 and start_coord[1] - 1 <= end_coord[1] <= start_coord[1] + 1:
            if data_map[player][start_coord][0] == 'E' or (sum(start_coord) - 1 <= sum(end_coord) <= sum(start_coord) + 1):
                data_map[player][end_coord] = data_map[player].pop(start_coord)
                data_ia[player][end_coord] = data_ia[player].pop(start_coord)
    return data_map, data_ia

def is_not_game_ended(data_map):
    """Check if the game is allow to continue.

    Parameter:
    ----------
    data_map: the whole database (dict)

    Returns:
    --------
    continue_game : boolean value who said if the game need to continue(bool).
    loser : the player who lose the game(str).
    winner : the player who won the game(str).

    Notes:
    ------
    The game stop when a player run out of unit or if 20 turn have been played without any attack.
    In this case, the player 1 win.

    Version:
    -------
    specification: Maroit Jonathan(v.1 21/03/16)
    implementation: Maroit Jonathan & Bienvenu Joffrey (v.1.1 22/03/16)
    """

    continue_game = True
    loser = None
    winner = None

    # If a player has not any units, the other player win.
    for i in range(2):
        if not len(data_map['player' + str(i + 1)]) and continue_game:
            loser = data_map['player' + str(i + 1)]
            winner = data_map['player' + str(3 - (i + 1))]
            continue_game = False

    # If there's 20 turn without any attack, player1 loose and player2 win.
    if float(data_map['attack_turn']) / 2 > 19:
        loser = data_map['player1']
        winner = data_map['player2']
        continue_game = False

    return continue_game, loser, winner

def create_data_ui(data_map, clear):
    """Generate the whole user's interface with the statistics.

    Parameters:
    -----------
    data_map: the whole database (dict)
    clear: Activate the "clear_output" of the notebook. Game looks more realistic (bool)

    Returns:
    --------
    data_ui: the user's interface to print (list)

    Versions:
    ---------
    specification: Laurent Emilie v.1 (15/03/16)
    implementation: Bienvenu Joffrey v.3.1 (24/03/16)
    """
    data_ui = [[]] * (16 + data_map['map_size'])

    # Initialisation of the displaying constants.
    grid_size = 5 * data_map['map_size']
    ui_color = '%(ui_color)s'

    margin = 5
    line_coloured = ui_color + ('█' * (117 + margin)) + Style.RESET_ALL
    if clear:
        margin = 9
        line_coloured = ui_color + ('█' * (121 + margin)) + Style.RESET_ALL


    border_black = Back.BLACK + '  ' + Style.RESET_ALL
    margin_left = ((20 - data_map['map_size']) * 5) / 2
    margin_right = ((20 - data_map['map_size']) * 5) - (((20 - data_map['map_size']) * 5) / 2)
    border_coloured_margin_left = ui_color + ('█' * (margin + margin_left)) + Style.RESET_ALL
    border_coloured_margin_right = ui_color + ('█' * (margin + margin_right)) + Style.RESET_ALL
    border_coloured_left = ui_color + ('█' * margin) + Style.RESET_ALL
    border_coloured_right = ui_color + ('█' * margin) + Style.RESET_ALL
    border_coloured_middle = ui_color + ('█' * 8) + Style.RESET_ALL

    border_white = ' ' * 2

    # Generate and save the top of the UI.
    for i in range(3):
        data_ui[i] = line_coloured

    # Generate and save the top of the grid.
    turn_message = 'Turn %(turn)s - %(playername)s, it\'s up to you ! %(blank)s'
    data_ui[3] = border_coloured_margin_left + Fore.WHITE + Back.BLACK + '  ' + turn_message + '  ' + Style.RESET_ALL + border_coloured_margin_right
    data_ui[4] = border_coloured_margin_left + border_black + ' ' * (grid_size + 8) + border_black + border_coloured_margin_right

    # Generate and save the architecture of the grid.
    for i in range(1, data_map['map_size'] + 1):
        data_ui[i + 4] = border_coloured_margin_left + border_black + Fore.BLACK + ' ' + ('0' + str(i))[-2:] + ' ' + Style.RESET_ALL
        for j in range(1, data_map['map_size'] + 1):
            data_ui[i + 4] += '%((' + str(i) + ',' + str(j) + '))5s' + Style.RESET_ALL
        data_ui[i + 4] += '    ' + border_black + border_coloured_margin_right

    # Generate and save the foot of the grid.
    data_ui[data_map['map_size'] + 5] = border_coloured_margin_left + border_black + Fore.BLACK + '   '
    for i in range(1, data_map['map_size'] + 1):
        data_ui[data_map['map_size'] + 5] += '  ' + ('0' + str(i))[-2:] + ' '
    data_ui[data_map['map_size'] + 5] += '     ' + border_black + border_coloured_margin_right

    data_ui[data_map['map_size'] + 6] = border_coloured_margin_left + Back.BLACK + (grid_size + 12) * ' ' + Style.RESET_ALL + border_coloured_margin_right

    # Generate and save the top of the statistics.
    data_ui[data_map['map_size'] + 7] = line_coloured

    data_ui[data_map['map_size'] + 8] = border_coloured_left + Fore.WHITE + Back.BLACK + '  Your units:' + (' ' * 39) + Style.RESET_ALL + border_coloured_middle
    data_ui[data_map['map_size'] + 8] += Fore.WHITE + Back.BLACK + '  Opponent\'s units:' + (' ' * 33) + Style.RESET_ALL + border_coloured_right

    # Generate and save the content of the statistics.
    for i in range(4):
        data_ui[data_map['map_size'] + 9 + i] = border_coloured_left + border_black + ' ' + border_white + Fore.BLACK + '%(stat' + str(i+1) + '1)s' + border_white + '%(stat' + str(i+1) + '2)s' + border_white + ' ' + border_black + border_coloured_middle
        data_ui[data_map['map_size'] + 9 + i] += border_black + ' ' + border_white + '%(stat' + str(i+1) + '3)s' + border_white + '%(stat' + str(i+1) + '4)s' + border_white + ' ' + border_black + border_coloured_right

    # Generate and save the foot of the statistics.
    data_ui[data_map['map_size'] + 13] = border_coloured_left + Back.BLACK + (' ' * 52) + Style.RESET_ALL + border_coloured_middle
    data_ui[data_map['map_size'] + 13] += Back.BLACK + (' ' * 52) + Style.RESET_ALL + border_coloured_right

    for i in range(2):
        data_ui[data_map['map_size'] + 14 + i] = line_coloured

    return data_ui


def create_data_map(remote, map_size, name_player1, name_player2, clear, enemy_id, ia_id, remote):
    """ Create a dictionary that the game will use as database with units at their initial places.

    Parameters:
    ----------
    map_size : the length of the board game, every unit add one unit to vertical axis and horizontal axis (int, optional).
    name_player1: name of the first player (str)
    name_player2: name of the second player (str)
    clear: if you want to activate the clear screen (bool)

    Returns:
    -------
    data_map : dictionary that contain information's of every cells of the board (dict).
    data_ui : list with data to display the ui (list of str).

    Notes:
    -----
    The game board is a square, the size must be a positive integer, minimum 7 and maximum 30 units,
    or the game will be stopped after 20 turns if nobody attack.

    Version:
    -------
    specification: Maroit Jonathan & Bienvenu Joffrey v.2 (04/03/16)
    implementation: Maroit Jonathan & Bienvenu Joffrey & Laurent Emilie v.5 (23/03/16)
    """
    # Initialisation of variables
    data_map = {'player1': {},
                'player1info': [],
                'player2': {},
                'player2info': [],
                'main_turn': 1,
                'attack_turn': 0,
                'map_size': map_size,
                'enemy_id': enemy_id,
                'ia_id': ia_id,
                'remote': remote}

    # Place units to their initial positions.
    player_data = [Fore.BLUE, Fore.RED, name_player1, name_player2]
    for i in range(2):
        for line in range(1, 4):
            for column in range(1, 4):
                unit = 'E'
                life = 4

                if line >= 2 and column >= 2:
                    unit = 'D'
                    life = 10

                if line + column != 6:
                    x_pos = abs(i * map_size - line + i)
                    y_pos = abs(i * map_size - column + i)

                    data_map['player' + str(i + 1)][(x_pos, y_pos)] = [unit, player_data[i], life]
        data_map['player' + str(i + 1) + 'info'].extend([player_data[i], player_data[i + 2]])

    if not remote:
        # Randomize which player will start the game.
        number = random.randint(1, 2)
        if number == 1:
            data_map['player1info'][1] = name_player1
            data_map['player2info'][1] = name_player2
        else:
            data_map['player1info'][1] = name_player2
            data_map['player2info'][1] = name_player1

    data_map['data_ui'] = create_data_ui(data_map, clear)

    return data_map

def choose_action(data_map, connection, data_ia):
    """Ask and execute the instruction given by the players to move or attack units.

    Parameters:
    ----------
    data_map: the whole database (dict)

    Returns:
    -------
    data_map: the database changed by moves or attacks (dict)

    Notes:
    -----
    Instructions must be in one line, with format xx_xx -a-> xx_xx for an attack and xx_xx -m-> xx_xx for a movement.
    Each instruction must be spaced by 3 characters.

    Version:
    -------
    specification: Laurent Emilie v.1 (11/02/16)
    implementation: Laurent Emilie v.3 (21/03/16)
    """
    player = 'player' + str((data_map['main_turn'] % 2) + 1)
    enemy = 'player' + str(2 - (data_map['main_turn'] % 2))
    if data_map['remote']:
        player = 'player' + str(data_map['ia_id'])
        enemy = 'player' + str(data_map['enemy_id'])

    # Tells whether IA or player's turn.
    if data_map['main_turn'] % 2 == data_map['ia_id'] or data_map[str(player + 'info')][1] == 'IA':
        game_instruction = ia_action(data_map, data_ia, player)
        if data_map['remote']:
            notify_remote_orders(connection, game_instruction)
    else:
        if data_map['remote']:
            game_instruction = get_remote_orders(connection)
        else:
            game_instruction = raw_input('Enter your commands in format xx_xx -a-> xx_xx or xx_xx -m-> xx_xx')

    # Split commands string by string.
    list_action = game_instruction.split()

    # grouper instruction par instructions
    list_action2 = []
    for instruction in range(0, len(list_action), 3):
        list_action2.append((list_action[instruction], list_action[instruction + 1], list_action[instruction + 2]))

    # Call attack_unit or move_unit in function of instruction.
    attack_counter = 0
    for i in range(len(list_action2)):
        if '-a->' in list_action2[i]:
            data_map, attacked, data_ia = attack_unit(data_map, (int(list_action2[i][0][:2]), int(list_action2[i][0][3:])),
                        (int(list_action2[i][2][:2]), int(list_action2[i][2][3:])), player, enemy, data_ia)
            attack_counter += attacked
        elif '-m->' in list_action2[i]:
            data_map, data_ia = move_unit(data_map, (int(list_action2[i][0][:2]), int(list_action2[i][0][3:])),
                      (int(list_action2[i][2][:2]), int(list_action2[i][2][3:])), player, enemy, data_ia)

    # Save if a player have attacked.
    if attack_counter:
        data_map['attack_turn'] = 0
    else:
        data_map['attack_turn'] += 1
    data_map['main_turn'] += 1

    return data_map

def attack_unit(data_map, attacker_coord, target_coord, player, enemy, data_ia):
    """Attack an adverse cell and check whether it is a legal attack.

    Parameters:
    -----------
    data_map: the whole database (dict)
    attacker_coord: coordinates of the attacker's pawn (tuple)
    target_coord: coordinates of the attacked's pawn (tuple)
    player: the player who is attacking (str)
    enemy: the other player (str)

    Returns:
    --------
    data_map: the database modified by the attack (dict)

    Notes:
    ------
    The database will only change by decrement unit's life and, eventually, decrementing the unit's number of the player.
    attacker_coord and attacked_coord will be tuple of int.

    Version:
    -------
    specification: Laurent Emilie & Bienvenu Joffrey v.2 (17/03/16)
    implementation: Bienvenu Joffrey v.1 (17/03/16)
    """
    damage = {'E': 1, 'D': 3}
    attacked = 0

    # Check if there's a unit on the attacker cell, and if the attacked cell is occupied.
    if attacker_coord in data_map[player] and target_coord in data_map[enemy]:

        # Check if the attack is rightful and save it.
        if attacker_coord[0] - 2 <= target_coord[0] <= attacker_coord[0] + 2 and attacker_coord[1] - 2 <= target_coord[1] <= attacker_coord[1] + 2:
            attacker_type = data_map[player][attacker_coord][0]
            if attacker_type == 'E' or (attacker_coord[0] - 1 <= target_coord[0] <= attacker_coord[0] + 1 and attacker_coord[1] - 1 <= target_coord[1] <= attacker_coord[1] + 1):

                # Decrement the heal point and delete the unit if their hp are equal or less than 0.
                data_map[enemy][target_coord][2] -= damage[attacker_type]
                if data_map[enemy][target_coord][2] <= 0:
                    del data_map[enemy][target_coord]

                data_ia[enemy][target_coord][1] -= damage[attacker_type]
                if data_ia[enemy][target_coord][1] <= 0:
                    del data_ia[enemy][target_coord]

                attacked = 1

    return data_map, attacked, data_ia
