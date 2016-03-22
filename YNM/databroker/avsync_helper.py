import os
import ctypes
import sys
from YNM.utility.data_type_def import DWORD
from YNM.databroker.avsync_header import *
from YNM.databroker.media_type_def import EMediaCodecType
from YNM.utility import utility
from YNM.utility.error import *
from logging import info


class AvSyncCallback(object):
    def __init__(self, on_status, on_display, decode=None):
        self.on_status = on_status
        self.on_display = on_display
        self.decode = decode


class AvSyncHelper(object):
    def __init__(self, callback):
        info('AvSyncHelper::init')
        self.__handle = None
        self.__avsync = None
        self.__callback = callback

        self.__load_lib()
        self.__initial()

    def __load_lib(self):
        """Load AvSynchronizer library using ctypes"""
        if self.__avsync:
            return

        lib_path = os.path.join(os.path.dirname(__file__), 'libs')
        try:
            if utility.is_linux():
                info('The platform is LINUX')
                ctypes.CDLL(lib_path+'/libavcodec.so.57',
                            mode=ctypes.RTLD_GLOBAL)
                ctypes.CDLL(lib_path+'/libswresample.so.2',
                            mode=ctypes.RTLD_GLOBAL)
                ctypes.CDLL(lib_path+'/libavutil.so.55',
                            mode=ctypes.RTLD_GLOBAL)
                ctypes.CDLL(lib_path+'/libswscale.so.4',
                            mode=ctypes.RTLD_GLOBAL)
                self.__avsync = \
                    ctypes.CDLL(lib_path+'/libAVSynchronizer.so',
                                mode=ctypes.RTLD_GLOBAL)
            else:
                raise PlatformError('Do not support the system!')
        except Exception as e:
            print('%s' % e)
            raise LoadLibError("Load AvSynchronizer Failed!")

    def __initial(self):
        ''' Create AvSyncHelper '''
        if self.__avsync is None:
            self.__load_lib()

        AvSynchronizer_InitialEx = self.__avsync.AvSynchronizer_InitialEx
        # TODO :Set the argtypes.
        '''
        dummy = ctypes.POINTER(ctypes.c_void_p),
#        FTLPStatusCallBack = dummy
#        FTLPDisplayCallBack = dummy
        self.decoded_status_cb = FTLPStatusCallBack(self.__callback.on_status)
        self.display_cb = FTLPDisplayCallBack(self.__callback.on_display)
        HWND = dummy
        AvSynchronizer_InitialEx.argtypes = [
            ctypes.POINTER(ctypes.c_void_p),
            self.decoded_status_cb, self.display_cb, HWND,
#            None, None, None,
            ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong,
            ctypes.c_ulong, ctypes.c_ulong
        ]
        '''
        self.__handle = ctypes.c_void_p()

        ret = AvSynchronizer_InitialEx(
            ctypes.byref(self.__handle), None, None, None,
            TAudioFocusType.AUDIOOUT_FOCUS_NORMAL,
            0, utility.makefourcc(5, 4, 0, 9),
            EAYSyncInitFlag.DECODER_CHANNEL_ONLY, 1, 0)
        if utility.is_fail(ret) == 1:
            raise LoadLibError

    def create_decoder_channel(self, cb=None):
        ''' Create Decorder channel '''

        AvSynchronizer_CreateDecoderChannel = \
            self.__avsync.AvSynchronizer_CreateDecoderChannel
        # Set the argtypes.
        AvSynchronizer_CreateDecoderChannel.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_void_p),
            ctypes.POINTER(TDECHOPTION)
        ]

        # Invoke API AvSynchronizer_CreateDecoderChannel
        decode_handle = ctypes.c_void_p()
        dec_ch_options = TDECHOPTION()
        dec_ch_options.dwRawDataFormat = EPIXELFORMAT.PF_YUV
        if cb is not None:
            self.__callback.decode = FTLPDecordeFrameCallback(cb)
            dec_ch_options.pfDecodeFrame = \
                self.__callback.decode
        ret = AvSynchronizer_CreateDecoderChannel(
            self.__handle, ctypes.byref(decode_handle),
            ctypes.byref(dec_ch_options))

        if utility.is_fail(ret) == 1:
            raise AVSyncCreateDecoderError(
                'AvSynchronizer_CreateDecoderChannel fail')
        return decode_handle

    def set_decoder_channel_option(self):
        # TODO
        AvSynchronizer_SetChannelOption = \
            self.__avsync.AvSynchronizer_SetChannelOption
        # Set the argtypes.
        AvSynchronizer_SetChannelOption.argtypes = [
            ctypes.c_void_p,
        ]

        # Invoke API AvSynchronizer_SetChannelOption

    # for async mode
    def input_frame_to_decode(self, decode_handle, media_data_packet):
        info = ctypes.cast(
            media_data_packet,
            ctypes.POINTER(TMediaDataPacketInfo))

        AvSynchronizer_InputToBeDecodedMediaFrame = \
            self.__avsync.AvSynchronizer_InputToBeDecodedMediaFrame
        # Set the argtypes.
        AvSynchronizer_InputToBeDecodedMediaFrame.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(TMediaDataPacketInfo)
        ]

        # Invoke API AvSynchronizer_CreateDecoderChannel
        AvSynchronizer_InputToBeDecodedMediaFrame(decode_handle, info)

    def decode_one_frame(self, decode_handle, media_data_packet):

        v3_info = ctypes.cast(
            media_data_packet,
            ctypes.POINTER(TMediaDataPacketInfoV3)).contents
        tPacketInfo = ctypes.cast(
            media_data_packet, ctypes.POINTER(TMediaDataPacketInfo)).contents

        f_info = TFRAMEINFO()

        if v3_info.tIfEx.tInfo.dwStreamType < EMediaCodecType.mctG7221.value:
            buf_size = v3_info.tVUExt.tCapWinInfo.wCapW *\
                v3_info.tVUExt.tCapWinInfo.wCapH * 3 >> 1
            is_video = True
        else:
            buf_size = 2048 * 10
            is_video = False

        buf = (ctypes.c_ubyte * buf_size)()
        pbuf = ctypes.cast(buf, BYTE_p)
        decoded_size = DWORD()

        if is_video:
            f_info.tVideoFrame.pbyHeader = pbuf
            f_info.tVideoFrame.dwSize = buf_size

            AvSynchronizer_DecodeVideo = \
                self.__avsync.AvSynchronizer_DecodeVideo
            # Set the argtypes.
            AvSynchronizer_DecodeVideo.argtypes = [
                ctypes.c_void_p,
                ctypes.POINTER(TMediaDataPacketInfo),
                ctypes.POINTER(TVFRAMEINFO),
                ctypes.POINTER(DWORD),
            ]

            ret = AvSynchronizer_DecodeVideo(
                decode_handle, tPacketInfo,
                ctypes.byref(f_info.tVideoFrame), decoded_size)
            if utility.is_fail(ret) == 1:
                raise AVSyncDecodeError(
                    'AvSynchronizer_DecodeVideo fail')

        else:
            f_info.tAudioFrame.pbySound = pbuf
            f_info.tAudioFrame.dwsize = buf_size
            AvSynchronizer_DecodeAudio = \
                self.__avsync.AvSynchronizer_DecodeAudio
            # Set the argtypes.
            AvSynchronizer_DecodeAudio.argtypes = [
                ctypes.c_void_p,
                ctypes.POINTER(TMediaDataPacketInfo),
                ctypes.POINTER(TAFRAMEINFO),
                ctypes.POINTER(DWORD),
            ]

            ret = AvSynchronizer_DecodeAudio(
                decode_handle, tPacketInfo,
                ctypes.byref(f_info.tAudioFrame), decoded_size)
            if utility.is_fail(ret) == 1:
                raise AVSyncDecodeError(
                    'AvSynchronizer_DecodeAudio fail')
        return buf, decoded_size

    def delete_decoder_channel(self, decode_handle):
        AvSynchronizer_DeleteDecoderChannel = \
            self.__avsync.AvSynchronizer_DeleteDecoderChannel

        # Set the argtypes.
        AvSynchronizer_DeleteDecoderChannel.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_void_p)
        ]
        ret = AvSynchronizer_DeleteDecoderChannel(
            self.__handle, ctypes.byref(decode_handle))

        if utility.is_fail(ret) == 1:
            raise AVSyncDeleteDecoderError(
                'AvSynchronizer_DeleteDecoderChannel fail')

    def __del__(self):
        AvSynchronizer_Release = \
            self.__avsync.AvSynchronizer_Release

        # Set the argtypes.
        AvSynchronizer_Release.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_void_p)
        ]
        ret = AvSynchronizer_Release(
            self.__handle, ctypes.byref(decode_handle))

        if utility.is_fail(ret) == 1:
            raise AVSyncDeleteDecoderError(
                'AvSynchronizer_Release fail')
