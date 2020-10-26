

import tkinter as tk
from tkinter import filedialog, StringVar, ttk, messagebox,Scrollbar,simpledialog
import os
import sys
import queue
import datetime
import time
import json
import shutil
from functools import partial
import threading

import modules.app_fun as app_fun
import modules.wallet_tab as wallet_tab
import modules.localdb as localdb
import modules.deamon as deamon
import modules.wallet_api as wallet_api
import modules.flexitable as flexitable
import modules.addr_book as addr_book
import modules.msg as msg
import modules.aes as aes
import modules.donate as donate



global app_password,dmn,cc, wallet_display_set, queue_start_stop,autostart, queue_com

app_fun.check_already_running(os.path.basename(__file__))

localdb.init_init()
cc=aes.Crypto()

def deamon_setup(sql_res):
	
	dpath= tt[0][0]+'/komodod'
	cpath=tt[0][0]+'/komodo-cli'
	ddatap=tt[0][1]
	
	if sys.platform=='win32':
		dpath+='.exe'
		cpath+='.exe'

	deamon_cfg={
		"deamon-path":dpath, 
		"cli-path":cpath, 
		"ac_name": "PIRATE",
		"ac_params":"-ac_supply=0 -ac_reward=25600000000 -ac_halving=77777 -ac_private=1", # -rescan if needed
		"datadir":ddatap, 
		"fee":"0.0001"# "addnode":["136.243.102.225", "78.47.205.239"],
	}	
	
	return deamon_cfg




def isvalid(pas):

	ppath=os.getcwd()
	
	if os.path.exists(os.path.join(ppath , 'local_storage.encr')):
		
		cc.aes_decrypt_file( os.path.join(ppath , 'local_storage.encr'), os.path.join(ppath,'local_storage.db') , pas)
		
		idb=localdb.DB( )
		at=idb.all_tables()
		if len(at)>0:
			app_fun.secure_delete(os.path.join(ppath , 'local_storage.encr'))

			return True
			
	elif os.path.exists(os.path.join(ppath , 'local_storage.db')):
		return True
		
	return False

	
	
	
tt=None
deamon_cfg=None


###################### ASK INIT SETUP

is_deamon_working=app_fun.check_deamon_running()
idb=localdb.DB('init.db')
tt=idb.select('init_settings',columns=["komodo","datadir","start_chain"]) #"password_on",
if is_deamon_working[0]:
	if len(tt)==0:
		flexitable.messagebox_showinfo("init.db file missing while running - exit", "init.db file missing while running - exit")
		exit()
		

else: # is_deamon_working[0]==False:
	wallet_tab.ask_paths()
	# after change load tt from db
	tt=idb.select('init_settings',columns=["komodo","datadir","start_chain"])  
	if len(tt)==0:
		flexitable.messagebox_showinfo("init.db file missing while running - exit", "init.db file missing while running - exit")
		exit()

autostart=tt[0][2]
if is_deamon_working[0]:
	autostart='yes'	

	
deamon_cfg=deamon_setup(tt)
dict_set={}
dict_set['lock_db_threads']=[{'lock':'no'}]
if idb.check_table_exist('lock_db_threads'):
	idb.upsert(dict_set,["lock"],{})

	

app_password=None
pass_expected=True



ppath=os.getcwd()

###################### ENTER PASSWORD
if pass_expected:
	
	if os.path.exists(os.path.join(ppath , 'local_storage.encr'))==False and os.path.exists(os.path.join(ppath , 'local_storage.db'))==False:
		flexitable.messagebox_showinfo("Creating new local_storage.db","Creating new local_storage.db")
		idbtmp=localdb.DB()
		localdb.init_tables()

	while app_password==None:
	
		tmpv=[]
		wallet_tab.ask_password( tmpv )
		
		if len(tmpv)==0:
			flexitable.messagebox_showinfo("Cancelled - exiting", "Exiting app...")
			exit()
		
		if isvalid(tmpv[0]):
			app_password=tmpv[0]
		else:
			flexitable.messagebox_showinfo("Wrong password", "Password was not correct - try again.")
else:
	if not os.path.exists(os.path.join(ppath , 'local_storage.db')) and os.path.exists(os.path.join(ppath , 'local_storage.encr')):

		flexitable.messagebox_showinfo("Exiting", "You already have local storage DB - it is encrypted. Please run the app with password to decrypt it.")
		exit()
	


			
		

###################### ROOT INIT		

root = tk.Tk()
root.title('zUnderNet : wallet - chat - profile - blog - trade')
ttk.Style().configure("TNotebook.Tab", padding=[5, 2], width=12,   background="#ccc" )
ttk.Style().layout("TNotebook.Tab",
    [('Plain.Notebook.tab', {'children':
        [('Notebook.padding', {'side': 'top', 'children':
            # [('Notebook.focus', {'side': 'top', 'children':
                [('Notebook.label', {'side': 'top', 'sticky': ''})],
            # 'sticky': 'nswe'})],
        'sticky': 'nswe'})],
    'sticky': 'nswe'})])



###################### INIT DB AND DEAMON	
tt11=time.time()
localdb.init_tables()
dmn=deamon.DeamonInit(deamon_cfg)
dmn.init_clear_queue()	
	


###################### EXIT CONFIGS
			
def encr_db():
	global wallet_display_set ,dmn,cc #app_password
	
	# add db lock for threads
	dict_set={}
	dict_set['lock_db_threads']=[{'lock':'yes'}]
	idb=localdb.DB('init.db')
	if idb.check_table_exist('lock_db_threads'):
		idb.upsert(dict_set,["lock"],{})
		
	dmn.started=False # ???
	ppath =os.getcwd()
	
	if localdb.is_busy():
		time.sleep(1)
	
	tryii=2
	while localdb.is_busy():

		time.sleep(1)
		tryii=tryii-1
		if tryii<0:
			print('exit anyway ...')
			break
			
		localdb.del_busy_too_long()
			
	tryii=3
	while tryii>0:
		tryii=tryii-1
		# try:
		if True:
			cc.aes_encrypt_file( os.path.join(ppath ,'local_storage.db'), os.path.join(ppath ,'local_storage.encr') , wallet_display_set.password)
			
			if os.path.exists(os.path.join(ppath ,'local_storage.encr')):
				
				app_fun.secure_delete(os.path.join(ppath ,'local_storage.db'))
			
				flexitable.messagebox_showinfo("local_storage.db encrypted", "DB secure: local_storage.db -> local_storage.encr ")
		
				break
		# except:
			print('Exception in delete local_storage.db', tryii)
		
		time.sleep(1)

global close_thread	
close_thread=False
	
def on_closing():
	global dmn, close_thread #, app_password
	close_thread=True
	idb=localdb.DB( )
	idb.vacuum()
	is_deamon_working=app_fun.check_deamon_running()
	if is_deamon_working[0]:

		if messagebox.askokcancel("Quit", "Are you sure you want to quit? Blockchain deamon is still running. If you plan to shut down your computer it is better to STOP blockchain and quit afterwards."):
		
			encr_db()#True	
			root.destroy()
	else:
		encr_db()	
		root.destroy()
		
root.protocol("WM_DELETE_WINDOW", on_closing)


###################### TABS

tabs0=ttk.Notebook(root)
tabs0.pack(fill='both')

	
queue_start_stop = queue.Queue()	
queue_com=queue.Queue()	
additional_obj={}

stat_lab,bstartstop,wallet_summary_frame,wallet_details,wallet_display_set  =wallet_tab.setwallet(tabs0,app_password,autostart,queue_start_stop,queue_com,additional_obj)


################################################### Address book
tabs2=ttk.Frame(tabs0)  
tabs2.pack()
tabs0.add( tabs2, text = 'Address book')

addrb=addr_book.AddressBook(wallet_display_set)
addrb.setaddrbook(tabs2)
# t2=time.time()

# print(t2-t1)
###################################################  chat
tabs3=ttk.Frame(tabs0)  
tabs3.pack()
tabs0.add( tabs3, text = 'Messages')

messages=msg.Msg(tabs3,tabs0,addrb)


# print('2 started',dmn.started,'autostart',autostart)
def thread_loop():

	global queue_start_stop,autostart,queue_com,wallet_display_set,dmn
	
	while len(additional_obj)!=4:
		time.sleep(1)
		
	dmn.set_wallet_widgets( stat_lab,bstartstop,wallet_summary_frame,wallet_details,wallet_display_set,additional_obj['queue_status'],additional_obj['tahi'],additional_obj['txhi'],additional_obj['notif'],messages)	
	
	while not close_thread:
	
		grid_queue=wallet_display_set.prepare_queue_frame()
		if len(grid_queue)>0:
			additional_obj['queue_status'].update_frame(grid_queue)
			wallet_display_set.queue_frame_buttons( grid_queue, additional_obj['queue_status'])
	
		
		if queue_com.qsize(): # start stop blockchain ON/OFF
			try:
				id,msgstr,ffunn = queue_com.get(0)
				idb=localdb.DB()
				done=idb.select('queue_done',['result'],{'id':['=',id]})
				if len(done)>0:
					ffunn( id,msgstr,done)
			except Queue.Empty:
				pass
	
	
		
		if queue_start_stop.qsize(): # start stop blockchain ON/OFF
			try:
				cmd = queue_start_stop.get(0)
				if cmd['cmd']=='stop_deamon':
					dmn.stop_deamon()
				elif cmd['cmd']=='start_deamon':
					dmn.start_deamon(cmd['addrescan'])
			except : #Queue.Empty:
				pass
			
		if dmn.started:
			dmn.update_status()
		elif autostart!='no':
			autostart='no'
			dmn.start_deamon( )
			
		time.sleep(2)
		# root.after(2000,thread_loop)

# root.after(0,thread_loop)
t = threading.Thread(target=thread_loop)
t.daemon = True 
t.setDaemon(True)
t.start()



###################################################  donate
tabs_donate=ttk.Frame(tabs0)  
tabs_donate.pack()
tabs0.add( tabs_donate, text = 'Donate')
donate.donate(tabs_donate,wallet_display_set)


################################################### Profile

# tabs4=ttk.Frame(tabs0)  
# tabs4.pack()
# tabs0.add( tabs4, text = 'Profile')

################################################### Blog
# tabs5=ttk.Frame(tabs0)  
# tabs5.pack()
# tabs0.add( tabs5, text = 'Blog')

# tabs6=ttk.Frame(tabs0)  
# tabs6.pack()
# tabs0.add( tabs6, text = 'Forum')

# tabs7=ttk.Frame(tabs0)  
# tabs7.pack()
# tabs0.add( tabs7, text = 'Market')

# tabs8=ttk.Frame(tabs0)  
# tabs8.pack()
# tabs0.add( tabs8, text = 'Vendor')

root.mainloop()