# -*- coding: utf-8 -*-

import datetime


def human_readable_size(num, suffix='B'):
    for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)


""" A Frame object is used for representing any kind of frame, including
audio/video/metadata


"""


class Frame (object):

    def __init__(self, sec, msec, size_in_bytes, codec, type, width, height,
                 motion, extension):
        self.time = datetime.datetime.utcfromtimestamp(sec)
        self.time += datetime.timedelta(milliseconds=msec)
        self.size_in_bytes = size_in_bytes
        self.width = width
        self.height = height
        self.motion = motion
        self.extension = extension

        # following variables should use enum to implement
        self.codec = codec
        self.type = type

    def __str__(self):
        tVUExt = self.extension.tVUExt

        time = "%26s" % str(self.time)
        dimension = "%4dx%4d" % (self.width, self.height)
        frametype = "[%s]" % self.type
        framesize = "%9s" % human_readable_size(self.size_in_bytes)
        codec = self.codec
        eptzoffxy = (tVUExt.tCapWinInfo.wOffX, tVUExt.tCapWinInfo.wOffY)
        eptzcapwh = (tVUExt.tCapWinInfo.wCapW, tVUExt.tCapWinInfo.wCapH)
        eptzcropwh = (tVUExt.tCapWinInfo.wCropW, tVUExt.tCapWinInfo.wCropH)
        eptzinfo = "%s, %s, %s" % (eptzoffxy, eptzcapwh, eptzcropwh)

        frameinfo = (time, dimension, frametype, framesize, codec, eptzinfo,
                     self.motion)

        return "%s, %s, %s, %s, %s, %s, %s" % frameinfo

    """ Use `is_audio()` to determine if this frame is audio frame"""
    def is_audio(self):
        audio_codecs = ['G711', 'G726', 'GAMR', 'AAC4']
        if self.codec in audio_codecs:
            return True

        return False

    """ Use `is_video()` to determine if this frame is video frame"""
    def is_video(self):
        video_codecs = ['HEVC', 'H264', 'MPEG4', 'JPEG']
        if self.codec in video_codecs:
            return True

        return False

    """ Use `is_meta()` to determine if this frame is meta frame"""
    def is_meta(self):
        raise NotImplemented()

    def add_rawdata(self, rawdata, size):
        self.rawdata = rawdata
        self.raw_size = size
