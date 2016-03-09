# -*- coding: utf-8 -*-

import abc
from YNM.camera.service.config import Configer


class ISystem():
    __metaclass__ = abc.ABCMeta

    @abc.abstractproperty
    def hostname(self):
        raise NotImplemented()

    @abc.abstractmethod
    def reboot(self, delay=3):
        raise NotImplemented()

    @abc.abstractmethod
    def time(self, time):
        raise NotImplemented()

    @abc.abstractmethod
    def restore(self, exceptfor=None):
        raise NotImplemented()


class System(ISystem):
    def __init__(self, cam):
        self._camera = cam
        self._configer = Configer(cam)

    def reboot(self, delay=3):
        configer = self._configer
        configer.set('system_reset=%d', delay)

    def time(self, time):
        pass

    def restore(self, exclude=None):
        pass

    def hostname(self, exclude=None):
        pass
