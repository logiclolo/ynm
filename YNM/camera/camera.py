# -*- coding: utf-8 -*-

import requests
import sys
import YNM.camera.service.config as config
import StringIO
from datetime import datetime, timedelta, tzinfo

"""Camera is an abstraction of a IP camera.

Instantiate this object with following parameters:
    url: IP camera URL
    user: Username of the IP camera
    passwd: Password of the IP camera
    http_port: Specify camera http port. Default set to 80
    httl_alt_port: Specify camera alternative port. Default set to 8080

After this object has been instatiated, ```probe()``` will be invoked to
determine camera further parameters.  You can also call ```probe()``` later one
to get these information again

"""


class CST(tzinfo):
    def utcoffset(self, dt):
        return timedelta(hours=8)

    def tzname(self, dt):
        return "GMT+8"


class NoDeviceWithMACError(Exception):
    pass


def cgi_get_one(ip, auth, param):
    import requests
    value = ''
    url = 'http://' + ip + '/cgi-bin/viewer/getparam.cgi?' + param
    r = requests.get(url, auth=auth)
    if r.status_code == 200:
        name, value = r.content.split('=')

    return value


def mac_to_ip(mac):
    from YNM.camera.discovery import DRM
    d = DRM()
    d.refresh()
    iplist = d.search(mac)
    if iplist:
        # only return 1st item from searched result
        return iplist[0]['ip']
    else:
        raise NoDeviceWithMACError("MAC %s" % mac)


class Camera:
    def __init__(self, settings, http_port=80, http_alt_port=8080):
        self.url = ''
        if 'ip' in settings and 'mac' in settings:
            from textwrap import wrap
            mac = cgi_get_one(settings['ip'], (settings['user'], settings['passwd']), 'system_info_serialnumber').rstrip().strip("'")
            mac = ':'.join(wrap(mac, 2))
            if mac != settings['mac']:
                self.url = mac_to_ip(mac)
            else:
                self.url = settings['ip']

        elif 'mac' in settings:
            self.url = mac_to_ip(settings['mac'])

        else:
            self.url = settings['ip']

        self.username = settings['user']
        self.password = settings['passwd']
        self.http_port = http_port
        self.http_alt_port = http_alt_port

        self.probe()

    """ Get some information from the camera """
    def probe(self):
        c = config.Configer(self)
#         sys.stderr.write("connecting %s ..." % self.url)
        try:
            content = c.get("capability&system&network")
        except Exception as e:
            raise Exception(e)
#             sys.stderr.write(" failed! %s\n" % e)
#         else:
#             sys.stderr.write(" connected!\n")

        self.capability = content.capability
        capability = self.capability
        self.supported_codecs = capability.videoin.codec
        self.num_of_streams = capability.nmediastream
        self.audio_supported = True if capability.naudioin > 0 else False

        self.system = content.system
        system = self.system
        self.model = system.info.modelname
        self.modelext = system.info.extendedmodelname
        self.macaddress = system.info.serialnumber
        self.fwversion = system.info.firmwareversion

        self.network = content.network

    def upgrade(self, url):
        upgrade_url = "http://" + self.url + "/cgi-bin/admin/upgrade.cgi"
        firmware_url = url
        r = requests.get(firmware_url)
        if r.status_code != 200:
            return None

        firmware = StringIO.StringIO(r.content)
        r = requests.post(upgrade_url, files={'file': firmware})

        return r

    def get_time(self, configer):
        try:
           c = configer.get("system_date&system_time")
        except Exception as e:
            raise Exception(e)

        timestr = c.system.date + 'T' + c.system.time
        time = datetime.strptime(timestr, '%Y/%m/%dT%H:%M:%S')

        # FIXME : assume tz of camera is GMT+8
        return time.replace(tzinfo=CST())
