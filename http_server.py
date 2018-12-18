from twisted.internet import protocol, reactor, endpoints

class HTTP(protocol.Protocol):
    def dataReceived(self, data):  
        print("=> req data:\n%s\n" % data)
        content = "...hello...http...fuck..."
        response = b"""HTTP/1.0 200 OK
Date: fuck
Server: fuck
Last-Modified: fuck
Content-Length: %d
Content-Type: text/plain
Connection: Closed

%s """ % (len(content), content)
        print("=> send http response.")        
        self.transport.write(response)
        # http协议是一次req+一次response,所以默认断开连接.后面再重新建立连接.
        # 当然也可以传Connection: keep-alive的header来表明不断开socket连接,后面的交互再复用它.
        self.transport.loseConnection()  

class HTTPFactory(protocol.Factory):
    def buildProtocol(self, addr):
        return HTTP()

endpoints.serverFromString(reactor, "tcp:18000").listen(HTTPFactory())
print("HTTP server started at :18000")
reactor.run()



