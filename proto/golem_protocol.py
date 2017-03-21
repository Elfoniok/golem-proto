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
        Note: this message will be implemented on Ethereum instead!

        Task announcement. This message should be routed by nodes to flood
        the network. Every particular (requestor_id, announcement_id, allowed_peers)
        combination should be broadcasted to node's peers only once.

        Two separate keys are using.
        * one is for devp2p encryption and node identification
        * other is for Ethereum accounts and signatures
        This is required because of need to be able to use single Ethereum account
        for multiple Golem nodes.
        """
        cmd_id = 0

        structure = [
            ('utc_time', rlp.sedes.binary), # string with ISO 8601 time representation
            ('price', rlp.sedes.big_endian_int), # GNT in wei
            ('requestor_id', rlp.sedes.binary), # Ethereum address
            ('node_id', rlp.sedes.binary), # requestor devp2p node id
            ('node_address', rlp.sedes.raw), # req node (address,port)
            ('announcement_hash', rlp.sedes.big_endian_int), # hash of fields above
            ('allowed_peers', rlp.sedes.binary),
            ('signature', rlp.sedes.binary) # signed with Ethereum private key
        ]

    class offer(BaseProtocol.command):
        """
        To accept offer, requestor should reply with 'acceptance'.
        Otherwise 'offer' is considered non-binding after 10 seconds.

        """
        cmd_id = 1

        structure = [
            ('announcement_hash', rlp.sedes.big_endian_int),
            ('provider_id', rlp.sedes.binary), # Ethereum address
            ('offer_hash', rlp.sedes.big_endian_int), # hash of fields above
            ('signature', rlp.sedes.binary) # signed with Ethereum private key
        ]

    class acceptance(BaseProtocol.command):
        """
        Acceptance: message that seals the contract between
        provider and requestor
        """
        cmd_id = 2

        structure = [
            ('offer_hash', rlp.sedes.big_endian_int),
            ('acceptance_hash', rlp.sedes.big_endian_int), # hash of fields above
            ('signature', rlp.sedes.binary) # signed with Ethereum private key
        ]
