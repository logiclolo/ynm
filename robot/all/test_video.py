# -*- coding: utf-8 -*-

from fixture import *
import time
from YNM.camera.frame.filter import Filter, video_filter
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
                f = streaming.get_one_frame(video_filter)

            f = streaming.get_one_frame(video_filter)
            print "frame: %dx%d" % (f.width, f.height)
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
    caps = cam.capability
    c = configer.get('videoin')
    current_mode = c.videoin.c[0].mode
    mode = caps.videoin['c'][0]['mode%s' % current_mode]
    resolution = mode.resolution[0]
    max_resolution = mode.maxresolution[0]
    print 'resolutioni %s' % resolution
    print 'max resolution %s' % max_resolution
    configer.set('roi_c0_s0_size=%s' % resolution)
    configer.set('videoin_c0_s0_resolution=%s' % resolution)

    def fin():
        configer.set('videoin_c0_s0_resolution=%s' % max_resolution)
        configer.set('roi_c0_s0_size=%s' % max_resolution)
    request.addfinalizer(fin)

    width, height = resolution.split('x')

    status, image = snapshot.take()
    assert status is True, "Snapshot fake failed"
    assert image.size[0] == int(width), "Expect snapshot width matches ROI\
        width"
    assert image.size[1] == int(height), "Expect snapshot height matches ROI\
        height"
