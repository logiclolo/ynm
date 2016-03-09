# -*- coding: utf-8 -*-

import ctypes

from YNM.utility import utility


boolean = ctypes.c_long
if utility.is_linux():
    boolean = ctypes.c_bool

SCODE    = ctypes.c_long
HANDLE   = ctypes.c_void_p
HANDLE_p = ctypes.POINTER(HANDLE)
PVOID    = ctypes.c_void_p
BOOL     = ctypes.c_bool
CHAR     = ctypes.c_char
CHAR_p   = ctypes.c_char_p
BYTE     = ctypes.c_ubyte
BYTE_p   = ctypes.POINTER(BYTE)
BYTE_pp  = ctypes.POINTER(BYTE_p)
WORD     = ctypes.c_ushort
DWORD    = ctypes.c_ulong
DWORD_p  = ctypes.POINTER(DWORD)
DOUBLE   = ctypes.c_double
