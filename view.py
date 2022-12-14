# import customtkinter as tk
from customtkinter import *

class App(CTk):
  def __init__(self):
    super().__init__()
  
    self.geometry("1000x500")
    self.columnconfigure(0, weight=3)
    self.columnconfigure(1, weight=7)

    # Connnection frame
    self.connection_frame = CTkFrame(self, width=300, height=500)
    self.reload_btn = CTkButton(
      self.connection_frame,
      width=300,
      height=50,
      text="Reload",
      command=self.get_active_nodes
    )
    self.reload_btn.grid(row = 0, column = 0)
    self.connection_frame.grid(row = 0, column = 0, sticky = N)

    # Message frame
    self.message_frame = CTkFrame(self, width=700, height=500)
    self.message_frame.grid(row = 0, column = 1)


  

  def get_active_nodes(self):
    self.friend_list.configure(values = ["nam", "hoang", "dat"])

if __name__ == "__main__":
  app = App()
  app.mainloop()
