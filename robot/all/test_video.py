# -*- coding: utf-8 -*-


from time import sleep
import time

from fixture import *
from YNM.camera.frame.filter import CodecFilter, video_filter, Filter
from YNM.utility.utility import is_grayscale, is_color


@pytest.mark.video
def test_resolution_change_ok(cam, streaming, configer):

    # Test camera streaming could be change successfully

    c = configer.get('capability&videoin')
    channels = int(c.capability.nvideoin)

    for channel in range(0, channels):
        configer.set('videoin_c%d_rotate=0' % channel)
        time.sleep(2)

        current_mode = c.videoin.c[channel].mode

        exec("resolutions = c.capability.videoin.c[channel].mode%d.resolution" %
             current_mode)

        for resolution in resolutions:
            resolution_filter = Filter('resolution', resolution)
            configer.set('videoin_c%d_s0_resolution=%s' % (channel, resolution))
            time.sleep(3)

            print "testing resolution %s" % resolution

            streaming.connect()
            for i in range(0, 30):
                # resolution may not change immediately, so we drop some frames
                f = streaming.get_one_frame(video_filter)

            f = streaming.get_one_frame(video_filter)
            print "frame got: %dx%d" % (f.width, f.height)
            assert resolution_filter.filter(f) is True, "Resolution change\
                failed. Exp %s, Act %dx%d\n" % (resolution, f.width, f.height)
            streaming.disconnect()


@pytest.mark.video
def test_video_color_bwmode(cam, configer, snapshot, request):

    # Test if camera able to switch B/W or color mode

    def fin():
        configer.set('videoin_c0_color=1')
    request.addfinalizer(fin)

    # switch to monochrome mode
    configer.set('videoin_c0_color=0')
    time.sleep(2)

    status, image = snapshot.take()
    assert status is True, "Snapshot take failed"

    assert is_grayscale(image), "B/W mode failed"

    # switch back to color mode
    configer.set('videoin_c0_color=1')
    time.sleep(2)

    status, image = snapshot.take()
    assert status is True, "Snapshot take failed"

    assert is_color(image), "Color mdoe failed"


@pytest.mark.video
def test_video_switch_video_mode(cam, configer, snapshot, request, streaming):

    # Test if video mode works by iterating each mode and
    # take a #   snapshot.  By checking dimension of snapshot taken, we could
    # know if we have switched to specified mode successfully.  More in depth
    # verification could be like checking streaming fps or something.

    def helper_streaming_playback(cam, configer, streaming, resolution):
        resolution_filter = Filter('resolution', resolution)
        video_filter = Filter('video')
        video_resolution = video_filter + resolution_filter

        streaming.connect()
        f = streaming.get_one_frame(video_resolution)
        assert f, "No valid frame passed. (%s)" % str(f)
        streaming.disconnect()

    def helper_video_switch_mode(cam, configer, snapshot, ch, mode):
        print 'channel %d, mode %d' % (ch, mode)
        caps = cam.capability
        # switch to specified mode
        configer.set('videoin_c%d_mode=%d' % (ch, mode))
        time.sleep(10)

        # max resolution
        resolution = caps.videoin['c'][ch]['mode%d' % mode].maxresolution[0]
        status, image = snapshot.take()
        assert status is True, "Snapshot take failed"
        exp_width, exp_height = resolution.split('x')
        exp_width, exp_height = int(exp_width), int(exp_height)
        act_width, act_height = image.size[0], image.size[1]
        assert exp_width == act_width, "Width doesn't match"
        assert exp_height == act_height, "Height doesn't match"

        return resolution

    caps = cam.capability
    channels = caps.nvideoin
    for channel in range(0, channels):
        modes = caps.videoin['c'][channel].nmode
        for mode in range(0, modes):
            resolution = helper_video_switch_mode(cam, configer,
                                                  snapshot, channel, mode)
            helper_streaming_playback(cam, configer, streaming, resolution)


@pytest.mark.video
@pytest.mark.snapshot
def test_video_snapshot_resolution_matches_with_roi(cam, configer,
                                                    snapshot, request):

    # Test if snapshot resolution matches with ROI configuration
    # Snapshot taken with `streamid' provided should matches with roi_cx_sx_size
    # For example, if roi_c0_s0_size == 640x480, then snapshot size taken with
    # `streamid=0' should also be 640x480.  This test case verifies this, we
    # change roi_c0_s0_size and take a snapshot to know if resolution matches

    # Setup
    caps = cam.capability
    c = configer.get('videoin')
    current_mode = c.videoin.c[0].mode
    mode = caps.videoin['c'][0]['mode%s' % current_mode]
    # Select smallest resolution, typically 320x240
    resolution = mode.resolution[0]
    max_resolution = mode.maxresolution[0]

    # Change resolution
    configer.set('videoin_c0_s0_resolution=%s' % resolution)
    configer.set('roi_c0_s0_size=%s' % resolution)

    def fin():
        configer.set('videoin_c0_s0_resolution=%s' % max_resolution)
        configer.set('roi_c0_s0_size=%s' % max_resolution)
    request.addfinalizer(fin)

    width, height = resolution.split('x')

    status, image = snapshot.take()
    assert status is True, "Snapshot fake failed"
    assert image.size[0] == int(width), \
        "Expect snapshot width matches ROI width"
    assert image.size[1] == int(height), \
        "Expect snapshot height matches ROI height"


@pytest.mark.video
def test_video_codec_c0_s0_change_ok(cam, streaming, configer):

    # Test if camera is able to change video codec

    supported_codecs = cam.capability.videoin.codec

    f = None
    codec_change_success = False
    for codec in supported_codecs:
        configer.set('videoin_c0_s0_codectype=%s' % codec)
        codec_filter = CodecFilter(codec)
        time.sleep(5)
        streaming.connect()
        # wait 60 frames for codec to change
        for frame_count in range(0, 60):
            f = streaming.get_one_frame(video_filter)
            print f
            if codec_filter.filter(f) is True:
                codec_change_success = True
                break

        streaming.disconnect()

    assert codec_change_success, "Codec change failed. Expected %s, actual %s" % (codec, f.codec)

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


def find_appropriate_codec_and_fps(cam, configer):
    caps = cam.capability

    codec_preference = ['h265', 'h264', 'mpeg4', 'mjpeg']
    codec_appropriate = ''
    for codec in codec_preference:
        if codec in caps.videoin.codec:
            codec_appropriate = codec
            break

    exec("fps_appropriate=caps.videoin.c[0].%s.maxframerate[0]" %
         codec_appropriate)
    configer.set('videoin_c0_s0_codectype=%s' % (codec))

    return (codec_appropriate, fps_appropriate)


@pytest.mark.video
def test_cmosfreq_to_50_fps_gte_24_ok(cam, streaming,
                                      configer, cmosfreq_50hz_with_60hz_fin):

    # Test camera frame rate is greater than 24fps when cmos freq is set to 50Hz

    streaming.connect()
    caps = cam.capability

    codecs, fps = find_appropriate_codec_and_fps(cam, configer)
    configer.set('videoin_c0_s0_%s_maxframe=%d' % (codecs, fps))

    for channel in range(0, int(caps.nvideoin)):
        measure = Filter('measure')
        video = Filter('video') + measure

        for frame in range(0, 300):
            streaming.get_one_frame(video)

        exp_fps = 24
        assert measure.fps >= exp_fps, "FPS too low f(under 50Hz). Exp %d, Act\
            %d" % (exp_fps, measure.fps)

    streaming.disconnect()


def fps_helper(cam, configer, streaming):

    streaming.connect()

    codec, max_fps = find_appropriate_codec_and_fps(cam, configer)
    print 'codec %s' % codec
    print 'max_fps %d' % max_fps
    measure = Filter('measure')

    configer.set('videoin_c0_s0_%s_maxframe=%d' % (codec, max_fps))

    for frame in range(0, 300):
        streaming.get_one_frame(measure)

    streaming.disconnect()

    return (max_fps, measure)


@pytest.mark.video
def test_fps_ok(cam, configer, streaming):

    # Test if camera could achieve max fps it declared

    max_fps, measure = fps_helper(cam, configer, streaming)
    assert float(max_fps) * 0.9 <= float(measure.fps), "FPS too low. Exp %d, Act\
        %d" % (max_fps, measure.fps)


@pytest.mark.slow
@pytest.mark.video
def test_fps_steps_ok(cam, configer, streaming, request):

    # Test if camera could achieve customized fps (e.g., fps = 5, 6, 7, 8...
    # etc)

    codec, max_fps = find_appropriate_codec_and_fps(cam, configer)
    measure = Filter('measure')
    video_fps_measure = video_filter + measure

    for fps in range(5, max_fps, 5):
        # test fps from 5 to max, increase 5fps each iteration
        configer.set('videoin_c0_s0_%s_maxframe=%d' % (codec, fps))
        sleep(2)
        streaming.connect()

        for frame in range(0, fps * 10):
            f = streaming.get_one_frame(video_fps_measure)
            print f

        streaming.disconnect()

        assert float(fps) * 0.9 <= float(measure.fps) <= float(fps) * 1.1, "FPS\
            out of range. Exp %f ~ %f, Act %f" % (float(fps) * 0.9, float(fps) *
                                                  1.1, measure.fps)

    def fin():
        configer.set('videoin_c0_s0_%s_maxframe=%d' % (codec, max_fps))

    request.addfinalizer(fin)


@pytest.mark.video
def test_fps_with_wdr_on_ok(cam, configer, streaming, request):

    # Test if frame rate changes when WDR turned on

    caps = cam.capability

    # FIXME. try to figure out how to use c0 correctly in channel
    if caps.image['c'][0].wdrpro.mode == 0:
        pytest.skip("This device doesn't support WDR, skip this test")

    # enable WDR pro
    configer.set('videoin_c0_wdrpro_mode=1')

    max_fps, measure = fps_helper(cam, configer, streaming)
    assert float(max_fps) * 0.9 <= float(measure.fps), "FPS too low. Exp %d, Act\
        %d" % (max_fps, measure.fps)


@pytest.mark.skipif(True, reason="Skip this test right now")
@pytest.mark.video
def test_video_bitrate(cam, configer, streaming, request):

    # Test video bitrate

    def helper_test_video_bitrate(ch, stream, codec, bitrate):
        config = 'videoin_c%d_s%d_%s_bitrate=%d' % (ch, stream, codec, bitrate)
        config += '&videoin_c%d_s%d_codectype=%s' % (ch, stream, codec)
        configer.set(config)
        streaming.connect()
        streaming.setprofile(stream)
        time.sleep(2)
        video = Filter('video')
        measure = Filter('measure')
        video_measure = video + measure

        # measure bitrate for 300 frames
        for idx in range(0, 300):
            f = streaming.get_one_frame(video_measure)
            print f

        streaming.disconnect()
        lower_bound = float(bitrate) * 0.9
        upper_bound = float(bitrate) * 1.1
        print 'measure bitrate %f' % float(measure.bitrate)

        assert lower_bound <= measure.bitrate <= upper_bound, \
            "Bitrate range mismatchm exp %f <= %f <= %f" % (lower_bound,
                                                            measure.bitrate,
                                                            upper_bound)

    # This list is copied from firmware drop list
#     bitrates = [40000000, 36000000, 32000000, 28000000, 24000000, 20000000,
#                 18000000, 16000000, 14000000, 12000000, 10000000, 8000000,
#                 6000000, 4000000, 3000000, 2000000, 1000000, 768000, 512000,
#                 256000, 128000, 64000, 50000, 40000, 30000, 20000]

    bitrates = [8000000, 6000000, 4000000, 3000000, 2000000, 1000000]

    supported_codecs = cam.capability.videoin.codec
    supported_streams = cam.capability.nmediastream
    supported_channels = cam.capability.nvideoin

    for ch in range(0, supported_channels):
        for stream in range(0, supported_streams):
            for codec in supported_codecs:
                for bitrate in bitrates:
                    helper_test_video_bitrate(ch, stream, codec, bitrate)
