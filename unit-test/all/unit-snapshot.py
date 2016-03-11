# -*- coding: utf-8 -*-

import mock
import requests

from PIL import Image
from YNM.camera.service.snapshot import Snapshot
from YNM.camera.camera import Camera


def test_snapshot_take():
    mocked_get = mock.MagicMock(spec=requests.get)
    mocked_cam = mock.MagicMock(spec=Camera)
    mocked_image_open = mock.MagicMock(spec=Image.open)
    mocked_post = mock.MagicMock(spec=requests.post)
    mcam = mocked_cam()
    mcam.url = 'test.snapshot.com'
    mcam.username = 'test'
    mcam.password = 'test'
    test_cgi = '/test/cgi-bin/viewer/video.jpg'
    test_param = {'name': 'value'}

    p1 = mock.patch('PIL.Image.open', mocked_image_open)
    p2 = mock.patch('requests.get', mocked_get)
    p3 = mock.patch('requests.post', mocked_post)

    p1.start()
    p2.start()
    p3.start()

    mocked_get.return_value.status_code = 200
    shot = Snapshot(mcam, cgi=test_cgi)
    stat, image = shot.take()
    assert stat is True

    call_url = 'http://%s/test/cgi-bin/viewer/video.jpg' % mcam.url
    mocked_get.assert_called_once_with(call_url, auth=(mcam.username,
                                                       mcam.password))

    # test snapshot CGI returns error case
    mocked_get.reset_mock()
    mocked_get.return_value.status_code = 400
    stat, image = shot.take()
    assert stat is False

    mocked_post.return_value.status_code = 200
    shot = Snapshot(mcam, cgi=test_cgi)
    stat, image = shot.take(param=test_param)
    assert stat is True
    mocked_post.assert_called_once_with(call_url, auth=(mcam.username,
                                                        mcam.password),
                                        data=test_param)

    p3.stop()
    p2.stop()
    p1.stop()
