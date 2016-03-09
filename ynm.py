#!/usr/local/bin/python-2.7.7-32bits

# -*- coding: utf-8 -*-

from YNM.camera.camera import Camera
from YNM.camera.service.streaming import DataBrokerStreaming
from YNM.camera.frame.filter import Filter, keyframe_filter, video_filter, audio_filter, increasing_filter, decreasing_filter
from YNM.camera.frame.catcher import Catcher
import sys
import argparse
import signal
import itertools


# http://stackoverflow.com/questions/4205317/capture-keyboardinterrupt-in-python-without-try-except
def signal_handler(signal, frame):
    sys.stderr.write("Program exit.")
    sys.exit(0)


default_playback_time = 3
default_playback_frames = 100
default_profile = '0'

signal.signal(signal.SIGINT, signal_handler)
parser = argparse.ArgumentParser(description='YaoNiMing usage')
parser.add_argument('URL')
parser.add_argument('-u', '--user', help='username')
parser.add_argument('-p', '--passwd', help='password')
parser.add_argument('-v', '--verbose', help='Verbose', action='count')
parser.add_argument('-t', '--time', help='Playback time, in seconds', default=default_playback_time, type=int)
parser.add_argument('-f', '--frames', help='Playback frames', default=default_playback_frames, type=int)
parser.add_argument('-o', '--profile', help='set streaming index', default=default_profile, type=str)
args = parser.parse_args()

if args.time != default_playback_time:
    args.frames = 0
elif args.frames != default_playback_frames:
    args.time = 0


cam = None
try:
    config = {'ip': args.URL, 'user': args.user, 'passwd': args.passwd}
    cam = Camera(config)
except Exception as e:
    print e
    sys.exit(1)

streaming = DataBrokerStreaming(cam)
streaming.connect()

if args.profile != default_profile:
    print 'set profile to %s' % args.profile
    streaming.setprofile(args.profile)

# key frame first then video
video_keyframe_filter = keyframe_filter + video_filter
video_increasing_filter = video_filter + increasing_filter
video_decreasing_filter = video_filter + decreasing_filter
video_nojumpforward_filter = video_filter + Filter("timenojumpforward")
video_decreasing_catcher = Catcher(video_decreasing_filter)
measurev = Filter('measure')
measurea = Filter('measure')
measure = Filter('measure')

video_measure = video_filter + measurev
audio_measure = audio_filter + measurea

msg = ''
spinner = itertools.cycle(['-', '/', '|', '\\'])
sys.stderr.write("playing... ")
f = None
marker = ""
fps = 0
bitrate = None

while streaming.connected():
    f = None
    try:
        f = streaming.get_one_frame(measure)
        if f.is_audio():
            audio_measure.filter(f)
        elif f.is_video():
            video_measure.filter(f)
    except Exception as e:
        print "%s" % e
        sys.exit(0)

    if video_decreasing_filter.filter(f) is True:
        marker = "* "
    else:
        marker = ""

    if args.frames > 0 and measure.frames >= args.frames:
        break

    if args.time > 0 and measure.played >= args.time:
        break

    if f.is_audio():
        fps = measurea.fps
        bitrate = measurea.bitrate
    elif f.is_video():
        fps = measurev.fps
        bitrate = measurev.bitrate
    msg = "%sfps %2s, bitrate %8sps, %s" % (marker, fps, bitrate, f)

    if args.verbose is None:
        sys.stderr.write(spinner.next())
        sys.stderr.flush()
        sys.stderr.write('\b')
    else:
        sys.stderr.write("%s\n" % msg)

frame_count = measurev.frames
played = measure.played
print "\nPlayed for %d frames, %d seconds.\n  %s, %s, %s %s" % (frame_count, played, cam.model, cam.macaddress, cam.fwversion, msg)
