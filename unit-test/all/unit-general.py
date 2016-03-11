# -*- coding: utf-8 -*-


import mock
import requests
import StringIO
import pytest

from YNM.camera.camera import Camera
from YNM.camera.camera import NoDeviceWithMACError
from YNM.camera.discovery import DRM


def test_camera_instantiate_ok():
    with mock.patch('YNM.camera.camera.Camera.probe'):
        configs = {'ip': 'test.com', 'user': 'root', 'passwd': ''}
        Camera(configs)


def test_camera_upgrade_ok():
    mck_get = mock.MagicMock(spec=requests.get)
    mck_get.return_value.status_code = 200
    mck_post = mock.MagicMock(spec=requests.post)
    mck_stringio = mock.MagicMock(spec=StringIO.StringIO)
    mck_stringio.return_value = 'mocked_string'
    p1 = mock.patch('requests.get', mck_get)
    p2 = mock.patch('requests.post', mck_post)
    p3 = mock.patch('YNM.camera.camera.Camera.probe')
    p4 = mock.patch('StringIO.StringIO', mck_stringio)

    p1.start()
    p2.start()
    p3.start()
    p4.start()

    configs = {'ip': 'test.com', 'user': 'root', 'passwd': ''}
    cam = Camera(configs)

    # mock upgrade pkg
    pkg_url = 'http://mock.com/mock.pkg'
    cam.upgrade(pkg_url)

    mck_get.assert_called_once_with(pkg_url)
    mck_post.assert_called_once_with('http://' + cam.url +
                                     '/cgi-bin/admin/upgrade.cgi',
                                     files={'file': StringIO.StringIO()})

    mck_get.reset_mock()
    mck_get.return_value.status_code = 500

    assert cam.upgrade(pkg_url) is None

    p1.stop()
    p2.stop()
    p3.stop()
    p4.stop()


@pytest.mark.slow
@pytest.mark.drm
def test_drm_ok():
    from YNM.camera.discovery import DRM
    d = DRM()
    d.refresh()

    assert len(d.search('')) > 0
    assert len(d.search('00:02:D1')) > 0


@pytest.mark.slow
@pytest.mark.drm
def test_general_drm_ip():
    d = DRM()
    d.refresh()

    camera = d.search('unlocked')[0]
    incorrect_IP = '172.16.1.222'
    incorrect_MAC = '00:02:D1:FF:FF:FF'
    correct_IP = camera['ip']
    correct_MAC = camera['mac']

    param = {
        'incorrect_IP': incorrect_IP,
        'incorrect_MAC': incorrect_MAC,
        'correct_IP': correct_IP,
        'correct_MAC': correct_MAC,
        'camera': camera
    }

    test_cases = [
        helper_general_drm_ip_1,
        helper_general_drm_ip_2,
        helper_general_drm_ip_3,
        helper_general_drm_ip_4,
        helper_general_drm_ip_5,
        helper_general_drm_ip_6,
        helper_general_drm_ip_7
    ]

    for case in test_cases:
        case(param)


@pytest.mark.slow
@pytest.mark.drm
def helper_general_drm_ip_1(param):
    # test case 1. only correct IP. assert connected
    camera_config = {'ip': param['correct_IP'], 'user': 'root', 'passwd': ''}
    Camera(camera_config)


@pytest.mark.slow
@pytest.mark.drm
def helper_general_drm_ip_2(param):
    # test case 2. only correct mac. assert IP retrieved
    camera_config = {'mac': param['correct_MAC'], 'user': 'root', 'passwd': ''}
    cam = Camera(camera_config)
    assert cam.url == param['camera']['ip'], "IP doesn't match"


@pytest.mark.slow
@pytest.mark.drm
def helper_general_drm_ip_3(param):
    # test case 3. only incorrect IP. catch exception
    camera_config = {'ip': param['incorrect_IP'], 'user': 'root', 'passwd': ''}
    try:
        Camera(camera_config)
    except Exception as e:
        # expected exception
        print "Expected exception caught %s. This test passed" % str(e)


@pytest.mark.slow
@pytest.mark.drm
def helper_general_drm_ip_4(param):
    # test case 4. only incorrect mac. catch exception
    camera_config = {
        'mac': param['incorrect_MAC'],
        'user': 'root', 'passwd': ''
    }
    try:
        Camera(camera_config)
    except NoDeviceWithMACError:
        print "Expected except caught. This test passed"
    except Exception as e:
        assert False, "Unexpected exception %s" % str(e)


@pytest.mark.slow
@pytest.mark.drm
def helper_general_drm_ip_5(param):
    # test case 5. correct IP and correct mac. assert connected
    camera_config = {
        'ip': param['correct_IP'],
        'mac': param['correct_MAC'],
        'user': 'root',
        'passwd': ''
    }
    Camera(camera_config)


@pytest.mark.slow
@pytest.mark.drm
def helper_general_drm_ip_6(param):
    # test case 6. correct IP and incorrect mac. since mac first then ip, catch
    # exception
    camera_config = {'ip': param['correct_IP'], 'mac': param['incorrect_MAC'],
                     'user': 'root', 'passwd': ''}
    try:
        Camera(camera_config)
    except NoDeviceWithMACError:
        print "Expected exception caught. This test passed"
    except Exception as e:
        assert False, "Unexpcted exception %s" % str(e)


@pytest.mark.slow
@pytest.mark.drm
def helper_general_drm_ip_7(param):
    # test case 7. incorrect IP and correct mac. assert connected
    camera_config = {'ip': param['incorrect_IP'], 'mac': param['correct_MAC'],
                     'user': 'root', 'passwd': ''}
    try:
        Camera(camera_config)
    except Exception as e:
        print "Expected Exception caught %s. This test passed" % str(e)
