# -*- coding: utf-8 -*-

import mock
import pytest

from YNM.camera.camera import Camera
from YNM.camera.frame.filter import Filter
from YNM.databroker.dbrk_helper import DBRKHelper
from fixture import DataBrokerStreaming
from setting import config
import YNM.camera.service.streaming as streaming


@pytest.mark.slow
def test_dbrk_streaming_ok():
    cam = Camera(config)
    streaming1 = streaming.DataBrokerStreaming(cam)

    # get one frame before connecting to test exception
    try:
        f = streaming1.get_one_frame()
    except streaming.NoFramesReceivedTimeout:
        pass

    streaming1.connect()

    # test profile changing
    streaming1.setprofile(1)

    # grab 10 frames
    for i in range(0, 10):
        f = streaming1.get_one_frame()
        if f.is_audio():
            assert not f.is_video()
        else:
            assert f.is_video()
        assert str(f)
        print "Motion trig. %s" % f.motion.triggered()

    # test getframes
    for i in range(0, 10):
        f = streaming1.getframes(2)
        assert f[0]
        assert f[1]

    nothingpass = Filter('h264') + Filter('h265')
    try:
        f = streaming1.get_one_frame(nothingpass)
    except streaming.NoFramesPassFilterTimeout:
        pass

    streaming1.disconnect()


def test_dbrk_streaming_by_mock():
    mckDBRKHelper = mock.MagicMock(spec=DBRKHelper)
    mckCamera = mock.MagicMock(spec=Camera)
    mckCamera.url = '192.168.1.1'
    mckCamera.username = 'admin'
    mckCamera.password = ''
    mckCamera.http_port = 80
    streaming = DataBrokerStreaming(mckCamera, dbrkhelper=mckDBRKHelper)

    streaming.connect()
    assert streaming._databroker.create_connection.called
    assert streaming._databroker.set_connection_options.called

    streaming._databroker.set_connection_options.reset_mock()
    streaming.connect()
    assert streaming.connected() is True
    assert streaming._databroker.set_connection_options.called is not True

    streaming.disconnect()
    assert streaming._databroker.disconnect.called
    assert streaming._databroker.delete_connection.called
