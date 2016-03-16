# -*- coding: utf-8 -*-

import time

from fixture import *
from YNM.camera.frame.catcher import Catcher
from YNM.camera.service.config import Config
from YNM.camera.frame.filter import Filter, video_filter, audio_filter


def test_streaming_ok(cam, configer, streaming):

    # Test video streaming ok

    caps = cam.capability
    num_of_streams = caps.nmediastream
    audio_supported = True if caps.naudioin > 0 else False
    if audio_supported:
        configer.set("audioin_c0_mute=0")

    print "this camera supports %d streams" % num_of_streams

    for stream_idx in range(0, num_of_streams):
        audio_frame_count = 0
        video_frame_count = 0

        print "set profile to %d" % stream_idx
        streaming.connect()
        streaming.setprofile(stream_idx)
        time.sleep(2)
        for frames in range(0, 90):
            f = streaming.get_one_frame()
            if video_filter.filter(f) is True:
                video_frame_count += 1
            elif audio_filter.filter(f) is True:
                audio_frame_count += 1
#             print f

        assert video_frame_count > 0
        if audio_supported:
            assert audio_frame_count > 0

        print "%d video frames." % video_frame_count
        if audio_supported:
            print "%d audio frames." % audio_frame_count

        streaming.disconnect()


@pytest.mark.slow
def test_videotimestamp_should_not_rollback(streaming):

    # Test streaming ok and check if timestamp embedded in the extension is
    # monotonically increasing.  However, this test case should be run as long
    # as possible, current run time is obviously not long enough.

    # TODO: think if there is any solution to make this test case reasonably
    # long and reasonably short

    streaming.connect()

    decrease_catcher = Catcher(Filter("timedecreasing"))
    videofilter = Filter('video')

    # wait 3000 frames to see if timestamp rollback happens
    for frame_count in range(0, 3000):
        f = streaming.get_one_frame(videofilter)
        decrease_catcher.catch(f)


def test_timestamp_rotate_streaming_ok(cam, configer, streaming):

    # Test streaming ok when streaming rotated

    caps = cam.capability
    num_of_streams = caps.nmediastream
    conf = Config()
    conf.videoin.c[0].imprinttimestamp = 1
    configer.set(conf)

    print "this camera supports %d streams" % num_of_streams

    for stream_idx in range(0, num_of_streams):
        video_frame_count = 0

        print "set profile to %d" % stream_idx
        streaming.connect()
        streaming.setprofile(stream_idx)
        time.sleep(2)
        rotates = [0, 90, 180, 270]
        for rotate in rotates:
            if caps.videoin.c[0].rotation == 1:
                conf.videoin.c[0].rotate = rotate
                configer.set(conf)
            for frames in range(0, 90):
                f = streaming.get_one_frame()
                if video_filter.filter(f) is True:
                    video_frame_count += 1

            assert video_frame_count > 0
            print "%d video frames." % video_frame_count

        streaming.disconnect()


def test_enable_dis_streaming_ok(cam, configer, streaming, request):

    # Test if camera able to stream after EIS enabled.  Cmaera doesn't support
    # EIS will auto skip this test

    caps = cam.capability
    num_of_streams = caps.nmediastream
    try:
        eis_supported = True if str(caps.image.c[0].eis) == "0" else False
    except KeyError:
        # compat for old model which doesn't support OneFW
        c = configer.get('image_c0_eis')
        if len(c) > 0:
            eis_supported = True
        else:
            eis_supported = False

    pytest.mark.skipif(not eis_supported,
                       reason="Camera does not support EIS, skip this test")

    def eis_generator(enable):
        def generated():
            configer.set('videoin_c0_eis=%d' % enable)
        return generated

    e = eis_generator(1)
    e()

    d = eis_generator(0)

    request.addfinalizer(d)

    for stream_idx in range(0, num_of_streams):
        video_frame_count = 0

        print "set profile to %d" % stream_idx
        streaming.connect()
        streaming.setprofile(stream_idx)
        time.sleep(2)
        for frames in range(0, 90):
            f = streaming.get_one_frame()
            if video_filter.filter(f) is True:
                video_frame_count += 1
#             print f

        assert video_frame_count > 0, "Camera stop streaming after EIS enabled"

        print "%d video frames." % video_frame_count

        streaming.disconnect()


""" play all streamings that a device could provide to see anything happens """

from threading import Thread


class StreamLoop(Thread):
    def __init__(self, handle, stream_idx):
        Thread.__init__(self)
        self._handle = handle
        self._stream_idx = stream_idx

    def run(self):
        handle = self._handle
        stream_idx = self._stream_idx
        handle.connect()
        handle.setprofile(stream_idx)
        time.sleep(2)
        for i in range(0, 300):
            f = handle.get_one_frame()
            print "<%d> %s" % (stream_idx, f)
        handle.disconnect()


def test_streaming_all_at_once(cam):

    # Test if ALL streaming could be played at once

    caps = cam.capability
    streams_supported = caps.nmediastream

    print "this camera supports %d streams" % streams_supported

    # instantiate all streams and store them into a list
    streams = []
    for i in range(0, streams_supported):
        stream = DataBrokerStreaming(cam)
        streams.append(StreamLoop(stream, i))

    for stream in streams:
        stream.start()

    # wait until all threads are terminated
    for stream in streams:
        stream.join()
