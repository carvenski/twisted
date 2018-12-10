# learn twisted framework

[twisted官网](https://twistedmatrix.com/trac/)

#### twisted框架介绍
```
Twisted is an event-driven networking engine written in Python2.
twisted框架基于tcp/ip协议的socket通信,简单点说其实twisted就是把socket的api又封装成更简洁易用的api了.
然后你可以不直接使用底层socket来实现网络通信程序,而使用twisted框架提供的api来写各种基于tcp/ip协议和socket编程的网络程序.
典型的如:
  基于http协议的http client/server
  基于rpc协议的rpc client/server
  基于SMTP/POP3/IMAP4等邮件协议的mail client/server
  基于ssh协议的ssh client/server
以及等等的 凡基于tcp/ip协议之上的各种自定义协议,使用socket api编程 的各种网络通信程序...

**************************************
 所以,twisted被称为网络通信程序的引擎!!
**************************************

twisted还实现了reactor设计模式以及基于回调函数风格的非阻塞异步IO,所以网络性能很好.(也是epoll那一套?)


```

### 其实和直接使用server socket + client socket的方式来写网络程序类似

#### EchoServer example
```python
from twisted.internet import protocol, reactor, endpoints

class Echo(protocol.Protocol):
    def dataReceived(self, data):
        self.transport.write(data)

class EchoFactory(protocol.Factory):
    def buildProtocol(self, addr):
        return Echo()

endpoints.serverFromString(reactor, "tcp:1234").listen(EchoFactory())
reactor.run()
```

#### HttpServer example
```python
from twisted.web import server, resource
from twisted.internet import reactor, endpoints

class Counter(resource.Resource):
    isLeaf = True
    numberRequests = 0

    def render_GET(self, request):
        self.numberRequests += 1
        request.setHeader(b"content-type", b"text/plain")
        content = u"I am request #{}\n".format(self.numberRequests)
        return content.encode("ascii")

endpoints.serverFromString(reactor, "tcp:8080").listen(server.Site(Counter()))
reactor.run()

```

#### Chatroom example
```python
from twisted.internet import reactor, protocol, endpoints
from twisted.protocols import basic

class PubProtocol(basic.LineReceiver):
    def __init__(self, factory):
        self.factory = factory

    def connectionMade(self):
        self.factory.clients.add(self)

    def connectionLost(self, reason):
        self.factory.clients.remove(self)

    # when server receive meaasge, it send message to all clients.
    def lineReceived(self, line):
        for c in self.factory.clients:
            source = u"<{}> ".format(self.transport.getHost()).encode("ascii")
            c.sendLine(source + line)

class PubFactory(protocol.Factory):
    def __init__(self):
        self.clients = set()

    def buildProtocol(self, addr):
        return PubProtocol(self)

endpoints.serverFromString(reactor, "tcp:1025").listen(PubFactory())
reactor.run()
```




