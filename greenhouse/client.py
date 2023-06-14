import socket
from time import sleep
from tcp_class import Connection

host="127.0.0.1"
port=11027
timeout=1
server_address = (host, port) 

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
sock.settimeout(timeout)
sock.connect(server_address)
print("about to make class")
connection = Connection(sock,server_address)
print("connect")
sleep(2)
print("done")
while True:
    
    try:
        message = "Test message. This will be echoed" 
        print ("Sending %s" % message) 
        # sock.sendall(message.encode('utf-8')) 
        try:
            connection.send(message.encode('utf-8'))

        # message="test"
        # sock.sendall(message.encode('utf-8')) 
        # print("sent")
            sleep(1)
            print ("Sending %s" % message) 
            connection.send(message.encode('utf-8'))
            sleep(1)
            incoming = connection.read()
            print(incoming)
        except OSError as e:
            print("caught",e)
            break
    except socket.timeout:
        print("waiting")