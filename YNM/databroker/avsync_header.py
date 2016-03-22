import ctypes
from YNM.utility.data_type_def import BYTE_p, DWORD
from YNM.databroker.data_packet_def import *
from YNM.utility.utility import CtypesEnum


class TAudioFocusType(CtypesEnum):
    AUDIOOUT_FOCUS_NORMAL = 1,
    AUDIOOUT_FOCUS_STICKY = 2,
    AUDIOOUT_FOCUS_GLOBAL = 3,


class EPIXELFORMAT(CtypesEnum):
    PF_YUY2 = 1,
    PF_RGB16565 = 2,
    PF_RGB24 = 3,
    PF_RGB32 = 4,
    PF_BMP16565 = 5,
    PF_BMP24 = 6,
    PF_BMP32 = 7,
    PF_JPEG = 8,    # 2K servers don't have to use this to get the jpeg data
    PF_RGB16555 = 9,
    PF_BMP16555 = 10,
    PF_YUV = 11,        # 4:2:0 format
    PF_IYUV = 11,       # 4:2:0 format
    PF_BGR16565 = 12,   # decoder supports BGR format, only for linux
    PF_BGR24 = 13,      # only for linux
    PF_BGR32 = 14,      # only for linux
    PF_BGR16555 = 15,   # only for linux
    PF_YV12 = 16,       # YVU in order
    PF_UYVY = 17        # UYVY


class EAYSyncInitFlag(CtypesEnum):
    DECODER_CHANNEL_ONLY = 0x0001,
    # these two settings can't be used together
    USE_GDI_ONLY = 0x0002,
    USE_DIRECTDRAW_ONLY = 0x0004,
    # the caption cache machenism will be cancelled
    CAPTION_ON_GRAPH = 0x0008,
    # use stretch rather than dib draw
    BETTER_GDI_STRETCH = 0x0010,
    # when in DDraw mode(offscreen), don't use intermediate surface for drawing
    # just put the decoded data on to primary surface, it will be faster, but
    # if stretching, the video will shiver when other window moves over
    ONE_PASS_DDRAW = 0x0020,
    # if possible, each channel uses one YUV surface
    INDIVIDUAL_SURFACE = 0x0040,
    CHANGE_TIME_PRECISION = 0x0200,
    # for some cards, the yuv operation will cause green screen
    # set this flag could avoid the problem, but
    # the system performance will be worse than yuv mode (maybe 5 ~ 15% decade)
    FORCE_NON_YUV = 0x0400,
    MEGA_PIXEL = 0x0800,
    DECODER_NO_ACCELERATE = 0x1000,
'''
    # stacey : limited by data length
    (OverflowError: Python int too large to convert to C long)
    # A/V will not sync if this is set, going on their best speed
    AV_DONT_SYNC = 0x80000000,
'''


class TFRAMEINFO(ctypes.Structure):
    pass

# TODO correct parameter type
'''
typedef SCODE (__stdcall * LPDECODEFRAMECALLBACK)
(DWORD_PTR dwContext, EMEDIATYPE tFrameType, TFRAMEINFO * tframeinfo );
'''
FTLPDecordeFrameCallback = ctypes.CFUNCTYPE(ctypes.c_ulong, ctypes.c_ulong,
                                            ctypes.POINTER(TFRAMEINFO))

FTLPDisplayCallBack = ctypes.CFUNCTYPE(ctypes.c_ulong, ctypes.c_ulong,
                                       ctypes.c_ulong)

FTLPStatusCallBack = ctypes.CFUNCTYPE(ctypes.c_ulong, ctypes.c_ulong,
                                      ctypes.c_ulong)


class TVFRAMEINFO(ctypes.Structure):
    _fields_ = [
        ("dwWidth", DWORD),
        ("dwHeight", DWORD),
        ("dwSize", DWORD),
        ("pbyPicture", BYTE_p),
        ("pbyHeader", BYTE_p),
        ("dwReserved", DWORD),
        ("tPacketInfo", ctypes.POINTER(TMediaDataPacketInfo)),
    ]


class TAFRAMEINFO(ctypes.Structure):
    _fields_ = [
        ("dwTime", DWORD),
        ("dwSize", DWORD),
        ("pbySound", BYTE_p),
        ("dwTimeStampSec", DWORD),
        ("dwTimeStampMilliSec", DWORD),
        ("tPacketInfo", ctypes.POINTER(TMediaDataPacketInfo)),
    ]


class TFRAMEINFO(ctypes.Structure):
    _fields_ = [
        ("tVideoFrame", TVFRAMEINFO),
        ("tAudioFrame", TAFRAMEINFO),
    ]


class TDECHOPTION(ctypes.Structure):
    _fields_ = [
        ("pfDecodeFrame", FTLPDecordeFrameCallback),
        ("dwAvDecodeContext", ctypes.c_ulong),
        ("dwRawDataFormat", ctypes.c_ulong),
        # only used when the output format is JPEG
        # value range 1-125, the smaller the better quality
        ("dwJpegQualityFactor", ctypes.c_ulong),
    ]
