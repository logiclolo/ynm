# -*- coding: utf-8 -*-


from YNM.databroker.dbrk_header import *
from YNM.databroker import __version__
from YNM.utility import utility
from YNM.databroker.media_type_def import *
from YNM.databroker.srv_type_def import *
from YNM.utility.error import *
from logging import *


class DBRKCallback(object):
    def __init__(self, on_av, on_status):
        self.on_av = on_av
        self.on_status = on_status


class DBRKHelper(object):
    def __init__(self, callback):
        info('DBRKHelper::init')
        self.__databroker = None
        self.__handle = None
        self.__callback = callback

        self.__load_lib()
        self.__initial()

    def __load_lib(self):
        """Load databroker library using ctypes"""
        if self.__databroker:
            return

        import platform
        # is_64bit = platform.architecture()[0] == '64bit'
        is_64bit = False

        import os
        dll_path = os.path.join(os.path.dirname(__file__), 'dlls')
        lib_path = os.path.join(os.path.dirname(__file__), 'libs')
        cur_wd = os.getcwd()
        try:
            if utility.is_windows():
                info('The platform is WINDOWS.')
                os.chdir(dll_path)
                self.__databroker = ctypes.windll.LoadLibrary('databroker.dll')
                os.chdir(cur_wd)
            elif utility.is_linux():
                info('The platform is LINUX')
                ctypes.CDLL(lib_path+'/libboost_chrono.so.1.59.0', mode=ctypes.RTLD_GLOBAL)
                ctypes.CDLL(lib_path+'/libPBEngine.so', mode=ctypes.RTLD_GLOBAL)
                ctypes.CDLL(lib_path+'/libosisolate.so', mode=ctypes.RTLD_GLOBAL)
                ctypes.CDLL(lib_path+'/libencrypt_md5.so', mode=ctypes.RTLD_GLOBAL)
                ctypes.CDLL(lib_path+'/libcommon.so', mode=ctypes.RTLD_GLOBAL)
                ctypes.CDLL(lib_path+'/libnetutility.so', mode=ctypes.RTLD_GLOBAL)
                ctypes.CDLL(lib_path+'/libsipua.so', mode=ctypes.RTLD_GLOBAL)
                ctypes.CDLL(lib_path+'/librtprtcp.so', mode=ctypes.RTLD_GLOBAL)
                ctypes.CDLL(lib_path+'/libsdpdecoder.so', mode=ctypes.RTLD_GLOBAL)
                ctypes.CDLL(lib_path+'/libencrypt_vivostrcodec.so', mode=ctypes.RTLD_GLOBAL)
                ctypes.CDLL(lib_path+'/libActiveDirectoryClient.so', mode=ctypes.RTLD_GLOBAL)
                ctypes.CDLL(lib_path+'/libntlm.so', mode=ctypes.RTLD_GLOBAL)
                if is_64bit is True:
                    self.__databroker = ctypes.CDLL(lib_path+'/libDataBroker.so', mode=ctypes.RTLD_GLOBAL)
                else:
                    self.__databroker = ctypes.CDLL(lib_path+'/libDataBroker.so', mode=ctypes.RTLD_GLOBAL)
            else:
                raise PlatformError('Do not support the system!')
        except Exception as e:
            print('%s' % e)
            raise LoadDBRKLibError("Load DataBroker Failed!")

    def __initial(self):
        """Create DataBroker handle"""
        if self.__databroker is None:
            self.__load_lib()

        DataBroker_Initial = self.__databroker.DataBroker_Initial

        # Set the argtypes.
        DataBroker_Initial.argtypes = [ctypes.POINTER(ctypes.c_void_p), ctypes.c_ulong, FTDataBrokerStatusCallback,
                                       FTDataBrokerAVCallback, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong]
        self.__handle = ctypes.c_void_p()
        all_codec = EMediaCodecType.mctALLCODEC.value
        self.status_cb = FTDataBrokerStatusCallback(self.__callback.on_status)
        self.av_cb = FTDataBrokerAVCallback(self.__callback.on_av)
        ret = DataBroker_Initial(ctypes.byref(self.__handle),
                                 MAX_CONNECTION,
                                 self.status_cb,
                                 self.av_cb,
                                 all_codec,
                                 0,
                                 utility.makefourcc(__version__[0], __version__[2], __version__[4], __version__[6]))
        if utility.is_fail(ret) == 1:
            raise LoadDBRKLibError

    def __release(self):
        """Release Databroker handle"""
        if self.__databroker is None:
            self.__load_lib()

        DataBroker_Release = self.__databroker.DataBroker_Release

        # Set the argtypes.
        DataBroker_Release.argtypes = [ctypes.POINTER(ctypes.c_void_p)]
        ret = DataBroker_Release(ctypes.byref(self.__handle))
        if utility.is_fail(ret) == 1:
            raise DBRKReleaseError('DataBroker_Release is Fail.')

    def __del__(self):
        if self.__handle:
            info('DBHelper::release')
            self.__release()

    def create_connection(self):
        """Create DataBroker connection"""
        if self.__handle is None:
            raise DBRKHandleIsNotCreatedError("DataBroker handle is not created!")

        DataBroker_CreateConnection = self.__databroker.DataBroker_CreateConnection

        # Set the argtypes.
        DataBroker_CreateConnection.argtypes = [ctypes.c_void_p,
                                                ctypes.POINTER(ctypes.c_void_p)]

        # Invoke API DataBroker_CreateConnection.
        conn_handle = ctypes.c_void_p()
        ret = DataBroker_CreateConnection(self.__handle, ctypes.byref(conn_handle))
        if utility.is_fail(ret) == 1:
            raise DBRKCreateConnectionError('DataBroker_CreateConnection fail')
        return conn_handle

    def delete_connection(self, conn_handle):
        """Delete Databroker connection"""
        info('DBRKHelper::delete_connection')
        if conn_handle is None:
            raise ConnHandleIsNotCreatedError("Connection handle is not be created!")

        DataBroker_DeleteConnection = self.__databroker.DataBroker_DeleteConnection
        # Set the argtypes.
        DataBroker_DeleteConnection.argtypes = [ctypes.c_void_p,
                                                ctypes.POINTER(ctypes.c_void_p)]
        ret = DataBroker_DeleteConnection(self.__handle, ctypes.byref(conn_handle))
        if utility.is_fail(ret) == 1:
            raise DBRKDeleteConnectionError('DataBroker_DeleteConnection fail')

    def connect(self, conn_handle):
        """Connect"""
        info('DBRKHelper::connect')
        if conn_handle is None:
            raise ConnHandleIsNotCreatedError("Connection handle is not be created!")

        DataBroker_Connect = self.__databroker.DataBroker_Connect
        # Set the argtypes.
        DataBroker_Connect.argtypes = [ctypes.c_void_p]
        ret = DataBroker_Connect(conn_handle)
        if utility.is_fail(ret) == 1:
            raise DBRKConnectError("DataBroker_Connect is Fail.")

    def disconnect(self, conn_handle):
        """Disconnect"""
        info('DBRKHelper::disconnect')
        if conn_handle is None:
            raise ConnHandleIsNotCreatedError("Connection handle is not be created!")

        DataBroker_Disconnect = self.__databroker.DataBroker_Disconnect
        # Set the argtypes.
        DataBroker_Disconnect.argtypes = [ctypes.c_void_p]
        ret = DataBroker_Disconnect(conn_handle)
        if utility.is_fail(ret) == 1:
            raise DBRKDisconnectError("DataBroker_Disconnect is Fail.")

    def set_connection_options(self, conn_handle, conn_option):
        """Set connection option"""
        info('DBRKHelper::dbrk_set_connection_options')
        if conn_handle is None:
            raise ConnHandleIsNotCreatedError("Connection handle is not be created!")

        DataBroker_SetConnectionOptions = self.__databroker.DataBroker_SetConnectionOptions
        DataBroker_SetConnectionOptions.argtypes = [ctypes.c_void_p, ctypes.POINTER(TDataBrokerConnectionOptions)]
        ret = DataBroker_SetConnectionOptions(conn_handle, ctypes.byref(conn_option))
        if utility.is_fail(ret) == 1:
            raise DBRKSetConnectionOptionError("DataBroker_SetConnectionOption Fail!")

    def set_connection_url(self, conn_handle, video_url):
        """Set connection extra option for urls"""
        if conn_handle is None:
            raise ConnHandleIsNotCreatedError("Connection handle is not be created!")

        DataBroker_SetConnectionUrlsExtra = self.__databroker.DataBroker_SetConnectionUrlsExtra
        DataBroker_SetConnectionUrlsExtra.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_char),
                                                      ctypes.POINTER(ctypes.c_char), ctypes.POINTER(ctypes.c_char),
                                                      ctypes.POINTER(ctypes.c_char), ctypes.POINTER(ctypes.c_char),
                                                      ctypes.POINTER(ctypes.c_char)]
        null_ptr = ctypes.POINTER(ctypes.c_char)()
        ret = DataBroker_SetConnectionUrlsExtra(conn_handle, video_url, null_ptr, null_ptr, null_ptr, null_ptr, null_ptr)
        if utility.is_fail(ret) == 1:
            raise DBRKSetConnectionUrlsExtraError("DataBroker_SetConnectionUrlsExtra Fail!")

    def set_connection_extra_option(self, conn_handle, option, param1, param2):
        """Set connection extra option for urls"""
        if conn_handle is None:
            raise ConnHandleIsNotCreatedError("Connection handle is None")

        DataBroker_SetConnectionExtraOption = self.__databroker.DataBroker_SetConnectionExtraOption
        DataBroker_SetConnectionExtraOption.argtypes = [ctypes.c_void_p, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong]

        ret = DataBroker_SetConnectionExtraOption(conn_handle, option, param1, param2)
        if utility.is_fail(ret) == 1:
            raise DBRKSetConnectionExtraOptionError("DataBroker_SetConnectionExtraOption Fail!")
