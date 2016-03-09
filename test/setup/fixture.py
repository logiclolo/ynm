# -*- coding: utf-8 -*-

import pytest

from YNM.camera.camera import Camera
from YNM.camera.service.streaming import DataBrokerStreaming
from YNM.camera.service.config import Configer
from YNM.camera.service.snapshot import Snapshot

import setting


@pytest.fixture(scope="session")
def configs():
    return setting.config


@pytest.fixture(scope="session")
def cam(configs):
    cam = Camera(configs)
    return cam


@pytest.fixture
def streaming(cam):
    return DataBrokerStreaming(cam)


@pytest.fixture
def snapshot(cam):
    return Snapshot(cam)


@pytest.fixture
def configer(cam):
    return Configer(cam)


@pytest.fixture
def cmosfreq_50hz_with_60hz_fin(cam, request, configer):
    caps = cam.capability
    channels = range(0, caps.nvideoin)

    for channel in channels:
        configer.set('videoin_c%d_cmosfreq=%d' % (channel, 50))

    def fin():
        # revert back to 60Hz settings
        streams = int(caps.nmediastream)
        codecs = caps.videoin.codec
        maxframe = caps.videoin.maxframerate[0]
        configer.set('videoin_c%d_cmosfreq=%d' % (channel, 60))
        changeset = ''
        for stream in range(0, streams):
            for codec in codecs:
                changeset += 'videoin_c%d_s%d_%s_maxframe=%d&' % (channel, stream, codec, maxframe)

        configer.set(changeset)

    request.addfinalizer(fin)
