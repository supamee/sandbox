import socket
from tcp_class import Connection
from email_class import Emailer
from time import time,sleep

#  sending_thread = Thread(target=self._write_data, name="mac_writer")
#             sending_thread.daemon = True
#             sending_thread.start()




class server_side(Connection):
    def __init__(self, conn, addr,email_conn,email_dest,other_connections):
        super().__init__(conn,addr)
        self.email_conn=email_conn
        self.email_dest=email_dest
        self.other_connections=other_connections
    def on_disconnect(self):
        print("new connection lost",self.addr)
        sleep(10)
        print("done connection lost sleep")
        if self.addr[0] not in self.other_connections or self.other_connections[self.addr[0]].done:
            print("not in list so send email")
            print("self.addr[0] not in self.other_connections",self.addr[0] not in self.other_connections)
            print("self.other_connections[self.addr[0]].done",self.other_connections[self.addr[0]].done)
            self.email_conn.send(body="This is just a test",subject="Test Email For your greenhouse",dst=self.email_dest)
        else:
            print("client reconnected")







Email_point=Emailer()
host=""
port=11027
timeout=5
data_payload = 2048

server_address = (host, port)
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(server_address)  
sock.settimeout(timeout)
sock.listen(5)
print("waiting")
connections={}
i=0
while True:
    i+=1
    try:
        client, address = sock.accept() 
        # connections.append(Connection(client,address))
        connections[address[0]]=server_side(client,address,Email_point,["elliottbtwilley@gmail.com"],connections)
        print(address)
    except socket.timeout:
        if len(connections)>0:
            for con in connections:
                try:
                    connections[con].send(str("message"+str(i)).encode('utf-8'))
                except OSError as e:
                    print("not able to sent message to ",con)
                    # Email_point.send(body="This is just a test",subject="Test Email For your greenhouse",dst=["elliottbtwilley@gmail.com"])
                    # smtpObj = smtplib.SMTP('smtp.gmail.com', port=587)
                    # smtpObj.starttls()
                    # smtpObj.login(user, password)
                    # smtpObj.sendmail(sender, receivers, message)         
                    # print ("Successfully sent email")
        print("just a timeout on connect")

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