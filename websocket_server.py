#encoding=utf8
from twisted.internet import protocol, reactor, endpoints
import re
import base64
import hashlib
import time

"""
//js ws client test code:
ws = new WebSocket("ws://IP:18000");
ws.send("hello websocket...")
"""
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
            print("=> send ws handshake http response.")
            print("=> ws handshake succeed !\n")
            # ws can't close connection.
            # self.transport.loseConnection()
        # parse req data frame by websocket protocol format
        else:
            '''see https://blog.csdn.net/u010487568/article/details/20569027
            +-+-+-+-+-------+-+-------------+-------------------------------+
                    1                2               3           4
             0 1 2 3 4 5 6 7 0 1 2 3 4 5 6 7 0 1 2 3 4 5 6 7 0 1 2 3 4 5 6 7
            +-+-+-+-+-------+-+-------------+-------------------------------+
            |F|R|R|R| opcode|M| Payload len |    Extended payload length    |
            |I|S|S|S|  (4)  |A|     (7)     |             (16/64)           |
            |N|V|V|V|       |S|             |   (if payload len==126/127)   |
            | |1|2|3|       |K|             |                               |
            +-+-+-+-+-------+-+-------------+ - - - - - - - - - - - - - - - +
            |   payload length continued, if payload len == 127             |
            + - - - - - - - - - - - - - - - +-------------------------------+
            |   payload length continued    + Masking-key if MASK set to 1  |
            + - - - - - - - - - - - - - - - +-------------------------------+   
            |   Masking-key continued       +         Payload Data          |
            + - - - - - - - - - - - - - - - +-------------------------------+            
            |                     Payload Data continued...                 |
            +---------------------------------------------------------------+
            FIN:1位,用于描述消息是否结束,如果为1则该消息为消息尾部,如果为零则还有后续数据包;
            RSV1,RSV2,RSV3,各1位,用于扩展定义的,如果没有扩展约定的情况则必须为0;
            OPCODE:4位,用于表示消息接收类型,如果接收到未知的opcode,接收端必须关闭连接,如下:
                Opcode中的值代表着这个帧的作用(0-7:数据帧 8-F:控制帧)
                0: 后续帧,分片时用到
                1: 文本帧,说明发过来的数据是文本
                2: 二进制帧,说明发过来的数据是二进制
                3-7: 保留的数据帧,暂时无作用
                8: 关闭帧,说明对面要关闭连接了
                9: ping帧,对方ping过来,你就要pong回去→_→
                A: pong帧,对方ping过来时,需要返回pong帧回去,以示响应
                B-F: 保留的控制帧,暂时无作用
            MASK:1位,标识PayloadData是否掩码处理,
                客户端发送的数据帧必须进行掩码处理后才能发送到服务器,服务端发送的帧不能有掩码
            Masking-key:0/4字节，如果MASK位设为1则有4个字节的掩码解密密钥，否则就没有
                Masking-key域的数据即是32位的掩码密钥,用于解码PayloadData,
                掩码的密钥是一个32位的随机值,客户端随机选取密钥,这个掩码处理后并不影响Payload数据的长度,
                服务器收到掩码处理后的数据后,解码算法如下(这个算法对于加密和解密的操作都是一样的):                
                第i个数据(pyload) 需要和 第 i%4 个掩码做 异或运算,即                
                var data = new ByteArray("我是demo")  //数据字节数组                
                var mask = [0x24, 0x48, 0xad, 0x54]  //四个字节的掩码字节数组
                for(var i = 0; i < data.length; i++) {
                    data[i] = data[i] ^ mask[i % 4]
                }  //data即可变成 加密或解密后的数据
            PayloadData的长度：7位,7+16位,7+64位
                如果其值在0-125,则是payload的真实长度,
                如果值是126,则后面2个字节形成的16位无符号整型数的值是payload的真实长度
                如果值是127,则后面8个字节形成的64位无符号整型数的值是payload的真实长度
                长度表示遵循一个原则,用最少的字节表示长度,尽量减少不必要的传输
            '''            
            # convert data string to bytearray, not data_bytes = bytes(data) !!
            data_bytes = bytearray(data)
            print(len(data_bytes))        
            print("=> got origin ws client sended data bytes: %s" % [int(i) for i in data_bytes])
            # convert byte to bits
            # bin() return a string of a byte like "0b10000001"
            first_byte = bin(data_bytes[0])[2:]
            second_byte = bin(data_bytes[1])[2:]
            mask_key_bytes = data_bytes[2:6]
            payload_bytes = data_bytes[6:]
            for i, _ in enumerate(payload_bytes):
                payload_bytes[i] = payload_bytes[i] ^ mask_key_bytes[i % 4]
            ## 这里只考虑payload长度小于125的情况...
            print("""=> parse data frame:
FIN= %s, RSV1= %s, RSV2= %s, RSV3= %s, opcode= %s,
MASK= %s, MASK key= %s, 
Payload len= %s, Payload= %s.""" % (
                first_byte[0], first_byte[1], first_byte[2], first_byte[3], hex(int(first_byte[4:])),
                second_byte[0], [int(i) for i in mask_key_bytes], len(payload_bytes), payload_bytes))
            print("\n=> got parsed ws client sended data string: %s" % payload_bytes)
            
            
            ''' construct resp data frame by websocket protocol format
            '''
            # self.transport.write(b"")


class WSFactory(protocol.Factory): 
    def buildProtocol(self, addr):
        return WS()

endpoints.serverFromString(reactor, "tcp:18000").listen(WSFactory())
print("WS server started at :18000")
reactor.run()



