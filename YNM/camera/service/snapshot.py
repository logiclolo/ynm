# -*- coding: utf-8 -*-

import requests
import abc
import scipy
import numpy
from PIL import Image, ImageOps
from StringIO import StringIO
from YNM.utility.video_quality.ssim import ssim_exact


class ISnapshot:
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def take(self, option):
        raise NotImplemented()


class Snapshot(ISnapshot):
    def __init__(self, cam, cgi='/cgi-bin/viewer/video.jpg'):
        self._camera = cam
        self._cgi = cgi

    def take(self, param={}):
        cam = self._camera
        url = 'http://' + self._camera.url + self._cgi
        if bool(param) is False:
            r = requests.get(url, auth=(cam.username, cam.password))
        else:
            r = requests.post(url, auth=(cam.username, cam.password), data=param)

        if r.status_code != 200:
            return (False, None)

        i = Image.open(StringIO(r.content))
        return (True, i)

ISnapshot.register(Snapshot)


def difference_by_ssim(before, after):

    before_io = StringIO()
    before = ImageOps.flip(before)
    before.save(before_io, format='jpeg')
    before_ref = scipy.misc.imread(before_io, flatten=True).astype(numpy.float32)

    after_io = StringIO()
    after.save(after_io, format='jpeg')
    after_ref = scipy.misc.imread(after_io, flatten=True).astype(numpy.float32)

    return ssim_exact(before_ref / 255, after_ref / 255)


import YNM.cv2 as cv2
import pytesseract


def text_on_video(snapshot_image):
    def pil_to_opencv(pil):
        # copy from
        # http://stackoverflow.com/questions/14134892/convert-image-from-pil-to-opencv-format
        opencv = numpy.array(pil)
        opencv = opencv[:, :, ::-1].copy()
        return opencv

    def opencv_to_pil(opencv):
        # copy from
        # http://stackoverflow.com/questions/13576161/convert-opencv-image-into-pil-image-in-python-for-use-with-zbar-library
        pil = Image.fromarray(opencv)
        return pil

    s = snapshot_image
    s = s.crop((0, 0, 640, 40))
    s = pil_to_opencv(s)

    s = cv2.cvtColor(s, cv2.COLOR_BGR2GRAY)

    _, s_bin = cv2.threshold(s, 210, 255, cv2.THRESH_BINARY_INV)
    kernel = numpy.ones((2, 2), numpy.uint8)
    s_bin = cv2.morphologyEx(s_bin, cv2.MORPH_OPEN, kernel)
    i_bin = opencv_to_pil(s_bin)
    text = pytesseract.image_to_string(i_bin)
    return text
