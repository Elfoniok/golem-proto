from devp2p.service import WiredService
from pulse_protocol import PulseProtocol
from ethereum import slogging

log = slogging.get_logger('casper')


class PulseService(WiredService):

    name = 'pulse'
    default_config = dict(
        casper=dict(
            network_id=0,
            epoch_length=100
        )
    )

    # required by WiredService
    wire_protocol = PulseProtocol  # create for each peer

    def __init__(self, app):
        log.info("Pulse service init")
        self.bcast = app.services.peermanager.broadcast

        self.cfg = app.config['pulse']
        self.max_n = self.cfg['count_to']

        super(PulseService, self).__init__(app)

    def on_wire_protocol_start(self, proto):
        log.debug('----------------------------------')
        log.debug('on_wire_protocol_start', proto=proto)
        assert isinstance(proto, self.wire_protocol)
        # register callbacks
        proto.receive_pulse_callbacks.append(self.on_receive_pulse)

        proto.send_pulse(self.cfg['count_from'])

    def on_wire_protocol_stop(self, proto):
        assert isinstance(proto, self.wire_protocol)
        log.debug('----------------------------------')
        log.debug('on_wire_protocol_stop', proto=proto)

    def on_receive_pulse(self, number):
        print "got {}".format(number)

    def broadcast_prepare(self, n, origin=None):
        self.bcast(PulseProtocol,
                   'pulse',
                   args=(n),
                   exclude_peers=[origin.peer] if origin else [])
