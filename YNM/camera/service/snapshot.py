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
