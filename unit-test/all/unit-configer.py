# -*- coding: utf-8 -*-


import mock
import pytest
from pprint import pprint
from YNM.camera.service.config import Configer, EFormat, Config


@pytest.mark.configer
def test_configer_instantiate():
    cam = mock.MagicMock()
    Configer(cam)


@pytest.mark.configer
def test_configer_get_ok():
    cam = mock.MagicMock()
    mget = mock.MagicMock()

    mget.return_value.status_code = 200
    mget.return_value.text = "capability_videoin_c0_mode='0'\r\n\
        capability_videoout_codec='-'\r\n\
        capability_version_onviftesttool='1412,Profile-S,Profile-G'\r\n"
    p1 = mock.patch('requests.get', new=mget)
    p1.start()

    config = Configer(cam)

    # test config.get with returnd format: Namevalue
    c = config.get('capability', EFormat.eNameValue)
    assert c == mget.return_value.text, \
        "Configer get(raw) error, exp '%s', act '%s'"  \
        % (mget.return_value.text, c)

    # test config.get with returnd format: Dict
    c = config.get('capability')
    cap = c.capability

    assert cap.videoin.c[0].mode == 0, \
        "Configer get(dict) error, exp '0', act '%d'" \
        % cap.videoin.c[0].mode
    assert cap.videoout.codec == '-', \
        "Configer get(dict) error, exp '-', act '%s'" \
        % cap.videoout.codec

    exp_result = [1412, 'Profile-S', 'Profile-G']
    assert cap.version.onviftesttool == exp_result, \
        "Configer get(dict) error, exp '-', act '%s'" \
        % cap.version.onviftesttool
    p1.stop()


@pytest.mark.configer
def test_configer_get_value_ok():
    cam = mock.MagicMock()
    reqs = mock.MagicMock()
    get = mock.MagicMock()
    get.return_value = "capability_videoin_c0_mode='0'\r\n"

    p1 = mock.patch('requests.get', new=reqs)
    p2 = mock.patch('YNM.camera.service.config.Configer.get', new=get)

    patches = [p1, p2]
    for patch in patches:
        patch.start()

    config = Configer(cam)

    result = config.get_value('capability_videoin_c0_mode')
    assert result == 0, \
        "Configer get_value incorrect, exp '0', act '%s'" % result

    for patch in patches:
        patch.stop()


@pytest.mark.configer
def test_configer_set_ok():
    cam = mock.MagicMock()
    mset = mock.MagicMock()

    config = Configer(cam)

    url = 'http://' + cam.url + config.admin.set
    command = "&videoin_c0_s0_resolution=800x600&videoin_c0_s1_enableeptz=1"
    mset.return_value.status_code = 200

    p1 = mock.patch('requests.get', new=mset)
    p1.start()

    # set method: set by dict
    conf = Config()
    conf.videoin.c[0].s[0].resolution = '800x600'
    conf.videoin.c0.s1.enableeptz = '1'
    config.set(conf)
    mset.assert_called_once_with(url, params=command, auth=config._auth)

    p1.stop()
