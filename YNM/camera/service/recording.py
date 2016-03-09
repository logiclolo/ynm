# -*- coding: utf-8 -*-

import abc
import requests


class IHealth(object):
    __metaclass__ = abc.ABCMeta
    ''' deteremine storage health (esp. edge storage)

    Some storage may have capability of getting storage's health information
    This interface make the caller to know if currently handled storage supports
    this capability
    '''

    @abc.abstractmethod
    def health(self):
        ''' health() returns the information of storage health. '''
        raise NotImplemented()


class IStorage(object):
    __metaclass__ = abc.ABCMeta
    ''' storage interface, edge or nas storage

    returns a string represents current storate status, which includes:
    - online/offline
    '''
    @abc.abstractmethod
    def status(self):
        raise NotImplemented()

    @abc.abstractmethod
    def capacity(self):
        ''' returns a int represents total capacity in KBytes '''
        raise NotImplemented()

    @abc.abstractmethod
    def availablesize(self):
        ''' returns a int represents avail space in KBytes '''
        raise NotImplemented()

    @abc.abstractmethod
    def usedsize(self):
        ''' returns a int represents used space in KBytes '''
        raise NotImplemented()

    @abc.abstractmethod
    def location(self):
        ''' returns a string represents storage URI '''
        raise NotImplemented()

    @abc.abstractmethod
    def filesystem(self):
        ''' returns a string represets underlying file system for the storage
        '''
        raise NotImplemented

    @abc.abstractmethod
    def search(self, criteria):
        ''' returns a list of file with matched criteria in search '''
        raise NotImplemented()


class ITimeline(object):
    __metaclass__ = abc.ABCMeta
    ''' timeline interface, abstraction of continuous recording '''

    @abc.abstractmethod
    def timelines(self, criteria):
        ''' returns a list of timeline each timeline contains several tracks
        which is associated together '''
        raise NotImplemented()


class ITrack(object):
    __metaclass__ = abc.ABCMeta
    ''' abstraction of a content type in a continuous recording

    recording consists of multiple tracks, for example, a typical recording
    contains video tracks and audio track '''

    @abc.abstractmethod
    def content_type(self):
        ''' returns a string which follows HTTP content type.  For example,
        video/H264 '''
        raise NotImplemented()

    @abc.abstractmethod
    def desdcription(self):
        ''' returns a text represents description '''
        raise NotImplemented()

    @abc.abstractmethod
    def time(self):
        ''' returns a tuple which represents start/end time '''
        raise NotImplemented()


class IRecordingItem(object):
    __metaclass__ = abc.ABCMeta
    ''' recording entry in camera config (e.g., recoridng_i0_name.../etc) '''

    @abc.abstractmethod
    def enable(self):
        ''' make system start to generate recordings '''
        raise NotImplemented()

    @abc.abstractmethod
    def disable(self):
        ''' make system stop to generate recordings '''
        raise NotImplemented()

    @abc.abstractmethod
    def set(self, setting):
        ''' configure recording options '''
        raise NotImplemented()

    @abc.abstractmethod
    def reset(self):
        ''' clear recording options, useful when deleting recording '''
        raise NotImplemented()


class IRecordingService(object):
    __metaclass__ = abc.ABCMeta
    ''' collection of recordingitems

    IRecordingService is an interface which regulates recording service on a
    device.  According to the device computing power, various recording item
    count may be supported
    '''

    @abc.abstractmethod
    def additem(self, item):
        ''' add a recording item in to device '''
        raise NotImplemented()

    def removeitem(self, item):
        ''' remove a recording item from device '''
        raise NotImplemented()


import xml.etree.ElementTree as xmltree


class EdgeRecording (IStorage, IHealth):
    ''' VIVOTEK edge recording implementation '''

    def __init__(self, cam):
        self._camera = cam
        self._edgecgi = 'http://' + self._camera.url + '/cgi-bin/admin/lsctrlrec.cgi'
        self._legacycgi = 'http://' + self._camera.url + '/cgi-bin/admin/lsctrl.cgi'
        self._auth = (self._camera.username, self._camera.password)
        self._status = ''
        self._capacity = 0
        self._availablesize = 0
        self._usedsize = 0

        self._update_all_status()

    def _update_all_status(self):
        command = {'cmd': 'queryStatus'}
        r = requests.get(self._legacycgi, params=command, auth=self._auth)
        if r.status_code != 200:
            raise Exception("Command edge error %s" % r)

        x = xmltree.fromstring(r.content)
        self._status = x.find('disk/i0/cond').text
        self._capacity = int(x.find('disk/i0/totalsize').text)
        self._availablesize = int(x.find('disk/i0/freespace').text)
        self._usedsize = int(x.find('disk/i0/usedspace').text)

    # IStroage interface
    def status(self):
        self._update_all_status()
        return self._status

    def capacity(self):
        self._update_all_status()
        return self._capacity

    def availablesize(self):
        self._update_all_status()
        return self._availablesize

    def usedsize(self):
        self._update_all_status()
        return self._usedsize

    def location(self):
        self._update_all_status()
        # reserve the space for future extension
        return self._camera.url + "/disk0"

    def filesystem(self):
        raise NotImplemented()

    def search(self):
        self._update_all_status()
        raise NotImplemented()

    # IHealth interface
    def health(self):
        raise NotImplemented()

    # custome interface, solely owned by edge storage
    def update_summary(self):
        raise NotImplemented()


IStorage.register(EdgeRecording)
ITimeline.register(EdgeRecording)
