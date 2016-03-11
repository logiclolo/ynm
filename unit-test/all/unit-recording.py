# -*- coding: utf-8 -*-

from YNM.camera.service.recording import EdgeRecording
from fixture import *
import mock


def test_edge_recording_status(cam):
    mget = mock.MagicMock()
    response = mock.MagicMock()
    response.content = '<?xml version="1.0" encoding="ISO-8859-1"?><stormgr version="1.0.9.20"><disk><i0><cond>detached</cond><dbcond>notready</dbcond><totalsize>0</totalsize><freespace>0</freespace><usedspace>0</usedspace></i0></disk><statusCode>200</statusCode><statusString>OK</statusString></stormgr>'
    response.status_code = 200
    mget.return_value = response
    p1 = mock.patch('requests.get', new=mget)
    p1.start()

    edge_rec = EdgeRecording(cam)

    assert edge_rec.status() == "detached", "Storage status incorrect, exp\
           'detached', act '%s'" % edge_rec.status()
    assert edge_rec.capacity() == 0, "Storage capacity incorrect, exp '0', act\
           '%d'" % edge_rec.capacity()
    assert edge_rec.availablesize() == 0, "Storage availablesize incorrect, exp\
           '0', act '%d'" % edge_rec.availablesize()
    assert edge_rec.usedsize() == 0, "Storage usedsize incorrect, exp '0', act\
           '%d'" % edge_rec.usedsize()
    assert edge_rec.location() == cam.url + '/disk0', "Storage location\
           incorrect, exp %s, act %s" % (cam.url + '/disk0',
                                         edge_rec.location())

    p1.stop()
