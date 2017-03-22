from golem_protocol import GolemProtocol
from task import Task, Announcement

from ethereum.utils import encode_hex, decode_hex

from devp2p.service import WiredService
import devp2p.discovery

import gevent
import random
import cron
from devp2p.crypto import privtopub

import datetime

from ethereum import slogging
log = slogging.get_logger('golem.service')

GC_ANN_AFTER=12
OFFERS_COLLECTION_TIMEOUT=10
OFFER_LOCK_TIMEOUT=10

class GolemService(WiredService):

    name = 'golem'
    default_config = dict(
        golem=dict(
            network_id = 0,
            announcement = False,
            min_price = 1,
            privkey_hex = None,
            pubkey_hex = None
        )
    )

    # provider
    offer = None # your offer that correspond to some announcement
    ann = None
    # requestor
    my_announcements = [] # tasks owned by this node
    # everyone
    known_announcements = {} # task announcements broadcasted though the network

    # required by WiredService
    wire_protocol = GolemProtocol  # create for each peer

    def __init__(self, app):
        log.info("Golem service init")
        self.bcast = app.services.peermanager.broadcast
        self.app = app
        self.cfg = app.config['golem']
        self.node_id = app.config['node']['id']
        assert self.cfg['privkey_hex']
        assert self.cfg['pubkey_hex']
        log.info("do announcement: {}".format(self.cfg['announcement']))
        self.do_publish = self.cfg['announcement']
        super(GolemService, self).__init__(app)

        # setup nodeid based on privkey
        if 'id' not in self.config['p2p']:
            self.id = privtopub(
                self.config['node']['privkey_hex'].decode('hex'))
        else:
            self.id = self.config['p2p']['id']

        if self.do_publish:
            cron.apply_after(10, self.create_task, 100)

    def on_wire_protocol_start(self, proto):
        log.debug('----------------------------------')
        log.debug('on_wire_protocol_start', proto=proto)
        assert isinstance(proto, self.wire_protocol)
        # register callbacks
        proto.receive_announcement_callbacks.append(self.on_receive_announcement)
        proto.receive_offer_callbacks.append(self.on_receive_offer)
        # log.info("peers: {}".format(self.app.services.peermanager.peers))

    def on_wire_protocol_stop(self, proto):
        assert isinstance(proto, self.wire_protocol)
        log.debug('----------------------------------')
        log.debug('on_wire_protocol_stop', proto=proto)

    def on_receive_announcement(self, proto, utc_time, price, requestor_id,
                                node_id, node_address, announcement_hash, allowed_peers,
                                signature):
        ann = (utc_time, price, requestor_id, node_id, node_address, announcement_hash,
               allowed_peers, signature)
        ann = Announcement.from_pack(*ann)
        log.info("received ann: {}".format(ann))
        self.maybe_rebroadcast_announcement(proto, ann)
        if not self.evaluate_ann(ann):
            log.info("skipping offer")
            return
        log.info("provider: going to place an bid at {}".format(ann.node_id))
        # TODO: Provider should have a more sophisticated way of dealing with
        # offers. E.g. not answer immediately and instead collect until deadline
        # and then only answer to the best ann
        gevent.sleep(random.random()*3) # to ease ddos a little
        peer = self.get_peer_by_node_id(self.get_peers(), node_id)
        pm = self.app.services.peermanager
        if peer is None:
            addr = ann.node_address
            res = pm.connect((addr.ip, addr.tcp_port), decode_hex(ann.node_id))
            if res:
                peer = self.get_peer_by_node_id(pm.peers, node_id)
        if peer is None:
            log.warning("failed to connect to {}".format(ann.node_id))
            return
        offer = self.create_offer(ann)
        if GolemProtocol in peer.protocols:
            proto = peer.protocols[GolemProtocol]
            proto.send_offer(*offer)
            self.ann = ann
            self.offer = offer
            self.ack = None
            cron.apply_after(OFFER_LOCK_TIMEOUT, self.mb_drop_obligation, offer)

    def get_peers(self):
        peers = self.app.services.peermanager.peers
        return peers

    def get_peer_by_node_id(self, peers, target):
        for peer in peers:
            enc = encode_hex(peer.remote_pubkey)
            if enc == target:
                return peer
        return None

    def get_peers(self):
        peers = self.app.services.peermanager.peers
        return peers

    def announce_task(self, ann, origin=None):
        ann_short = shorten(ann)
        log.debug("announce task: {}".format(ann_short))

    def mb_drop_obligation(self, offer):
        if self.ack is None:
            self.offer = None
            self.ann = None

    def evaluate_ann(self, ann):
        if ann.requestor_id == self.cfg['pubkey_hex']:
            return False
        if self.offer:
            return False
        return self.cfg['min_price'] < ann.task.price

    def create_offer(self, ann):
        offer_hash = 4
        return (ann.announcement_hash, self.cfg['pubkey_hex'],
                offer_hash, "signature")

    def on_receive_offer(self, proto, announcement_hash, provider_id,
                         offer_hash, signature):
        # check if known announcement_hash
        # check timeouts?
        # check signature
        # check price >= price
        # add offer to offers for this ann
        log.warning("got offer, not_impl")

    def create_task(self, price):
        tsk = Task(price)
        ip = self.app.config['discovery']['listen_host']
        port = self.app.config['discovery']['listen_port']
        ann = Announcement(tsk)
        ann.requestor_id = self.cfg['pubkey_hex']
        ann.node_address = devp2p.discovery.Address(ip, port)
        ann.node_id = encode_hex(self.app.config['node']['id'])
        log.warning("created ann: {}".format(ann))
        cron.apply_after(OFFERS_COLLECTION_TIMEOUT, self.process_offers, ann)
        self.my_announcements.append(ann)
        self.broadcast_task(ann)

    def process_offers(self, ann):
        got_offers = len(ann.offers)
        log.warning("process offers - got {} offers".format(got_offers))
        # (ok, best) = pick_offers(self.offers[ann], ann)
        # if ok:
        #     self.send_acks(best)
        #     send payload
        #     collect payload acks
        #     first round
        log.warning("process offers - not_impl")

    def broadcast_task(self, ann, origin=None):
        ann_short = ann.shorten()
        self.known_announcements[ann_short] = datetime.datetime.utcnow()
        cron.apply_after(GC_ANN_AFTER, self.gc_ann, ann_short)
        self.bcast(GolemProtocol,
                   'announcement',
                   args=ann.pack(),
                   exclude_peers=[origin.peer] if origin else [])

    def maybe_rebroadcast_announcement(self, proto, ann):
        ann_short = ann.shorten()
        # FIXME: don't rebroadcast if abs(t(ann)-now())>1min
        if self.known_announcements.has_key(ann_short):
            log.debug("known announcement, skip {}".format(ann_short))
            pass
        else:
            self.broadcast_task(ann, origin=proto)

    def gc_ann(self, ann_short):
        log.debug("cleanup announcements {}".format(ann_short))
        self.known_announcements.pop(ann_short)

