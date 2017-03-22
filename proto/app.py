import os
import signal
import sys
from logging import StreamHandler

import click
import gevent
import random
from gevent.event import Event

import ethereum.slogging as slogging
from devp2p.app import BaseApp
from devp2p.discovery import NodeDiscovery
from devp2p.peermanager import PeerManager
from golem_service import GolemService
from devp2p.service import BaseService
from ethereum.utils import encode_hex, decode_hex
from devp2p import crypto
"""
It should be noted that we are using devep2p implementation of keys which
makes 64 bytes public keys. This is not compatible with 65 bytes raw
ECCx keys which are used to sign ethereum transactions.
"""

slogging.PRINT_FORMAT = '%(asctime)s %(name)s:%(levelname).1s\t%(message)s'
log = slogging.get_logger('app')

services = [NodeDiscovery, PeerManager, GolemService]

bs_k = encode_hex(crypto.mk_privkey(str(2**30+1234567)))
bs_pk = encode_hex(crypto.privtopub(decode_hex(bs_k)))

secret = random.randint(2**20, 2**21)
privkey = encode_hex(crypto.mk_privkey(str(secret)))
pubkey = encode_hex(crypto.privtopub(decode_hex(privkey)))

class Golem(BaseApp):
    client_name = 'golem'
    client_version_string = '%s' % (client_name)
    start_console = False
    default_config = dict(BaseApp.default_config)
    default_config['client_version_string'] = client_version_string
    default_config['post_app_start_callback'] = None
    script_globals = {}

@click.group(help='Welcome to {}'.format(Golem.client_name))
@click.option('-l', '--log_config', multiple=False, type=str, default=":info",
              help='log_config string: e.g. ":info,eth:debug', show_default=True)
@click.option('--log-file', type=click.Path(dir_okay=False, writable=True, resolve_path=True),
              help="Log to file instead of stderr.")
@click.pass_context
def app(ctx, log_config, log_file):
    slogging.configure(log_config, log_file=log_file)
    ctx.obj = {
        'log_config': log_config,
        'log_file': log_file,
        'config': {
            'node': {
                'data_dir': 'data',
                'privkey_hex': None,
                'pubkey_hex': None
            },
            'golem': {
                'network_id': 0,
                'min_price': 1,
                'announcement': False,
                'privkey_hex': None,
                'pubkey_hex': None
            },
            'discovery': {
                'listen_host': '0.0.0.0',
                'listen_port': 20170,
                'bootstrap_nodes': [
                    'enode://%s@127.0.0.1:20170' % bs_pk
                ]
            },
            'p2p': {
                'listen_host': '0.0.0.0',
                'listen_port': 20170,
                'min_peers': 2,
                'max_peers': 5
            }
        }
    }


@app.command()
@click.argument('node_id', type=click.IntRange(0,100))
@click.option('--console',  is_flag=True, help='Immediately drop into interactive console.')
@click.pass_context
def run(ctx, node_id, console):
    """Start the daemon"""

    config = ctx.obj['config']
    config['node']['data_dir'] += str(node_id)
    config['node']['pubkey_hex'] = pubkey
    config['node']['privkey_hex'] = privkey
    config['golem']['privkey_hex'] = privkey
    config['golem']['pubkey_hex'] = pubkey
    config['discovery']['listen_port'] += node_id
    config['p2p']['listen_port'] += node_id
    log.info("starting", config=config)

    if node_id == 0:
        config['golem']['announcement'] = True
        config['node']['pubkey_hex'] = bs_pk
        config['node']['privkey_hex'] = bs_k
        config['golem']['pubkey_hex'] = bs_pk
        config['golem']['privkey_hex'] = bs_k

    app = Golem(config)
    log.debug("ann: {}, node_id: {}".format(config['golem']['announcement'],
                                            config['golem']['pubkey_hex']))
    app.start_console = console

    for service in services:
        assert issubclass(service, BaseService)
        assert service.name not in app.services
        service.register_with_app(app)
        assert hasattr(app.services, service.name)

    # start app
    log.info('starting')
    app.start()

    if ctx.obj['log_file']:
        log.info("Logging to file %s", ctx.obj['log_file'])
        # User requested file logging - remove stderr handler
        root_logger = slogging.getLogger()
        for hdl in root_logger.handlers:
            if isinstance(hdl, StreamHandler) and hdl.stream == sys.stderr:
                root_logger.removeHandler(hdl)
                break

    # wait for interrupt
    evt = Event()
    gevent.signal(signal.SIGQUIT, evt.set)
    gevent.signal(signal.SIGTERM, evt.set)
    evt.wait()

    # finally stop
    app.stop()


if __name__ == '__main__':
    app()
