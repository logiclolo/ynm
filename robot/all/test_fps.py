# -*- coding: utf-8 -*-

from fixture import *
from YNM.camera.frame.filter import Filter, video_filter
from time import sleep


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
