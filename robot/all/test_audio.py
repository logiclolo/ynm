# -*- coding: utf-8 -*-

from fixture import *
from time import sleep
from YNM.camera.frame.filter import Filter, audio_filter, CodecFilter


@pytest.mark.audio
def test_all_audio_codec_bitrate_change_and_match(streaming, configer):

    # Test camera bitrate by ALL audio codec type that could be changed
    # successfully and match expected bitrate

    def helper_general_codec_bitrate_change_and_match(streaming,
                                                    configer, codec, bitrates):
        supported_bitrates = bitrates

        # enable audio and set codec type
        configer.set('audioin_c0_mute=0&audioin_c0_s0_codectype=%s' % codec)

        for bitrate in supported_bitrates:
            # currently all products support only 1 audio stream
            # we just simply change audioin_c0_s0_<codec>_bitrate
            configer.set('audioin_c0_s0_%s_bitrate=%d' % (codec, bitrate))
            sleep(2)

            streaming.connect()

            measure = Filter('measure')
            audio_codec = CodecFilter(codec)
            audio_measure = audio_filter + audio_codec + measure

            for i in range(0, 100):
                streaming.get_one_frame(audio_measure)

            rate_config = float(bitrate)
            rate_measure = float(measure.bitrate)
            assert rate_config * 0.95 <= rate_measure <= rate_config * 1.05, \
                "%s audio bitrate doesn't match. Exp %d, Act %f" % (codec, bitrate,
                                                                    measure.bitrate)

            streaming.disconnect()

    codec_bitrates = {
        'aac4': [16000, 32000, 48000, 64000, 96000, 128000],
        'gamr': [4750, 5150, 5900, 6700, 7400, 7950, 10200, 12200],
        'g726': [16000, 24000, 32000, 40000],
        'g711': None
    }

    c = configer.get('capability&audioin')
    supported_audio_codecs = c.capability.audioin.codec
    for codec in supported_audio_codecs:
        bitrates = codec_bitrates[codec]
        print 'codec %s' % codec
        if bitrates is None:
            continue  # currently only g711 bitrate is not configurable
        helper_general_codec_bitrate_change_and_match(streaming, configer,
                                                      codec, bitrates)


@pytest.mark.audio
def test_audio_codec_c0_s0_change_ok(cam, streaming, configer):

    # Test if camera is able to change audio codec

    if cam.capability.naudioin < 1:
        pytest.skip("This device doesn't support audio, skip this test")

    configer.set('audioin_c0_mute=0')

    supported_codecs = cam.capability.audioin.codec

    for codec in supported_codecs:
        configer.set('audioin_c0_s0_codectype=%s' % codec)
        codec_filter = CodecFilter(codec)
        sleep(4)
        streaming.connect()
        count = 0
        for frame_count in range(0, 30):
            f = streaming.get_one_frame(audio_filter)
            print f
            count += 1
            assert codec_filter.filter(f), "Codec change failed. Expected %s,\
                actual %s" % (codec, f.codec)
        streaming.disconnect()
