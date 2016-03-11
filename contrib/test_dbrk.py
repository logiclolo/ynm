# -*- coding: utf-8 -*-


from library import utility
from YNM.databroker.data_packet_def import *
from YNM.databroker.dbrk_callback_def import *
from YNM.databroker.media_type_def import *
from YNM.databroker.dbrk_header import *
from YNM.databroker.srv_type_def import *
from YNM.databroker import __version__


import threading
event = threading.Event()

def status_callback(context, status_type, param1, param2):
    print "status_type: %s" % status_to_string(status_type)

    if status_type == eOnStopped or status_type == eOnOtherError:
        print "err_code: %s-%s" % (param1, param2)

    elif status_type == eOnConnectionInfo or status_type == eOnProtocolChanged:
        if status_type == eOnConnectionInfo:
            conn_info = ctypes.cast(param1, ctypes.POINTER(TDataBrokerConnInfo))
            protocol = conn_info.contents.dwProtocol

        else:
            protocol = ctypes.cast(param2, ctypes.c_ulong)
        print "protocol: %s" % protocol_to_string(protocol)
    return 0

def av_callback(context, media_data_packet):
    v3_info = ctypes.cast(media_data_packet, ctypes.POINTER(TMediaDataPacketInfoV3))
    width = v3_info.contents.tIfEx.dwWidth
    height = v3_info.contents.tIfEx.dwHeight
    print "resolution: %s x %s" % (width, height)
    dwutctime = v3_info.contents.dwUTCTime
    print "dwUTCTime: %s" % dwutctime

    print "firstunitsecond.firstunitmillisecond: {0}.{1:0>3}".format(v3_info.contents.tIfEx.tInfo.dwFirstUnitSecond, v3_info.contents.tIfEx.tInfo.dwFirstUnitMilliSecond)
    stream_type = codec_to_string(v3_info.contents.tIfEx.tInfo.dwStreamType)
    print "stream_type: %s" % stream_type
    event.set()
    return 0

if __name__ == '__main__':
    import platform
    #is_64bit = platform.architecture()[0] == '64bit'
    is_64bit = False

    import os
    dll_path = os.path.join(os.path.dirname(__file__), 'library', 'databroker', 'dlls', 'DataBroker.dll')
    cur_wd = os.getcwd()
    os.chdir(os.path.dirname(dll_path))
    try:
        if utility.is_windows():
            print "The platform WINDOWS"
            databroker = ctypes.windll.LoadLibrary(os.path.abspath(dll_path))
        elif utility.is_linux():
            print "The platform LINUX"
            if is_64bit is True:
                databroker = ctypes.cdll.LoadLibrary(cur_wd+'/library/databroker/libs/libDataBroker.so')
            else:
                ctypes.CDLL('libboost_chrono.so.1.59.0', mode=ctypes.RTLD_GLOBAL)
                ctypes.CDLL('libPBEngine.so', mode=ctypes.RTLD_GLOBAL)
                ctypes.CDLL('libosisolate.so', mode=ctypes.RTLD_GLOBAL)
                ctypes.CDLL('libencrypt_md5.so', mode=ctypes.RTLD_GLOBAL)
                ctypes.CDLL('libcommon.so', mode=ctypes.RTLD_GLOBAL)
                ctypes.CDLL('libnetutility.so', mode=ctypes.RTLD_GLOBAL)
                ctypes.CDLL('libsipua.so', mode=ctypes.RTLD_GLOBAL)
                ctypes.CDLL('librtprtcp.so', mode=ctypes.RTLD_GLOBAL)
                ctypes.CDLL('libsdpdecoder.so', mode=ctypes.RTLD_GLOBAL)
                ctypes.CDLL('libencrypt_vivostrcodec.so', mode=ctypes.RTLD_GLOBAL)
                ctypes.CDLL('libActiveDirectoryClient.so', mode=ctypes.RTLD_GLOBAL)
                ctypes.CDLL('libntlm.so', mode=ctypes.RTLD_GLOBAL)
                databroker = ctypes.cdll.LoadLibrary(cur_wd+'/library/databroker/libs/libDataBroker.so')
        else:
            print "Error! Do not support the system!"
    except Exception as e:
        print "Error! Load library failed! %s" % e
    os.chdir(cur_wd)

    # --- STEP 1: Create DataBroker handle --- #
    # Get the function object.
    DataBroker_Initial = databroker.DataBroker_Initial

    # Set the argtypes.
    DataBroker_Initial.argtypes = [ctypes.POINTER(ctypes.c_void_p), ctypes.c_ulong, FTDataBrokerStatusCallback,
                                   FTDataBrokerAVCallback, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong]
    # Invoke API DataBroker_Initial.
    dbrk_handle = ctypes.c_void_p()
    all_codec = EMediaCodecType.mctALLCODEC.value
    status_cb = FTDataBrokerStatusCallback(status_callback)
    av_cb = FTDataBrokerAVCallback(av_callback)
    ret = DataBroker_Initial(ctypes.byref(dbrk_handle),
                             MAX_CONNECTION,
                             status_cb,
                             av_cb,
                             all_codec,
                             0,
                             utility.makefourcc(__version__[0], __version__[2], __version__[4], __version__[6]))
    if utility.is_fail(ret) == 1:
        print "DataBroker_Initial fail"

    # --- STEP 2: Create connection --- #
    DataBroker_CreateConnection = databroker.DataBroker_CreateConnection

    # Set the argtypes.
    DataBroker_CreateConnection.argtypes = [ctypes.c_void_p,
                                            ctypes.POINTER(ctypes.c_void_p)]

    # Invoke API DataBroker_CreateConnection.
    dbrk_connectin_handle = ctypes.c_void_p()
    ret = DataBroker_CreateConnection(dbrk_handle, ctypes.byref(dbrk_connectin_handle))
    if utility.is_fail(ret) == 1:
        print "DataBroker_CreateConnection fail"

    # Set option to connection
    tOpt = TDataBrokerConnectionOptions()
    tOpt.pzIPAddr = '172.16.2.192'
    tOpt.wHttpPort = 80
    tOpt.pzUID = "root"
    tOpt.pzPWD = "123"
    tOpt.dwProtocolType = eptTCP
    tOpt.pzServerType = "auto"
    tOpt.dwMediaType = 3  # (emtVideo | emtAudio)
    #tOpt.dwStatusContext = None  # NULL
    tOpt.pfStatus = status_cb
    tOpt.pfAV = av_cb

    DataBroker_SetConnectionOptions = databroker.DataBroker_SetConnectionOptions
    DataBroker_SetConnectionOptions.argtypes = [ctypes.c_void_p, ctypes.POINTER(TDataBrokerConnectionOptions)]
    ret = DataBroker_SetConnectionOptions(dbrk_connectin_handle, ctypes.byref(tOpt))
    if utility.is_fail(ret) == 1:
        print "DataBroker_SetConnectionOptions fail"

    # Connect
    DataBroker_Connect = databroker.DataBroker_Connect
    DataBroker_Connect.argtypes = [ctypes.c_void_p]
    ret = DataBroker_Connect(dbrk_connectin_handle)
    if utility.is_fail(ret) == 1:
        print "DataBroker_Connect fail"

    import time
    time.sleep(10)
    event.set()
    print "over"


