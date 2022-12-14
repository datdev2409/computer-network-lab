import time
import threading

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
  
  def receive(self):
    return self.sock.recv(1024)

  def close(self):
    self.terminate_flag.set()
    # self.sock.close()

  def run(self):
    self.callback(self)
