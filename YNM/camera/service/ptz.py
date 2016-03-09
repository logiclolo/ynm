# -*- coding: utf-8 -*-

import threading
import abc
import weakref
import httplib2
from time import sleep
import requests
from decimal import Decimal, getcontext

from YNM.camera.service.config import Configer, EFormat
from YNM.camera.parser import parse_vivotek_response
from YNM.utility.utility import merge_dict


class CameraCommandError(Exception):
    pass


class PTZObject(object):
    def __init__(self):
        self.mechanism = 'mechanical'
        self.category = 'standardptz'


def PanTiltJoystickable(ptzf):
    return True if issubclass(type(ptzf), IPanTiltJoystick) else False


def ZoomJoystickable(ptzf):
    return True if issubclass(type(ptzf), IZoomJoystick) else False


def PanTiltable(ptzf):
    return True if issubclass(type(ptzf), IPanTilt) else False


def AbsPanTiltable(ptzf):
    return True if issubclass(type(ptzf), IPanTiltAbs) else False


def Zoomable(ptzf):
    return True if issubclass(type(ptzf), IZoom) else False


def AbsZoomable(ptzf):
    return True if issubclass(type(ptzf), IZoomAbs) else False


def Focusable(ptzf):
    return True if issubclass(type(ptzf), IFocus) else False


def AbsFocusable(ptzf):
    return True if issubclass(type(ptzf), IFocusAbs) else False


def Patrolable(ptzf):
    return True if issubclass(type(ptzf), IPatrol) else False


def Presetable(ptzf):
    return True if issubclass(type(ptzf), IPreset) else False


class Angle(object):

    def __init__(self, angle):
        self._angle = float(angle)

    @property
    def angle(self):
        return self._angle

    def __eq__(self, other):
        if isinstance(other, Angle):
            getcontext().prec = 3
            a = Decimal(self._angle)
            o = Decimal(other.angle)
            tolerance = Decimal(0.1)
            difference = a - o if a > o else o - a
            if tolerance >= difference:
                return True
            return False
        raise NotImplemented()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __int__(self):
        return int(self._angle)

    def __str__(self):
        return str(self._angle)


class IPreset(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def recall_preset(self, name):
        raise NotImplemented()

    @abc.abstractmethod
    def get_presets(self):
        raise NotImplemented()

    @abc.abstractmethod
    def add_preset(self, name):
        raise NotImplemented()

    @abc.abstractmethod
    def del_preset(self, name):
        raise NotImplemented()


class IPatrol(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def patrol(self, name=None):
        raise NotImplemented()

    @abc.abstractmethod
    def add_patrol(self, name):
        raise NotImplemented()

    @abc.abstractmethod
    def del_patrol(self, name):
        raise NotImplemented()


class IFocus(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def focus(self, action):
        raise NotImplemented()

    @abc.abstractmethod
    def get_focus_limits(self):
        raise NotImplemented()

    @abc.abstractmethod
    def get_focus_position(self, cache=True):
        raise NotImplemented()


class IFocusAbs(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def _focus_absolute(self, action):
        raise NotImplemented()


class IZoom(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def zoom(self, action):
        raise NotImplemented()

    @abc.abstractmethod
    def get_zoom_limits(self):
        raise NotImplemented()

    @abc.abstractmethod
    def get_zoom_position(self, cache=True):
        raise NotImplemented()


class IZoomAbs(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def _zoom_absolute(self, action):
        raise NotImplemented()


class IPanTilt(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def pantilt(self, action):
        raise NotImplemented()

    @abc.abstractmethod
    def get_pantilt_limits(self):
        raise NotImplemented()

    @abc.abstractmethod
    def get_pantilt_position(self, cache=True):
        raise NotImplemented()


class IPanTiltAbs(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def _pantilt_absolute(self, action):
        raise NotImplemented()

    @abc.abstractmethod
    def get_pantilt_angle(self, cache=True):
        raise NotImplemented()


class IPanTiltJoystick(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def _pantilt_joystick(self, action):
        raise NotImplemented()


class IZoomJoystick(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def _zoom_joystick(self, action):
        raise NotImplemented()


# implementations


class RS485(PTZObject):
    def __init__(self, cam):
        pass

# IFocus.register(RS485)
# IZoom.register(RS485)
# IPanTilt.register(RS485)
# IPreset.register(RS485)


class SDPTZ(PTZObject, IPanTilt, IPanTiltAbs, IZoom, IZoomAbs, IFocus,
            IPreset, IPanTiltJoystick, IZoomJoystick, IPatrol):
    def __init__(self, cam):
        self._camera = cam
        self._cgi = "/cgi-bin/camctrl/camctrl.cgi"
        self.cgi = 'http://' + self._camera.url + self._cgi
        self._presetcgi = "/cgi-bin/camctrl/preset.cgi"
        self.presetcgi = 'http://' + self._camera.url + self._presetcgi
        self._patrolcgi = "/cgi-bin/camctrl/patrol.cgi"
        self.patrolcgi = 'http://' + self._camera.url + self._patrolcgi
        h = httplib2.Http()
        h.add_credentials(self._camera.username, self._camera.password)
        self._auth = (self._camera.username, self._camera.password)
        self._zoom = 0
        self._panangle = Angle(0)
        self._tiltangle = Angle(0)
        self._pan = 0
        self._tilt = 0
        self._focus = 0
        self._aux_param = {'setptmode': 'block'}

        self._maxpanangle = 0
        self._maxtiltangle = 0
        self._maxpan = 0
        self._maxtilt = 0
        self._maxzoom = 0
        self._maxfocus = 0

        self._zoom = 0
        self._focus = 0
        self._panangle = 0
        self._tiltangle = 0
        self._pan = 0
        self._tilt = 0

        self._getlimits_all()
        self._getstatus_all()

        # following technique is referenced from stackoverflow artcile:
        # http://bit.ly/1offr7N

        self._main_thread = threading.current_thread()
        self._location = threading.Thread(target=SDPTZ._location_updater,
                                          args=(weakref.proxy(self), ))
        self._initialized = threading.Event()
        self._location.start()
        while not self._initialized.is_set():
            pass

    def _location_updater(self):
        self._initialized.set()

        try:
            # update position every 300ms
            while True:
                if not self._main_thread.is_alive():
                    break

                self.get_pantilt_position(cache=False)
                self.get_zoom_position(cache=False)
                self.get_focus_position(cache=False)
                sleep(0.5)

        except ReferenceError:
            pass

    def __del__(self):
        self._location.join()

    def _getstatus_all(self):
        command = {
            'getpanangle': '0',
            'gettiltangle': '0',
            'getpan': '0',
            'gettilt': '0',
            'getzoom': '0',
            'getfocus': '0'
        }
        r = requests.get(self.cgi, auth=self._auth, params=command)
        param = parse_vivotek_response(r.content)
        self._zoom = float(param['zoom'])
        self._focus = float(param['focus'])
        self._panangle = Angle(float(param['panangle']))
        self._tiltangle = Angle(float(param['tiltangle']))
        self._pan = int(param['pan'])
        self._tilt = int(param['tilt'])

    def _getlimits_all(self):
        getlimits = {
            'getmaxpanangle': '0',
            'getmaxtiltangle': '0',
            'getmaxpan': '0',
            'getmaxtilt': '0',
            'getmaxzoom': '0',
            'getmaxfocus': '0'
        }
        r = requests.get(self.cgi, auth=self._auth, params=getlimits)
        param = parse_vivotek_response(r.content)
        self._maxpanangle = Angle(float(param['maxpanangle']))
        self._maxtiltangle = Angle(float(param['maxtiltangle']))
        self._maxpan = int(param['maxpan'])
        self._maxtilt = int(param['maxtilt'])
        self._maxzoom = float(param['maxzoom'])
        self._maxfocus = float(param['maxfocus'])

    # IPanTilt method
    def pantilt(self, action):

        def command_factory(action):
            pt_command = {
                'relative': self._pantilt_relative,
                'absolute': self._pantilt_absolute,
                'joystick': self._pantilt_joystick
            }
            if any(x in action for x in
                   ['left', 'right', 'up', 'down', 'home']):
                return pt_command['relative']
            elif any(x in action for x in
                     ['l-joy', 'r-joy', 'u-joy', 'd-joy', 'stop']):
                return pt_command['joystick']
            else:
                return pt_command['absolute']

        command = command_factory(action)
        command(action)

        return self.get_pantilt_position()

    def _pantilt_relative(self, action):
        moves = {
            'left': {'move': 'left'},
            'right': {'move': 'right'},
            'up': {'move': 'up'},
            'down': {'move': 'down'},
            'home': {'move': 'home'}
        }
        command = merge_dict(moves[action], self._aux_param)
        requests.get(self.cgi, params=command, auth=self._auth)
        sleep(0.5)
        self._getstatus_all()

    def _pantilt_absolute(self, action):
        command = {}
        if 'setpanangle' in action:
            command = merge_dict(command, {'setpanangle': action['setpanangle']})
        if 'settiltangle' in action:
            command = merge_dict(command, {'settiltangle': action['settiltangle']})
        if 'setpan' in action:
            command = merge_dict(command, {'setpan': action['setpan']})
        if 'settilt' in action:
            command = merge_dict(command, {'settilt': action['settilt']})

        if not command:
            raise Exception("Invalid pantilt command %s" % action)

        r = requests.get(self.cgi, params=command, auth=self._auth)
        if r.status_code != 200:
            raise CameraCommandError()
        self._getstatus_all()

    def get_pantilt_position(self, cache=True):
        if cache is False:
            self._getstatus_all()
#         return (self._maxpan - self._pan, self._maxtilt - self._tilt)
        return (self._maxpan - self._pan, self._tilt)

    def get_pantilt_angle(self, cache=True):
        if cache is False:
            self._getstatus_all()
        return (self._panangle, self._tiltangle)

    def get_pantilt_limits(self):
        return (self._maxpan, self._maxtilt)

    # IZoom methods
    def zoom(self, action):

        def command_factory(action):
            zoom_command = {
                'relative': self._zoom_relative,
                'absolute': self._zoom_absolute,
                'joystick': self._zoom_joystick
            }
            print 'action %s' % action
            if any(x in action for x in ['in-joy', 'out-joy', 'stop']):
                return zoom_command['joystick']
            elif any(x in action for x in ['in', 'out']):
                return zoom_command['relative']
            else:
                return zoom_command['absolute']

        command = command_factory(action)
        command(action)

        return self.get_zoom_position()

    def get_zoom_limits(self):
        return self._maxzoom

    def get_zoom_position(self, cache=True):
        if cache is False:
            self._getstatus_all()
        return self._zoom

    def _zoom_relative(self, action):
        moves = {'in': {'zoom': 'tele'}, 'out': {'zoom': 'wide'}}
        command = merge_dict(moves[action], self._aux_param)
        requests.get(self.cgi, params=command, auth=self._auth)
        sleep(0.5)
        self._getstatus_all()

    # IZoomAbs
    def _zoom_absolute(self, action):
        if 'setzoom' not in action:
            return

        r = requests.get(self.cgi, params=action, auth=self._auth)
        if r.status_code != 200:
            raise CameraCommandError()

    # IFocus methods
    def focus(self, action):

        def type_of_action(action):
            if any(x in action for x in ['near', 'far', 'auto']):
                return 'relative'
            else:
                return 'absolute'

        focus_command = {
            'relative': self._focus_relative,
            'absolute': self._focus_absolute
        }
        focus_command[type_of_action(action)](action)

        return self.get_focus_position()

    def get_focus_limits(self):
        return self._maxfocus

    def get_focus_position(self, cache=True):
        if cache is False:
            self._getstatus_all()
        return self._focus

    def _focus_relative(self, action):
        moves = {
            'near': {'focus': 'near'},
            'far': {'focus': 'far'},
            'auto': {'focus': 'auto'}
        }
        command = merge_dict(moves[action], self._aux_param)
        requests.get(self.cgi, params=command, auth=self._auth)

        self._getstatus_all()

    # IFocusAbs
    def _focus_absolute(self, action):
        command = {}
        if 'setfocus' in action:
            command['setfocus'] = action['setfocus']
            r = requests.get(self.cgi, params=command, auth=self._auth)
            if r.status_code != 200:
                raise CameraCommandError()

    # IPreset
    def recall_preset(self, name):
        url = 'http://' + self._camera.url + self._presetcgi
        command = {'recall': name}
        r = requests.get(url, params=command, auth=self._auth)
        if r.status_code != 200:
            raise CameraCommandError()

    def get_presets(self, name):
        cam = self._camera
        configer = Configer(cam)
        c = configer.get('camctrl')
        camctrl = c.camctrl
        return camctrl.c[0].preset

    def add_preset(self, name):
        command = {'addpos': name}
        r = requests.get(self.patrolcgi, params=command, auth=self._auth)
        if r.status_code != 200:
            raise CameraCommandError()

    def del_preset(self, name):
        command = {'delpos': name}
        r = requests.get(self.patrolcgi, params=command, auth=self._auth)
        if r.status_code != 200:
            raise CameraCommandError()

    # IPatrol
    def patrol(self, name=None):
        command = {'auto': 'patrol'}
        r = requests.get(self.cgi, params=command, auth=self._auth)
        if r.status_code != 200:
            raise CameraCommandError()

    def add_patrol(self, name):
        raise NotImplemented()

    def del_patrol(self, name):
        raise NotImplemented()

    # IZoomJoystick
    def _zoom_joystick(self, action):
        commands = {
            'in-joy': {'zooming': 'in'},
            'out-joy': {'zooming': 'out'},
            'stop': {'zoom': 'stop'}
        }
        r = requests.get(self.cgi, params=commands[action], auth=self._auth)
        if r.status_code != 200:
            raise CameraCommandError()

    # IPanTiltJoystick
    def _pantilt_joystick(self, action):
        commands = {
            'l-joy': {'vx': '2', 'vy': '0', 'vs': '2'},
            'r-joy': {'vx': '-2', 'vy': '0', 'vs': '2'},
            'u-joy': {'vx': '0', 'vy': '2', 'vs': '2'},
            'd-joy': {'vx': '0', 'vy': '-2', 'vs': '2'},
            'stop': {'vx': '0', 'vy': '0', 'vs': '0'}
        }

        r = requests.get(self.cgi, params=commands[action], auth=self._auth)
#         print 'requesting url: %s, command: %s' % (self.cgi, commands[action])

        if r.status_code != 200:
            raise CameraCommandError()

IFocus.register(SDPTZ)
IFocusAbs.register(SDPTZ)
IZoom.register(SDPTZ)
IZoomAbs.register(SDPTZ)
IPanTilt.register(SDPTZ)
IPanTiltAbs.register(SDPTZ)
IPreset.register(SDPTZ)
IPatrol.register(SDPTZ)
IPanTiltJoystick.register(SDPTZ)


class RemoteZF(PTZObject, IFocus, IZoom):
    def __init__(self, cam):
        self._zoom = RemoteZoom(cam)
        self._focus = RemoteFocus(cam)
        self.mechanism = 'mechanical'
        self.category = 'remotezf'

    def zoom(self, action):
        return self._zoom.zoom(action)

    def get_zoom_limits(self):
        return self._zoom.get_zoom_limits()

    def get_zoom_position(self, cache=True):
        return self._zoom.get_zoom_position(cache)

    def focus(self, action):
        return self._focus.focus(action)

    def get_focus_limits(self):
        return self._focus.get_focus_limits()

    def get_focus_position(self, cache=True):
        if cache is False:
            raise NotImplemented()
        return self._focus.get_focus_position(cache)

IFocus.register(RemoteZF)
IZoom.register(RemoteZF)


class RemoteFocus(PTZObject, IFocus):
    def __init__(self, cam):
        self._camera = cam
        self._cgi = "/cgi-bin/admin/remotefocus.cgi"
        self.cgi = 'http://' + self._camera.url + self._cgi
        self._focuslimits = {}
        self._focusposition = 0
        self._auth = (self._camera.username, self._camera.password)
        self._getstatus()

        self.mechanism = 'mechanical'
        self.category = 'remotefocus'

    def _getstatus(self):
        command = {'function': 'getstatus'}

        r = requests.get(self.cgi, auth=self._auth, params=command)
        if r.status_code != 200:
            raise CameraCommandError()

#         print "resp %s, content %s" % (resp, content)

        content = r.content.split('\r\n')
        for c in content:
            pos = c.find("remote_focus_focus")
            if pos > -1:
                pos += len("remote_focus_focus") + 1
                value = c[pos:]
                parameter, value = value.split('=')
                value = value.translate(None, "'")
                if parameter == "motor_max":
                    self._focuslimits['max'] = int(value)
                elif parameter == "motor_start":
                    self._focuslimits['start'] = int(value)
                elif parameter == "motor_end":
                    self._focuslimits['end'] = int(value)
                elif parameter == "enable":
                    self._focuslimits['enable'] = int(value)
                elif parameter == "motor":
                    self._focusposition = int(value)

    def _focus_relative(self, action):
        valid_action = ['near', 'far']
        if action not in valid_action:
            return

        if action == 'near':
            step = 30
        elif action == 'far':
            step = -30

        pos = self.get_focus_position() + step
        focusto = {}
        focusto['position'] = pos
        self._focus_absolute(focusto)

    def _focus_absolute(self, action):
        position = action['position']
        if position > self._focuslimits['end']:
            position = self._focuslimits['end']
        elif position < self._focuslimits['start']:
            position = self._focuslimits['start']

        command = {
            'function': 'focus',
            'direction': 'direct',
            'position': position
        }

        r = requests.get(self.cgi, auth=self._auth, params=command)
        if r.status_code != 200:
            raise CameraCommandError()
        sleep(3)

        self._getstatus()

    def focus(self, action):
        if type(action) is str:
            self._focus_relative(action)
        elif action['position'] is not None:
            self._focus_absolute(action)

        return self.get_focus_position()

    def get_focus_limits(self):
        return self._focuslimits

    def get_focus_position(self, cache=True):
        if cache is False:
            raise NotImplemented()
        return self._focusposition


IFocus.register(RemoteFocus)


class RemoteZoom(PTZObject, IZoom, IZoomAbs):
    def __init__(self, cam):
        self._camera = cam
        self._cgi = "/cgi-bin/admin/remotefocus.cgi"
        self.cgi = 'http://' + self._camera.url + self._cgi
        self._zoomlimits = {}
        self._zoomposition = 0
        self.headers = {'connection': 'close'}
        self._auth = (self._camera.username, self._camera.password)
        self._getstatus()

        self.mechanizm = 'mechanical'
        self.category = 'remotezoom'

    def _getstatus(self):
        command = {'function': 'getstatus'}
        r = requests.get(self.cgi, auth=self._auth, params=command)
        if r.status_code != 200:
            raise CameraCommandError()

        content = r.content.split('\r\n')
        for c in content:
            pos = c.find("remote_focus_zoom")
            if pos > -1:
                pos += len("remote_focus_zoom") + 1
                value = c[pos:]
                parameter, value = value.split('=')
                value = value.translate(None, "'")
                if parameter == "motor_max":
                    self._zoomlimits['max'] = int(value)
                elif parameter == "motor_start":
                    self._zoomlimits['start'] = int(value)
                elif parameter == "motor_end":
                    self._zoomlimits['end'] = int(value)
                elif parameter == "enable":
                    self._zoomlimits['enable'] = int(value)
                elif parameter == "motor":
                    self._zoomposition = int(value)

    def _zoom_relative(self, action):
        if action == 'in':
            step = 100
        elif action == 'out':
            step = -100

        pos = self.get_zoom_position() + step
        zoomto = {}
        zoomto['position'] = pos
        self._zoom_absolute(zoomto)

    def _zoom_absolute(self, action):
        position = action['position']
        if position > self._zoomlimits['end']:
            position = self._zoomlimits['end']
        elif position < self._zoomlimits['start']:
            position = self._zoomlimits['start']

        command = {
            'function': 'zoom',
            'direction': 'direct',
            'position': position
        }

        r = requests.get(self.cgi, auth=self._auth, params=command)
        if r.status_code != 200:
            raise CameraCommandError()

        sleep(3)
        self._getstatus()

    def zoom(self, action):
        if type(action) is str:
            self._zoom_relative(action)
        elif action['position'] is not None:
            self._zoom_absolute(action)

        return self.get_zoom_position()

    def get_zoom_limits(self):
        return self._zoomlimits

    def get_zoom_position(self, cache=True):
        if cache is False:
            self._getstatus()
        return self._zoomposition

IZoom.register(RemoteZoom)
IZoomAbs.register(RemoteZoom)


class StandardPTZ(PTZObject):
    # StandardPTZ, for supporting legacy PTZ and SpeedDome PTZ
    def __init__(self, cam):
        pass

IFocus.register(StandardPTZ)
IZoom.register(StandardPTZ)
IPanTilt.register(StandardPTZ)
IPreset.register(StandardPTZ)


class ElectronicPTZ(PTZObject, IPanTilt, IZoom):
    # ElectronicPTZ (EPTZ in the following) could implement pan/tilt/zoom
    def __init__(self, cam, channel, stream):
        self._camera = cam
        self._cgi = "/cgi-bin/camctrl/eCamCtrl.cgi?stream=%d" % int(stream)
        self.cgi = 'http://' + self._camera.url + self._cgi
        self._stream = stream
        self._x = 0
        self._y = 0
        self._w = 0
        self._h = 0
        self._auth = (self._camera.username, self._camera.password)

        # should be induced from self
        configer = Configer(cam)
        resolution = configer.get(
            'videoin_c%d_s%d_resolution' % (channel, stream), EFormat.eNameValue
        )
        resolution = str(resolution).translate(None, "'")
        (self._encw, self._ench) = resolution.split('=')[1].split('x')
        self._encw = int(self._encw)
        self._ench = int(self._ench)

        self.mechanism = 'electronic'
        self.category = 'eptz'

    def pantilt(self, action):
        moves = {
            'left': {'move': 'left'},
            'right': {'move': 'right'},
            'up': {'move': 'up'},
            'down': {'move': 'down'},
            'home': {'move': 'home'}
        }
        command = moves[action]

        r = requests.get(self.cgi, auth=self._auth, params=command)
        if r.status_code != 200:
            raise CameraCommandError()

        # "content: x=568,y=428,w=912,h=680"
        coords = r.content.split(',')
        self._x = int(coords[0].split('=')[1])
        self._y = int(coords[1].split('=')[1])
        self._w = int(coords[2].split('=')[1])
        self._h = int(coords[3].split('=')[1])

        return self.get_pantilt_position()

    def get_pantilt_limits(self):
        raise Exception('not implemented')

    def get_pantilt_position(self, cache=True):
        if cache is False:
            raise NotImplemented()
        # pan/tilt position of eptz should be calculated from center of the
        # window
        center_x = self._x + (self._encw / 2)
        center_y = self._y + (self._ench / 2)
        return (center_x, center_y)

    def get_zoom_position(self, cache=True):
        if cache is False:
            raise NotImplemented('Implement non-cached version!!')
        self._encw = float(self._encw)
        self._w = float(self._w)
        self._ench = float(self._ench)
        self._h = float(self._h)
        return (self._encw / self._w) * (self._ench / self._h)

    def get_zoom_limits(self):
        raise Exception('not implemented')

    def zoom(self, action):
        zooms = {
            'in': {'zoom': 'tele'},
            'out': {'zoom': 'wide'},
            'home': {'move': 'home'}
        }
        command = zooms[action]
        r = requests.get(self.cgi, auth=self._auth, params=command)

        # "content: x=568,y=428,w=912,h=680"
        coords = r.content.split(',')
        self._x = int(coords[0].split('=')[1])
        self._y = int(coords[1].split('=')[1])
        self._w = int(coords[2].split('=')[1])
        self._h = int(coords[3].split('=')[1])

        return self.get_zoom_position()

IPanTilt.register(ElectronicPTZ)
IZoom.register(ElectronicPTZ)
IPreset.register(ElectronicPTZ)


# PTZ factory
class PTZ(object):
    def __init__(self, cam):
        self._cam = cam
        self.controllers = []
        self.probe()

    def _probe_and_create_eptz(self, cam):
        caps = cam.capability
        if caps.eptz > 0:
            return ElectronicPTZ(cam, 0, 0)
        return None

    def _probe_and_create_zf(self, cam):
        caps = cam.capability
        if caps.remotefocus == 1:
            return RemoteZF(cam)
        elif caps.remotefocus == 2:
            return RemoteZoom(cam)
        elif caps.remotefocus == 4:
            return RemoteFocus(cam)
        return None

    def _probe_and_create_rs485(self, cam):
        caps = cam.capability
        if (caps.nuart > 0 and caps.camctrl.c[0].rs485 == 1):
            return RS485(cam)
        return None

    def _probe_and_create_sdptz(self, cam):
        caps = cam.capability
        if (caps.ptzenabled > 0 and
                caps.camctrl.c[0].rs485 == 0 and
                caps.camctrl.c[0].buildinpt > 0 and
                caps.camctrl.c[0].zoommodule > 0):
            return SDPTZ(cam)
        return None

    def probe(self):
        probelist = [
            self._probe_and_create_eptz,
            self._probe_and_create_zf,
            self._probe_and_create_sdptz,
            self._probe_and_create_rs485
        ]

        for toprobe in probelist:
            result = toprobe(self._cam)
            if result is not None:
                print "%s supported" % toprobe.__name__
                self.controllers.append(result)
            else:
                print "%s NOT supported" % toprobe.__name__

# vim: set expandtab
