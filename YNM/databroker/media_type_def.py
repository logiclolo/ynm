from enum import Enum

# --- enumerations for TMediaDBFrameType --- #
class TMediaDBFrameType(Enum):
    (MEDIADB_FRAME_INTRA, MEDIADB_FRAME_PRED, MEDIADB_FRAME_BIPRED) = (0, 1, 2)
    def __str__(self):
        return str(self.name[14:15])

# --- EMediaCodecType: The media codec type --- #
class EMediaCodecType(Enum):
    mctJPEG = 0x0001        # the codec type is JPEG (image, video)
    mctH263 = 0x0002        # the codec type is H263 (video)
    mctMP4V = 0x0004        # the codec type is MPEG-4 video (video)
    mctH264 = 0x0008        # the codec type is H264 video (video)
    mctHEVC = 0x0010        # the codec type is H265 video (video)
    mctDMYV = 0x00FF        # the codec type is DMYV video dummy (video) */ //bruce add for video dummy codec 20061013
    mctG7221 = 0x0100       # the codec type is G.722.1 (audio)
    mctG729A = 0x0200       # the codec type is G.729A (audio)
    mctAAC = 0x0400         # the codec type is AAC (audio)
    mctGAMR = 0x0800        # the codec type is AMR (audio)
    mctSAMR	= 0x1000
    mctG711 = 0x2000
    mctG711A = 0x4000
    mctG726 = 0x8000
    mctDMYA = 0xFF00        # the codec type is DMYA audio dummy (audio) */ //bruce add for audio dummy codec 20061013
    mctIVA1 = 0x010000      # the codec type is IVA (intelligent video)
    mctMETX = 0x020000
    mctALLCODEC = 0xFFFFFFFF

    def __str__(self):
        return str(self.name)[3:]

