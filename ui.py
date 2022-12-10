import sys
import tkinter
import customtkinter
from peer import Peer
from datetime import datetime

host = '127.0.0.1'
port = sys.argv[1] or 8001
name = sys.argv[2] or "dat"
customtkinter.set_default_color_theme("./theme.json")

class App(customtkinter.CTk):
  def __init__(self):
    super().__init__()

    self.title(name)
    self.minsize(400, 300)

    self.peer = Peer(name, host, port, self.receive_msg)
    self.peer.start()

    self.friend_frame = customtkinter.CTkFrame(master=self, width=800, height=50)
    self.friend_list = customtkinter.CTkComboBox(master=self.friend_frame, width=500, height=50)
    self.friend_list.grid(row = 0, column = 0)
    self.reload_btn = customtkinter.CTkButton(
      master=self.friend_frame,
      width=100,
      text="Reload",
      height=50,
      command=self.reload_active_nodes
    )
    self.reload_btn.grid(row = 0, column = 1)
    self.friend_frame.pack()
  
    self.textbox = customtkinter.CTkTextbox(master=self, width=800, height=400)
    # self.textbox.configure(state="readonly")
    self.textbox.pack()

    self.input_frame = customtkinter.CTkFrame(master=self, width=800, height=50)
    self.msg_input = customtkinter.CTkEntry(master=self.input_frame, width=650, height=50)
    self.msg_input.grid(row = 0, column = 0)
    self.send_btn = customtkinter.CTkButton(
      master=self.input_frame,
      height=50,
      text="Send >",
      command=self.send_msg
    )
    self.send_btn.grid(row = 0, column = 1)
    self.input_frame.pack()

  def receive_msg(self, msg):
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    self.textbox.insert(tkinter.END, "\n----" + current_time + "\n" + msg )

  def reload_active_nodes(self):
    if self.friend_list: self.friend_list.destroy()
    active_nodes = self.peer.get_active_node().split("\n")

    self.friend_list = customtkinter.CTkComboBox(master=self.friend_frame, width=500, height=50, values=active_nodes)
    self.friend_list.grid(row = 0, column = 0)
  
  def connect_to_node(self):
    node_str = self.combobox.get()
    name = node_str.split(" ")[0]
    self.peer.connect_to_other_by_name(name)
  
  def send_msg(self):
    node_str = self.friend_list.get()
    name = node_str.split(" ")[0]

    if not self.peer.check_connection(name):
      self.peer.connect_to_other_by_name(name)

    print(self.msg_input.get())
    self.peer.send_msg_by_name(self.msg_input.get(), name)

  
if __name__ == "__main__":
    app = App()
    app.mainloop()
