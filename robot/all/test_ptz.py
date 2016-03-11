# -*- coding: utf-8 -*-

from fixture import *
from YNM.camera.service.ptz import PTZ, PanTiltable, Zoomable, Focusable
from YNM.camera.service.ptz import AbsPanTiltable, AbsZoomable, AbsFocusable
from YNM.camera.service.ptz import PanTiltJoystickable, Angle
from YNM.camera.service.snapshot import difference_by_ssim
import time


def tilt_down(ptz):
    (bx, by) = before = ptz.get_pantilt_position()
    (ax, ay) = after = ptz.pantilt('down')

    print 'b %s, a %s' % (before, after)

    assert (ax == bx and ay > by)


def tilt_up(ptz):
    (bx, by) = before = ptz.get_pantilt_position()
    (ax, ay) = after = ptz.pantilt('up')

    print 'b %s, a %s' % (before, after)

    assert (ax == bx and ay < by)


def pan_right(ptz):
    (bx, by) = before = ptz.get_pantilt_position()
    (ax, ay) = after = ptz.pantilt('right')

    print 'b %s, a %s' % (before, after)

    assert (ax > bx and ay == by)


def pan_left(ptz):
    (bx, by) = before = ptz.get_pantilt_position()
    (ax, ay) = after = ptz.pantilt('left')

    print 'b %s, a %s' % (before, after)

    assert (ax < bx and ay == by)


def pantilt_test(cam, ptz):
    tests = [pan_left, pan_right, tilt_up, tilt_down]
    for test in tests:
        test(ptz)


def zoom_out(ptz):
    before = ptz.get_zoom_position()
    after = ptz.zoom('out')

    print 'b %s, a %s' % (before, after)

    assert (before > after)


def zoom_in(ptz):
    before = ptz.get_zoom_position()
    after = ptz.zoom('in')

    print 'b %s, a %s' % (before, after)

    assert (before < after)


def zoom_test(cam, ptz):
    tests = [zoom_in, zoom_out]
    for test in tests:
        test(ptz)
        time.sleep(2)


def focus_near(ptz):
    before = ptz.get_focus_position()
    after = ptz.focus('near')

    print 'b %s, a %s' % (before, after)

    assert (before < after)


def focus_far(ptz):
    before = ptz.get_focus_position()
    after = ptz.focus('far')

    print 'b %s, a %s' % (before, after)

    assert (before > after)


def focus_test(cam, ptz):
    tests = [focus_near, focus_far]
    for test in tests:
        test(ptz)
        time.sleep(2)


def test_ptz_ok(cam, configer):

    # Test if PTZ works by iterating each PTZ controller provided by camera

    ptz = PTZ(cam)
    caps = cam.capability

    rotation_supported = True if caps.videoin.c[0].rotation == 1 else False

    for controller in ptz.controllers:
        ctrler_pantiltable = PanTiltable(controller)
        ctrler_zoomable = Zoomable(controller)
        ctrler_focusable = Focusable(controller)
        ctrler_abspantiltable = AbsPanTiltable(controller)
        ctrler_abszoomable = AbsZoomable(controller)
        ctrler_absfocusable = AbsFocusable(controller)

        stuff = (
            controller, ctrler_zoomable, ctrler_abszoomable, ctrler_pantiltable,
            ctrler_abspantiltable, ctrler_focusable, ctrler_absfocusable
        )

        print('ctrller %s: z %s, (abs)z %s, pt %s, (abs)pt %s, (abs)f %s, f %s'
              % stuff)

        if (ctrler_pantiltable is False and
                ctrler_zoomable is False and
                ctrler_focusable is False):
            continue

        angles = [0, 90, 180, 270]
        if rotation_supported is not True:
            angles = [0]

        ''' test different angles to see if ptz still works as expected under
        different angles '''

        for angle in angles:
            if rotation_supported is True:
                configer.set('videoin_c0_rotate=%d' % angle)
                time.sleep(3)

            if ctrler_pantiltable and ctrler_zoomable:
                controller.pantilt('home')
                controller.zoom('in')
                pantilt_test(cam, controller)
                zoom_test(cam, controller)
                controller.zoom('out')
                controller.pantilt('home')

            elif ctrler_abszoomable:
                to = controller.get_zoom_limits()['end'] / 2
                zoomto = {}
                zoomto['position'] = to
                controller.zoom(zoomto)
                zoom_test(cam, controller)
                controller.zoom(zoomto)

            elif ctrler_abspantiltable:
                controller.pantilt('home')
                pantilt_test(cam, controller)

            elif ctrler_absfocusable:
                to = controller.get_focus_limits()['end'] / 2
                focusto = {}
                focusto['position'] = to
                controller.focus(focusto)
                focus_test(cam, controller)
                controller.focus(focusto)


@pytest.mark.skipif(True, reason="Turn off this test case temporarily")
def test_ptz_image_freeze_ok(cam, configer, snapshot, request):

    # Test if camera image is frozen if image freeze is enabled

    caps = cam.capability
    if caps.image.c[0].freeze == 0:
        pytest.skip("This device doesn't support image freeze, skip this test")

    def fin():
        # turn off image freeze feature
        configer.set('image_c0_freeze=0')

    request.addfinalizer(fin)

    # turn on image freeze feature
    configer.set('image_c0_freeze=1')

    # take a snapshot before testing
    status, image = snapshot.take()
    assert status, "Take a snapshot failed %s" % cam.url

    ptz = PTZ(cam)
    for controller in ptz.controllers:
        if PanTiltJoystickable(controller) is not True:
            continue

        status, image = snapshot.take()
        assert status, "Take a snapshot failed"

        location = controller.get_pantilt_position(cache=False)

        controller.patrol('play')

        time.sleep(0.2)

        location_moved = controller.get_pantilt_position(cache=False)
        status, image_moved = snapshot.take()
        assert status, "Take a snapshot failed"

        assert location != location_moved, "Location should be changed after\
               patrol called"
        diff = difference_by_ssim(image, image_moved)
        assert diff >= 0.90, "Image seems changed after 'image_c0_freeze'\
               enabled"


def test_ptz_absolute_angle_pt(cam, configer, ptz):

    # Test device PTZ which support absolute PTZ angle

    caps = cam.capability

    if "ptz" not in caps:
        pytest.skip("This device doesn't have ptz capability. Skip this test")

    maxpan, maxtilt = caps.ptz.c[0].maxpanangle, caps.ptz.c[0].maxtiltangle

    panunit = maxpan / 4
    tiltunit = maxtilt / 4

    steps = [
        (Angle(1), Angle(1)),
        (Angle(panunit), Angle(tiltunit)),
        (Angle(panunit * 2), Angle(tiltunit * 2)),
        (Angle(panunit * 3), Angle(tiltunit * 3)),
        (Angle(panunit * 4), Angle(tiltunit * 4))
    ]

    for controller in ptz.controllers:
        if AbsPanTiltable(controller) is not True:
            continue

        for step in steps:
            action = {}
            action['panangle'], action['tiltangle'] = step[0], step[1]
            controller.pantilt(action)

            moved_pan, moved_tilt = controller.get_pantilt_angle()

            assert moved_pan == step[0], "Device doesn't pan. Exp %d, Act %d" %\
                (step[0], moved_pan)
            assert moved_tilt == step[1], "Device doesn't tilt. Exp %d, Act %d"\
                % (step[1], moved_tilt)


def test_ptz_absolute_pt(cam, configer, ptz):

    # Test device PTZ which support absolute PTZ step (not angle)

    caps = cam.capability
    if "ptz" not in caps:
        pytest.skip("This device doesn't have ptz caps. Skip this test")

    maxpan, maxtilt = caps.ptz.c[0].maxpan, caps.ptz.c[0].maxtilt

    panunit = maxpan / 4
    tiltunit = maxtilt / 4

    steps = [
        (1, 1),
        (panunit, tiltunit),
        (panunit * 2, tiltunit * 2),
        (panunit * 3, tiltunit * 3),
        (panunit * 4, tiltunit * 4)
    ]

    for controller in ptz.controllers:
        if AbsPanTiltable(controller) is not True:
            continue

        for step in steps:

            action = {}
            action['pan'], action['tilt'] = step[0], step[1]
            controller.pantilt(action)

            moved_pan, moved_tilt = controller.get_pantilt_position()

            assert moved_pan == step[0], "Camera doesn't pan. Exp %d, Act %d" %\
                (step[0], moved_pan)
            assert moved_tilt == step[1], "Camera doesn't tilt. Exp %d, Act %d"\
                % (step[1], moved_tilt)


def test_ptz_absolute_zoom(cam, configer, ptz):

    # Test device PTZ which support absolute zoom

    caps = cam.capability
    if "ptz" not in caps:
        pytest.skip("This devices doesn't have ptz capability")

    maxzoom = caps.ptz.c[0].maxzoom

    zoomunit = maxzoom / 4

    steps = [0, zoomunit, zoomunit * 2, zoomunit * 3, zoomunit * 4]

    for controller in ptz.controllers:
        if AbsZoomable(controller) is not True:
            continue

        for step in steps:
            print step
            command = {'setzoom': step}
            ptz.zoom(command)
