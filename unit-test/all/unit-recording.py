# -*- coding: utf-8 -*-

from YNM.camera.service.recording import EdgeRecording, VideoTrack, AudioTrack
from YNM.camera.service.recording import VideoFile, TextFile, SnapFile
from YNM.camera.service.recording import time_convert
import mock
import pytest


@pytest.mark.recording
def test_edge_recording_status():
    cam = mock.MagicMock()
    mget = mock.MagicMock()
    response = mock.MagicMock()
    response.content = '<?xml version="1.0" encoding="ISO-8859-1"?>\
        <stormgr version="1.0.9.20"><disk><i0><cond>detached</cond>\
        <dbcond>notready</dbcond><totalsize>0</totalsize>\
        <freespace>0</freespace><usedspace>0</usedspace></i0></disk>\
        <statusCode>200</statusCode><statusString>OK</statusString></stormgr>'
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


def mock_recording_init():
    cam = mock.MagicMock()
    mget = mock.MagicMock()

    status = mock.MagicMock()
    status.status_code = 200
    status.content = '<?xml version="1.0" encoding="ISO-8859-1"?>\
        <stormgr version="1.0.9.20"><disk><i0><cond>detached</cond>\
        <dbcond>notready</dbcond><totalsize>0</totalsize>\
        <freespace>0</freespace><usedspace>0</usedspace></i0></disk>\
        <statusCode>200</statusCode><statusString>OK</statusString></stormgr>'

    mget.return_value = status
    p1 = mock.patch('requests.get', new=mget)
    p1.start()

    edge_rec = EdgeRecording(cam)

    p1.stop()
    return edge_rec


@pytest.mark.recording
def test_edge_nativeapi_search():
    mget = mock.MagicMock()
    psr = mock.MagicMock()
    getfiles = mock.MagicMock()

    response = mock.MagicMock()
    response.status_code = 200
    response.content = '<?xml version="1.0" encoding="ISO-8859-1"?>\
        <stormgr version="1.0.9.20"><statusCode>200</statusCode>\
        <statusString>OK</statusString><root>\
        <slices>\
        <label>s1</label>\
        <recordingToken>64079596710121389635</recordingToken>\
        <islocked>0</islocked>\
        <sliceStart>2016-02-07T14:44:42.000Z</sliceStart>\
        <sliceEnd>2016-02-08T09:32:47.000Z</sliceEnd>\
        </slices>\
        <slices>\
        <label>s2</label>\
        <recordingToken>64079596710121389635</recordingToken>\
        <islocked>0</islocked>\
        <sliceStart>2016-02-15T06:34:04.206Z</sliceStart>\
        <sliceEnd>2016-02-18T03:19:42.782Z</sliceEnd>\
        </slices>\
        </root></stormgr>'
    tracks = []
    time = ('2016-02-15T06:34:04.206Z', '2016-02-18T03:19:42.782Z')
    tracks.append(VideoTrack('H265', 'videotest', time))
    tracks.append(AudioTrack('G711', 'audiotest', time))

    files = []
    vpath = '/mnt/auto/CF/NCMF//20160215/14/IZ9361_rec-34.mp4'
    spath = '/mnt/auto/CF/NCMF//20160215/14/ss1.jpg'
    tpath = '/mnt/auto/CF/NCMF//20160215/14/abc.log'
    files.append(VideoFile(1, 'seq', vpath, 0, time))
    files.append(SnapFile(1, 'seq', spath))
    files.append(TextFile(1, 'seq', tpath))

    mget.return_value = response
    psr.return_value = tracks
    getfiles.return_value = files

    edge = mock_recording_init()

    p1 = mock.patch('requests.get', new=mget)
    p2 = mock.patch(
        'YNM.camera.service.recording.EdgeRecording.get_tracks', new=psr)
    p3 = mock.patch(
        'YNM.camera.service.recording.EdgeRecording.get_files', new=getfiles)

    plist = [p1, p2, p3]

    for p in plist:
        p.start()

    # search criteria 1
    criteria = {
        'mediatype': 'videoclip',
        'triggertype': ['VADP', 'di'],
        'starttime': '2016-02-01T12:34:56.789Z',
        'endtime': '2016-02-19T12:00:00.000Z',
    }
    slices = edge.search(criteria)

    for p in plist:
        p.stop()

    assert slices[0]['recordingToken'] == '64079596710121389635',\
        "Search recTokn incorrect, exp '64079596710121389635', act '%s'"\
        % slices[0]['recordingToken']

    assert slices[0]['sliceStart'] == time_convert('2016-02-07T14:44:42.000Z'),\
        "Search sliceStart incorrect, exp '%s', act '%s'"\
        % (time_convert('2016-02-07T14:44:42.000Z'), slices[0]['sliceStart'])

    assert slices[0]['tracks'][0].content_type() == 'video/H265',\
        "Search tracks type incorrect, exp 'video/H265', act '%s'"\
        % slices[0]['tracks'][0].content_type()

    assert slices[0]['tracks'][1].content_type() == 'audio/G711',\
        "Search tracks type incorrect, exp 'video/H265', act '%s'"\
        % slices[0]['tracks'][1].content_type()

    assert slices[0]['files'][0].path() == vpath,\
        "Search tracks type incorrect, exp '%s', act '%s'"\
        % (vpath, slices[0]['files'][0].path())

    assert slices[0]['files'][1].path() == spath,\
        "Search tracks type incorrect, exp '%s', act '%s'"\
        % (spath, slices[0]['files'][1].path())


@pytest.mark.recording
def test_get_tracks():
    res = mock.MagicMock()

    res.return_value.status_code = 200
    res.return_value.content = '<?xml version="1.0" encoding="ISO-8859-1"?>\
        <stormgr version="1.0.9.20"><statusCode>200</statusCode>\
        <statusString>OK</statusString>\
        <root><recording><i0>\
        <recordingToken>07327823181623539486</recordingToken>\
        <from>2016-03-04T03:24:26.598Z</from>\
        <until>2016-03-04T03:25:32.093Z</until>\
        <backup>0</backup><trackAttributes>\
        <i0><trackInformation><trackToken>a9486-28</trackToken>\
        <trackType>Audio</trackType><description>Description</description>\
        <dataFrom>2016-03-04T03:24:26.598Z</dataFrom>\
        <dataTo>2016-03-04T03:25:32.093Z</dataTo></trackInformation>\
        <audioAttributes><bitrate>3.15</bitrate><encoding>G711</encoding>\
        <samplerate>8</samplerate></audioAttributes></i0>\
        <i1><trackInformation><trackToken>v9486-29</trackToken>\
        <trackType>Video</trackType><description>Description</description>\
        <dataFrom>2016-03-04T03:24:26.598Z</dataFrom>\
        <dataTo>2016-03-04T03:25:32.093Z</dataTo></trackInformation>\
        <videoAttributes><bitrate>4538.00</bitrate>\
        <width>600</width><height>800</height><encoding>H265</encoding>\
        <framerate>29.90</framerate></videoAttributes></i1>\
        </trackAttributes><trackNum>2</trackNum>\
        </i0></recording><recordingNum>1</recordingNum></root></stormgr>'

    edge = mock_recording_init()

    p1 = mock.patch('requests.get', new=res)
    p1.start()

    slice = {
        'sliceStart': '2016-03-04T03:24:26.598Z',
        'sliceEnd': '2016-03-04T03:25:32.093Z',
        'recordingToken': '07327823181623539486'
    }

    command = {'cmd': 'getmediaattr',
               'recToken': slice['recordingToken'],
               'recTime': slice['sliceStart']}
    tracks = edge.get_tracks(slice)
    url = edge._edgecgi
    res.assert_called_once_with(url, params=command, auth=edge._auth)

    p1.stop()

    starttime = time_convert(slice['sliceStart'])
    endtime = time_convert(slice['sliceEnd'])
    assert tracks[0].content_type() == 'audio/G711',\
        "Search tracks type incorrect, exp 'audio/G711', act '%s'"\
        % tracks[0].content_type()
    assert tracks[0].time() == (starttime, endtime),\
        "Search tracks type incorrect, exp '(%s, %s)', act '%s'"\
        % (starttime, endtime, tracks[0].time())
    assert tracks[1].content_type() == 'video/H265',\
        "Search tracks type incorrect, exp 'video/H265', act '%s'"\
        % tracks[1].content_type()
    assert tracks[1].time() == (starttime, endtime),\
        "Search tracks type incorrect, exp '(%s, %s)', act '%s'"\
        % (starttime, endtime, tracks[1].time())


@pytest.mark.recording
def test_get_files():
    res = mock.MagicMock()
    res.return_value.status_code = 200
    res.return_value.content = '<?xml version="1.0" encoding="ISO-8859-1"?>\
    <stormgr version="1.0.9.20"><counts>2</counts>\
    <i0><label>2</label><triggerType>seq</triggerType>\
    <mediaType>videoclip</mediaType>\
    <destPath>/mnt/auto/CF/NCMF//20160215/14/IZ9361_rec-34.mp4</destPath>\
    <resolution>1920x1080</resolution><isLocked>0</isLocked>\
    <triggerTime>2016-02-15 14:34:04.206</triggerTime>\
    <beginTime>2016-02-15 14:34:04.206</beginTime>\
    <endTime>2016-02-15 14:44:04.055</endTime>\
    <dst>0</dst><tz>320</tz><backup>0</backup><seamless>0</seamless></i0>\
    <i1><label>3</label><triggerType>seq</triggerType>\
    <mediaType>videoclip</mediaType>\
    <destPath>/mnt/auto/CF/NCMF//20160215/14/IZ9361_rec-44.mp4</destPath>\
    <resolution>1920x1080</resolution><isLocked>0</isLocked>\
    <triggerTime>2016-02-15 14:44:04.055</triggerTime>\
    <beginTime>2016-02-15 14:44:04.055</beginTime>\
    <endTime>2016-02-15 14:54:04.320</endTime>\
    <dst>0</dst><tz>320</tz><backup>0</backup><seamless>0</seamless></i1>\
    <statusCode>200</statusCode><statusString>OK</statusString></stormgr>'

    edge = mock_recording_init()

    p1 = mock.patch('requests.get', new=res)
    p1.start()

    slice = {
        'recordingToken': '07327823181623539486',
        'sliceStart': '2016-02-15 14:34:04.206',
        'sliceEnd': '2016-02-15 14:54:04.320'
    }

    files = edge.get_files(slice, mediaType="videoclip")

    starttime = time_convert(slice['sliceStart'])
    middletime = time_convert('2016-02-15 14:44:04.055')
    endtime = time_convert(slice['sliceEnd'])

    assert files[0].time() == (starttime, middletime),\
        "Search files incorrect, exp '(%s, %s)', act '%s'"\
        % (middletime, endtime, files[0].time())

    assert files[1].time() == (middletime, endtime),\
        "Search files incorrect, exp '(%s, %s)', act '%s'"\
        % (middletime, endtime, files[1].time())

    p1.stop()
