# -*- coding: utf-8 -*-

import pytest

from YNM.camera.camera import Camera
from YNM.camera.service.streaming import DataBrokerStreaming
from YNM.camera.service.config import Configer
from YNM.camera.service.snapshot import Snapshot
from YNM.camera.service.ptz import PTZ
from YNM.camera.service.privacy import Privacy
from YNM.camera.service.motion import Motion
import setting


@pytest.fixture(scope="session")
def configs():
    ''' Return DUT (Device Under Test) config '''
    return setting.config


@pytest.fixture(scope="session")
def cam(configs):
    ''' Create camera object for you '''
    cam = Camera(configs)
    return cam


@pytest.fixture
def streaming(cam):
    ''' Create streaming service for you'''
    return DataBrokerStreaming(cam)


@pytest.fixture
def snapshot(cam):
    ''' Create snapshot service for you'''
    return Snapshot(cam)


@pytest.fixture
def configer(cam):
    ''' Create configer service for you '''
    return Configer(cam)


@pytest.fixture
def ptz(cam):

    ''' Create PTZ object for you '''

    return PTZ(cam)


@pytest.fixture
def motion(cam):

    ''' Create motion object for you '''

    return Motion(cam)


@pytest.fixture
def cmosfreq_50hz_with_60hz_fin(cam, request, configer):

    ''' Set CMOS freq to 50Mhz. Will auto change to 60Hz after test case '''

    def freq_change_generator(freq, maxfps):
        def changer():
            caps = cam.capability
            channels = range(0, caps.nvideoin)
            streams = range(0, int(caps.nmediastream))
            codecs = caps.videoin.codec
            changeset = ''
            for channel in channels:
                for stream in streams:
                    for codec in codecs:
                        changeset += 'videoin_c%d_cmosfreq=%d&' % (channel,
                                                                   freq)
                        changeset += 'videoin_c%d_s%d_%s_maxframe=%d&' % \
                            (channel, stream, codec, maxfps)

            print 'changeset %s' % changeset
            configer.set(changeset)

        return changer

    f = freq_change_generator(freq=50, maxfps=25)
    f()

    caps = cam.capability
    maxframe = caps.videoin.maxframerate[0]
    fin = freq_change_generator(freq=60, maxfps=maxframe)
    request.addfinalizer(fin)


@pytest.fixture
def orientation0_ch0(cam, configer):

    ''' Set ch0 orientation to 0. Will NOT auto revert back to original
    orientation. '''

    configer.set('videoin_c0_rotate=0')


@pytest.fixture
def orientation90_ch0(cam, configer):

    ''' Set ch0 orientation to 90. Will NOT auto revert back to original
    orientation. '''

    configer.set('videoin_c0_rotate=90')


@pytest.fixture
def pmask(cam, configer):

    ''' Generate privacy object automatically for you. '''

    return Privacy(cam)


@pytest.fixture
def no_timestamp(configer, request):

    ''' Turn off timesatmp. Useful for some OCR test case. Will auto revert back
    to original after test '''

    def turn_on_timestamp():
        configer.set('videoin_c0_imprinttimestamp=1')

    c = configer.get('videoin_c0_imprinttimestamp')
    if str(c.videoin.c[0].imprinttimestamp) == '1':
        configer.set('videoin_c0_imprinttimestamp=0')
        request.addfinalizer(turn_on_timestamp)


@pytest.fixture
def brightness100_contrast50(configer, request):

    ''' Set brightness to 100 and contrast to 50. This will make some image
    recognition more easily. Will auto revert back to brightness=0 contrast=50
    after test case  '''

    brightness_100 = 'image_c0_brightnesspercent=100'
    brightness_50 = 'image_c0_brightnesspercent=50'
    contrast_0 = 'image_c0_contrastpercent=0'
    contrast_50 = 'image_c0_contrastpercent=50'

    def restore_brightness_contrast():
        print 'Teardown!!!'
        teardown = brightness_50 + '&' + contrast_50
        configer.set(teardown)

    request.addfinalizer(restore_brightness_contrast)
    setup = brightness_100 + '&' + contrast_0
    configer.set(setup)
