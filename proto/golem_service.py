from devp2p.service import WiredService
from golem_protocol import GolemProtocol
from ethereum import slogging

import gevent
import cron

import datetime

log = slogging.get_logger('golem.service')

GC_ANN_AFTER=12

class GolemService(WiredService):

    name = 'golem'
    default_config = dict(
        golem=dict(
            network_id = 0,
            announcement = False
        )
    )

    known_announcements = {}
    commitments = []

    # required by WiredService
    wire_protocol = GolemProtocol  # create for each peer

    def __init__(self, app):
        log.info("Golem service init")
        self.bcast = app.services.peermanager.broadcast

        self.cfg = app.config['golem']
        log.info("do announcement: {}".format(self.cfg['announcement']))
        self.do_publish = self.cfg['announcement']
        super(GolemService, self).__init__(app)
        if self.do_publish:
            ann = (1, "some text", "some peers", 100, "my own public key", "signature")
            cron.apply_after(10, self.announce_task, ann)

    def on_wire_protocol_start(self, proto):
        log.debug('----------------------------------')
        log.debug('on_wire_protocol_start', proto=proto)
        assert isinstance(proto, self.wire_protocol)
        # register callbacks
        proto.receive_announcement_callbacks.append(self.on_receive_announcement)

    def on_wire_protocol_stop(self, proto):
        assert isinstance(proto, self.wire_protocol)
        log.debug('----------------------------------')
        log.debug('on_wire_protocol_stop', proto=proto)

    def on_receive_announcement(self, proto, announcement_id, utc_time, allowed_peers, max_price, requestor_id, signature):
        ann = (announcement_id, utc_time, allowed_peers, max_price, requestor_id, signature)
        self.maybe_rebroadcast_announcement(proto, ann)

    def announce_task(self, ann, origin=None):
        ann_short = shorten(ann)
        log.debug("announce task: {}".format(ann_short))
        self.known_announcements[ann_short] = datetime.datetime.utcnow()
        cron.apply_after(GC_ANN_AFTER, self.gc_ann, ann_short)
        self.bcast(GolemProtocol,
                   'announcement',
                   args=ann,
                   exclude_peers=[origin.peer] if origin else [])

    def maybe_rebroadcast_announcement(self, proto, ann):
        ann_short = shorten(ann)
        # FIXME: don't rebroadcast if abs(t(ann)-now())>1min
        if self.known_announcements.has_key(ann_short):
            log.debug("known announcement, skip {}".format(ann_short))
            pass
        else:
            self.announce_task(ann, origin=proto)

    def gc_ann(self, ann_short):
        log.debug("cleanup announcements {}".format(ann_short))
        self.known_announcements.pop(ann_short)

def shorten(ann):
    (announcement_id, utc_time, allowed_peers, max_price, requestor_id, signature) = ann
    return requestor_id, announcement_id, allowed_peers
