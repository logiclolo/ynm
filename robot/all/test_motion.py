# -*- coding: utf-8 -*-

from fixture import *
from YNM.camera.frame.filter import video_filter
import time


def test_motion_polygon_with_sense100_objsize1_rotate(cam, configer, streaming,
                                                      motion, request):

    # Test motion. Create poloygons with sensitivity 100, objsize 1 and rotate
    # if device supports this feature

    helper_motion_clear_all(configer, cam, motion)
    clear = 'videoin_c0_rotate=0&motion_c0_enable=0'

    def fin():
        configer.set(clear)
        helper_motion_clear_all(configer, cam, motion)
    request.addfinalizer(fin)

    wins = motion.windows()

    # create a single huge motion mask covers whole view
    win = wins[0]
    win['name'] = 'ynm-motion-0'
    win['enable'] = 1
    win['polygon'] = [0, 0, 9999, 0, 9999, 9999, 0, 9999]
    win['objsize'] = 1
    win['sensitivity'] = 100

    v = configer.get('videoin')
    cur_mode = v.videoin.c[0].mode
    angles = [0]
    if int(cam.capability.videoin.c[0]['mode%d' % cur_mode].rotation) == 1:
        angles = [0, 90, 270]

    motion.enable()

    for angle in angles:
        configer.set('videoin_c0_rotate=%d' % angle)
        time.sleep(5)

        # rotate will clear motion window setting. so we need to configure it
        # every time after rotation
        motion.windows(wins)
        time.sleep(2)

        streaming.connect()

        found_motion_triggered_frame = False
        frames_to_wait = 600
        for i in range(0, frames_to_wait):
            frame = streaming.get_one_frame(video_filter)
            print frame
            motionframe = frame.motion
            if motionframe.triggered():
                found_motion_triggered_frame = True
                break

        streaming.disconnect()
        assert found_motion_triggered_frame, "No motion triggered for %d frames"\
            % frames_to_wait


def helper_motion_clear_all(configer, cam, motion):
    nmotion = cam.capability.nmotion
    clear = {'enable': '0', 'name': '', 'objsize': 15, 'sensitivity': 85,
             'polygon': [0, 0, 0, 0, 0, 0, 0, 0]}
    wins = []

    for i in range(0, nmotion):
        wins.append(clear)

    motion.windows(wins)
