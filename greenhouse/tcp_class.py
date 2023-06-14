from time import time, sleep
from threading import Thread
import socket
from struct import pack, unpack

class Connection:
    """
    Base class for managing data accross the network

    Parameters:
    -----------
    conn: socket
        bi-directional SSL TCP socket
    addr: list
        [ip address,port]

    """
    def __init__(self, conn, addr):
        print("start class init")
        self.conn = conn
        self.addr = addr
        self.done = False
        self.incoming = []
        print("make thread")
        self.main=Thread(target=self.connect)
        print("start thread")
        self.main.start()
        print("done thread")
    def _receive_message_length(self):
        """
        Helper method to find the total size of the next
        serialized message

        Parameters:
        -----------

        Returns:
        -------
        message_length: int
            Number of bytes to read to consume whole
            next message.
        """
        size_length = 8
        chunks = [] 
        bytes_recorded = 0
        while bytes_recorded < size_length:
            incoming_bytes_size = min((size_length - bytes_recorded), 2048)
            chunk = self.conn.recv(incoming_bytes_size)
            if chunk == b"":
                raise RuntimeError("socket connection is broken")
            chunks.append(chunk)
            bytes_recorded += len(chunk)
        message_length = unpack("<Q",b"".join(chunks))[0]
        print("message lenght=",message_length)
        return message_length

    def _receive_message(self, message_length: int):
        """
        Given the message length receive the message.

        Parameters:
        -----------
        message_length: int
            Number of bytes to read.

        Returns:
        -------
        message: str
        """
        chunks, bytes_recorded = [], 0
        while bytes_recorded < message_length:
            incoming_bytes_size = min((message_length - bytes_recorded), 2048)
            chunk = self.conn.recv(incoming_bytes_size)
            if chunk == b"":
                raise RuntimeError("socket connection is broken")
            chunks.append(chunk)
            bytes_recorded += len(chunk)

        try:
            message = b"".join(chunks).decode("utf-8")
            # message = json.loads(message)
        except UnicodeDecodeError:
            print("time:",time())
            print("message is not json")
            print(e)
        except Exception as e:
            print("time:",time())
            print(e,message,type(message))
        return message
    def _receive(self):
        """
        receive a message on the socket.

        Parameters:
        -----------

        Returns:
        -------
        message: str

        """
        message_length = self._receive_message_length()
        message = self._receive_message(message_length)
        return message

    def send(self, msg: bytes):
        """
        Send encoded message over network in a series of packets

        Parameters:
        -----------
        socket:
            The TCP socket the topic and message were received on.
        message: str
            The message to be processed, stored, etc

        Returns:
        -------
        amount_sent: int
            this will be approximate the number of bytes sent accross the network including the packet headers
            it is approximate becase it assumes no resends (I am not sure how to check that from python)
        """
        amount_sent = 0
        l = len(msg)
        attempts_left= 40
        while attempts_left > 0:
            try:
                sent = self.conn.send(pack("<Q",l))
                break
            except socket.timeout:
                print("\nALMOST TIMEOUT  attempts left:"+str(attempts_left)+str(time())+"\n")
                sleep(0.25)
                attempts_left-=1
        amount_sent += 20 + sent  # header plus 5byte payload
        totalsent = 0
        while totalsent < l:
            force = True
            while force:
                try:
                    sent = self.conn.send(msg[totalsent:min(totalsent+65536,len(msg))])
                    force = False
                except socket.timeout:
                    print("\nALMOST TIMEOUT  "+str(time())+"\n")
                    sleep(0.25)
                    
            if sent == 0:
                raise RuntimeError(
                    "socket connection most likely broken: sent size is 0"
                )
            else:
                totalsent += sent
                amount_sent += 20 + sent  # header plus 5byte payload
        return amount_sent

    def connect(self):
        """
        running loop for the connection.
        This handles the reading from the queue and sending, as well as receiving and writing to a list

        Parameters:
        -----------

        Returns:
        -------
        """
        while not self.done:
            # print("loop")
            try:
                # msg=self.conn.recv(1024)
                msg = self._receive()
                if not self.on_recv(msg):
                    self.incoming.append(msg)
                # print("XX", self.addr)
            except ConnectionResetError:
                print("client disconnect(on recv) ConnectionResetError")
                self.done = True
                self.on_disconnect()
            except RuntimeError:
                print("client disconnect(on recv) RuntimeError")
                self.done = True
                self.on_disconnect()
            except socket.timeout:
                # print("no read yet")
                pass
        self.stop()

    def on_recv(self, msg):
        """
        abstract function to allow a hook for when the connection recives data.
        intended for if you need the connection to be more reactive
        Parameters:
        -----------
        msg: str
            message that was just recived
        Returns:
        -------
        None
            Return True to prevent the message from being added to the "incomming" list (distructive read)
        """
        return False
        pass

    def read(self):
        """
        read from the incomming message que
        Parameters:
        -----------
        Returns:
        -------
        messages: list[str]
            returns a list of the messages recived in the order they were recived
        Remarks:
        -------
        this is differnt then just returning self.incomming as that wont delete then,
        and deleting after reading has a race condition where you could delete something you havn't read
        """
        temp = []
        while self.incoming:
            temp.append(self.incoming.pop(0))
        return temp

    def stop(self):
        """
        cleanly closes and exits
        Parameters:
        -----------
        Returns:
        -------
        """
        print("connection done", self.addr)
        self.done = True
        self.conn.close()
        self = None
    def on_disconnect(self):
        """
        abstract function to allow a hook for when the connection recives data.
        intended for if you need the connection to be more reactive
        Parameters:
        -----------
        msg: str
            message that was just recived
        Returns:
        -------
        None
            Return True to prevent the message from being added to the "incomming" list (distructive read)
        """
        print("disconnect detected for address",self.addr)
        return False
        pass