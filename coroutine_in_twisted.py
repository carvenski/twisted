from twisted.internet import reactor as ioloop
from twisted.internet.defer import inlineCallbacks as coroutine
from twisted.internet.defer import Deferred as Future
from twisted.web.client import Agent as AsyncHttpClient

async_http_client = AsyncHttpClient(ioloop)

def twisted_sleep(seconds):
    future = Future()
    ioloop.callLater(seconds, future.callback, None)
    return future

@coroutine
def f1():
    print("coroutine 1...start")
    resp = yield async_http_client.request('GET', 'http://baidu.com/',)
    print("coroutine 1...end, with resp code: %s" % resp.code) 

@coroutine
def f2():
    print("coroutine 2...start")
    resp = yield async_http_client.request('GET', 'http://jd.com/')
    print("coroutine 2...end, with resp code: %s" % resp.code) 

@coroutine
def f3():
    print("coroutine 3...start")
    yield twisted_sleep(1)
    print("coroutine 3...end") 

@coroutine
def f4():
    print("coroutine 4...start")
    yield twisted_sleep(2)
    print("coroutine 4...end") 

# *********************************************************************************
#twisted vs tornado/asyncio:
# reactor == ioloop
# inlineCallbacks == coroutine
# defer == future 
#   (defer even has a function called asFuture() to convert a derfer to a future.)
# *********************************************************************************

def run_until_complete(loop, coroutines):
    try:
        loop.run()
    except Exception as e:
        print("ioloop stopped...of %s" % e.message)

# start all coroutine generator:
coroutines = [f1(), f2(), f3(), f4()]
# start loop
run_until_complete(ioloop, coroutines)

# *********************************************************************************
# now you can see that, twisted/tornado/asyncio is same thing actually...
#     the essence is => selector/loop + socket + yield/generator
# *********************************************************************************



