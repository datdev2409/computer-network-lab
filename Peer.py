import os
import sys
import time
import socket as s
import threading
from pathlib import Path
from NodeConnection import NodeConnection

class Peer(threading.Thread):
  def __init__(self, name, host, port, server_addr):
    threading.Thread.__init__(self, daemon=True)
    self.name = name

    # host and port for server program
    self.host = host
    self.port = port

    # central server address (to get list friend)
    self.server_addr = server_addr

    # socket open for listenning incomming request
    self.server_socket = s.socket(s.AF_INET, s.SOCK_STREAM)

    # socket used for connect central server
    self.sock = s.socket(s.AF_INET, s.SOCK_STREAM)

    # store list of connections of Peer
    self.inbound_conns  = [] # Node <-
    self.outbound_conns = [] # Node ->

    self.debug = True
    self.active = False
    self.file_receiving = False
    self.terminate_flag = threading.Event()

    # Hooks
    self.on_file_sent = None
    self.on_receive_msg = None
    self.on_sent_msg = None
    self.on_sent_file = None

  def use_hook(self, hook, *args):
    if hook : hook(*args)

  def debug_print(self, msg):
    if self.debug: print(msg)

  def start_server(self):
    self.server_socket.setsockopt(s.SOL_SOCKET, s.SO_REUSEADDR, 1)
    self.server_socket.bind((self.host, int(self.port)))
    self.server_socket.listen(10)
    self.debug_print(f"[+] Server program started at {self.host}:{self.port}")
  
  def connect_central_server(self):
    self.sock.connect(self.server_addr) 
    syn_msg = f"{self.name} {self.host}:{self.port}"
    self.sock.send(syn_msg.encode())
    self.active = True
    self.debug_print("[+] Connected to central server")
  
  # def get_active_peers(self):
  def get_peer_info(self, syn_msg):
    print(syn_msg)
    (name, addr) = syn_msg.split()
    (host, port) = addr.split(":")
    return (name, host, port)
    
  def create_inbound_connection(self, sock, syn_msg, callback = None):
    (name, host, port) = self.get_peer_info(syn_msg)
    return NodeConnection(self, sock, name, host, port, callback)
  
  def create_outbound_connection(self, sock, name, host, port, callback = None):
    return NodeConnection(self, sock, name, host, port, callback)

  def get_file_info(self, inital_msg):
    # initial_msg: /FILE/:{file_name}:{file_size}
    file_name, file_size = inital_msg.split(":")[1:]
    return (file_name, int(file_size))
  
  def create_dir(self, dir_name):
    Path(dir_name).mkdir(exist_ok=True)
  
  def receive_file_data(self, conn : NodeConnection, file_size):
    chunks = []
    totalrecv = 0
    chunk = conn.receive()
    totalrecv += len(chunk)
    chunks.append(chunk)

    if (totalrecv == file_size):
      self.file_receiving = False

  def handle_connection(self, conn : NodeConnection):
    buffers = []
    file_size = 0
    file_name = ''
    totalrecv = 0

    while not conn.terminate_flag.is_set():
      data = conn.receive()
      if not data:
        conn.close()
        return
      
      print(data.decode(errors="ignore"))
      if not self.file_receiving and data.decode().startswith("/FILE/"):
        msg = data.decode()
        self.file_receiving = True
        dir_name = f"{self.name}_data"
        self.create_dir(dir_name)
        file_name, file_size = self.get_file_info(msg)
        self.des_file = Path(f"{dir_name}/{file_name}")
        self.debug_print("Start receive file data")

      elif data.decode(errors="ignore") == "/END/":
        self.debug_print("End receive file data")
        self.file_receiving = False
        self.des_file.write_bytes(b''.join(buffers))
        path = self.des_file.absolute()
        self.des_file = None
        buffers = []
        self.use_hook(self.on_file_sent, path)

      elif self.file_receiving:
        buffers.append(data)

      else:
        msg = data.decode()
        self.use_hook(self.on_receive_msg, f"{conn.name}: {msg}")
          
  def get_active_nodes(self):
    if not self.active:
      self.connect_central_server()
    
    print('sent message')
    self.sock.send("list".encode())
    node_list = self.sock.recv(1024).decode()
    return node_list

  def get_peer_addr(self, name):
    node_list = self.get_active_nodes()
    node_list = node_list.split("\n")
    for node in node_list:
      (node_name, addr) = node.split()
      (host, port) = addr.split(":")
      if node_name == name:
        return (host, int(port))
    return None
  
  def get_connections(self):
    for conn in self.inbound_conns + self.outbound_conns:
      print(conn.to_string())

  def connect_other_node(self, name):
    # get addr by name from central server
    addr = self.get_peer_addr(name)

    if not addr:
      self.debug_print(f"Can not find node with name={name}")
      return False

    # Connect to other peer
    sock = s.socket(s.AF_INET, s.SOCK_STREAM)
    sock.connect(addr)

    # send syn msg
    syn_msg = f"{self.name} {self.host}:{self.port}"
    sock.send(syn_msg.encode())

    # store connection in outbound connections
    connection = self.create_outbound_connection(sock, name, addr[0], addr[1], self.handle_connection)
    connection.start()
    self.outbound_conns.append(connection)
    self.debug_print(f"[+] Connect to {name}")
  
  def check_connection(self, name):
    for conn in self.outbound_conns + self.inbound_conns:
      if conn.name == name:
        return True
    return False
  
  def send_msg(self, name, msg):
    for conn in self.outbound_conns + self.inbound_conns:
      if conn.name == name:
        conn.send(msg.encode())
        self.on_sent_msg(msg)
        return True
    
    self.debug_print(f"[-] Can not find node with name={name}")
    return False

  def get_connection_by_name(self, name) -> NodeConnection:
    for conn in self.outbound_conns + self.inbound_conns:
      if conn.name == name:
        return conn
    return None
  
  def send_file(self, name, filepath):
    connection = self.get_connection_by_name(name)
    if not connection:
      self.debug_print(f"[-] Can not find node with name={name}")
      return False

    file_name = os.path.basename(filepath)
    file_extension = os.path.splitext(file_name)[1]
    file_size = os.stat(filepath).st_size

    print(f"File name: {file_name}")
    print(f"File extension: {file_extension}")
    print(f"File size in bytes {file_size}")

    source_file = open(filepath, "rb")
    initial_msg = f"/FILE/:{file_name}:{file_size}"

    # send initial msg to indicate file name, extension and size
    connection.send(initial_msg.encode())
    time.sleep(0.5)

    # send file data
    while True:
      data = source_file.read(1024)
      if not data:
        print("send done")
        break
      connection.sock.send(data)

    time.sleep(1)
    connection.sock.send("/END/".encode("utf-8"))

    # data = source_file.read()
    # connection.sock.sendall(data)

    self.use_hook(self.on_sent_file, f"Sent {file_name}")

  def close(self):
    self.sock.settimeout(0.0)
    self.server_socket.close()
    self.sock.close()
    self.terminate_flag.set()

  def run(self):
    self.start_server()
    self.connect_central_server()

    while not self.terminate_flag.is_set():
      conn, addr = self.server_socket.accept()

      # {name} {host}:{port}
      syn_msg = conn.recv(1024).decode()
      connection = self.create_inbound_connection(conn, syn_msg, self.handle_connection)
      connection.start()
      self.debug_print(f"[+] {connection.to_string()} connected")
      self.inbound_conns.append(connection)

def main():
  host = '127.0.0.1'
  port = int(sys.argv[1])
  name = sys.argv[2] or "dat"
  server_port = int(sys.argv[3])

  peer = Peer(name, host, port, (host, server_port))
  peer.start()
      
  print("1: get active nodes")
  print("2: get connected nodes")
  print("3: connect to other node")
  print("4: send message")

  while True:
    option = input("Option: ")
    
    match int(option):
      case 1:
        print(peer.get_active_nodes())
      
      case 2:
        peer.get_connections()

      case 3:
        name = input("Name: ")
        peer.connect_other_node(name)

      case 4:
        print("Connect to other node")
        name = input("Name: ")
        msg = input('>| ')
        peer.send_msg(name, msg)

      case 5:
        path = input("File path: ")
        peer.send_file(path)

if __name__ == "__main__":
  main()
