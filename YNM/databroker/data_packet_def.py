import ctypes
from YNM.utility.utility import *
from YNM.utility.data_type_def import boolean


# --- A structure provides the information in the Data Packet --- #
class TMediaDataPacketInfo(ctypes.Structure):
    _fields_ = [
        ("pbyBuff", ctypes.POINTER(ctypes.c_byte)),             # the pointer of buffer containing this Data Packet
        ("dwOffset", ctypes.c_ulong),                           # the offset of buffer refer to the media bitstream,
                                                                # 32-bits align
        ("dwBitstreamSize", ctypes.c_ulong),                    # the size of media bitstream
        ("dwStreamType", ctypes.c_ulong),                       # the type of stream in the Data Packet
        ("dwFrameNumber", ctypes.c_ulong),                      # the number of frame in the Data Packet
        ("tFrameType", ctypes.c_int),                           # the type of frame
        ("dwFirstUnitSecond", ctypes.c_ulong),                  # the second of first frame
        ("dwFirstUnitMilliSecond", ctypes.c_ulong),             # the millisecond of first frame
        ("bFixedFrameSize", boolean),                           # the flag indicates the frame size is fixed
        ("dwAudioSamplingFreq", ctypes.c_ulong),                # audio sampling frequency
        ("byAudioChannelNum", ctypes.c_byte),                   # the channel number of audio
        ("dwDIAlert", ctypes.c_ulong),                          # the digital input alert,
                                                                # each bit presents a digital input source.
                                                                # Bit 0 is for DI 0, bit 1 is for DI 1, ...
        ("dwDO", ctypes.c_ulong),                               # the digital output, each bit presents a digital output.
                                                                # Bit 0 is for DO 0, bit 1 is for DO 1
        ("bMotionDetection", boolean * 3),                      # the flags of motion detection
        ("bMotionDetectionAlertFlag", boolean * 3),             # the flags of motion detection alert
        ("byMotionDetectionPercent", ctypes.c_byte * 3),        # the percentage of motion detection
        ("wMotionDetectionAxis", (ctypes.c_ushort * 4) * 3),    # the window axis of motion detection
        ("bTimeModified", boolean),                             # the flag indicates the time is modified according to timezone
        ("bAudioDI", boolean),                                  # the flag indicates audio packets take the DI Alert information
        ("bNoVideoSignal", boolean)                             # the flag indicates the loss of video signal
    ]


# predefined
class TMediaDataPacketInfoV3(ctypes.Structure):
    pass

if is_windows():
    PFMediaPacketAddRef = ctypes.WINFUNCTYPE(ctypes.c_void_p, ctypes.POINTER(TMediaDataPacketInfoV3))
    PFMediaPacketRelease = ctypes.WINFUNCTYPE(ctypes.c_void_p, ctypes.POINTER(TMediaDataPacketInfoV3))
elif is_linux():
    PFMediaPacketAddRef = ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.POINTER(TMediaDataPacketInfoV3))
    PFMediaPacketRelease = ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.POINTER(TMediaDataPacketInfoV3))


class TMediaDataPacketFuntionTable(ctypes.Structure):
    _fields_ = [
        ("pfAddRef", PFMediaPacketAddRef),
        ("pfRelease", PFMediaPacketRelease)
    ]


class TMediaPacketFirstReserved(ctypes.Structure):
    _fields_ = [
        ("pbyTLVExt", ctypes.POINTER(ctypes.c_byte)),   # the pointer to the tag/length/data extension of a frame
                                                        # the pointer would point to the location after media data
                                                        # in pbyBuff
        ("dwTLVExtLen", ctypes.c_ulong),                # the length of the tag length
        ("dwStructSize", ctypes.c_ulong),               # the size of the structure.
                                                        # If this is 0, it means the packet is Ex only,
                                                        # else this maps the size of the overall packet structure
        ("ptFunctionTable", ctypes.POINTER(TMediaDataPacketFuntionTable))
    ]


class UMeidaPktReserved1(ctypes.Union):
    _fields_ = [
        ("tExt", TMediaPacketFirstReserved),
        ("apvReserved", ctypes.c_void_p * 4)        # because we do not release 64 bit library yet,
                                                    # so the change will cause no harm
    ]


class TMediaDataPacketInfoEx(ctypes.Structure):
    _fields_ = [
        ("tInfo", TMediaDataPacketInfo),       # The handle of DataBroker instance
        ("tRv1", UMeidaPktReserved1),           # Reserved for future use
        ("dwWidth", ctypes.c_ulong),            # the with of the video frame if it's video (includes padding if any)
        ("dwHeight", ctypes.c_ulong),           # the height of the video frame if it's video (includes padding if any)
        ("dwWidthPadLeft", ctypes.c_ulong),     # padded width, usually this is 0
        ("dwWidthPadRight", ctypes.c_ulong),    # padded width, usually this is 0
        ("dwHeightPadTop", ctypes.c_ulong),     # padded height on top, usually this is 0
        ("dwHeightPadBottom", ctypes.c_ulong)   # padded height on bottom, usually this is 0
    ]


class TMediaPacketTimeZoneInfo(ctypes.Structure):
    _fields_ = [
        ("bTimeZone", boolean),                 # if the packet contains time zone information, if no,
                                                # the following fields are from client machine
        ("lDLSaving", ctypes.c_long),           # the daylight saving time in seconds
                                                # (if 0 it means no day-light saving), -3600 for most case
        ("lOffsetSeconds", ctypes.c_long)       # offset of seconds from GMT time;
                                                # for example taipei will be 8 * 3600 = 28000
    ]


class TCaptureWinInfo(ctypes.Structure):
    _fields_ = [
        ("bWithInfo", boolean),
        ("wCapW", ctypes.c_ushort),
        ("wCapH", ctypes.c_ushort),
        ("wOffX", ctypes.c_ushort),
        ("wOffY", ctypes.c_ushort),
        ("wCropW", ctypes.c_ushort),
        ("wCropH", ctypes.c_ushort),
    ]


class TMotionTriggerInfo(ctypes.Structure):
    _fields_ = [
        ("bMotionDetection", boolean * 3),                      # the flags of motion detection
        ("bMotionDetectionAlertFlag", boolean * 3),             # the flags of motion detection alert
        ("byMotionDetectionPercent", ctypes.c_byte * 3),        # the percentage of motion detection
        ("wMotionDetectionAxis", (ctypes.c_ushort * 4) * 3),    # the window axis of motion detection
    ]


class TVUExtInfo(ctypes.Structure):
    _fields_ = [
        ("dwPIR", ctypes.c_ulong),                  # the PIR status, this field is not set yet in current stage, waiting for
                                                    # HIGH word means the PIR enabled flag, LOW word contains the values
        ("dwWLLed", ctypes.c_ulong),                # the status for white light LED in some model
        ("tCapWinInfo", TCaptureWinInfo),           # it contains the capture window info, current not used yet
        ("dwTamperingAlert", ctypes.c_ulong),       # it contains the tamperingalert info, current not used yet
        ("ptMTI", ctypes.POINTER(TMotionTriggerInfo))   # point to the data in TMediaDataPacketInfo
    ]


class TPoint(ctypes.Structure):
    _fields_ = [
        ("wX", ctypes.c_ushort),    # X-axis of the point
        ("wY", ctypes.c_ushort),    # Y-axis of the point
    ]


class TMotionTriggerInfoEx(ctypes.Structure):
    _fields_ = [
        ("byWindowNumber", ctypes.c_byte),              # the index of motion detection
        ("bMotionDection", boolean),                    # the flags of motion detection
        ("bMotionDetectionAlertFlag", boolean),         # the flags of motion detection alert
        ("byMotionDetectionPercent", boolean),          # the percentage of motion detection
        ("tPoint1", TPoint),                            # the first point of motion detection
        ("tPoint2", TPoint),                            # the second point of motion detection
        ("tPoint3", TPoint),                            # the third point of motion detection
        ("tPoint4", TPoint),                            # the fourth point of motion detection
    ]


# --- TMediaDataPacketInfoV3 elements --- #
TMediaDataPacketInfoV3._fields_ = [
    ("tIfEx", TMediaDataPacketInfoEx),                          # The handle of DataBroker instance
    ("tTZ", TMediaPacketTimeZoneInfo),
    ("dwUTCTime", ctypes.c_ulong),                              # this is a redundant filed,
                                                                # it could be got from dwFristUnitSecond and time zone information
    ("tVUExt", TVUExtInfo),
    ("pbyVExtBuf", ctypes.POINTER(ctypes.c_byte)),              # video further extension, it points to some point in pbyBuff,
                                                                # if null, means no such extension
    ("dwVExtLen", ctypes.c_ulong),                              # if there are any new member, it goes here
    ("bTemperatureAlert", boolean),                             # the information about temperature alter
    ("byMotionNumber", ctypes.c_byte),                          # Number of data in ptMotionInfoEx
    ("ptMotionInfoEx", ctypes.POINTER(TMotionTriggerInfoEx))    # The pointer to the structure of motion window infoex */
]
