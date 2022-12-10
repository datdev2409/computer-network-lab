import socket
import threading

connected_node = []

class ConnectedNode(threading.Thread):
  def __init__(self, socket, name, host, port):
    threading.Thread.__init__(self)
    self.socket = socket
    self.name = name
    self.host = host
    self.port = port
    self.terminate_flag = threading.Event()
  
  def to_string(self):
    return "{name} {host}:{port}".format(
      name = self.name,
      host = self.host,
      port = self.port
    )
  
  def close(self):
    connected_node = filter(lambda x : x.name != self.name, connected_node)
    self.socket.close()
  
  def send(self, msg):
    self.socket.send(msg.encode())
  
  def run(self):
    while not self.terminate_flag.is_set():
      msg = self.socket.recv(1024).decode()
      if not msg or msg == "bye":
        self.terminate_flag.set()
        self.close()
      
      if msg == "list":
        returned_msg = map(lambda node : node.to_string(), connected_node)
        returned_msg = "\n".join(returned_msg)
        self.send(returned_msg)


  


def get_msg(conn, addr):
  while True:
    msg = conn.recv(1024).decode()
    if not msg or msg == "bye":
      break

    if msg == "list":
      returned_msg = map(lambda node : node.to_string(), connected_node)
      returned_msg = "\n".join(returned_msg)
      conn.send(returned_msg.encode())

    print(msg)


def main():
  terminate_flag = 0

  HOST = '127.0.0.1'
  PORT = int(input("PORT: "))

  s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  s.bind((HOST, PORT))
  s.listen(10)

  while not terminate_flag:
    try:
      conn, addr = s.accept()
      # name host:port
      initial_msg = conn.recv(1024).decode()
      name = initial_msg.split()[0]
      addr = initial_msg.split()[1]
      host = addr.split(":")[0]
      port = addr.split(":")[1]

      node = ConnectedNode(conn, name, host, port)
      connected_node.append(node)
      node.start()

    except KeyboardInterrupt:
      terminate_flag = 1
      for node in connected_node:
        node.close()
      
      s.close()



main()
