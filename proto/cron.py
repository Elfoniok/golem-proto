import gevent

"""Modelled after erlang's STDLIB's timer.erl module"""

def apply_after(delay, func, *args, **kw_args):
    gevent.spawn_later(delay, func, *args, **kw_args)

def apply_interval(delay, func, *args, **kw_args):
    gevent.spawn_later(delay, _interval_runner, delay, func, *args, **kw_args)

def _interval_runner(delay, func, *args, **kw_args):
    gevent.spawn_later(0, func, *args, **kw_args)
    gevent.spawn_later(delay, _interval_runner, delay, func, *args, **kw_args)
