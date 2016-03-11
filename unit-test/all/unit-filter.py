# -*- coding: utf-8 -*-

from YNM.camera.frame.filter import Filter, CodecFilter
from YNM.camera.frame.frame import Frame
import YNM.databroker.media_type_def as dbrk_type_def
from mock import Mock
from datetime import datetime, timedelta


def test_or_filters():
    h265 = Filter('h265')
    h264 = Filter('h264')

    h265_or_h264 = h265 | h264

    mocked_h265 = Mock(spec=Frame)
    mocked_h265.codec = 'HEVC'

    mocked_h264 = Mock(spec=Frame)
    mocked_h264.codec = 'H264'

    mocked_mpeg4 = Mock(spec=Frame)
    mocked_mpeg4.codec = 'MPEG4'

    assert h265_or_h264.filter(mocked_h265) is True
    assert h265_or_h264.filter(mocked_h264) is True
    assert h265_or_h264.filter(mocked_mpeg4) is False
    assert isinstance(h265_or_h264.getfilters(), list)


def test_and_filters():
    h265 = Filter('h265')
    key = Filter('keyframe')

    h265_add_key = key + h265
    h265_and_key = key & h265

    mocked_h265_key = Mock(spec=Frame)
    mocked_h265_key.codec = 'HEVC'
    mocked_h265_key.type = dbrk_type_def.TMediaDBFrameType.MEDIADB_FRAME_INTRA

    mocked_h264_key = Mock(spec=Frame)
    mocked_h264_key.codec = 'H264'
    mocked_h264_key.type = dbrk_type_def.TMediaDBFrameType.MEDIADB_FRAME_INTRA

    assert h265_add_key.filter(mocked_h265_key) is True
    assert h265_and_key.filter(mocked_h265_key) is True
    assert h265_and_key.filter(mocked_h264_key) is False
    assert isinstance(h265_and_key.getfilters(), list)


def test_gop_filters():
    iframe = Mock(spec=Frame)
    iframe.type = dbrk_type_def.TMediaDBFrameType.MEDIADB_FRAME_INTRA
    pframe = Mock(spec=Frame)
    pframe.type = dbrk_type_def.TMediaDBFrameType.MEDIADB_FRAME_PRED

    gop30 = Filter('gop', 30)
    assert gop30.filter(iframe) is True

    for i in range(0, 29):
        assert gop30.filter(pframe) is True


def test_gop_with_pframe_first():
    iframe = Mock(spec=Frame)
    iframe.type = dbrk_type_def.TMediaDBFrameType.MEDIADB_FRAME_INTRA
    pframe = Mock(spec=Frame)
    pframe.type = dbrk_type_def.TMediaDBFrameType.MEDIADB_FRAME_PRED

    gop15 = Filter('gop', 15)
    assert gop15.filter(pframe) is False


def test_gop_with_outofrange_frames():
    iframe = Mock(spec=Frame)
    iframe.type = dbrk_type_def.TMediaDBFrameType.MEDIADB_FRAME_INTRA
    pframe = Mock(spec=Frame)
    pframe.type = dbrk_type_def.TMediaDBFrameType.MEDIADB_FRAME_PRED

    gop30 = Filter('gop', 30)
    assert gop30.filter(iframe) is True
    for i in range(0, 29):
        assert gop30.filter(pframe) is True

    assert gop30.filter(pframe) is False


def test_gop_cut_in_the_middle_frame():
    iframe = Mock(spec=Frame)
    iframe.type = dbrk_type_def.TMediaDBFrameType.MEDIADB_FRAME_INTRA
    pframe = Mock(spec=Frame)
    pframe.type = dbrk_type_def.TMediaDBFrameType.MEDIADB_FRAME_PRED

    gop30 = Filter('gop', 30)
    assert gop30.filter(iframe) is True
    for i in range(0, 20):
        assert gop30.filter(pframe) is True

    assert gop30.filter(iframe) is False


def test_not_filter():
    iframe = Mock(spec=Frame)
    iframe.type = dbrk_type_def.TMediaDBFrameType.MEDIADB_FRAME_INTRA
    pframe = Mock(spec=Frame)
    pframe.type = dbrk_type_def.TMediaDBFrameType.MEDIADB_FRAME_PRED

    not_key_frame = ~ Filter('keyframe')
    assert not_key_frame.filter(iframe) is False
    assert not_key_frame.filter(pframe) is True


def test_measure_filter():

    measure = Filter('measure')

    frame = Mock(spec=Frame)
    frame.size_in_bytes = 1000
    frame.time = datetime.now()

    for i in range(0, 300):
        measure.filter(frame)
        frame.time += timedelta(0, 0.033)

    print measure


def test_timeincreasing_filter():
    increasing = Filter('timeincreasing')
    frame1 = Mock(spec=Frame)
    frame1.time = datetime.now()

    frame2 = Mock(spec=Frame)
    frame2.time = datetime.now()

    assert increasing.filter(frame1) is True
    assert increasing.filter(frame2) is True
    assert increasing.filter(frame1) is False


def test_timedecreasing_filter():
    decreasing = Filter('timedecreasing')
    frame1 = Mock(spec=Frame)
    frame1.time = datetime.now()

    frame2 = Mock(spec=Frame)
    frame2.time = datetime.now()

    assert decreasing.filter(frame2) is False
    assert decreasing.filter(frame1) is True
    assert decreasing.filter(frame2) is False


def test_timenojumpforward_filter():
    nojumpforward = Filter('timenojumpforward')
    frame1 = Mock(spec=Frame)
    frame1.time = datetime.now()

    frame2 = Mock(spec=Frame)
    frame2.time = datetime.now()

    frame3 = Mock(spec=Frame)
    frame3.time = frame2.time + timedelta(0, 6)

    assert nojumpforward.filter(frame1) is True
    assert nojumpforward.filter(frame2) is True
    assert nojumpforward.filter(frame3) is False


def test_video_audio_filter():
    h264f = Mock(spec=Frame)
    h264f.codec = 'H264'

    g711 = Mock(spec=Frame)
    g711.codec = 'G711'

    video = Filter('video')
    audio = Filter('audio')

    assert video.filter(h264f) is True
    assert video.filter(g711) is False

    assert audio.filter(g711) is True
    assert audio.filter(h264f) is False


def test_resolution_filter():
    vga = Filter('resolution', '640x480')
    frame_640x480 = Mock(spec=Frame)
    frame_640x480.width = 640
    frame_640x480.height = 480

    frame_800x600 = Mock(spec=Frame)
    frame_800x600.width = 800
    frame_800x600.height = 600

    assert vga.filter(frame_640x480) is True
    assert vga.filter(frame_800x600) is False


def test_nosuch_filter():
    exception_caught = False
    try:
        Filter('no-such-filter')
    except Exception as e:
        exception_caught = True
        print e

    assert exception_caught is True


def test_codec_filter():
    h264 = Filter('codecfilter', 'h264')
    assert isinstance(h264, CodecFilter)
