# -*- coding: utf-8 -*-

import re
import StringIO
import scipy
import numpy
from PIL import ImageOps
from time import sleep

import YNM.utility.video_quality.ssim as ssim
from YNM.camera.service.ptz import ElectronicPTZ
from YNM.utility.vvcv.vvcv import text_from_image
from fixture import *


def test_snapshot_custom_resolution(snapshot, configer, cam):

    # Test if snapshot could be taken by giving custom resolutions instead of
    # using streaming resolution

    # change orientation to 0
    configer.set('videoin_c0_rotate=0')
    sleep(3)

    caps = cam.capability
    resolutions = caps.videoin.c[0].resolution
    for resolution in resolutions:
        param = {'resolution': resolution}
        res, i = snapshot.take(param)
        assert res is True, "Taking custom snapshot with (%s) failed" % \
            resolution
        w, h = resolution.split('x')
        assert int(w) == i.size[0], "Width should be %s" % w
        assert int(h) == i.size[1], "Height should be %s" % h


def test_snapshot_ok(snapshot):

    # Test if snapshot is ok

    for i in range(0, 5):
        res, r = snapshot.take()
        assert res is True, "Taking snapshot failed"


def test_snapshot_rotate_with_resolution_check(cam, snapshot, configer):

    # Test if snapshot also rotates with camera.  Note that some of camera which
    # doesn't support snapshot rotation will fail on this case

    if cam.capability.videoin.c[0].rotation == 0:
        # this camera doesn't support rotation
        pytest.skip("this camera doesn't support rotation, skip this test")

    rotations = [0, 90, 180, 270]
    for rotation in rotations:
        resolution = '640x480'
        configer.set('videoin_c0_rotate=%d' % rotation)
        param = {'resolution': resolution}
        sleep(3)

        res, i = snapshot.take(param)
        assert res is True, "Take snapshot with (%s) failed" % (param)
        w, h = resolution.split('x')
        if rotation == 0 or rotation == 180:
            assert int(w) == i.size[0], "Width should be %s" % w
            assert int(h) == i.size[1], "Height should be %s" % h
        elif rotation == 90 or rotation == 270:
            assert int(w) == i.size[1], "Width should be %s (after rotate)" % w
            assert int(h) == i.size[0], "Height should be %s (after rotate)" % h


def test_snapshot_rotate_with_ssim_check(cam, configer, snapshot):

    # Test camera actually rotates image after rotation is enabled Check if
    # image is rotated correctly by comparing SSIM.  See
    # https://www.wikiwand.com/en/Structural_similarity

    if cam.capability.videoin.c[0].rotation == 0:
        # this camera doesn't support rotation
        pytest.skip("this camera doesn't support rotation, skip this test")

    configer.set('videoin_c0_imprinttimestamp=0')

    configer.set('videoin_c0_rotate=0&videoin_c0_mirror=0&videoin_c0_flip=0')
    sleep(2)
    option = {'resolution': '640x640'}

    # take a snapshot
    status, image = snapshot.take(option)
    assert status, "Snapshot failed with resolution %s" % (option['resolution'])

    # use 270 since PIL rotate in counter-clockwise while camera rotate in
    # clockwise
    image_90 = image
    image_90_io = StringIO.StringIO()
    image_90 = image.rotate(270)
    image_90.save(image_90_io, format='jpeg')
    image_90_ref = scipy.misc.imread(image_90_io, flatten=True).astype(numpy.float32)

    # rotate
    configer.set('videoin_c0_rotate=90&videoin_c0_mirror=0&videoin_c0_flip=0')
    sleep(2)

    # take another snapshot
    status, image = snapshot.take(option)
    assert status, "Snapshot failed with resolution %s" % (option['resolution'])

    image_90_cam = image
    image_90_cam_io = StringIO.StringIO()
    image_90_cam.save(image_90_cam_io, format='jpeg')
    image_90_cam_ref = scipy.misc.imread(image_90_cam_io, flatten=True).astype(numpy.float32)

    ssim_exact = ssim.ssim_exact(image_90_ref / 255, image_90_cam_ref / 255)
    print 'ssim (exact): %f' % ssim_exact

    lower_bound = 0.700
    if ssim_exact <= lower_bound:
        image_90.save('image-90.jpg')
        image_90_cam.save('image-90-cam.jpg')

    assert ssim_exact > lower_bound, "SSIM too low. Image may not been rotated. \
        Exp %f, Act %f" % (lower_bound, ssim_exact)


def test_snapshot_mirror_with_ssim_check(cam, configer, snapshot):

    # Test camera actually mirror image after mirror is enabled Check if image
    # is set to mirror correctly by comparing SSIM.

    configer.set('videoin_c0_imprinttimestamp=0')
    configer.set('videoin_c0_rotate=0&videoin_c0_mirror=0&videoin_c0_flip=0')
    sleep(2)

    option = {'resolution': '640x480'}

    # take a snapshot
    status, image = snapshot.take(option)
    assert status, "Snapshot failed with resolution %s" % (option['resolution'])

    # mirror image
    image_mirror = image
    image_mirror_io = StringIO.StringIO()
    image_mirror = ImageOps.mirror(image_mirror)
    image_mirror.save(image_mirror_io, format='jpeg')
    image_mirror_ref = scipy.misc.imread(image_mirror_io, flatten=True).astype(numpy.float32)

    # mirror
    configer.set('videoin_c0_rotate=0&videoin_c0_mirror=1&videoin_c0_flip=0')
    sleep(2)

    # take another snapshot
    status, image = snapshot.take(option)
    assert status, "Snapshot failed with resolution %s" % (option['resolution'])

    image_mirror_cam = image
    image_mirror_cam_io = StringIO.StringIO()
    image_mirror_cam.save(image_mirror_cam_io, format='jpeg')
    image_mirror_cam_ref = scipy.misc.imread(image_mirror_cam_io, flatten=True).astype(numpy.float32)

    ssim_exact = ssim.ssim_exact(image_mirror_ref / 255, image_mirror_cam_ref / 255)
    print 'ssim (exact): %f' % ssim_exact

    lower_bound = 0.700
    if ssim_exact <= lower_bound:
        image_mirror.save('image-mirror.jpg')
        image_mirror_cam.save('image-mirror-cam.jpg')

    assert ssim_exact > lower_bound, "SSIM too low. Image may not been mirrored. \
        Exp %f, Act %f" % (lower_bound, ssim_exact)


def test_snapshot_flip_with_ssim_check(cam, configer, snapshot):

    # Test camera actually flip image after flip is enabled Check if image is
    # set to flip correctly by comparing SSIM.

    configer.set('video_c0_imprinttimestamp=0')
    configer.set('video_c0_rotate=0&videoin_c0_mirror=0&videoin_c0_flip=0')
    sleep(2)

    option = {'resolution': '640x480'}

    # take a snapshot
    status, image = snapshot.take(option)
    assert status, "Snapshot failed with resolution %s" % (option['resolution'])

    # flip image
    image_flip = image
    image_flip_io = StringIO.StringIO()
    image_flip = ImageOps.flip(image_flip)
    image_flip.save(image_flip_io, format='jpeg')
    image_flip_ref = scipy.misc.imread(image_flip_io, flatten=True).astype(numpy.float32)

    # rotate
    configer.set('videoin_c0_rotate=0&videoin_c0_mirror=0&videoin_c0_flip=1')
    sleep(2)

    # take another snapshot
    status, image = snapshot.take(option)
    assert status, "Snapshot failed with resolution %s" % (option['resolution'])

    image_flip_cam = image
    image_flip_cam_io = StringIO.StringIO()
    image_flip_cam.save(image_flip_cam_io, format='jpeg')
    image_flip_cam_ref = scipy.misc.imread(image_flip_cam_io, flatten=True).astype(numpy.float32)

    ssim_exact = ssim.ssim_exact(image_flip_ref / 255, image_flip_cam_ref / 255)
    print 'ssim (exact): %f' % ssim_exact

    lower_bound = 0.700
    if ssim_exact <= lower_bound:
        image_flip.save('image-flip.jpg')
        image_flip_cam.save('image-flip-cam.jpg')

    assert ssim_exact > lower_bound, "SSIM too low. Image may not been flipped.\
        Exp %f, Act %f" % (lower_bound, ssim_exact)


def test_snapshot_eptz_affect_snapshot(cam, configer, snapshot):

    # Test if snapshot follows live stream eptz setting.  For example, if live
    # stream zooms in to 2.0x, the snapshot should also captures to 2.0x when
    # parameter 'streamid' provided.

    eptzable = True if cam.capability.eptz > 0 else False
    pytest.mark.skipif(eptzable is False, reason="This device doesn't support eptz")

    # create eptz handle
    eptz = ElectronicPTZ(cam, channel=0, stream=0)

    param = 'streamid=0'
    status, image_zoom_0 = snapshot.take(param)
    assert status is True, "Snapshot take failed"

    eptz.zoom('in')
    eptz.zoom('in')
    eptz.zoom('in')
    sleep(3)

    status, image_zoom_1 = snapshot.take(param)
    assert status is True, "Snapshot take failed"

    eptz.zoom('home')

    image_zoom_0_io = StringIO.StringIO()
    image_zoom_1_io = StringIO.StringIO()
    image_zoom_0.save(image_zoom_0_io, format='jpeg')
    image_zoom_1.save(image_zoom_1_io, format='jpeg')
    image_zoom_0_ref = scipy.misc.imread(image_zoom_0_io, flatten=True).astype(numpy.float32)
    image_zoom_1_ref = scipy.misc.imread(image_zoom_1_io, flatten=True).astype(numpy.float32)

    ssim_exact = ssim.ssim_exact(image_zoom_0_ref / 255, image_zoom_1_ref / 255)
    upper_bound = 0.950

    assert ssim_exact < upper_bound, \
        "SSIM too high, Image may not been zoomed. Exp %f, Act %f" % \
        (upper_bound, ssim_exact)


def test_snapshot_ocr(cam, configer, snapshot, request,
                      brightness100_contrast50):

    # Test if camera could show text on video at snapshot correctly
    #   a) original
    #   b) rotate 90, 270
    #   c) each stream

    # 這個 test case 有可能產生 Fail.  參數可能仍還需要調整
    # Technical detail: This test case uses tesseract OCR to recognize text on
    # video content.  tesseract recognizes text in unicode. But unicode stores
    # variations, especailly symbols.  Try only to use a-z0-9 in video title to
    # prevent error

    video_title = 'ynmtest'
    configer.set('videoin_c0_imprinttimestamp=1&videoin_c0_text=%s' %
                 video_title)
    sleep(0.3)

    # Test if text on video is working by enable/disable imprint text
    def fin():
        configer.set('videoin_c0_imprinttimestamp=0&videoin_c0_text=')
    request.addfinalizer(fin)

    rotations = [0]
    c = configer.get('videoin_c0_mode')
    current_mode = c.videoin.c[0].mode
    support_rotations = cam.capability.videoin.c[0]['mode%d' %
                                                    current_mode].rotation
    if support_rotations:
        rotations = [0, 90, 180, 270]

    nmediastream = cam.capability.nmediastream

    for rotate in rotations:
        configer.set('videoin_c0_rotate=%d' % rotate)
        sleep(2)
        for idx in range(0, nmediastream):

            param = {'resolution': '1024x768', 'quality': '5', 'streamid': idx}
            _, i = snapshot.take(param)
#             i.save('before-crop.jpg')

            text = text_from_image(i.crop((0, 0, 640, 80)))

            pattern = "%s[ ]*\d\d\d\d.\d\d.\d\d[ ]*\d\d.\d\d.\d\d" % video_title
            match = re.search(pattern, text)
            print 'text is "%s" ' % text

            assert match, "Expect something apperas in streaming when text on video is enabled"


def test_snapshot_ocr_disabled(cam, configer, snapshot, request,
                               brightness100_contrast50):

    # Test disable text on video to see if it DOES disappear

    configer.set('videoin_c0_imprinttimestamp=0&videoin_c0_text=')
    sleep(2)

    param = {'resolution': '1024x768', 'quality': '5', 'streamid': '0'}
    _, image = snapshot.take(param)
    text = text_from_image(image.crop((0, 0, 640, 80)))

    assert text == "", "Text on video should NOT appear"
