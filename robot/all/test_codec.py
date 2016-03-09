# -*- coding: utf-8 -*-

from fixture import *
import time
from YNM.camera.frame.filter import CodecFilter, video_filter, audio_filter


@pytest.mark.video
def test_video_codec_c0_s0_change_ok(cam, streaming, configer):

    # Test if camera is able to change video codec

    supported_codecs = cam.capability.videoin.codec

    for codec in supported_codecs:
        configer.set('videoin_c0_s0_codectype=%s' % codec)
        codec_filter = CodecFilter(codec)
        time.sleep(5)
        streaming.connect()
        count = 0
        for frame_count in range(0, 30):
            f = streaming.get_one_frame(video_filter)
            print f
            count += 1
            assert codec_filter.filter(f) is True, "Codec change failed.\
                Expected %s, actual %s" % (codec, f.codec)

        streaming.disconnect()


@pytest.mark.audio
def test_audio_codec_c0_s0_change_ok(cam, streaming, configer):

    # Test if camera is able to change audio codec

    if cam.capability.naudioin < 1:
        pytest.skip("This device doesn't support audio, skip this test")

    configer.set('audioin_c0_mute=0')

    supported_codecs = cam.capability.audioin.codec

    for codec in supported_codecs:
        configer.set('audioin_c0_s0_codectype=%s' % codec)
        codec_filter = CodecFilter(codec)
        time.sleep(4)
        streaming.connect()
        count = 0
        for frame_count in range(0, 30):
            f = streaming.get_one_frame(audio_filter)
            print f
            count += 1
            assert codec_filter.filter(f), "Codec change failed. Expected %s,\
                actual %s" % (codec, f.codec)
        streaming.disconnect()


""" change codec at once """
from threading import Thread


class StreamLoop(Thread):
    def __init__(self, cam, channel, stream, codec, streaming):
        Thread.__init__(self)
        self._cam = cam
        self._streaming = DataBrokerStreaming(cam)
        self._stream = stream
        self._channel = channel
        self._codec = codec
        self._configer = Configer(cam)
        self.frames_played = 0

    def run(self):
        """ This function (run()) is used for playing streaming from camera and
        may be called in multiple test cases.  See original python program for
        detail how this case failed """
        channel = self._channel
        stream = self._stream
        codec = self._codec
        streaming = self._streaming
        configer = self._configer

        configer.set("videoin_c%d_s%d_codectype=%s" % (channel, stream, codec))
        time.sleep(5)
        codec_filter = CodecFilter(codec)

        streaming.connect()

        for i in range(0, 10):
            f = streaming.get_one_frame(video_filter, timeout=10)
            print "<%d> %s" % (stream, f)
            assert codec_filter.filter(f), "<%d> codec mismatch, exp %s, act %s"\
                % (stream, codec, f.codec)
            self.frames_played += 1

        streaming.disconnect()


@pytest.mark.slow
@pytest.mark.video
def test_video_codec_change_all_at_once(cam, streaming):

    # Test if camera's codec could be changed all at once.  Camera with bug may
    # failed to serve streaming after changing codec

    caps = cam.capability
    supported_codecs = caps.videoin.codec
    num_of_streams = caps.nmediastream

    loops = []
    for codec in supported_codecs:
        for stream in range(0, num_of_streams):
            loops.append(StreamLoop(cam, 0, stream, codec, streaming))

        for loop in loops:
            loop.start()

        for idx, loop in enumerate(loops):
            loop.join()
            assert loop.frames_played > 0, "Stream %d is not working" % idx

        # clear this list, from
        #   http://stackoverflow.com/questions/1400608/how-to-empty-a-list-in-python
        loops[:] = []


@pytest.mark.video
def test_video_codec_jpeg_max_resolution_over_rtsp(cam, streaming,
                                                   configer, orientation0_ch0):

    # Test if streaming could be played correctly through rtsp under jpeg if
    # resolution goes too high

    caps = cam.capability
    supported_codecs = caps.videoin.codec
    max_resolution = caps.videoin.c[0].maxresolution[0]
    exp_width, exp_height = max_resolution.split('x')

    if 'mjpeg' not in supported_codecs:
        pytest.skip("This device doesn't support jpeg codec (supports %s),\
                    skip this test" % supported_codecs)

    # test channel=0, stream=0, codec=jpeg
    configer.set('videoin_c0_s0_codectype=mjpeg&videoin_c0_s0_resolution=%s' %
                 max_resolution)
    time.sleep(2)

    streaming.connect()
    for i in range(0, 300):
        f = streaming.get_one_frame(video_filter)
        assert f.width == int(exp_width), "Frame width mismatch"
        assert f.height == int(exp_height), "Frame height mismatch"

    streaming.disconnect()
