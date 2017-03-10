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

    protocol_id = 56469 # just a random number; not sure what to put here
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

        def create(self, proto, n):
            self.sent = True
            return dict(pulse_number=n)
