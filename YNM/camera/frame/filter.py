# -*- coding: utf-8 -*-

import abc
from YNM.databroker.media_type_def import TMediaDBFrameType


class Bitrate(object):
    def __init__(self, bitrate):
        self.bps = float(bitrate * 8)

    def __str__(self):
        suffix = 'b'
        num = self.bps
        for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
            if abs(num) < 1024.0:
                return "%3.1f%s%s" % (num, unit, suffix)
            num /= 1024.0

        return "%.1f%s%s" % (num, 'Yi', suffix)

    def __float__(self):
        return self.bps


class IFilter (object):

    """IFilter defines the interface of filter.  All kinds of filter should
    follow IFilter """

    __metaclass__ = abc.ABCMeta

    """ filter input and return a boolean. `True` means input matches the
    criteria it looks for `False` means input doesn't match the criteria """
    @abc.abstractmethod
    def filter(self, input_frame):
        raise NotImplemented()

    """ AND-ing filters """
    def __add__(self, other):
        filters = [self, other]
        return AndFilter(filters)

    """ AND-ing filters """
    def __and__(self, other):
        filters = [other, self]
        return AndFilter(filters)

    """ OR-ing filters """
    def __or__(self, other):
        filters = [other, self]
        return OrFilter(filters)

    """ NOT-ing filters """
    def __invert__(self):
        return NotFilter(self.filter)


class AndFilter(IFilter):

    """ Filter combination.  AndFilter is a kind of filter which doesn't filter
    it self.  Instead, it store filters in an array and use these filters to
    determine if input matches the criteria.  """

    def __init__(self, filters):
        self._filters = filters

    def filter(self, input_frame):
        for filter in self._filters:
            if filter.filter(input_frame) is False:
                return False
        return True

    """ Returns filters contained in this connectedfilter """
    def getfilters(self):
        return self._filters

IFilter.register(AndFilter)


class OrFilter(IFilter):

    """ Filter combination.  OrFilter is a kind of filter which doesn't filter
    it self.  Instead, it store filters in an array and use these filters to
    determin if input matches the criteria """

    def __init__(self, filters):
        self._filters = filters

    def filter(self, input_frame):
        for filter in self._filters:
            if filter.filter(input_frame) is True:
                return True
        return False

    """ Returns filters contained in this connectedfilter """
    def getfilters(self):
        return self._filters


class NotFilter(IFilter):

    """ Filter combination.  NotFilter is a kind of filter which doesn't filter
    it self.  Instead, it store filters in an array and use these filters to
    determin if input matches the criteria """

    def __init__(self, filter):
        self._filter = filter

    def filter(self, input_frame):
        if self._filter(input_frame) is True:
            return False
        return True


def Filter(criteria, param1=0):

    """ Filter factory.  Return a filter object by giving a parameter """

    if criteria == "video":
        return VideoFilter()
    elif criteria == "audio":
        return AudioFilter()
    elif criteria == "timeincreasing":
        return TimeIncreasingFilter()
    elif criteria == "timedecreasing":
        return TimeDecreasingFilter()
    elif criteria == "timenojumpforward":
        return TimeNoJumpForwardFilter()
    elif criteria == "keyframe":
        return KeyFrameFilter()
    elif criteria == "gop":
        return GOPFilter(param1)
    elif criteria == "codecfilter":
        return CodecFilter(str(param1))
    elif (criteria == "h264" or criteria == "h265" or criteria == "mjpeg" or
          criteria == "mpeg4"):
        return CodecFilter(criteria)
    elif (criteria == "g726" or criteria == "g711" or criteria == "aac4" or
          criteria == "gamr"):
        return CodecFilter(criteria)
    elif criteria == "measure":
        return MeasureFilter()
    elif criteria == "resolution":
        return ResolutionFilter(param1)
    else:
        raise Exception("nosuchfilter (%s)" % criteria)


class TimeIncreasingFilter (IFilter):

    """ TimeIcnreasingFilter. `filter()` returns `True` if input frame timestamp
    is greater or equal then previous frame """

    def __init__(self):
        self._previous_frame = None

    def filter(self, input_frame):
        if self._previous_frame is None:
            self._previous_frame = input_frame
            return True
        else:
            previous_time = self._previous_frame.time
            current_time = input_frame.time
            if previous_time <= current_time:
                self._previous_frame = input_frame
                return True
            else:
                self._previous_frame = input_frame
                return False
IFilter.register(TimeIncreasingFilter)


class TimeNoJumpForwardFilter (IFilter):

    """ TimeNoJumpForwardFilter. `filter()` returns `True` if input frame
    timestamp difference is less or equal than parameter `forward_gap` (default
    = 5 seconds) """

    def __init__(self, forward_gap=5):
        self._previous_frame = None
        self._forward_gap = forward_gap

    def filter(self, input_frame):
        if self._previous_frame is None:
            self._previous_frame = input_frame
            return True
        else:
            previous_time = self._previous_frame.time
            current_time = input_frame.time

            if (current_time - previous_time).total_seconds() <= self._forward_gap:
                self._previous_frame = input_frame

                return True
            else:
                self._previous_frame = input_frame
                return False
IFilter.register(TimeNoJumpForwardFilter)


class TimeDecreasingFilter (IFilter):

    """ TimeDecreasingFilter. `filter()` returns `True` if input time stamp is
    less then previous frame """

    def __init__(self):
        self._previous_frame = None

    def filter(self, input_frame):
        if self._previous_frame is None:
            self._previous_frame = input_frame
            return False
        else:
            previous_time = self._previous_frame.time
            current_time = input_frame.time
            if previous_time > current_time:
                self._previous_frame = input_frame
                return True
            else:
                self._previous_frame = input_frame
                return False
IFilter.register(TimeDecreasingFilter)


class VideoFilter (IFilter):

    """ VideoFilter. `filter()` returns `True` if input frame is video frame """

    def filter(self, input_frame):
        codecs = ['H264', 'JPEG', 'HEVC', 'MPEG4']
        if str(input_frame.codec) in codecs:
            return True
        return False
IFilter.register(VideoFilter)


class AudioFilter (IFilter):

    """ AudioFilter. `filter()` returns `True` if input frame is audio frame """

    def filter(self, input_frame):
        codecs = ['G726', 'G711', 'GAMR', 'AAC4']
        if str(input_frame.codec) in codecs:
            return True
        return False
IFilter.register(AudioFilter)


class KeyFrameFilter (IFilter):

    """ KeyFrameFilter. `filter()` returns `True` if input frame is key frame.
    """

    def __init__(self):
        pass

    def filter(self, input_frame):
        if input_frame.type == TMediaDBFrameType.MEDIADB_FRAME_INTRA:
            return True
        return False

IFilter.register(KeyFrameFilter)


class CodecFilter(IFilter):

    """ CodecFilter. `filter()` returns `True` if input frame codec matches
    `codec` which were set when `__init__` called """

    def __init__(self, codec):
        # only video codecs right now

        mapping = {'mjpeg': 'JPEG', 'mpeg4': 'MPEG4', 'h264': 'H264', 'h265':
                   'HEVC', 'g711': 'G711', 'g726': 'G726', 'aac4': 'AAC',
                   'gamr': 'GAMR'}

        if codec in mapping.keys():
            self._codec = mapping[codec]
        else:
            self._codec = codec

    def filter(self, input_frame):
        if str(input_frame.codec) == self._codec:
            return True
        return False
IFilter.register(CodecFilter)


class GOPFilter(IFilter):

    """ GOPFilter. `filter()` returns `False` when GOP size doesn't match
    `_gopsize` which were set when `__init__` called """

    def __init__(self, gopsize=30):
        self._gopsize = gopsize
        self._predframe_count = -1

    def filter(self, input_frame):
        if input_frame.type == TMediaDBFrameType.MEDIADB_FRAME_INTRA:
            if self._predframe_count != -1 and self._predframe_count != self._gopsize:
                return False
            self._predframe_count = 0
        elif input_frame.type == TMediaDBFrameType.MEDIADB_FRAME_PRED:
            if self._predframe_count == -1:
                return False
            if self._predframe_count >= (self._gopsize - 1):
                return False
            self._predframe_count += 1

        return True
IFilter.register(GOPFilter)


class ResolutionFilter(IFilter):

    """ ResolutilFilter. `filter()` returns `False` when input frame resolution
    doesn't match """

    def __init__(self, resolution):
        self._width, self._height = resolution.split('x')

    def filter(self, input_frame):
        iwidth = int(input_frame.width)
        iheight = int(input_frame.height)
        swidth = int(self._width)
        sheight = int(self._height)

        if (iwidth == swidth and iheight == sheight):
            return True

        return False
IFilter.register(ResolutionFilter)


class MeasureFilter(IFilter):

    """ MeasureFilter. `filter()` never returns `False`, just measure
    fps/bitrate """

    def __init__(self):
        self._fps_meta = {}
        self.fps = 0
        self._bitrate_meta = {}
        self.bitrate = None
        self.frames = 0
        self.played = 0
        self._first_frame = None

    def filter(self, input_frame):
        self.frames += 1
        time = input_frame.time
        time_key = time.strftime("%s")

        if self._first_frame is None:
            self._first_frame = input_frame
        else:
            self.played = (input_frame.time -
                           self._first_frame.time).total_seconds()

        if time_key in self._fps_meta:
            self._fps_meta[time_key] += 1
        else:
            self._fps_meta[time_key] = 1

        if len(self._fps_meta) > 1:
            self.fps = self._fps_meta[min(self._fps_meta.keys())]

        if len(self._fps_meta) > 2:
            self._fps_meta.pop(min(self._fps_meta.keys()))

        if time_key in self._bitrate_meta:
            self._bitrate_meta[time_key] += input_frame.size_in_bytes
        else:
            self._bitrate_meta[time_key] = input_frame.size_in_bytes

        if len(self._bitrate_meta) > 1:
            self.bitrate = Bitrate(self._bitrate_meta[min(self._bitrate_meta.keys())])

        if len(self._bitrate_meta) > 2:
            self._bitrate_meta.pop(min(self._bitrate_meta.keys()))

        return True


h264_filter = Filter('h264')
h265_filter = Filter('h265')
mjpeg_filter = Filter('mjpeg')
mpeg4_filter = Filter('mpeg4')
g726_filter = Filter('g726')
gamr_filter = Filter('gamr')
g711_filter = Filter('g711')
aac4_filter = Filter('aac4')
video_filter = Filter("video")
audio_filter = Filter("audio")
keyframe_filter = Filter("keyframe")
increasing_filter = Filter("timeincreasing")
decreasing_filter = Filter("timedecreasing")
