from YNM.databroker.data_packet_def import *
from YNM.utility import utility
from YNM.utility.data_type_def import *
from ctypes import *

# --- enumeration for TDataBrokerStatusType --- #
# This enumeration indicates the status of DataBroker
class TDataBrokerStatusType(Enum4ctypes):
    (eOnConnectionInfo,             # Indicate connection info when connecting to the server
     eOnAuthFailed,                 # Can not pass the authorization of server
     eOnStartMediaChannel,          # Begin to receive media stream
     eOnChannelClosed,              # Audio or Video channel closed
     eOnTimeout,                    # Audio or Video channel receives data timeout
     eOnProtocolChanged,            # The protocol of receiving media changed
     eOnPacketLoss,                 # Packet loss
     eOnDiDo,                       # Receiving the digital input alert and digital output status
     eOnLocationChanged,            # Detecting the change of location
     eOnInputInfo,                  # Indicate the width and height of the image when using Input to unpacketize and
                                    # parse the receiving packets
     eOnOtherError,                 # Other error occurs
     eOnStopped,                    # The Connection stopped
     eOnAudioMode,                  # Notify the audio mode set on server. This notification is only available when
                                    # connecting to 4000/5000/6000 series servers.
                                    # The pvParam1 contains the integer value that indicates the audio mod.
                                    # Please refer to TMediaAudioMode.
                                    # This status is also notified when someone changes the server audio mode.
                                    # So it is not subjected to called when connecting
     eOnChangeMediaType,            # Notify that due to server settings or users* permission, the media is changed.
                                    # This notification is only available when connecting to 4000/5000/6000 series servers.
                                    # The pvParam1 contains reason. Please refer to TMediaChangeReason.
     eOnAudioDisabled,              # This status code is similar to eOnChangeMediaType.
                                    # But when users get this notification, it means only control channel is established.
                                    # In such case, no audio or video data would be available
     eOnAudioUpstreamOccupied,      # When users start talk and DataBroker finds that the talk-channel is already used
                                    # by other user, this status code will be sent to users by callback.
                                    # This notification is only available when connecting to 4000/5000/6000 series servers
     eOnGetPrivilege,               # Notify the privilege for current user.
                                    # This notification is only available when connecting to 4000/5000/6000 series servers.
                                    # The privilege type is a ORed double word of the privilege define in TUserPrivilege.
     eOnTxChannelStart,             # Notify the Talk connection is established.
                                    # This notification is only available when connecting to 4000/5000/6000 series servers
     eOnTxChannelClosed,            # Notify the control channel has been closed
     eOnControlChannelClosed,       # Notify the control channel has been closed
     eOnVideoSignalChange,          # Notify that there is no signal for video input of Video server model.
                                    # The parameter would either be signal lost or signal restored
     eOnServiceUnavailable,         # Notify that the server is now serving 10 streaming clients and no more new client
                                    # could request for streaming now unless one of the previous connection closed
     eOnAudioUpstreamDisabled,      # Notify that the upstream channel is turned off by server.
                                    # The parameter is the new audio mode that server is set currently
     # for RTSP #
     eOnMediaRange,                 # This is the notification for RTSP server*s playing range for media.
                                    # This is only made if the requested media is file based. For live streaming,
                                    # there will not be such status notified
     eOnMP4VConfig,                 # This is the MP4 CI value for RTSP, pvParam1 is the CI starting address,
                                    # pvParam2 is the length for CI
     eOnMP4AConfig,                 # This is the AAC info value for RTSP, pvParam1 is the DWORD value for the type value
     eOnGAMRConfig,                 # This is the GAMR info value for RTSP, pvParam1 is the sample rate
     eOnG726Config,                 # Rick 2013/02/22 This is the G726 info value for RTSP, pvParam1 is the sample rate,
                                    # pvParam2 is the bit rate
     eOnH264Config,                 # This is the H264 info value for RTSP,
                                    # pvParam1 is the TDataBrokerH264Info pointer address
     eOnConnectionOptionError,
     eOnProxyAuthFailed,            # perkins 2006/11/1 proxy authentication failed
     eOnConnectionType,             # steven 2007/03/30 for dual stream. pvParam1: 1 indicates the connection type is 7k,
                                    # pvParam1: 2 indicates the connection type is 2k
     eOnConnectionTimeout,          # steven 2007/05/07 If user has connected to camera and camera does not send frames,
                                    # DataBroker will callback this status
     eOnTxChannelAuthFail,          # Notify the control channel autenication fail
     eOnMetaDataDisabled,           # When users connect to divece only using meta data type and DataBroker finds that
                                    # the device does not support meta data,
                                    # this status code will be sent to users by callback.
                                    # This notification is only available when connecting to 7000/8000 series servers
     eOnSVCLayerInfo,
     eOnAllocateMemoryFail,         # Rick 2012/05/31 If DataBroker allocate memory fail, It will callback this status
     eOnRTSPSDPData,                # Notify RTSP SDP data
     eOnHEVCConfig,                 # This is the H265 info value for RTSP
     eDataBrokerStatusTypeNum       # 2013/08/08 Vector, Always place this in the end of TDataBrokerStatusType to indicate
                                    # the number of StatusType^M
     ) = xrange(40)

    def __str__(self):
        return str(self.name[3:])

if utility.is_windows():
    FTDataBrokerStatusCallback = ctypes.WINFUNCTYPE(ctypes.c_ulong, ctypes.c_ulong,
                                                    ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p)
    FTDataBrokerAVCallback = ctypes.WINFUNCTYPE(ctypes.c_ulong, ctypes.c_ulong,
                                                ctypes.POINTER(TMediaDataPacketInfo))
    FTDataBrokerTxCallback = ctypes.WINFUNCTYPE(ctypes.c_ulong, ctypes.c_ulong, ctypes.POINTER(ctypes.POINTER(ctypes.c_byte)),
                                                ctypes.POINTER(ctypes.c_ulong), ctypes.POINTER(ctypes.c_ulong))
    FTDataBrokerSBCallback = ctypes.WINFUNCTYPE(ctypes.c_ulong, ctypes.c_ulong, ctypes.POINTER(ctypes.POINTER(ctypes.c_byte)),
                                                ctypes.POINTER(ctypes.c_ulong), ctypes.c_ulong, ctypes.c_ulong,
                                                ctypes.c_ulong)

elif utility.is_linux():
    FTDataBrokerStatusCallback = ctypes.CFUNCTYPE(SCODE, DWORD, ctypes.c_int, PVOID, PVOID)
    FTDataBrokerAVCallback = ctypes.CFUNCTYPE(ctypes.c_ulong, ctypes.c_ulong,
                                              ctypes.POINTER(TMediaDataPacketInfo))
    FTDataBrokerTxCallback = ctypes.CFUNCTYPE(ctypes.c_ulong, ctypes.c_ulong, ctypes.POINTER(ctypes.POINTER(ctypes.c_byte)),
                                              ctypes.POINTER(ctypes.c_ulong), ctypes.POINTER(ctypes.c_ulong))
    FTDataBrokerSBCallback = ctypes.CFUNCTYPE(ctypes.c_ulong, ctypes.c_ulong, ctypes.POINTER(ctypes.POINTER(ctypes.c_byte)),
                                              ctypes.POINTER(ctypes.c_ulong), ctypes.c_ulong, ctypes.c_ulong,
                                              ctypes.c_ulong)