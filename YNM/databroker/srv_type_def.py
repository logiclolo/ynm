from enum import Enum

# --- TProtocolType --- #
class TProtocolType(Enum):
    eptHTTP = 0
    eptTCP = 1
    eptUDP = 2
    eptMULTICAST = 3
    eptScalableMULTICAST = eptMULTICAST = 4
    eptBackchannelMULTICAST = 5
    def __str__(self):
        return str(self.name)[3:]


# --- TMediaType --- #
class TMediaType(Enum):
    emtAudio = 1
    emtVideo = 2
    emtTransmitAudio = 4
    emtMetaData = 8


#def get_protocol(protocol):
#    if protocol.lower() == 'tcp':
#        return eptHTTP
#    elif protocol.lower() == 'udp':
#        return eptUDP
#    elif protocol.lower() == 'http':
#        return eptHTTP
#    elif protocol.lower() == 'multicast':
#        return eptMULTICAST
#    else:
#        return False
#
#
#def get_media_type(media_type):
#    if media_type.lower() == 'video':
#        return emtVideo
#    elif media_type.lower() == 'audio':
#        return emtAudio
#    elif media_type.lower() == 'metadata':
#        return emtMetaData
#    else:
#        return False
