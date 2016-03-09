# -*- coding: utf-8 -*-

from YNM.camera.service.system import System
from YNM.camera.camera import Camera

import mock
import pytest


@pytest.mark.skipif(True, reason="skip this test right now")
@mock.patch('YNM.camera.camera.Camera.probe')
def test_system_instantiate():
        configs = {'ip': 'not-exist.com', 'user': 'root', 'passwd': ''}
        cam = Camera(configs)
        System(cam)
