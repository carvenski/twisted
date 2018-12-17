# learn twisted framework

[twisted官网](https://twistedmatrix.com/trac/)

[twisted原理介绍](https://www.cnblogs.com/xianguang/p/7027661.html)

#### twisted框架介绍
```python
Twisted is an event-driven networking engine written in Python.
twisted框架基于tcp/ip协议的socket通信,简单点说其实twisted就是把socket的api又封装成更简洁易用的api了.
框架就是这样,本质就是一层层的api封装.最后又提供给你它自己的一套开箱即用的api...
twisted就是封装了selector+socket,并且针对各种协议(http/rpc/ssh等)提供了一套该协议易用的api和其server/client的实现.
然后你可以不直接使用底层socket来实现网络通信程序,而使用twisted框架提供的api来写各种基于tcp/ip协议和socket编程的网络程序.
典型的如:
  基于http协议的http client/server
  基于rpc协议的rpc client/server
  基于SMTP/POP3/IMAP4等邮件协议的mail client/server
  基于ssh协议的ssh client/server
以及等等的 凡基于tcp/ip协议之上的各种自定义协议,使用socket api编程 的各种网络通信程序...

****************************************************************************
 网络通信程序的本质都是使用socket编程,而twisted就是socket的一层简洁的封装.
 所以,socket/twisted被称为网络通信程序的引擎!!
****************************************************************************

twisted核心思想中包含了reactor设计模式(ioloop) + select模型的回调函数风格的非阻塞异步IO.
其实核心就是: 一个死循环(ioloop) + select监控read/write事件,然后触发回调函数.
参考: https://github.com/yxzoro/py/blob/master/select/epoll_http_server.py
while True:
    events = select_wait_for_events(timeout)
    for event in events:
        event.process()

----------------------------------------------------------------------------------------------------------
twisted中的几个重点概念:
reactor:    就是select loop,一个包含select的死循环而已,循环监听注册的socket的read/write事件,然后触发回调.
defer:      就是tornado中的future的概念,为了不让函数阻塞,先立马返回一个future对象,等结果好了时再回调处理一下结果.
Transport:  其实就是socket的一层封装,基本上Transport的用法和socket的一样,无非connect/receive/send/close.
Protocol:   代表一个协议,实现一个自定义协议时就继承它,然后实现该协议的数据格式处理逻辑.其实它就是client socket.
ProtocolFactory: 负责生成协议实例,其实它就是server socket,每个连接建好后由它生成protocol/client socket实例.
----------------------------------------------------------------------------------------------------------

**************************************************************************************************************************
在twisted回调函数的基础上,又结合python的yield生成器实现了更简洁的协程写法:
tornado就是利用python的yield语法可以挂起函数的特点封装出了协程写法代替了回调写法,
而python3中又基于tornado修改一下成了asyncio.
而其实twisted本身,除了回调函数这一写法外,它也使用defer + yield实现了和tornado一样的协程写法效果(参考coroutine_in_twisted.py代码).
**************************************************************************************************************************
```

### 其实就和直接使用 selector + server/client socket 的方式来写网络通信程序本质一样.
### twisted的本质就是 selector + server/client socket 原生写法的封装.
```python
# ********************************************************************************************************
# twisted其实就是把以下epoll_http_server.py中的 (server_socket + client_socket + select_loop) 给封装一下 !!
# 并且按照各种基于tcp/ip协议/socket编程的常见协议所定义的数据格式给你封装好一个client和server的实现.
# 你当然也可以很轻松的使用twisted封装好的api来轻松实现自己定义的协议(按照自定义协议规定的数据格式完成数据读写即可).
# 当然,我觉得twisted之于我最大的用处是: 
#   撇开什么协议的不谈,就是简单的基于scoket的通信程序的开发.
#   比如实现chatroom这个功能,就不再需要直接操作底层socket读写数据了,而是直接使用twisted封装的api来写个server/client,
#   server端就定义个收到数据后的handler,client端就写个connect然后发送数据,这样就写好了一个client/server的网络程序了.
#   替你屏蔽了底层socket通信的数据读写的细节(所以说twisted的本质就是selector + server/client socket的封装).
#   并且因为有select/epoll异步回调模型,轻松实现单线程非阻塞效率高的网络程序.
# ********************************************************************************************************

# 原生版本 epoll_http_server.py 
# selector + socket to realize a HTTP server.
import selectors
import socket

# epoll on linux
selector = selectors.DefaultSelector()

def _get_socket_info(sock):
    return sock.getpeername()[0] + ":" +  str(sock.getpeername()[-1])

# accept new connection for server socket
def accept(server_socket, mask):
    client_socket, addr = server_socket.accept()  # Should be ready
    print('=> server socket accepted new connection %s' % (_get_socket_info(client_socket)))
    client_socket.setblocking(False)
    selector.register(client_socket, selectors.EVENT_READ, read)

# handler for client socket connection
def read(conn, mask):
    # conn == client_socket
    connec_info = _get_socket_info(conn)
    data = conn.recv(1024)  # Should be ready
    print('=> got request data from connection %s:\n%s' % (connec_info, data))

    # ---- parse request ----
    # there should be business logic code here, like visit db or some io staff...
    # 所以这里如果有网络请求之类的代码,必须要把它对应的底层socket也注册到loop中去,也加入监听事件,这样才能不阻塞.
    # ---- make response ----

    # HTTP protocol which is based on tcp/ip protocol socket.
    response = b"""HTTP/1.0 200 OK
Date: fuck
Server: fuck
Last-Modified: fuck
Content-Length: 100
Content-Type: text/plain
Connection: Closed

...hello...http...fuck..."""
    conn.send(response)  # Hope it won't block
    print("=> send response to %s" % connec_info)
    selector.unregister(conn)
    conn.close()
    print("=> close connection %s" % connec_info)


print("*server socket started at :80")
server_socket = socket.socket()
server_socket.bind(('0.0.0.0', 80))
server_socket.listen(100)
server_socket.setblocking(False)
selector.register(server_socket, selectors.EVENT_READ, accept)

# this is what they called => the ioloop !!
# selector wait for READ/WRITE event, then call callback
print("*socket selector started...")
while True:    
    events = selector.select() # this will block until event happen
    for key, mask in events:
        callback = key.data
        # callback can't be blocking, otherwise it will block selector loop here.
        # 在每一个请求的handler里面都不能有阻塞操作,否则会导致这里的callback阻塞住整个loop.
        # 所以在每一个请求里面的网络访问之类的操作,也要将其对应的底层socket也register到loop中去就行了.
        callback(key.fileobj, mask)

  ###
  ###
  ###
 #####   
  ###
   #
   
# twisted版本 epoll_http_server.py 
# 使用twisted的Protocol + Transport + Reactor to realize a HTTP server.
from twisted.internet import protocol, reactor, endpoints

# 协议的实现类.其实这就是client socket.
class HTTP(protocol.Protocol):  #实现个自定义协议就叫HTTP协议,协议规定请求和返回数据的格式:第一行+header(kv)+空行+body.
    def dataReceived(self, data):  #实现Http server socket接收到数据后应该怎么处理的逻辑
        print("=> req data:\n%s\n\n" % data)
        # HTTP返回的数据格式:
        response = b"""HTTP/1.0 200 OK
Date: fuck
Server: fuck
Last-Modified: fuck
Content-Length: 100
Content-Type: text/plain
Connection: Closed

...hello...http...fuck..."""
        print("=> send http response.")
        self.transport.write(response)  # 这里可以看到其实transport就是socket的封装,使用transport来读写数据.
        self.transport.loseConnection() # 这不就是socket.close()么...

# Factory工厂模式,就返回个协议实例.其实这个就是server socket,负责建立连接并返回client socket的.
class HTTPFactory(protocol.Factory): 
    def buildProtocol(self, addr):
        return HTTP()

endpoints.serverFromString(reactor, "tcp:80").listen(HTTPFactory())
print("HTTP server started at :80")
reactor.run()

```


#### EchoServer example
*可以认为这是个最简单的自定义协议: echo协议,该协议规定的数据格式就是:发送什么就返回什么.*
```python
from twisted.internet import protocol, reactor, endpoints

class Echo(protocol.Protocol): # 实现个自定义协议就叫Echo协议: 协议规定发送什么就返回什么.
    def dataReceived(self, data):  # 实现server socket接收到数据后应该做什么
        self.transport.write(data)  # 这里可以看到其实transport就是socket的封装,使用transport来读写数据.

class EchoFactory(protocol.Factory):
    def buildProtocol(self, addr):
        return Echo()

endpoints.serverFromString(reactor, "tcp:1234").listen(EchoFactory())
print("Echo server started at :1234")
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

#### ChatRoomServer example
```python
from twisted.internet import reactor, protocol, endpoints
from twisted.protocols import basic

class ChatRoomProtocol(basic.LineReceiver): # 实现个自定义ChatRoom协议的server/cient.
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

class ChatRoomFactory(protocol.Factory):
    def __init__(self):
        self.clients = set()

    def buildProtocol(self, addr):
        return ChatRoomProtocol(self)  # 在每个conn里获取当前factory维护的全局变量.

endpoints.serverFromString(reactor, "tcp:1025").listen(ChatRoomFactory())
reactor.run()
```




