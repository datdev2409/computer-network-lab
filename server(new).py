import time
import socket
import threading
from NodeConnection import NodeConnection

class Server():
  def __init__(self, host, port):
    self.host = host
    self.port = port
    self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.terminate_flag = threading.Event()

    self.active_nodes = []
    
  def create_new_connection(self, sock, name, host, port):
    return NodeConnection(self, sock, name, host, port)

  def node_connected(self, conn : NodeConnection):
    msg = conn.socket.recv(1024);
    if not msg:
      conn.stop()
  

  def close_connection(self, connection_str):
    print(connection_str + " disconnected")
    self.active_nodes = list(filter(
      lambda node : node.to_string() != connection_str,
      self.active_nodes
    ))


  def get_active_nodes(self):
    active_nodes_str = map(lambda node : node.to_string(), self.active_nodes)
    msg = "\n".join(active_nodes_str)
    return msg


  def start(self):
    self.socket.bind((self.host, self.port))
    self.socket.listen(10)
    while not self.terminate_flag.is_set():
      try:
        conn, addr = self.socket.accept()

        initial_msg = conn.recv(1024).decode()
        (name, node_addr) = initial_msg.split(" ")
        (host, port) = node_addr.split(":")

        client_thread = self.create_new_connection(conn, name, host, port)
        client_thread.start()

        self.active_nodes.append(client_thread)
      except KeyboardInterrupt:
        self.terminate_flag.set()

    for node in self.active_nodes:
      print("Disconnect")
      node.stop()

    time.sleep(1)

    for node in self.active_nodes:
      node.join()

  
def main():
  HOST = '127.0.0.1'
  PORT = int(input("PORT: "))
  server = Server(HOST, PORT)
  server.start()
    
main()
    



