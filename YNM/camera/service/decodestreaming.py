# -*- coding: utf-8 -*-
import sys
import ctypes

import YNM.databroker.dbrk_helper as dbrkhelper
import YNM.databroker.avsync_helper as avsynchelper
from YNM.camera.service.streaming import DataBrokerStreaming
from YNM.camera.service.motion import MotionFrame
from YNM.camera.frame.frame import Frame


class DecodeStreaming(DataBrokerStreaming):
    def __init__(self, camera,
                 avcallback=avsynchelper.AvSyncCallback,
                 avsynchelper=avsynchelper.AvSyncHelper):

        super(DecodeStreaming, self).__init__(camera)
        cb = avcallback(self._update_decode_status_cb, self._display_cb)
        self._avsync = avsynchelper(cb)

    def connect(self, async=True):
        super(DecodeStreaming, self).connect()
        self.is_async_mode = async

        # create decode_channel
        avsync = self._avsync
        if self.is_async_mode is False:
            raise NotImplementedError
            self._decode_channel = avsync.create_decoder_channel()
        else:
            self._decode_channel = \
                avsync.create_decoder_channel(self._async_decode_cb)
            self._frame_buf = {}
            self._frame_count = 0
            self._decode_count = 0

    def _put_one_frame(self, context, media_data_packet):
        self._lock.acquire()

        v3_info = ctypes.cast(
            media_data_packet,
            ctypes.POINTER(dbrkhelper.TMediaDataPacketInfoV3))

        tIfEx = v3_info.contents.tIfEx
        tInfo = tIfEx.tInfo
        codec = dbrkhelper.EMediaCodecType(tInfo.dwStreamType)
        frame_type = dbrkhelper.TMediaDBFrameType(tInfo.tFrameType)
        sec = tInfo.dwFirstUnitSecond
        msec = tInfo.dwFirstUnitMilliSecond
        size_in_bytes = tInfo.dwBitstreamSize
        width = tIfEx.dwWidth
        height = tIfEx.dwHeight
        m = MotionFrame(tInfo.bMotionDetection,
                        tInfo.bMotionDetectionAlertFlag,
                        tInfo.byMotionDetectionPercent,
                        tInfo.wMotionDetectionAxis)
        if self.is_async_mode is False:
            avsync = self._avsync
            (rawdata, size) = avsync.decode_one_frame(
                self._decode_channel, media_data_packet)
            f = Frame(sec, msec, size_in_bytes, str(codec), frame_type,
                      width, height, m, v3_info.contents, rawdata, size)
            self._frames.put(f)
            self._lock.release()
        else:
            avsync = self._avsync
            f = Frame(sec, msec, size_in_bytes, str(codec), frame_type,
                      width, height, m, v3_info.contents)
            self._frame_buf.update({self._frame_count: f})
            self._frame_count += 1
            self._lock.release()
            avsync.input_frame_to_decode(self._decode_channel,
                                         media_data_packet)
            # postpone put one frame in this mode,
            # due to decoding process at function _async_decode_cb

        return 0

    def _async_decode_cb(self, context, tFrameType, tFrameInfo):
        self._lock.acquire()
        info = ctypes.cast(
            tFrameInfo, ctypes.POINTER(avsynchelper.TFRAMEINFO)).contents

        if avsynchelper.TMediaType.AVSYNCHRONIZER_MEDIATYPE_VIDEO_ONLY.value \
                == tFrameType:
            data = info.tVideoFrame.pbyPicture
            size = info.tVideoFrame.dwSize

        if avsynchelper.TMediaType.AVSYNCHRONIZER_MEDIATYPE_AUDIO_ONLY.value \
                == tFrameType:
            data = info.tAudioFrame.pbySound
            size = info.tAudioFrame.dwSize

        buf = ctypes.cast(data, ctypes.POINTER(ctypes.c_ubyte * size))
        rawdata = ''.join(map(chr, buf.contents))
        f = self._frame_buf[self._decode_count]
        f.add_rawdata(rawdata, size)
        self._frames.put(f)
        self._frame_buf.pop(self._decode_count, None)
        self._decode_count += 1
        self._lock.release()
        return 0

    def _update_decode_status_cb(self, a, b, c):
        raise NotImplementedError

    def _display_cb(self, a, b, c):
        raise NotImplementedError

    def disconnect(self):
        super(DecodeStreaming, self).disconnect()
        self._avsync.delete_decoder_channel(self._decode_channel)
        if self.is_async_mode is True:
            self._frame_buf = None
            self._frame_count = 0
            self._decode_count = 0
            self.is_async_mode = None
