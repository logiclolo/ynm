# -*- coding: utf-8 -*-

import mock
from YNM.camera.camera import Camera


@mock.patch('YNM.camera.camera.Camera.probe')
def test_camera_instantiate(mocked):
    test_url = 'this-is-missing-ip.com'
    config = {'ip': 'this-is-missing-ip.com', 'user': 'root', 'passwd': ''}
    cam = Camera(config)

    assert cam.url == test_url, "URL doesn't match"
