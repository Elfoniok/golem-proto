import datetime
import ethereum.keys
import devp2p.discovery

from ethereum import slogging

log = slogging.get_logger('golem.service')

class Task(object):
    utc_time = None
    price = None

    def __init__(self, price):
        utc_time = datetime.datetime.utcnow()
        self.price = price

    @classmethod
    def from_pack(cls, utc_time, price):
        t = Task(price)
        t.utc_time = utc_time
        return t

class Announcement(object):
    requestor_id = None
    node_id = None
    node_address = None
    announcement_hash = "none"
    allowed_peers = "none"
    signature = None
    task = None
    offers = []

    def __init__(self, task):
        self.task = task

    def __repr__(self):
        return 'Announcement(by: %s, at:%s)' % (self.node_id, self.node_address)

    def sign(self, pk):
        self.requestor_id = ethereum.keys.privtoaddr(pk)
        self.node_id = ethereum.keys.privtoaddr(pk)
        self.announcement_hash = 42
        self.allowed_peers = 42

    def pack(self):
        price = self.task.price
        address = self.node_address
        node_id = self.node_id
        return ("utc time", price, self.requestor_id, node_id, address.to_binary(),
                41154, "some peers", "signature")

    @classmethod
    def from_pack(cls, utc_time, price, requestor_id, node_id, node_address,
                  announcement_hash, allowed_peers, signature):
        t = Task.from_pack(utc_time, price)
        r = cls(t)
        r.allowed_peers = allowed_peers
        r.requestor_id = requestor_id
        r.node_id = node_id
        r.node_address = devp2p.discovery.Address.from_binary(*node_address)
        r.announcement_hash = announcement_hash
        r.signature = signature
        return r

    def shorten(self):
        return self.requestor_id, self.announcement_hash, self.allowed_peers


