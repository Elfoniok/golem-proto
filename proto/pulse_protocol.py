import rlp
from devp2p.protocol import BaseProtocol, SubProtocolError
from ethereum import slogging

log = slogging.get_logger('protocol.csp')


class PulseProtocolError(SubProtocolError):
    pass


class PulseProtocol(BaseProtocol):

    """
    Protocol that allows to send numbered pings
    """

    protocol_id = 7367795 # "pls"
    network_id = 0
    max_cmd_id = 1
    name = 'pls'
    version = 1

    def __init__(self, peer, service):
        # required by P2PProtocol
        self.config = peer.config
        BaseProtocol.__init__(self, peer, service)

    class pulse(BaseProtocol.command):
        cmd_id = 0
        sent = False

        structure = [
            ('pulse_number', rlp.sedes.big_endian_int)]

        def create(self, n):
            self.sent = True
            return [n]

