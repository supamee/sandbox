import socket
from time import sleep

host="127.0.0.1"
port=11027
timeout=1
server_address = (host, port) 

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
sock.settimeout(timeout)
sock.connect(server_address)
print("connect")
sleep(2)
print("done")
while True:
    
    try:
        message = "Test message. This will be echoed" 
        print ("Sending %s" % message) 
        sock.sendall(message.encode('utf-8')) 

        # message="test"
        # sock.sendall(message.encode('utf-8')) 
        # print("sent")
        sleep(1)
        print ("Sending %s" % message) 
        sock.sendall(message.encode('utf-8')) 
        incoming = sock.recv(1024)
        print(incoming)
    except socket.timeout:
        print("waiting")