#best feature :)

import tkinter as tk
from tkinter import filedialog, StringVar, ttk, messagebox, Toplevel 
from functools import partial

def donate(parent_frame,wds):
		  
	frame0=ttk.Frame(parent_frame )  

	dbutton=ttk.Button(parent_frame,text='Donate 1 Pirate')
	
	dbutton.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

	addr='zs1nf7lsdgxpfj4m6tt7p0s4jfmnlhcdplnuu386xd5nfkm498w6nugvnaj20gfweeysg3zz6xutzm'
	dbutton.configure( command=partial(wds.send_to_addr,addr,1 ) )
	
		