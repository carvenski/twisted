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



