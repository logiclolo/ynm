# -*- coding: utf-8 -*-

import abc
import filter as fltr

""" ICatcher defines tne interface of a catcher.  A `Catcher` just like
`Filter`, however, a catcher raises an exception instead of returning boolean
which should be caught by programmer.  Use a filter as an input to instantiate a
catcher object.
"""


class ICatcher (object):
    __metaclass__ = abc.ABCMeta

    def catch(self, input_frame):
        print 'abc method'
        return None


class CatcherException(Exception):
    pass


def Catcher(criteria):
    class GeneratedCatcher(ICatcher):
        def __init__(self, criteria):
            self._criteria = criteria

        def catch(self, input_frame):
            if self._criteria.filter(input_frame) is True:
                raise CatcherException()

    return GeneratedCatcher(criteria)

video_catcher = Catcher(fltr.Filter('video'))
audio_catcher = Catcher(fltr.Filter('audio'))
keyframe_catcher = Catcher(fltr.Filter('keyframe'))
increasing_catcher = Catcher(fltr.Filter('timeincreasing'))
decreasing_catcher = Catcher(fltr.Filter('timedecreasing'))
