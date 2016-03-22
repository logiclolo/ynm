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

    def connect(self):
        super(DecodeStreaming, self).connect()
        # create decode_channel
        avsync = self._avsync
        self._decode_channel = avsync.create_decoder_channel()
        self.count = 0

    def _put_one_frame(self, context, media_data_packet):

        self._lock.acquire()
        self.count += 1

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

        avsync = self._avsync
        (rawdata, raw_size) = avsync.decode_one_frame(
            self._decode_channel, media_data_packet)
        f = Frame(sec, msec, size_in_bytes, str(codec), frame_type, width,
                  height, m, v3_info.contents)
        self._frames.put(f)
        self._lock.release()
        return 0

    def _update_decode_status_cb(self, a, b, c):
        raise NotImplementedError

    def _display_cb(self, a, b, c):
        raise NotImplementedError

    def disconnect(self):
        super(DecodeStreaming, self).disconnect()
        self._avsync.delete_decoder_channel(self._decode_channel)
