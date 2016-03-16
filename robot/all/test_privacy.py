# -*- coding: utf-8 -*-

from fixture import *
from YNM.utility.vvcv.vvcv import cv_detect_windows, pil_to_opencv
import time
import math


def test_privacy_create_rectangle(snapshot, configer, cam, pmask, no_timestamp,
                                  request, brightness100_contrast50):

    # Test to create privacy masks. This test case will generate 5 masks, 4 for
    # corners, 1 for single center dart shape mask
    # 目前準確度仍不夠高，需要一點時間調整參數。如果發現失敗有可能是 YNM
    # 本身的問題

    def fin():
        helper_privacy_clear_all(configer, cam, pmask)
    request.addfinalizer(fin)

    helper_privacy_clear_all(configer, cam, pmask)
    wins = helper_generate_pmask_windows()
    helper_privacy_rectangle_with_wins_rotate(snapshot, configer, cam, pmask,
                                              wins)


def helper_generate_pmask_windows():
    base_width = 320
    base_height = 240
    step_width = base_width / 8
    step_height = base_height / 8
    padding = 8

    # draw 4 rectangle at the corner of the pmask window
    origins = [
        {
            'x': padding,
            'y': padding
        },
        {
            'x': base_width - step_width - padding,
            'y': padding
        },
        {
            'x': padding,
            'y': base_height - step_height - padding
        },
        {
            'x': base_width - step_width - padding,
            'y': base_height - step_height - padding
        }
    ]
    wins = []
    for idx, origin in enumerate(origins):
        win = {'enable': 1,
               'name': 'ynm-rect-%d' % idx,
               'polygon': [
                   origin['x'], origin['y'],
                   origin['x'] + step_width, origin['y'],
                   origin['x'] + step_width, origin['y'] + step_height,
                   origin['x'], origin['y'] + step_height
               ]}
        wins.append(win)

    # draw a dart shape image at the center of the pmask window, 320x240 based
    wins.append(
        {'enable': '1',
         'name': 'ynm-star-0',
         'polygon': [160, 90, 190, 150, 160, 120, 130, 150]})

    return wins


def helper_privacy_rectangle_with_wins_rotate(snapshot, configer, cam, pmask,
                                              wins):

    def distance(p1, p2, orientation):
        if orientation == 90 or orientation == 270:
            return math.sqrt((p1[0] - p2[1]) ** 2 + (p1[1] - p2[0]) ** 2)
        else:
            return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)

    original_points = []
    for win in wins:
        if win['polygon'] != "":
            x1, y1, x2, y2, x3, y3, x4, y4 = win['polygon']
            original_points.append((x1, y1))
            original_points.append((x2, y2))
            original_points.append((x3, y3))
            original_points.append((x4, y4))

    if cam.capability.videoin.c[0].rotation == 1:
        orientations = [0, 90, 270]
    else:
        orientations = [0]

    for orientation in orientations:
        configer.set('videoin_c0_rotate=%d' % orientation)
        time.sleep(4)

        img1, img2 = helper_privacy_create(snapshot, wins, pmask)
        img2 = pil_to_opencv(img2)
        img1 = pil_to_opencv(img1)
        nwins, detected_points = cv_detect_windows([img1, img2])

        found_points = []
        for opoint in original_points:
            for dpoint in detected_points:
                if distance(opoint, dpoint, orientation) <= 7:
                    found_points.append(opoint)

        filtered_points = [elem for elem in original_points if elem not in
                           found_points]
        assert not filtered_points, "%d privacy mask expected" % len(wins)

    configer.set('videoin_c0_rotate=0')

# Helper Section #


def helper_privacy_create(snapshot, wins, pmask):
    param = {'resolution': '320x240', 'quality': 5}

    pmask.windows(wins)

    pmask.disable()
    time.sleep(1)

    status, pmask_disabled_image = snapshot.take(param)
    assert status, "Take snapshot failed"

    pmask.enable()
    time.sleep(3)

    status, pmask_enabled_image = snapshot.take(param)
    assert status, "Take snapshot failed"

    pmask.disable()

    return pmask_enabled_image, pmask_disabled_image


def helper_privacy_clear_all(configer, cam, pmask):
    nmask = cam.capability.videoin.c[0].nprivacymask
    clear = {'enable': '0', 'name': '', 'polygon': [0, 0, 0, 0, 0, 0, 0, 0]}
    wins = []

    for i in range(0, nmask):
        wins.append(clear)

    pmask.windows(wins)
