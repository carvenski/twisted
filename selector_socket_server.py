# 原生版本selector_socket_server.
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

"""
socket异步原理
参考:https://blog.csdn.net/hguisu/article/details/7453390

我们把一个SOCKET接口设置为非阻塞就是告诉内核(调用set_non_blocking)
当所请求的I/O操作无法完成时，不要将进程睡眠，而是返回一个错误
这样我们的I/O操作函数将不断的测试数据是否已经准备好，如果没有准备好，继续测试，直到数据准备好为止
                                                                                                                                      
把SOCKET设置为非阻塞模式，即通知系统内核：在调用Sockets API时，不要让线程睡眠，而应该让函数立即返回
在返回时，该函数返回一个错误代码。图所示，一个非阻塞模式套接字多次调用recv()函数的过程
前三次调用recv()函数时，内核数据还没有准备好。因此，该函数立即返回WSAEWOULDBLOCK错误代码
第四次调用recv()函数时，数据已经准备好，被复制到程序的缓冲区中，recv()函数返回成功，程序开始处理数据
                                                                                                                                      
*******************************************************************************************
从以上可知: 其实selector/epoll这些东西本质上做的事也就是: 轮训socket而已,你的数据好没好啊? 
从selector的api可以看出:把一组socket传给它,然后它自己阻塞(内部在轮训),哪个好了就通知你,调用回调函数
*******************************************************************************************
"""  



