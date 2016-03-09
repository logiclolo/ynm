# -*- coding: utf-8 -*-

import ctypes
import platform
from enum import Enum,IntEnum;
import ctypes


def is_windows():
    if platform.system() == 'Windows':
        return True
    return False


def is_linux():
    if platform.system() == 'Linux':
        return True
    return False


def is_fail(status):
    return status >> 31

def is_digit(n):
    try:
        int(n)
        return True
    except ValueError:
        return False

def makefourcc(ch0, ch1, ch2, ch3):
    version = int(ch0) | int(ch1) << 8 | int(ch2) << 16 | int(ch3) << 24
    return ctypes.c_ulong(version)


def get_buffer_data(pointer_to_byte, size, offset=0):
    str_buffer = ctypes.create_string_buffer(size)
    if offset:
        pointer_to_byte = ctypes.cast(ctypes.addressof(pointer_to_byte.contents)+offset, ctypes.POINTER(ctypes.c_byte))
    ctypes.memmove(str_buffer, pointer_to_byte, size)
    # hex_string = "".join("%02x" % eval(hex(ord(i))) for i in str_buffer)
    # hex_code = '0x{0}'.format(hex_string)
    # debug_log("HEXCODE:  %s" % hex_code, "info")
    # return hex_code
    # debug_log("~~~ strbuffer: %s" % str_buffer[:size], "info")
    return str_buffer[:size]

class Enum4ctypes(Enum):
    def __init(self, value):
        self._as_parameter = value

    @classmethod
    def from_param(cls,obj):
        return int(obj)


def merge_dict (a, b):
    c = a.copy()
    c.update(b)
    return c


def is_color(image):
    # check if image is grayscale
    rgb_im = image.convert('RGB')
    pixels = list(rgb_im.getdata())
    for pixel in pixels:
        r, g, b = pixel
        if r != g or g != b or r != b:
            return True

    return False


def is_grayscale(image):
    return not is_color(image)
