


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
        self.transport.loseConnection()  

class HTTPFactory(protocol.Factory):
    def buildProtocol(self, addr):
        return HTTP()

endpoints.serverFromString(reactor, "tcp:18000").listen(HTTPFactory())
print("HTTP server started at :18000")
reactor.run()



