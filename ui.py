import sys
import tkinter
from Peer import Peer
from datetime import datetime
from customtkinter import *

host = '127.0.0.1'
port = sys.argv[1] or 8001
name = sys.argv[2] or "dat"
server_port = int(sys.argv[3]) or 9000
set_default_color_theme("./theme.json")

class App(CTk):
  def __init__(self):
    super().__init__()

    self.title(name)

    self.peer = Peer(name, host, port, (host, server_port))
    self.peer.on_file_sent = self.receive_file
    self.peer.on_receive_msg = self.receive_msg
    self.peer.start()

    self.friend_frame = CTkFrame(master=self, width=800, height=50)
    self.friend_list = CTkComboBox(master=self.friend_frame, width=500, height=50)
    self.friend_list.grid(row = 0, column = 0)
    self.reload_btn = CTkButton(
      master=self.friend_frame,
      width=100,
      text="Reload",
      height=50,
      command=self.get_active_nodes
    )
    self.reload_btn.grid(row = 0, column = 1)
    self.friend_frame.pack()
  
    self.textbox = CTkTextbox(master=self, width=800, height=400)
    # self.textbox.configure(state="readonly")
    self.textbox.pack()

    self.input_frame = CTkFrame(master=self, width=800, height=50)
    self.msg_input = CTkEntry(master=self.input_frame, width=600, height=50)
    self.msg_input.grid(row = 0, column = 1)
    self.send_btn = CTkButton(
      master=self.input_frame,
      height=50,
      text="Send >",
      command=self.send_msg
    )
    self.send_btn.grid(row = 0, column = 2)
    self.browse_file_btn = CTkButton(
      master=self.input_frame,
      width=60,
      height=50,
      text="File",
      command=self.browse_file
    )
    self.browse_file_btn.grid(row = 0, column=0)
    self.input_frame.pack()


  def receive_file(self, path):
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    msg = f"File is stored in {path} \n"
    self.textbox.insert(END, "\n----" + current_time + "\n")
    self.textbox.insert(END, msg)

  def browse_file(self):
    print("Send file")
    filepath = filedialog.askopenfilename(initialdir="/home")

    name = self.get_current_name()
    self.peer.send_file(name, filepath)

  def receive_msg(self, msg):
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    self.textbox.insert(tkinter.END, "\n----" + current_time + "\n" + msg )

  def get_active_nodes(self):
    if self.friend_list: self.friend_list.destroy()
    active_nodes = self.peer.get_active_nodes().split("\n")

    self.friend_list = CTkComboBox(master=self.friend_frame, width=500, height=50, values=active_nodes)
    self.friend_list.grid(row = 0, column = 0)
  
  def connect_to_node(self):
    node_str = self.combobox.get()
    name = node_str.split(" ")[0]
    self.peer.connect_other_node(name)
  
  def get_current_name(self):
    node_str = self.friend_list.get()
    name = node_str.split(" ")[0]

    if not self.peer.check_connection(name):
      self.peer.connect_other_node(name)
    
    return name

  
  def send_msg(self):
    name = self.get_current_name()

    msg = self.msg_input.get()
    self.peer.send_msg(name, msg)
    self.msg_input.delete(0, END)

  
if __name__ == "__main__":
    app = App()
    app.mainloop()
    app.peer.close()
