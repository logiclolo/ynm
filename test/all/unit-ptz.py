# -*- coding: utf-8 -*-

import mock

from YNM.camera.service.ptz import PTZ, SDPTZ, Angle, PTZObject, ElectronicPTZ
from YNM.camera.service.ptz import PanTiltJoystickable, ZoomJoystickable
from YNM.camera.service.ptz import PanTiltable, AbsPanTiltable, Zoomable
from YNM.camera.service.ptz import AbsFocusable, AbsZoomable, Focusable
from YNM.camera.service.ptz import Patrolable, Presetable, CameraCommandError
from YNM.camera.service.ptz import RemoteZoom, RemoteFocus


def test_ptzobject_mechanism_and_category():
    ptz = PTZObject()
    assert (ptz.mechanism == 'mechanical',
            "PTZ default mechanism is 'mechanical'")
    assert (ptz.category == 'standardptz',
            "PTZ default category is 'standardptz'")


def test_sdptz_instantiate():
    cam = mock.MagicMock()
    p1 = mock.patch('YNM.camera.service.ptz.SDPTZ._getlimits_all')
    p2 = mock.patch('YNM.camera.service.ptz.SDPTZ._getstatus_all')
    p1.start()
    p2.start()
    ptz = SDPTZ(cam)
    del(ptz)
    p1.stop()
    p2.stop()


@mock.patch('YNM.camera.camera.Camera.probe')
@mock.patch('YNM.camera.service.ptz.SDPTZ._getlimits_all')
@mock.patch('YNM.camera.service.ptz.SDPTZ._getstatus_all')
def test_whateverable_interface(probe, getlimits, getstatus):
    cam = mock.MagicMock()
    sdptz = SDPTZ(cam)
    assert PanTiltJoystickable(sdptz),\
        "SDPTZ should be able to use joystick for PanTilt"
    assert ZoomJoystickable(sdptz),\
        "SDPTZ should be able to use joystick for Zoom"
    assert PanTiltable(sdptz), "SDPTZ should be able to PanTilt"
    assert AbsPanTiltable(sdptz), "SDPTZ should be able to absolute PanTilt"
    assert Zoomable(sdptz), "SDPTZ should be able to Zoom"
    assert AbsZoomable(sdptz), "SDPTZ should be able to absolute Zoom"
    assert Focusable(sdptz), "SDPTZ should be able to Focus"
    assert AbsFocusable(sdptz), "SDPTZ should be able to absolute Focus"
    assert Patrolable(sdptz), "SDPTZ should be able to Patrol"
    assert Presetable(sdptz), "SDPTZ should be able to Preset"


def test_angle():
    deg_1 = Angle(1)
    deg_1_dot_1 = Angle(1.1)
    deg_1_dot_2 = Angle(1.2)

    assert deg_1 == deg_1_dot_1, "Angle diff smaller than 0.1 should be ignored"
    assert deg_1 != deg_1_dot_2, "Angle diff larger than 0.1 should not pass"

    assert int(deg_1) == 1, "Angle(1) should return 1 on int()"
    assert int(deg_1_dot_2) == 1, "Angle(1.1) should return 1 on int()"
    assert str(deg_1) == "1.0", "Angle(1) should return \"1.0\" on str()"


def test_sdptz_getstatus_all():
    reqs = mock.MagicMock()
    reqs.return_value.status_code = 200
    reqs.return_value.content = 'pan=0&panangle=0&tilt=0&tiltangle=0&zoom=0&focus=0'

    p1 = mock.patch('requests.get', new=reqs)
    p2 = mock.patch('YNM.camera.service.ptz.SDPTZ._getlimits_all')
    p1.start()
    p2.start()

    cam = mock.MagicMock()
    SDPTZ(cam)

    p2.stop()
    p1.stop()


def test_sdptz_getlimits_all():
    reqs = mock.MagicMock()
    reqs.return_value.content = 'maxpan=0&maxpanangle=0&maxtilt=0&maxtiltangle=0&maxzoom=0&maxfocus=0'
    p1 = mock.patch('requests.get', new=reqs)
    p2 = mock.patch('YNM.camera.service.ptz.SDPTZ._getstatus_all')
    p1.start()
    p2.start()

    cam = mock.MagicMock()
    SDPTZ(cam)

    p2.stop()
    p1.stop()


def test_sdptz_action():
    cam = mock.MagicMock()
    reqs = mock.MagicMock()
    reqs.return_value.status_code = 200

    p1 = mock.patch('requests.get', new=reqs)
    p2 = mock.patch('YNM.camera.service.ptz.SDPTZ._getlimits_all')
    p3 = mock.patch('YNM.camera.service.ptz.SDPTZ._getstatus_all')
    p1.start()
    p2.start()
    p3.start()

    ptz = SDPTZ(cam)

    url = 'http://' + cam.url + ptz._cgi

    ptz.pantilt('up')
    command = {'move': 'up', 'setptmode': 'block'}
    reqs.assert_called_once_with(url, params=command, auth=ptz._auth)

    # test pantilt abs in steps
    reqs.reset_mock()
    command = {'setpan': 100, 'settilt': 100}
    ptz.pantilt(command)
    reqs.assert_called_once_with(url, params=command, auth=ptz._auth)

    # test pantilt abs in angle
    reqs.reset_mock()
    command = {'setpanangle': 100, 'settiltangle': 100}
    ptz.pantilt(command)
    reqs.assert_called_once_with(url, params=command, auth=ptz._auth)

    # test pantilt joystick
    reqs.reset_mock()
    command = 'l-joy'
    ptz.pantilt(command)
    assert reqs.called

    # test zoom in relative
    reqs.reset_mock()
    ptz.zoom('in')
    command = {'zoom': 'tele', 'setptmode': 'block'}
    reqs.assert_called_once_with(url, params=command, auth=ptz._auth)

    # test zoom in abs
    reqs.reset_mock()
    command = {'setzoom': 100}
    ptz.zoom(command)
    reqs.assert_called_once_with(url, params=command, auth=ptz._auth)

    # test zoom in joystick
    reqs.reset_mock()
    command = 'in-joy'
    ptz.zoom(command)
    assert reqs.called

    # test focus in relative
    reqs.reset_mock()
    ptz.focus('near')
    command = {'focus': 'near', 'setptmode': 'block'}
    reqs.assert_called_once_with(url, params=command, auth=ptz._auth)

    p3.stop()
    p2.stop()
    p1.stop()


def test_sdptz_get_stuff():
    p1 = mock.patch('YNM.camera.service.ptz.SDPTZ._getstatus_all')
    p2 = mock.patch('YNM.camera.service.ptz.SDPTZ._getlimits_all')

    p1.start()
    p2.start()

    cam = mock.MagicMock()
    ptz = SDPTZ(cam)

    ptz._maxpan = 100
    ptz._pan = 10
    ptz._panangle = 10
    ptz._tilt = 20
    ptz._tiltangle = 20
    ptz._maxzoom = 200
    ptz._maxfocus = 200

    panangle, tiltangle = ptz.get_pantilt_angle()
    assert panangle == ptz._panangle, "Pan angle doesn't match"
    assert tiltangle == ptz._tiltangle, "Tilt angle doesn't match"

    pan, tilt = ptz.get_pantilt_position()
    assert pan == ptz._maxpan - ptz._pan, "Pan doesn't match"
    assert tilt == ptz._tilt, "Tilt doesn't match"

    panlimit, tiltlimit = ptz.get_pantilt_limits()
    assert panlimit == ptz._maxpan, "Max pan doesn't match"
    assert tiltlimit == ptz._maxtilt, "Max tilt doesn't match"

    zoomlimits = ptz.get_zoom_limits()
    assert zoomlimits == ptz._maxzoom, "Max zoom doesn't match"

    focuslimits = ptz.get_focus_limits()
    assert focuslimits == ptz._maxfocus, "Max focus doesn't match"

    p2.stop()
    p1.stop()


def test_sdptz_presets():
    cam = mock.MagicMock()
    reqs = mock.MagicMock()

    p1 = mock.patch('YNM.camera.service.ptz.SDPTZ._getstatus_all')
    p2 = mock.patch('YNM.camera.service.ptz.SDPTZ._getlimits_all')
    p3 = mock.patch('requests.get', new=reqs)

    p1.start()
    p2.start()
    p3.start()

    recallname = 'test'

    ptz = SDPTZ(cam)

    # test recall preset HTTP 200
    reqs.return_value.status_code = 200
    command = {'recall': recallname}
    url = 'http://' + cam.url + ptz._presetcgi
    ptz.recall_preset(recallname)
    reqs.assert_called_once_with(url, params=command, auth=ptz._auth)

    # test recall preset HTTP 400
    reqs.reset_mock()
    reqs.return_value.status_code = 400
    command = {'recall': recallname}
    url = 'http://' + cam.url + ptz._presetcgi
    try:
        ptz.recall_preset(recallname)
    except CameraCommandError:
        pass
    else:
        assert False, "Exception should be thrown in this case"

    # test add preset
    reqs.reset_mock()
    reqs.return_value.status_code = 200
    command = {'addpos': recallname}
    ptz.add_preset(recallname)
    reqs.assert_called_once_with(url, params=command, auth=ptz._auth)

    # test del preset
    reqs.reset_mock()
    reqs.return_value.status_code = 200
    command = {'delpos': recallname}
    ptz.del_preset(recallname)
    reqs.assert_called_once_with(url, params=command, auth=ptz._auth)

    p3.stop()
    p2.stop()
    p1.stop()


def test_eptz_action_relative():
    cam = mock.MagicMock()
    reqs = mock.MagicMock()
    get = mock.MagicMock()
    get.return_value = "resolution='1920x1080'"

    p1 = mock.patch('requests.get', new=reqs)
    p2 = mock.patch('YNM.camera.service.config.Configer.get', new=get)

    patches = [p1, p2]

    for patch in patches:
        patch.start()

    ptz = ElectronicPTZ(cam, 0, 0)

    url = 'http://' + cam.url + ptz._cgi

    command = {'zoom': 'tele'}
    ptz.zoom('in')
    reqs.assert_called_once_with(url, params=command, auth=ptz._auth)

    # pantilt with HTTP 200
    reqs.reset_mock()
    reqs.return_value.status_code = 200
    command = {'move': 'left'}
    ptz.pantilt('left')
    reqs.assert_called_once_with(url, params=command, auth=ptz._auth)

    # pantilt with HTTP 400
    reqs.reset_mock()
    reqs.return_value.status_code = 400
    command = {'move': 'left'}
    try:
        ptz.pantilt('left')
    except CameraCommandError:
        pass
    else:
        assert False, "Exception should be thrown in this case"
#     reqs.assert_called_once_with(url, params=command, auth=ptz._auth)

    for patch in patches:
        patch.stop()


def test_eptz_get_stuff():
    cam = mock.MagicMock()
    reqs = mock.MagicMock()
    get = mock.MagicMock()
    get.return_value = "resolution='1920x1080'"

    p1 = mock.patch('requests.get', new=reqs)
    p2 = mock.patch('YNM.camera.service.config.Configer.get', new=get)

    patches = [p1, p2]
    for patch in patches:
        patch.start()

    ptz = ElectronicPTZ(cam, 0, 0)
    ptz._encw = 1920
    ptz._ench = 1080
    ptz._x = 320
    ptz._y = 240
    cx, cy = ((ptz._encw / 2) + ptz._x, (ptz._ench / 2) + ptz._y)

    pan, tilt = ptz.get_pantilt_position()

    assert cx == pan, "Pan doesn't match"
    assert cy == tilt, "Tilt doesn't match"

    for patch in patches:
        patch.stop()


def test_sdptz_patrols():
    cam = mock.MagicMock()
    reqs = mock.MagicMock()

    p1 = mock.patch('YNM.camera.service.ptz.SDPTZ._getstatus_all')
    p2 = mock.patch('YNM.camera.service.ptz.SDPTZ._getlimits_all')
    p3 = mock.patch('requests.get', new=reqs)

    p1.start()
    p2.start()
    p3.start()

    ptz = SDPTZ(cam)

    # test recall preset HTTP 200
    reqs.return_value.status_code = 200
    command = {'auto': 'patrol'}
    url = 'http://' + cam.url + ptz._presetcgi
    ptz.patrol()
    reqs.assert_called_once_with(url, params=command, auth=ptz._auth)

    # test recall preset HTTP 400
    reqs.reset_mock()
    reqs.return_value.status_code = 400
    url = 'http://' + cam.url + ptz._presetcgi
    try:
        ptz.patrol()
    except CameraCommandError:
        pass
    else:
        assert False, "Exception should be thrown in this case"

    p3.stop()
    p2.stop()
    p1.stop()


def test_ptz_factory():
    eptz = mock.MagicMock()
    rs485 = mock.MagicMock()
    remotef = mock.MagicMock()
    remotez = mock.MagicMock()
    remotezf = mock.MagicMock()
    sdptz = mock.MagicMock()

    p1 = mock.patch('YNM.camera.service.ptz.ElectronicPTZ', new=eptz)
    p2 = mock.patch('YNM.camera.service.ptz.RS485', new=rs485)
    p3 = mock.patch('YNM.camera.service.ptz.RemoteFocus', new=remotef)
    p4 = mock.patch('YNM.camera.service.ptz.RemoteZoom', new=remotez)
    p5 = mock.patch('YNM.camera.service.ptz.RemoteZF', new=remotezf)
    p6 = mock.patch('YNM.camera.service.ptz.SDPTZ', new=sdptz)

    patches = [p1, p2, p3, p4, p5, p6]
    for patch in patches:
        patch.start()

    tests = [
        {'func': helper_test_factory_eptz, 'param': eptz},
        {'func': helper_test_factory_sdptz, 'param': sdptz},
        {'func': helper_test_factory_remotezf, 'param': remotezf},
        {'func': helper_test_factory_remotef, 'param': remotef},
        {'func': helper_test_factory_remotez, 'param': remotez},
        {'func': helper_test_factory_rs485, 'param': rs485}
    ]

    for test in tests:
        test['func'](test['param'])

    for patch in patches:
        patch.stop()


def helper_test_factory_eptz(eptz):
    cam = mock.MagicMock()
    caps = cam.capability
    caps.eptz = 1
    PTZ(cam)
    eptz.assert_called_with(cam, 0, 0)


def helper_test_factory_sdptz(sdptz):
    cam = mock.MagicMock()
    caps = cam.capability
    caps.ptzenabled = 1
    caps.camctrl.c[0].rs485 = 0
    caps.camctrl.c[0].buildinpt = 1
    caps.camctrl.c[0].zoommodule = 1
    PTZ(cam)
    sdptz.assert_called_with(cam)


def helper_test_factory_remotez(remotez):
    cam = mock.MagicMock()
    caps = cam.capability
    caps.remotefocus = 2
    PTZ(cam)
    remotez.assert_called_with(cam)


def helper_test_factory_remotef(remotef):
    cam = mock.MagicMock()
    caps = cam.capability
    caps.remotefocus = 4
    PTZ(cam)
    remotef.assert_called_with(cam)


def helper_test_factory_remotezf(remotezf):
    cam = mock.MagicMock()
    caps = cam.capability
    caps.remotefocus = 1
    PTZ(cam)
    remotezf.assert_called_with(cam)


def helper_test_factory_rs485(rs485):
    cam = mock.MagicMock()
    caps = cam.capability
    caps.nuart = 1
    caps.camctrl.c[0].rs485 = 1
    PTZ(cam)
    rs485.assert_called_with(cam)


def test_ptz_remotezoom():
    cam = mock.MagicMock()
    remotecgi = mock.MagicMock()

    remotecgi.return_value.status_code = 200
    remotecgi.return_value.content = "remote_focus_zoom_motor_max='1150'\r\n\
        remote_focus_zoom_motor_start='0'\r\n\
        remote_focus_zoom_motor_end='1150'\r\n\
        remote_focus_zoom_motor='483'"
    p1 = mock.patch('requests.get', new=remotecgi)

    p1.start()

    remotezoom = RemoteZoom(cam)

    # test ordinary zoom position
    action = {'position': 200}
    remotezoom.zoom(action)

    # test zoom position beyond end of motor
    action = {'position': 5000}
    remotezoom.zoom(action)

    # test zoom position ahead of motor begin
    action = {'position': -1}
    remotezoom.zoom(action)

    # test relative zoom
    remotezoom.zoom('in')

    # test exception
    remotecgi.reset_mock()
    remotecgi.return_value.status_code = 400
    try:
        remotezoom = RemoteZoom(cam)
    except CameraCommandError:
        pass
    else:
        assert False, "Exception should be thrown in this case"

    p1.stop()


def test_ptz_remotefocus():
    cam = mock.MagicMock()
    remotecgi = mock.MagicMock()
    remotecgi.return_value.status_code = 200
    remotecgi.return_value.content = "remote_focus_focus_motor_max='1150'\r\n\
        remote_focus_focus_motor_start='0'\r\n\
        remote_focus_focus_motor_end='1150'\r\n\
        remote_focus_focus_motor='483'"

    p1 = mock.patch('requests.get', new=remotecgi)
    p1.start()

    remotefocus = RemoteFocus(cam)

    # test ordinary focus position
    action = {'position': 200}
    remotefocus.focus(action)

    # test position beyond end of motor
    action = {'position': 5000}
    remotefocus.focus(action)

    # test position ahead of motor begin
    action = {'position': -1}
    remotefocus.focus(action)

    # test get_focus_limist()
    focus_limits = remotefocus.get_focus_limits()
    expected_limits = {'start': 0, 'end': 1150, 'max': 1150}
    assert focus_limits == expected_limits, "Focus limit doesn't match"

    # test relative move
    remotefocus.focus('near')

    # test HTTP 400
    remotecgi.reset_mock()
    remotecgi.return_value.status_code = 400
    try:
        remotefocus.focus(action)
    except CameraCommandError:
        pass
    else:
        assert False, "Exception should be thrown in this case"

    p1.stop()
