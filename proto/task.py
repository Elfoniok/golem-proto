import datetime
import ethereum.keys
import devp2p.discovery

from ethereum import slogging

log = slogging.get_logger('golem.service')

class Task(object):
    price = None

    def __init__(self, price):
        self.price = price

    @classmethod
    def from_pack(cls, price):
        t = Task(price)
        return t

class Announcement(object):
    requestor_id = None
    node_id = None
    node_address = None
    announcement_hash = None
    allowed_peers = None
    signature = None
    task = None
    offers = []

    def __init__(self, task):
        self.task = task
        self.announcement_hash = 42

    def __repr__(self):
        return 'Announcement(hash: %s, by:%s)' % (self.announcement_hash, self.node_id)

    def pack(self):
        price = self.task.price
        address = self.node_address
        node_id = self.node_id
        utc_time = datetime.datetime.isoformat(datetime.datetime.utcnow())
        return (utc_time, price, self.requestor_id, node_id, address.to_binary(),
                self.announcement_hash, "some peers", "signature")

    @classmethod
    def from_pack(cls, utc_time, price, requestor_id, node_id, node_address,
                  announcement_hash, allowed_peers, signature):
        t = Task.from_pack(price)
        r = cls(t)
        r.utc_time = utc_time
        r.allowed_peers = allowed_peers
        r.requestor_id = requestor_id
        r.node_id = node_id
        r.node_address = devp2p.discovery.Address.from_binary(*node_address)
        r.announcement_hash = announcement_hash
        r.signature = signature
        return r

    def shorten(self):
        return self.requestor_id, self.announcement_hash, self.allowed_peers

class Offer(object):
    announcement_hash = None
    provider_id = None
    offer_hash = None
    signature = None

    def __init__(self, announcement_hash, provider_id, offer_hash, signature):
        self.announcement_hash = announcement_hash
        self.provider_id = provider_id
        self.offer_hash = offer_hash
        self.signature = signature

    def __repr__(self):
        return 'Offer(for: %s, by:%s)' % (self.announcement_hash, self.provider_id)
