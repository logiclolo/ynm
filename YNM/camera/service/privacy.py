# -*- coding: utf-8 -*-

import abc

from YNM.camera.service.config import Configer


class IPrivacy:
    __metaclass__ = abc.ABCMeta

    ''' List of privacy window, this interface could be used for get/set privacy
    masks.  Privacy window is represented in 4 dots whose coordinate system is
    320x240 based.  If function `windows()' is called by providing `wins'
    variable, the `windows()' will send window stored in `wins' to camera '''

    @abc.abstractmethod
    def windows(self, wins=None):
        raise NotImplemented()

    ''' Return shape of the privacy mask supported by camera in string.  Valid
    return will be "polygon" or "rectangle" '''
    @abc.abstractmethod
    def support_shape(self):
        raise NotImplemented()

    ''' Get privacy mask status. '''
    @abc.abstractmethod
    def enabled(self):
        raise NotImplemented()

    ''' Enable privacy mask '''
    @abc.abstractmethod
    def enable(self, status=None):
        raise NotImplemented()

    ''' Disable privacy mask '''
    @abc.abstractmethod
    def disable(self, status=None):
        raise NotImplemented()


def Privacy(cam):
    # Function Privacy() is a factory which generates instance which fits with
    # IPrivacy

    caps = cam.capability
    if caps.image.c[0].privacymask.wintype == 'polygon':
        return PolygonPrivacy(cam, ch=0)
    elif caps.image.c[0].privacymask.wintype == 'rectangle':
        return RectanglePrivacy(cam)


class PolygonPrivacy(IPrivacy):

    def __init__(self, cam, ch):
        self._cam = cam
        self._channel = ch

    def windows(self, wins=None):
        config = Configer(self._cam)
        ch = self._channel
        if wins:
            to_set = ''
            # set windows provided
            for idx, win in enumerate(wins):
                prefix = 'privacymask_c%d_win_i%d' % (ch, idx)
                enable = prefix + '_enable=%d&' % int(win['enable'])
                name = prefix + '_name=%s&' % str(win['name'])
                if win['polygon'] != '':
                    polygon = prefix + '_polygon=%d,%d,%d,%d,%d,%d,%d,%d&' % \
                        tuple(win['polygon'])
                to_set = enable + name + polygon
#                 print 'to set %s' % to_set
                config.set(to_set)
        else:
            c = config.get('privacymask')
            wins = []
            ch = self._channel
            for idx in range(0, 5):
                win = {}
                win['enable'] = c.privacymask.c[ch].win.i[idx].enable
                win['name'] = c.privacymask.c[ch].win.i[idx].name
                win['polygon'] = c.privacymask.c[ch].win.i[idx].polygon
                wins.append(win)

            return wins

    def support_shape(self):
        return 'polygon'

    def enabled(self):
        ch = self._channel
        config = Configer(self._cam)
        c = config.get('privacymask_c%d_enable' % ch)
        if c.privacymask.c[ch].enable == '1':
            return True

        # default return false
        return False

    def enable(self):
        config = Configer(self._cam)
        ch = self._channel
        setup_string = 'privacymask_c%d_enable=1' % ch
#         print 'to set %s' % setup_string
        config.set(setup_string)

    def disable(self):
        config = Configer(self._cam)
        ch = self._channel
        setup_string = 'privacymask_c%d_enable=0' % ch
#         print 'to set %s' % setup_string
        config.set(setup_string)

IPrivacy.register(PolygonPrivacy)


class RectanglePrivacy(IPrivacy):

    def __init__(self, cam):
        self._cam = cam

    def windows(self, wins=None):
        raise NotImplemented()

    def support_shape(self):
        return 'rectangle'

IPrivacy.register(RectanglePrivacy)
