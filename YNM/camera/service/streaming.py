# -*- coding: utf-8 -*-

import abc
import Queue
import threading
import ctypes

import YNM.databroker.dbrk_helper as dbrkhelper
import YNM.databroker.srv_type_def as dbrksvrtype
from YNM.camera.service.motion import MotionFrame
from YNM.camera.frame.frame import Frame


class IStreaming:
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def get_one_frame(self):
        raise NotImplemented()

    @abc.abstractmethod
    def connect(self):
        raise NotImplemented()

    @abc.abstractmethod
    def connected(self):
        raise NotImplemented()

    @abc.abstractmethod
    def getframes(self, num_of_frames, filter=None):
        raise NotImplemented()

    @abc.abstractmethod
    def setprofile(self, profile):
        raise NotImplemented()


class NoFramesReceivedTimeout(Exception):
    pass


class NoFramesPassFilterTimeout(Exception):
    pass


class DataBrokerStreaming (IStreaming):
    def __init__(self, camera, callback=dbrkhelper.DBRKCallback,
                 dbrkhelper=dbrkhelper.DBRKHelper):
        self._camera = camera
        self._frames = Queue.Queue()
        self._conn = None
        cb = callback(self._put_one_frame, self._update_connection_status)
        self._databroker = dbrkhelper(cb)
        self._lock = threading.Lock()
        self._connected = True

    def setprofile(self, profile):
        stream_index = int(profile)
        databroker = self._databroker
        eOptStreamIndex = 10
        databroker.set_connection_extra_option(self._conn, eOptStreamIndex,
                                               stream_index, 0)

    def _put_one_frame(self, context, media_data_packet):
        self._lock.acquire()

        v3_info = ctypes.cast(media_data_packet,
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
        m = MotionFrame(tInfo.bMotionDetection, tInfo.bMotionDetectionAlertFlag,
                        tInfo.byMotionDetectionPercent,
                        tInfo.wMotionDetectionAxis)
        f = Frame(sec, msec, size_in_bytes, str(codec), frame_type, width,
                  height, m, v3_info.contents)

        self._frames.put(f)

        self._lock.release()
        return 0

    def _update_connection_status(self, context, status_type, param1, param2):
        status = dbrkhelper.TDataBrokerStatusType(status_type)
        self._connection_status = status
#         print "status %s" % self._connection_status
        if status == dbrkhelper.TDataBrokerStatusType.eOnStopped:
            self._frames.queue.clear()
            self.connect()

        return 0

    def get_one_frame(self, custom_filter=None, timeout=2, frameout=300):
        filtered = False
        frame_to_get = None
        frame_count = 0
        while filtered is False:
            try:
                frame_to_get = self._frames.get(True, timeout)
            except Queue.Empty:
                raise NoFramesReceivedTimeout("no frame received for %d seconds"
                                              % timeout)

            frame_count += 1
            if frame_count >= frameout:
                raise NoFramesPassFilterTimeout("%d frame got, but no frame\
                                                passed" % frameout)
            if custom_filter is None or custom_filter.filter(frame_to_get) is True:
                filtered = True

        return frame_to_get

    def getframes(self, num_of_frames, filter=None):
        frames = []
        for i in range(0, num_of_frames):
            f = self.get_one_frame(filter)
            frames.append(f)

        return frames

    def connect(self):
        databroker = self._databroker
        if self._conn is None:
            conn = databroker.create_connection()
            self._conn = conn
            eptTCP = dbrksvrtype.TProtocolType.eptTCP.value
            emtVideo = dbrksvrtype.TMediaType.emtVideo.value
            emtAudio = dbrksvrtype.TMediaType.emtAudio.value
            conn_opt = dbrkhelper.TDataBrokerConnectionOptions()
            conn_opt.pzIPAddr = ctypes.c_char_p(self._camera.url)
            conn_opt.wHttpPort = ctypes.c_ushort(self._camera.http_port)
            conn_opt.pzUID = ctypes.c_char_p(self._camera.username)
            conn_opt.pzPWD = ctypes.c_char_p(self._camera.password)
            conn_opt.dwProtocolType = eptTCP
            conn_opt.pzServerType = "auto"
            conn_opt.dwMediaType = (emtVideo | emtAudio)
            conn_opt.pfStatus = dbrkhelper.FTDataBrokerStatusCallback(self._update_connection_status)
            conn_opt.pfAV = dbrkhelper.FTDataBrokerAVCallback(self._put_one_frame)
            dwFlags = dbrkhelper.TDataBrokerConnOptionFlag.eConOptProtocolAndMediaType.value
            dwFlags |= dbrkhelper.TDataBrokerConnOptionFlag.eConOptHttpPort.value
            conn_opt.dwFlags = ctypes.c_ulong(dwFlags)
            databroker.set_connection_options(conn, conn_opt)
        else:
            conn = self._conn

        return databroker.connect(conn)

    def connected(self):
        return self._connected

    def disconnect(self):
        databroker = self._databroker
        conn = self._conn
        databroker.disconnect(conn)
        databroker.delete_connection(conn)
        self._frames.queue.clear()
        self._conn = None

IStreaming.register(DataBrokerStreaming)
