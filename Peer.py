import os
import sys
import time
import socket as s
import threading
from pathlib import Path
from NodeConnection import NodeConnection

class Peer(threading.Thread):
  def __init__(self, name, host, port, server_addr, callback = None):
    threading.Thread.__init__(self, daemon=True)
    self.name = name
    self.host = host
    self.port = port
    self.server_addr = server_addr
    self.callback = callback

    # socket open for listenning incomming request
    self.server_socket = s.socket(s.AF_INET, s.SOCK_STREAM)

    # socket used for connect central server
    self.sock = s.socket(s.AF_INET, s.SOCK_STREAM)

    # store list of connections of Peer
    self.inbound_conns  = [] # Node <-
    self.outbound_conns = [] # Node ->

    self.debug = True
    self.active = False
    self.file_receive_mode = False
    self.terminate_flag = threading.Event()

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

  def handle_connection(self, conn : NodeConnection):
    data = []
    while not conn.terminate_flag.is_set():
      msg = conn.sock.recv(1024)

      if not msg:
        conn.terminate_flag.set()
        break
      
      if not self.file_receive_mode and msg.decode().startswith("/FILE/"):
        self.file_receive_mode = True
        Path(f"{self.name}").mkdir(exist_ok=True)
        file_name, file_size = msg.decode().split(":")[1:]
        self.des_file = Path(f"{self.name}/{file_name}")
        # self.des_file = open(f"{self.name}/{file_name}", "wb")
        self.debug_print("Handle receiving file")
      
      elif msg.decode(errors="ignore").startswith("/END/"):
        self.file_receive_mode = False
        self.des_file.write_bytes(b''.join(data))
        self.des_file = None
        data = []
        self.debug_print("File sent")
      
      elif self.file_receive_mode:
        data.append(msg)

      elif self.callback and not self.file_receive_mode:
        self.callback(msg.decode())

      print(msg)
      print("\n----------------------\n")
  
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
    addr = self.get_peer_addr(name)
    if not addr:
      self.debug_print(f"Can not find node with name={name}")
      return False
    sock = s.socket(s.AF_INET, s.SOCK_STREAM)
    sock.connect(addr)
    syn_msg = f"{self.name} {self.host}:{self.port}"
    sock.send(syn_msg.encode())
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

    # send file data
    data = source_file.read()
    connection.sock.sendall(data)
    time.sleep(1) 
    connection.sock.sendall("/END/".encode())

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
