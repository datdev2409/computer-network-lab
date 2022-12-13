import sys
import socket
import threading

server_host = '127.0.0.1'
server_port = int(sys.argv[3]) or 9000

class Connection():
  def __init__(self, name, conn, addr):
    self.name = name
    self.conn = conn
    self.addr = addr

  def to_string(self):
    return "{name} {host}:{port}".format(name=self.name, host=self.addr[0], port=self.addr[1])

class Peer(threading.Thread):
  def __init__(self, name, host, port, callback = None):
    threading.Thread.__init__(self)
    self.name = name
    self.host = host
    self.port = int(port)
    self.callback = callback
    self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    self.active = False

    self.inbound_conns = []
    self.outbound_conns = []

    self.terminate_flag = threading.Event()
  

  def connect_central_server(self):
    self.server_socket.connect((server_host, server_port))
    initial_msg = "{name} {host}:{port}".format(
      name=self.name,
      host=self.host,
      port=self.port
    )
    self.server_socket.send(initial_msg.encode())
    self.active = True
    print("Central server is connected")


  def get_active_node(self):
    while not self.active:
      self.connect_central_server()

    self.server_socket.send("list".encode()) 
    msg = self.server_socket.recv(1024).decode()
    return msg


  def get_msg(self, name, conn, addr):
    while not self.terminate_flag.is_set():
      msg = conn.recv(1024)  

      if not msg or msg == "bye":
        self.terminate_flag.set()
        break
      print(msg)

      if self.callback:
        self.callback(name + ": " + msg.decode())
  
  def check_connection(self, name):
    for connection in self.inbound_conns + self.outbound_conns:
      if connection.name == name:
        return True
    
    return False
  

  # def connect_to_other(self, host, port):
  #   s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  #   s.connect((host, port))

  #   initial_msg = "{name} {host}:{port}".format(
  #     name=self.name,
  #     host=self.host,
  #     port=self.port
  #   )
  #   s.send(initial_msg.encode())

  #   client_thread = threading.Thread(target=self.get_msg, args=[s, (host, port)])
  #   client_thread.start()
  #   connection = Connection(s, (host, port))
  #   self.outbound_conns.append(connection)
  def close(self):
    self.socket.close()
    self.server_socket.close()
    self.terminate_flag.set()
  

  def get_addr_by_name(self, name):
    active_nodes_str = self.get_active_node()
    active_nodes = active_nodes_str.split("\n")
    for node in active_nodes:
      node_name = node.split()[0]
      addr = node.split()[1]
      if node_name == name:
        return addr
    
    return None
  

  def connect_to_other_by_name(self, name):
    addr = self.get_addr_by_name(name)
    if not addr:
      print("Can not find node with that name")
      return
    
    host = addr.split(":")[0]
    port = int(addr.split(":")[1])
    
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))

    initial_msg = "{name} {host}:{port}".format(
      name = self.name,
      host = self.host,
      port = self.port
    )

    s.send(initial_msg.encode())

    connection = Connection(name, s, (host, port))
    self.outbound_conns.append(connection)

    client_thread = threading.Thread(target=self.get_msg, args=[name, s, (host, port)])
    client_thread.start()
    # self.connect_to_other(host, port)
    

  def send_msg(self, msg, host, port):
    for connection in self.outbound_conns + self.inbound_conns:
      if connection.addr[0] == host and str(connection.addr[1]) == str(port):
        connection.conn.send(msg.encode())
        return
    
    print('Can not find node with address')
  

  def send_msg_by_name(self, msg, name):
    print("name " + name)
    for connection in self.outbound_conns + self.inbound_conns:
      if connection.name == name:
        connection.conn.send(msg.encode())
        return
    
    print('Can not find node with that name')


  def get_connections(self):
    for connection in self.inbound_conns + self.outbound_conns:
      print(connection.to_string())


  def run(self):
    self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    self.socket.bind((self.host, self.port))
    self.socket.listen(10)
    self.connect_central_server()
    while not self.terminate_flag.is_set():
      try:
        conn, addr = self.socket.accept()
        initial_msg = conn.recv(1024).decode()
        name = initial_msg.split()[0]

        listen_thread = threading.Thread(target=self.get_msg, args=[name, conn, addr])
        listen_thread.start()
        connection = Connection(name, conn, addr)
        self.inbound_conns.append(connection)
    
      except KeyboardInterrupt:
        self.terminate_flag.set()


def main():
  host = '127.0.0.1'
  port = sys.argv[1] or 8001
  name = sys.argv[2] or "dat"

  peer = Peer(name, host, port)
  peer.start()

  print("1: get connected nodes")
  print("2: connect to other node")
  print("3: send message")
  print("4: get active nodes")
  print("5: connect to other node by name")
  print("6: send message by name")

  try:
    while True:
      option = int(input("Option: "))
      if option == 1:
        peer.get_connections()
      
      elif option == 2:
        name = input("Name: ")
        peer.connect_to_other_by_name(name)
        # port = int(input("Input port of node to connect: "))
        # peer.connect_to_other(host, port)
      
      elif option == 3:
        msg = input('>| ')
        port = int(input("Input port of node to send msg: "))
        peer.send_msg(msg, host, port)
      
      elif option == 4:
        active_nodes = peer.get_active_node()
        print(active_nodes)
      
      elif option == 5:
        name = input("Node's name: ")
        peer.connect_to_other_by_name(name)
      
      elif option == 6:
        msg = input('>|')
        name = input("Node's name: ")
        peer.send_msg_by_name(msg, name)
  
  except KeyboardInterrupt:
    peer.close()

if __name__ == "__main__":
  main()
