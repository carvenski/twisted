from twisted.internet import protocol, reactor, endpoints
import re
import base64
import hashlib
import time

class WS(protocol.Protocol):
    def connectionMade(self):
        print("=> socket connection established...")

    def dataReceived(self, data):
        # do handshake when first ws req here
        if data.startswith("GET"):
            print("=> got ws handshake http req:\n%s" % data)
            m = re.search("\nSec-WebSocket-Key.*\n", data)
            secret_key = m.group(0).split(": ")[-1].strip()
            print("secret_key: %s" % secret_key)
            # generate ws Sec-WebSocket-Accept by Sec-WebSocket-Key
            server_secret_key = base64.b64encode(
                hashlib.sha1(secret_key + '258EAFA5-E914-47DA-95CA-C5AB0DC85B11').digest())
            print("server_secret_key: %s" % server_secret_key)
            response = bytes("""HTTP/1.1 101 Switching Protocols
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Accept: %s

""" % server_secret_key)  # must have 2 empty line as end...
            self.transport.write(response)  
            print("=> send ws handshake http response.\n")
            # ws can't close connection.
            # self.transport.loseConnection()
        else:
            print("=> got ws sended data bytes:\n%s" % bytes(data))
            # parse data frame by ws protocol

            # wrap data frame by ws protocol
            # self.transport.write(b"")


class WSFactory(protocol.Factory): 
    def buildProtocol(self, addr):
        return WS()

endpoints.serverFromString(reactor, "tcp:18000").listen(WSFactory())
print("WS server started at :18000")
reactor.run()





