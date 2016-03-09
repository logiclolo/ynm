# -*- coding: utf-8 -*-

import abc
import requests
from time import sleep
from YNM.camera.camera import Camera
from YNM.camera.service.config import Configer
from textwrap import wrap


class IW2MissingError(Exception):
    pass

class IDiscovery (object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def refresh(self):
        raise NotImplemented()

    @abc.abstractmethod
    def search(self, criteria):
        raise NotImplemented()


class DRM (IDiscovery):
    def __init__(self):
        self._iw2_template = "/usr/local/bin/iw2_air -f %s"
        self.cameras = []

    def refresh(self):
        self.cameras = []
        from subprocess import call, STDOUT
        import os
        from tempfile import mkstemp
        handle, name = mkstemp()

        fnull = open(os.devnull, 'w')
        iw2_return = call(self._iw2_template % name, shell=True, stdout=fnull, stderr=STDOUT)
        if iw2_return != 0:
            raise Exception("command %s failed" % self._iw2_template % name)

        result = open(name, 'r').read()
        cameras = result.split('\n')

        for cam_raw in cameras:
            cam = cam_raw.split(',')
            # argh, I hate to do this, but how can I do? the output format is
            # written like this... 13 is the field number of outptu from iw2_air
            if len(cam) < 13:
                continue

            camdict = {'fwver': cam[0], 'mac': cam[3], 'ip': cam[6], 'model': cam[9], 'locked': cam[12]}
            self.cameras.append(camdict)

        os.remove(name)

    def search(self, criteria):
        matched_cams = []
        for cam in self.cameras:
            for value in cam.values():
                if criteria in value:
                    matched_cams.append(cam)

        return matched_cams


IDiscovery.register(DRM)


def http_ping(ip, httpauth=None):
    url = 'http://' + ip + '/cgi-bin/sysinfo.cgi'
    try:
        r = requests.get(url, auth=httpauth, timeout=3)
        if r.status_code == 200:
            return True
    except:
        # if we encounter any error then return false
        return False


def wait_to_http_rechable(ip, httpauth=None):
    for i in range(0, 30):
        if http_ping(ip, httpauth) is True:
            return True

        sleep(5)

    return False


def wait_to_http_unrechable(ip, httpauth=None):
    for i in range(0, 30):
        if http_ping(ip, httpauth) is False:
            return True

        sleep(5)

    return False


def wait_camera_appear(ip, httpauth=None, mac=None):
    if wait_to_http_rechable(ip, httpauth):
        # camera comes back again
        camera_config = {'ip': ip, 'user': 'root', 'passwd': ''}
        cam = Camera(camera_config)
        configer = Configer(cam)
        c = configer.get('system')
        if ':'.join(wrap(c.system.info.serialnumber, 2)) == mac:
            return (True, ip)

    d = DRM()
    d.refresh()
    matched = d.search(mac)
    if not matched:
        return (False, '0.0.0.0')
    elif len(matched) > 1:
        return (False, '0.0.0.0')

    return (True, matched[0]['ip'])
