# -*- coding: utf-8 -*-

import abc
import requests
import re
from datetime import datetime
import xml.etree.ElementTree as xmltree


def time_convert(timestr):

    if type(timestr) is datetime or timestr is None:
        return timestr

    timestr = timestr.replace('T', ' ')
    is_utc = 0
    if re.search('Z', timestr) is not None:
        is_utc = 1
        timestr = timestr.replace('Z', '')
    return datetime.strptime(timestr, '%Y-%m-%d %H:%M:%S.%f')


class IHealth(object):
    __metaclass__ = abc.ABCMeta
    ''' deteremine storage health (esp. edge storage)

    Some storage may have capability of getting storage's health information
    This interface make the caller to know if currently handled storage
    supports this capability
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
    def format(self, fs):
        ''' returns format massage '''
        raise NotImplemented()

    @abc.abstractmethod
    def search(self, criteria):
        ''' returns a list of file with matched criteria in search '''
        raise NotImplemented()


class ISlice(object):
    __metaclass__ = abc.ABCMeta
    ''' slice interface, abstraction of continuous recording '''

    @abc.abstractmethod
    def get_slices(self, criteria):
        ''' returns a list of slice each slice contains several tracks
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

    def desdcription(self):
        ''' returns a text represents description '''
        return self._description

    def time(self):
        ''' returns a tuple which represents start/end time '''
        return self._time


class IFile(object):
    __metaclass__ = abc.ABCMeta
    ''' abstraction of a file '''

    def path(self):
        ''' returns a string represents file's path '''
        return self._path

    def is_locked(self):
        ''' returns bool value '''
        return self._is_locked

    def time(self):
        return self._time

    def triggertype(self):
        return self._triggertype


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


class EdgeRecording (IStorage, IHealth):
    ''' VIVOTEK edge recording implementation '''

    def __init__(self, cam):
        self._camera = cam
        self._cgiurl = 'http://' + self._camera.url + '/cgi-bin'
        self._edgecgi = self._cgiurl + '/admin/lsctrlrec.cgi'
        self._legacycgi = self._cgiurl + '/admin/lsctrl.cgi'
        self._fscgi = self._cgiurl + '/admin/getSDfilesystem.cgi'
        self._formatcgi = self._cgiurl + '/admin/formatSD.cgi'
        self._auth = (self._camera.username, self._camera.password)
        self._status = ''
        self.reset()
        self._update_all_status()
    
    def reset(self):
        self._capacity = 0
        self._availablesize = 0
        self._usedsize = 0
        self._filesystem = ''

    def _update_all_status(self):
        command = {'cmd': 'queryStatus'}
        r = requests.get(self._legacycgi, params=command, auth=self._auth)
        if r.status_code != 200:
            raise Exception("Edge command (queryStatus) error %s" % r)

        x = xmltree.fromstring(r.content)
        self._status = x.find('disk/i0/cond').text
        self._capacity = int(x.find('disk/i0/totalsize').text)
        self._availablesize = int(x.find('disk/i0/freespace').text)
        self._usedsize = int(x.find('disk/i0/usedspace').text)

        if self._status == 'detached':
            self.reset()

        r = requests.get(self._fscgi, auth=self._auth)
        if r.status_code != 200:
            raise Exception("Edge command (getSDfilesystem.cgi) error %s" % r)
        self._filesystem = r.content.strip()

    def _nativeapi_search(self, criteria):
        command = {'cmd': 'getSlices',
                   'recStartTime': criteria['starttime'],
                   'recEndTime': criteria['endtime']}
        if 'triggertype' in criteria:
            command.update({'triggerType': ','.join(criteria['triggertype'])})

        r = requests.get(self._edgecgi, params=command, auth=self._auth)
        if r.status_code != 200:
            raise Exception("Edge command (getSlices) error %s" % r)

        x = xmltree.fromstring(r.content)
        root = x.find('root')
        slices = self.get_slices(root)
        return slices

    def _legacy_search(self, criteria):
        timeinterval = "BETWEEN '" + criteria['starttime'] + \
                       "' AND '" + slice['endtime'] + "'"
        command = {'cmd': 'search',
                   'triggerTime': timeinterval}
        r = requests.get(self._legacycgi, params=command, auth=self._auth)
        x = xmltree.fromstring(r.content)

    # IStorage interface

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
        self._update_all_status()
        return self._filesystem

    def format(self, fs='fat32'):

        fs = fs.lower().replace('-', '')
        command = {'fstype': fs, 'alerten': 1}
        requests.get(self._formatcgi, params=command, auth=self._auth)

    def search(self, criteria):
        if 'starttime' not in criteria:
            criteria['starttime'] = '1970-01-01T00:00:00.000Z'
        if 'endtime' not in criteria:
            criteria['endtime'] = '2035-12-31T23:59:59.000Z'
        if 'triggertype' in criteria:
            if 'backup' in criteria['triggertype']:
                criteria['backup'] = 1
        try:
            if criteria['mediatype'] == 'videoclip':
                return self._nativeapi_search(criteria)
            else:
                return self._legacy_search(criteria)
        except:
            assert False, "must have mediatype, \
                such as videoclip, snapshot, text"

    def get_slices(self, xml_obj):
        slices = dict()
        idx = 0
        for child in xml_obj:
            if child.tag == 'slices':
                slice = dict()
                for et in child:
                    if et.tag == 'sliceStart' or et.tag == 'sliceEnd':
                        if et.text is None:
                            xmltree.dump(et)
                        slice.update({et.tag: time_convert(et.text)})
                    else:
                        slice.update({et.tag: et.text})

                # append tracks information
                tracks = self._get_tracks(slice)
                slice.update({'tracks': tracks})
                # append files information
                files = self._get_files(slice, mediaType='videoclip')
                slice.update({'files': files})

                slices.update({idx: slice})
                idx += 1
        return slices

    def _get_files(self, slice, mediaType="all"):

        slice['sliceStart'] = time_convert(slice['sliceStart'])
        slice['sliceEnd'] = time_convert(slice['sliceEnd'])

        command = {'cmd': 'search',
                   'recToken': slice['recordingToken']}

        if mediaType == "videoclip":
            command.update({'mediaType': mediaType})
            if slice['sliceStart'] is not None:
                command.update({'starttime': slice['sliceStart'].isoformat()})
            if slice['sliceEnd'] is not None:
                command.update({'endtime': slice['sliceEnd'].isoformat()})
        elif mediaType != "all":
            timeinterval = "BETWEEN '" + slice['sliceStart'].isoformat() + \
                           "' AND '" + slice['sliceEnd'].isoformat() + "'"
            command.update({'triggerTime': timeinterval})
        r = requests.get(self._legacycgi, params=command, auth=self._auth)
        x = xmltree.fromstring(r.content)
        files = []
        for idx in range(0, int(x.find('counts').text)):
            info = x.find('i' + str(idx))
            media_type = info.find('mediaType').text
            label = info.find('label').text
            trigger = info.find('triggerType').text
            path = info.find('destPath').text
            locked = info.find('isLocked').text
            tri_time = info.find('triggerType').text
            starttime = time_convert(info.find('beginTime').text)
            endtime = time_convert(info.find('endTime').text)
            time = (starttime, endtime)
            if media_type == 'videoclip':
                files.append(VideoFile(label, trigger,  path, locked, time))
            elif media_type == 'text':
                files.append(TextFile(label, trigger,  path, locked, tri_time))
            elif media_type == 'snapshot':
                files.append(SnapFile(label, trigger,  path, locked, tri_time))
        return files

    def _get_tracks(self, slice):

        slice['sliceStart'] = time_convert(slice['sliceStart'])
        slice['sliceEnd'] = time_convert(slice['sliceEnd'])

        command = {'cmd': 'getmediaattr',
                   'recToken': slice['recordingToken'],
                   'recTime': slice['sliceStart'].isoformat()}
        r = requests.get(self._edgecgi, params=command, auth=self._auth)
        x = xmltree.fromstring(r.content)

        # error handle
        rec = x.find('root/recording/i0')
        if rec is None:
            return None
        tracks = []
        for idx in range(0, int(rec.find('trackNum').text)):
            idx_track = 'trackAttributes/i' + str(idx)

            info = rec.find(idx_track + '/trackInformation')
            track_type = info.find('trackType').text.lower()
            description = info.find('description').text
            starttime = time_convert(info.find('dataFrom').text)
            endtime = time_convert(info.find('dataTo').text)
            time = (starttime, endtime)

            attr = rec.find(idx_track + '/' + track_type + 'Attributes')
            codec = attr.find('encoding').text

            if track_type == 'video':
                tracks.append(VideoTrack(codec, description, time))
            elif track_type == 'audio':
                tracks.append(AudioTrack(codec, description, time))

        return tracks

    def delete_a_slice(self, slice):
        starttime = time_convert(slice['sliceStart']).isoformat()
        endtime = time_convert(slice['sliceEnd']).isoformat()

        command = {'cmd': 'truncateRecording',
                   'recToken': slice['recordingToken'],
                   'recStartTime': starttime,
                   'recEndTime': endtime}
        requests.get(self._edgecgi, params=command, auth=self._auth)

    
    # IHealth interface
    def health(self):
        raise NotImplemented()

    # custome interface, solely owned by edge storage
    def update_summary(self):
        raise NotImplemented()


class VideoTrack(ITrack):

    def __init__(self, codec='H264', description=None, time=None):
        self._codec = codec.upper()
        self._description = description
        self._time = time

    def content_type(self):
        return 'video/'+self._codec


class AudioTrack(ITrack):

    def __init__(self, codec='G711', description=None, time=None):
        self._codec = codec.upper()
        self._description = description
        self._time = time

    def content_type(self):
        return 'audio/'+self._codec


class VideoFile(IFile):

    def __init__(self, label, trigger=None, path=None, locked=0, time=None):
        self._label = label
        self._trigger = trigger
        self._path = path
        self._time = time
        self._is_locked = locked

    def __repr__(self):
        msg = "label: %s\t triggerType: %s\t path: %s\t" %\
            (self._label, self._trigger, self._path)

        if self._is_locked == '1':
            msg += '\t locked'
        return msg


class TextFile(IFile):

    def __init__(self, label, trigger=None, path=None, locked=0, time=None):
        self._label = label
        self._trigger = trigger
        self._path = path
        self._time = time
        self._is_locked = locked


class SnapFile(IFile):

    def __init__(self, label, trigger=None, path=None, locked=0, time=None):
        self._label = label
        self._trigger = trigger
        self._path = path
        self._time = time
        self._is_locked = locked


IStorage.register(EdgeRecording)
ISlice.register(EdgeRecording)

ITrack.register(VideoTrack)
ITrack.register(AudioTrack)

IFile.register(VideoFile)
IFile.register(TextFile)
IFile.register(SnapFile)
