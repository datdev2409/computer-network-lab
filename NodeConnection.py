import time
import threading

# class NodeConnection(threading.Thread):
#   def __init__(self, main_node, socket, name, host, port):
#     threading.Thread.__init__(self)
#     self.main_node = main_node
#     self.socket = socket
#     self.host = host
#     self.port = port
#     self.name = name
#     self.terminate_flag = threading.Event()
  
#   def to_string(self):
#     return f"{self.name} {self.host}:{self.port}"
  
#   def stop(self):
#     self.terminate_flag.set()
  
#   def send(self, msg):
#     self.socket.send(msg.encode())
  
#   def run(self):
#     while not self.terminate_flag.is_set():
#       try:
#         msg = self.socket.recv(1024).decode()
#         if not msg or msg == "bye":
#           self.main_node.close_connection(self.to_string())
#           self.stop()
        
#         if msg == "list":
#           active_nodes = self.main_node.get_active_nodes()
#           self.send(active_nodes)
        
#         print(msg)
#       except Exception as e:
#         print(e)
#         self.stop()
    
#     time.sleep(0.01)


class NodeConnection(threading.Thread):
  def __init__(self, main_node, sock, name, host, port, callback):
    threading.Thread.__init__(self)
    self.main_node = main_node
    self.sock = sock
    self.name = name
    self.host = host
    self.port = port
    self.callback = callback
    self.terminate_flag = threading.Event()
  
  def to_string(self):
    return f"{self.name} {self.host}:{self.port}"
  
  def send(self, msg):
    self.sock.send(msg)

  def run(self):
    self.callback(self)
