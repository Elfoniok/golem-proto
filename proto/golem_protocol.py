import rlp
from devp2p.protocol import BaseProtocol, SubProtocolError
from ethereum import slogging

log = slogging.get_logger('golem.protocol')


class GolemProtocolError(SubProtocolError):
    pass


class GolemProtocol(BaseProtocol):

    """
    Golem protocol.

    Assumptions:
    """

    protocol_id = 18317 # just a random number; not sure what to put here
    network_id = 0
    max_cmd_id = 10
    name = 'golem'
    version = 1

    def __init__(self, peer, service):
        # required by P2PProtocol
        self.config = peer.config
        BaseProtocol.__init__(self, peer, service)

    class announcement(BaseProtocol.command):
        """
        Task announcement. This message should be routed by nodes to flood
        the network. Every particular (requestor_id, announcement_id, allowed_peers)
        combination should be broadcasted to node's peers only once.
        """
        cmd_id = 0

        structure = [
            ('announcement_id', rlp.sedes.big_endian_int),
            ('utc_time', rlp.sedes.binary), # string with ISO 8601 time representation
            ('allowed_peers', rlp.sedes.binary),
            ('max_price', rlp.sedes.big_endian_int), # GNT in wei
            ('requestor_id', rlp.sedes.binary),
            ('signature', rlp.sedes.binary) # signed with Ethereum private key
        ]

    class offer(BaseProtocol.command):
        """
        Proposal

        """
        cmd_id = 1

        structure = [
            ('prop_id', rlp.sedes.big_endian_int),
            ('prop_hash', rlp.sedes.binary),
            ('req_id', rlp.sedes.big_endian_int),
            ('price', rlp.sedes.big_endian_int), # GNT in wei
            ('signature', rlp.sedes.binary) # signed with Ethereum private key
        ]

    class acceptance(BaseProtocol.command):
        """
        Acceptance: message that seals the contract between
        provider and requestor
        """
        cmd_id = 2

        structure = [
            ('prop_id', rlp.sedes.big_endian_int),
            ('req_id', rlp.sedes.big_endian_int),
            ('price', rlp.sedes.big_endian_int), # GNT in wei
            ('signature', rlp.sedes.binary) # signed with Ethereum private key
        ]
