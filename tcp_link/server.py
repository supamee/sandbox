import socket

host=""
port=11027
timeout=10
data_payload = 2048

server_address = (host, port)
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(server_address)  
sock.settimeout(timeout)
sock.listen(5)
print("waiting")
client, address = sock.accept() 
print("connected to",client, address )
while True:

    print ("Waiting to receive message from client")
    data = client.recv(data_payload) 
    if data:
        print ("Data: %s" %data)
        client.send(data)
        print ("sent %s bytes back to %s" % (data, address))
    # try:
    #     incoming = sock.recv(1024)
    #     print(incoming,conn,addr)
    # except socket.timeout:
    #     print("timeout")