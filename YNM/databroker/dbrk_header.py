from YNM.databroker.dbrk_callback_def import *
from enum import Enum

MAX_VIDEO_CODEC = 5
MAX_AUDIO_CODEC = 5
MAX_VSIZE_LEN = 10
MAX_CONNECTION = 100


# --- TDataBrokerConnOptionFlag --- #
# This enumeration indicates the flags that have to be turned on when you want to specify values to some fields of the
# TDataBrokerConnectionOptions.
# When the flag is set the corresponding field is checked and taken in function call. Otherwise, the field is ignored
class TDataBrokerConnOptionFlag(Enum):
    # the flag for wCam field of TdataBrokerConnectionOptions
    eConOptCam = 0x0001
    # the flag for zVSize field of TDataBrokerConnectionOptions
    eConOptVSize = 0x0002
    # the flag for dwQuality field of TDataBrokerConnectionOptions
    eConOptQuality = 0x0004
    # the flag for wHttpPort field of TDataBrokerConnectionOptions
    eConOptHttpPort = 0x0008
    # the flag for dwProtocolType and dwMediaType fields of TDataBrokerConnectionOptions.
    # You should specify these two values at the same time
    eConOptProtocolAndMediaType = 0x0010
    # the flag for dwVideoCodec field of TDataBrokerConnectionOptions
    eConOptVideoCodec = 0x0020
    # the flag for dwAudioCodec field of TDataBrokerConnectionOptions
    eConOptAudioCodec = 0x0040
    # the flag for pfStatus field of TDataBrokerConnectionOptions
    eConOptStatusCallback = 0x0080
    # the flag for pfAV field of TDataBrokerConnectionOptions
    eConOptAVCallback = 0x0100
    # the flag for dwStatusContext field of TDataBrokerConnectionOptions
    eConOptStatusContext = 0x0200
    # the flag for dwAVContext field of TDataBrokerConnectionOptions
    eConOptAVContext = 0x0400
    # sylvia(2003/10/31)
    # the flag for pfTx field of TDataBrokerConnectionOptions
    eConOptTxCallback = 0x0800
    # the flag for dwTxContext field of TDataBrokerConnectionOptions
    eConOptTxContext = 0x1000
    # the flag for dwAudioEnc field of TDataBrokerConnectionOptions
    eConOptAudioEncCodec = 0x2000
    # the flag for dwVCodecOrder field of TDataBrokerConnectionOptions
    eConOptVideoCodecPri = 0x4000
    # the flag for dwACodecOrder field of TDataBrokerConnectionOptions
    eConOptAudioCodecPri = 0x8000
    # the flag for dwAudioSample field of TDataBrokerConnectionOptions
    eConOptAudioSample = 0x10000
    # the flag for bEnableProxy field of TDataBrokerOptions
    # the flag for dwAudioEncSample field of TDataBrokerConnectionOptions
    eConOptAudioEncSample = 0x20000
    # the flag for pfSB field of TDataBrokerConnectionOptions
    eConOptSBCallback = 0x40000
    # the flag for dwSBContext field of TDataBrokerConnectionOptions
    eConOptSBContext = 0x80000


# --- This structure indicates the connection options --- #
class TDataBrokerConnectionOptions(ctypes.Structure):
    _fields_ = [
        ("wCam", ctypes.c_ushort),					            # the camera index
        ("zVSize", ctypes.c_char * (MAX_VSIZE_LEN + 1)),		# the Vsize (For 2K series only)
        ("dwQuality", ctypes.c_ulong),                          # the quality value (For 2K series only)
        ("pfStatus", FTDataBrokerStatusCallback),               # the pointer to the TDataBrokerStatusCallback callback function.
        ("pfAV", FTDataBrokerAVCallback),                       # the pointer to the callback function of receiving AV frames
        ("pfTx", FTDataBrokerTxCallback),		                # the pointer to the callback function of transmitting media
        ("dwStatusContext", ctypes.c_ulong),				    # the context value for status callback function
        ("dwAVContext", ctypes.c_ulong),						# the context value for AV callback function
        ("dwTxContext", ctypes.c_ulong),					    # the context value for Tx callback function
        ("wHttpPort", ctypes.c_ushort),						    # the HTTP port number
        ("dwProtocolType", ctypes.c_ulong),				        # the protocol type
        ("dwMediaType", ctypes.c_ulong),						# the requested media type
        ("dwVideoCodec", ctypes.c_ulong),						# the video codec type
        ("dwAudioCodec", ctypes.c_ulong),					    # the audio codec type
        ("dwAudioSample", ctypes.c_ulong),					    # audio sample rate, used only for 3135
        ("dwAudioEnc", ctypes.c_ulong),							# audio encoding codec type
        ("dwAudioEncSample", ctypes.c_ulong),				    # audio sample rate, only for 3135
        ("pzServerType", ctypes.c_char_p),						# Server friendly name. This option must be specified
        ("pzIPAddr", ctypes.c_char_p),                          # Remote IP address you want to connect to,
                                                                # the maximum length is 128 bytes.
                                                                # This option must be specified
        ("pzUID", ctypes.c_char_p),                             # User login ID, the maximum length is 40 bytes.
                                                                # This option must be specified
        ("pzPWD", ctypes.c_char_p),                             # User login password, the maximum length is 40 bytes.
                                                                # This option must be specified
        ("adwVCodecOrder", ctypes.c_ulong * MAX_VIDEO_CODEC),   # Server supports video codecs following this order.
                                                                # It's only valid for 4/5/6K server.
        ("adwACodecOrder", ctypes.c_ulong * MAX_AUDIO_CODEC),   # Server supports audio codecs following this order.
                                                                # It's only valid for 4/5/6K server
        ("dwFlags", ctypes.c_ulong),						    # Flags for the optional fields
        ("dPlaySpeed", ctypes.c_double),						# Play speed. It's only valid for 7K server
        ("pfSB", FTDataBrokerSBCallback),		                # the pointer to the callback function of get streaming buffer
        ("dwSBContext", ctypes.c_ulong),						# the context value for streaming buffer callback function
    ]

MAX_LANGUAGE_LEN = 10
MAX_SERVERTYPE_LEN = 20


class TDataBrokerConnInfo(ctypes.Structure):
    _fields_ = [
        ("dwWidth", ctypes.c_ulong),                            # the width of the image. Note that this value is only for reference
                                                                # because for HTTP mode of 3000 server,
                                                                # the value is not retrieved actually,
                                                                # so some reference value is returned.
                                                                # To get the exact value,
                                                                # please use the decoder callback from AVSynchronizer
        ("dwHeight", ctypes.c_ulong),						    # the height of the image. Note that this value is only for reference
                                                                # because for HTTP mode of 3000 server,
                                                                # the value is not retrieved actually,
                                                                # so some reference value is returned.
                                                                # To get the exact value,
                                                                # please use the decoder callback from AVSynchronizer
        ("zLanguage", ctypes.c_char * (MAX_LANGUAGE_LEN + 1)),  # the language type of the server
        ("dwAudioCodec", ctypes.c_ulong),                       # the audio codec type of the server
        ("dwVideoCodec", ctypes.c_ulong),                       # the video codec type of the server
        ("dwMediaType", ctypes.c_ulong),                        # the media type of the server
        ("dwProtocol", ctypes.c_ulong),                         # the actual protocol used by the connection
        ("wVideoPort", ctypes.c_ushort),                        # the server side video port used by the connection
        ("wAudioPort", ctypes.c_ushort),                        # the server side audio port used by the connection
        ("szServerType", ctypes.c_char * (MAX_SERVERTYPE_LEN + 1)),     # the server friendly name
        ("dwMetadataType", ctypes.c_ulong),                     # the meta data type of the server
    ]
