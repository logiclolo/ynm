# -*- coding: utf-8 -*-

import abc

from YNM.camera.service.config import Configer


class IMotion:
    __metaclass__ = abc.ABCMeta

    ''' Basically, motion interface is the same as privacy.  The difference
    between motion and privacy is -- privacy masks the video while motion only
    marks video '''

    @abc.abstractmethod
    def windows(self, wins=None):
        ''' Return/Set lists of motion windows '''
        raise NotImplemented()

    @abc.abstractmethod
    def support_shape(self):
        ''' Return shape of the motion mask supported by camera in string.
        Valid return will be "polygon" or "rectangle" '''
        raise NotImplemented()

    @abc.abstractmethod
    def enabled(self):
        ''' Get motion mask status. '''
        raise NotImplemented()

    @abc.abstractmethod
    def enable(self, status=None):
        ''' Enable motion mask '''
        raise NotImplemented()

    @abc.abstractmethod
    def disable(self, status=None):
        ''' Disable motion mask '''
        raise NotImplemented()


class MotionNotSupportError(Exception):
    ''' Exception for device which doesn't support motion detection.  In fact,
    there is no such device '''
    pass


class MotionNotSupportThisTypeError(Exception):
    ''' Exception for not supported type of motion detection '''
    pass


class PolygonMotionNotSupportNonStandardDomain(Exception):
    ''' Exception for device supports polygon motion but not support standard
    domain (0 - 9999) '''
    pass


class PolygonStandardMotion(IMotion):
    ''' Rectangle implementation of motion interface '''

    def __init__(self, cam, ch):
        self._cam = cam
        self._channel = ch

    def windows(self, wins=None):
        ''' Return list of motion windows or set list of motion windows if
        args provided.

        Please note that sensitivity will be set as maximum value in :wins:

        Args:
            wins: list of motion window to set

        Returns:
            list of currently configured motion window.

        Raises:
            RectangleMotionErrMotionNotRectangle: when input motion is not
            rectangle
        '''

        cam = self._cam
        config = Configer(cam)
        c = config.get('motion')
        ch = self._channel
        nmotion = cam.capability.nmotion

        if wins:
            sensitivity = max([int(x['sensitivity']) for x in wins])
            to_set = ''
            for idx, win in enumerate(wins):
                prefix = 'motion_c%d_win_i%d' % (ch, idx)

                enable = prefix + '_enable=%d&' % int(win['enable'])
                name = prefix + '_name=%s&' % str(win['name'])
                objsize = prefix + '_objsize=%d&' % int(win['objsize'])
                win_sensitivity = prefix + '_sensitivity=%d&' % sensitivity
                if win['polygon'] != '':
                    polygon = prefix + '_polygonstd=%d,%d,%d,%d,%d,%d,%d,%d&' % \
                        tuple(win['polygon'])
                to_set += enable + name + objsize + win_sensitivity + polygon

            to_set += 'motion_c0_win_sensitivity=%d' % sensitivity
            print 'to_set: %s' % to_set
            config.set(to_set)

        else:
            wins = []
            for idx in range(0, nmotion):
                win = {}
                win['name'] = c.motion.c[ch].win.i[idx].name
                win['enable'] = c.motion.c[ch].win.i[idx].enable
                win['polygon'] = c.motion.c[ch].win.i[idx].polygonstd
                win['objsize'] = c.motion.c[ch].win.i[idx].objsize
                win['sensitivity'] = c.motion.c[ch].win.i[idx].sensitivity
                wins.append(win)

        return wins

    def support_shape(self):
        ''' Return hard-coded rectangle '''
        return 'rectangle'

    def enabled(self):
        ''' Get motion status. '''
        ch = self._channel
        config = Configer(self._cam)
        c = config.get('motion_c%d_enable' % ch)
        if c.motion.c[ch].enable == '1':
            return True

        # default return false
        return False

    def enable(self, status=None):
        ''' Enable motion '''
        config = Configer(self._cam)
        ch = self._channel
        setup_string = 'motion_c%d_enable=1' % ch
        config.set(setup_string)

    def disable(self, status=None):
        ''' Disable motion '''
        config = Configer(self._cam)
        ch = self._channel
        setup_string = 'motion_c%d_enable=0' % ch
        config.set(setup_string)


IMotion.register(PolygonStandardMotion)


def Motion(cam, ch=0):
    ''' Motion factory, return motion object according to the camera capability
    '''

    caps = cam.capability
    wintype = caps.motion.wintype
    domain = caps.motion.windomain
    nmotion = caps.nmotion

    if nmotion <= 0:
        raise MotionNotSupportError()

    # currently we only support polygon and windomain == 'std'
    if wintype == 'polygon' and domain == 'std':
        return PolygonStandardMotion(cam, ch)
    else:
        raise MotionNotSupportThisTypeError()


class MotionFrame(object):
    """
    Interface for implementing streaming service

    param: :enable: motion enabled or not
    param: :triggered: motion window triggered or not
    param: :percent: if triggered, :percent: represents the trigger percent
    param: :axis: motion window location
    """

    def __init__(self, enable, triggered, percent, axis):
        self._enable = [enable[i] for i in range(len(enable))]
        self._triggered = [triggered[i] for i in range(len(triggered))]
        self._percent = [percent[i] for i in range(len(percent))]

    def __str__(self):
        msg = ''
        for i in range(len(self._enable)):
            msg += "win%d, triggered %d, %d%%. " % (i, self._triggered[i], self._percent[i])

        return msg

    def triggered(self):
        for i in range(3):
            if self._triggered[i] is True:
                return True

        return False
