# wallet main tab


import tkinter as tk
from tkinter import filedialog, StringVar, ttk, messagebox,Scrollbar,Toplevel,simpledialog
import os
import sys
# from tkcalendar import Calendar, DateEntry
import datetime, time
import json
import shutil
from functools import partial
import modules.flexitable as flexitable
import random
import modules.deamon as deamon
import modules.localdb as localdb
import getpass
import modules.app_fun as app_fun
from modules.wallet_display_set import WalDispSet
import modules.usb as usb
from modules.tasks_history import TasksHistory
from modules.tx_history import TransactionsHistory
from modules.frame_settings import Settings
from modules.notifications import Notifications
import modules.addr_book as addr_book

def update_paths(eldeamon,eldata,elchain,db,frame):

	komodod_ok=False
	if os.path.exists(eldeamon.get()+'/komodod.exe') or os.path.exists(eldeamon.get()+'/komodod'):
		komodod_ok=True
		
	komodo_cli_ok=False
	if os.path.exists(eldeamon.get()+'/komodo-cli.exe') or os.path.exists(eldeamon.get()+'/komodo-cli'):
		komodo_cli_ok=True
		
	blockchain_data_ok=False
	decr_wal_exist=os.path.exists(eldata.get()+'/wallet.dat')
	if decr_wal_exist or os.path.exists(eldata.get()+'/wallet.encr'):
		blockchain_data_ok=True
		
	if decr_wal_exist: # backup!
	
		uu=usb.USB()
		
		while len(uu.locate_usb())==0:
			messagebox.showinfo('Please insert USB pendrive','Please insert USB pendrive. Unencrypted wallet.dat file detected - needs to be backed up to external memory.')

		path=''
		while path==None or path=='':
			path=filedialog.askdirectory(initialdir=os.getcwd(), title="Select directory on your USB drive")
			if uu.verify_path_is_usb(path):
				messagebox.showinfo('Starting backup','Please wait untill backup is finished and relevant message is displayed.' )
				dest=os.path.join(path,'wallet_'+app_fun.now_to_str()+'.dat')  
				src=eldata.get()+'/wallet.dat'
				
				try:
					shutil.copy(src, dest)
					path=''
					messagebox.showinfo('Backup done','Your wallet is safe now at \n'+dest )
					break
				except:
					exit()
			else:
				messagebox.showinfo('Wrong path','Selected path is not USB drive, please try again.' )
				path=''
	
	
	if komodod_ok and komodo_cli_ok and blockchain_data_ok: #os.path.exists(eldeamon.get()) and os.path.exists(eldata.get()):

		dict_set={}
		dict_set['init_settings']=[]
		dict_set['init_settings'].append({
											"komodo": eldeamon.get(),
											"datadir":eldata.get(),
											# "password_on":elpas.get(),
											"start_chain":elchain.get()
										})
		
		db.delete_where('init_settings')
		db.insert(dict_set,["komodo","datadir","start_chain"]) #,"password_on"
		frame.destroy()
	elif not komodod_ok:
		flexitable.messagebox_showinfo('Path for komodo deamon is wrong',eldeamon.get()+'\n - no komodod file !')
	elif  not komodo_cli_ok:
		flexitable.messagebox_showinfo('Path for komodo-cli is wrong',eldata.get()+'\n - no komodo-cli file !')
	else:
		flexitable.messagebox_showinfo('Path for blockchain data is wrong',eldata.get()+'\n - no wallet file !')
		
		
def ask_paths(): # read from db if possible

	idb=localdb.DB('init.db')
	
	preset=[]
	tt=idb.select('init_settings',columns=["komodo","datadir","start_chain"]) #,"password_on"
	if len(tt)>0: #idb.check_table_exist('init_settings'):

		for t in tt[0]: # single row only
			preset.append(t)
	else:

		preset=['','', 'no']
		# preset win path
		curusr=getpass.getuser()
		curpath=os.getcwd().split('\\') #C:\Users\zxcv\AppData\Roaming\Komodo\PIRATE
		templatepath=curpath[0]+'/'+'/'.join(['Users',curusr,'AppData','Roaming','Komodo','PIRATE'])
		
		if sys.platform=='win32' and os.path.exists(templatepath):
			preset[1]=templatepath
		elif os.path.exists('/home/'+curusr+'/komodo/PIRATE'):
			preset[1]='/home/'+curusr+'/komodo/PIRATE'
		
	rootframe = tk.Tk()
	rootframe.title('Enter zUnderNet')
	
	frame_settings= ttk.LabelFrame(rootframe,text='Initial settings') 
	frame_settings.pack()
	
	automate_rowids=[ [{'T':'LabelC', 'L':'Set proper paths, otherwise the deamon may freez and you may need to kill the process manually.', 'span':3, 'width':120}, { }, { } ] ,
					[{'T':'LabelC', 'L':'Select deamon and cli path (komodod and komodo-cli inside)'}, {'T':'Button','L':'Komodo path:','uid':'p1'}, {'T':'LabelV', 'L':preset[0],'uid':'deamon'} ],
					[{'T':'LabelC', 'L':'Select data directory'}, {'T':'Button','L':'Data dir path:','uid':'p2'}, {'T':'LabelV', 'L':preset[1],'uid':'data'} ] ,
					[{'T':'LabelC', 'L':'Start blockchain'}, {'T':'Combox','V':['no','yes'],'uid':'cs2' }, {'T':'LabelE'} ],
					# [{'T':'LabelC', 'L':'Set password protection'}, {'T':'Combox','V':['no','yes'],'uid':'cs1'}, {} ],
					[{'T':'Button','L':'Confirm','uid':'conf', 'span':3, 'width':120}, {  }, { } ]	] #, 'width':128
									
	grid_settings=[]
	for ij,ar in enumerate(automate_rowids):
		tmpdict={}
		tmpdict[ij]=ar
		grid_settings.append(tmpdict)
					
					
	settings=flexitable.FlexiTable(frame_settings,grid_settings)#, scale_width=False
	
	settings.set_cmd( 'p1',['deamon'],flexitable.setdir )
	settings.set_cmd( 'p2',['data'],flexitable.setdir )
	settings.set_cmd( 'conf',['deamon','data','cs2', idb, rootframe], update_paths ) # save to db
	# settings.set_textvariable('cs1',preset[2])
	settings.set_textvariable('cs2',preset[2])
	# print('zxc')
	
	def on_closing():
		rootframe.destroy()
		exit()
	
	rootframe.protocol("WM_DELETE_WINDOW", on_closing)
	rootframe.mainloop()
	
	
	

def ask_password(tmpval):
	
	rootframe = tk.Tk()
	rootframe.title('Enter zUnderNet')
	ttk.Label(rootframe,text='Enter password to decrypt wallet.dat and local DB').pack(fill='x')
	tmpvar=StringVar()
	entr=ttk.Entry(rootframe,textvariable=tmpvar, show='*')
	entr.pack(fill='x')
	tmpvar.set('')
	
	
	def get_pass(*args):
		
		if len(entr.get().strip())>0:
			tmpvar.set(entr.get().strip())
		
		if len(tmpvar.get().strip())>0:
			tmpval.append(tmpvar.get().strip())
			rootframe.destroy()
			
	
	ttk.Button(rootframe,text='Enter',command=get_pass ).pack(fill='x')
	entr.bind('<Return>', get_pass)
	entr.focus()
	
	def on_closing():
		
		rootframe.destroy()
		
	
	rootframe.protocol("WM_DELETE_WINDOW", on_closing)
		
	rootframe.mainloop()



	
	
	
	
	

def setwallet(tabs0,app_password,autostart,queue_start_stop, queue_com, addit_frames ): 
	tabs1=ttk.Notebook(tabs0)
	tabs1.pack(fill='both')
	tabs0.add( tabs1, text = 'Wallet')


	#########
	######### SUBTAB 1 - Balance
	#########
	frame01=ttk.Frame(tabs1, width=200,height=200) 
	frame01.pack() #fill='both'
	tabs1.add( frame01, text = 'Balance')
	
	frame01.columnconfigure(0, weight=1)
	frame01.columnconfigure(1, weight=1)
	
	###
	### FRAME 1 - blockchain status
	###
	stat = ttk.LabelFrame(frame01,text='Blockchain status')
	stat.grid(row=0,column=1,sticky='nswe',padx=10,pady=5)
	
	stat_lab=StringVar()
	stat_lab.set('Blockchain off')
	ttk.Label(stat,textvariable=stat_lab).pack(side='left' )
	
	
	startstop=StringVar()
		
	bstartstop=ttk.Button(stat,textvariable=startstop)
	bstartstop.pack(side='right',padx=10,pady=5 )
	
	if autostart=='yes':
		startstop.set('Stop blockchain')
		bstartstop.configure(state='disabled')
	else:
		startstop.set('Start blockchain')

	def togglestartstop(elem):
		if elem.get()=='Stop blockchain':
			elem.set('Start blockchain')
			queue_start_stop.put({'cmd':'stop_deamon'})
			
		else:
			elem.set('Stop blockchain')
			 
			def restart(addrescan):
				if addrescan=='No':
					addrescan=False
				else:
					addrescan=True
				
				queue_start_stop.put({'cmd':'start_deamon','addrescan':addrescan})
				
			flexitable.simple_opt_box( "Rescan wallet?",['No','Yes'],restart)
				
	bstartstop.configure(command=partial(togglestartstop,startstop))

	
	
	###
	### FRAME 2 - summary
	### todo: save to db, add refresh, 
	

	summary = ttk.LabelFrame(frame01,text='Summary')
	summary.grid(row=0,column=0,sticky='nsew',padx=10,pady=5)
	summary.columnconfigure(0, weight=1)
	
	global wds 
	wds=WalDispSet(app_password,queue_com)
	
	
	grid_lol_wallet_sum= wds.prepare_summary_frame(True)

	
	
	wallet_summary_frame=flexitable.FlexiTable(summary,grid_lol_wallet_sum)
	
	
	###
	### FRAME 3 - wallet balances
	###

	
	table = ttk.LabelFrame(frame01,text='Balance by address') #, style='new.TLabelframe'
	table.grid(row=1,column=0,sticky='nsew',padx=10,pady=5)
	table.columnconfigure(0, weight=1)

	grid_lol3=wds.get_header(False)
	
	wallet_details=flexitable.FlexiTable(table,grid_lol3,600,True) #params=None, grid_lol=None
	
	
	def save_wallet_display(opt,*evnt):
		global wds
		idb=localdb.DB()
		table={}
		
		vv=wallet_summary_frame.get_value(opt.replace('ing','')) # name similar to uid hence hack 
		table['wallet_display']=[{'option':opt, 'value':vv  }]
		idb.upsert(table,['option','value'],{'option':['=',"'"+opt+"'"]})
		
		while wds.is_locked():
			time.sleep(1)
			
		wds.lock_basic_frames()
		
		grid_lol_wallet_sum=wds.prepare_summary_frame()
		wallet_summary_frame.update_frame(grid_lol_wallet_sum)
		
		grid_lol3=wds.prepare_byaddr_frame()
		wallet_details.update_frame(grid_lol3)
		wds.prepare_byaddr_button_cmd(grid_lol3,wallet_details)
		
		wds.unlock_basic_frames()
		
		
		
	wallet_summary_frame.bind_combox_cmd('sort',[ 'sorting'],save_wallet_display)
	wallet_summary_frame.bind_combox_cmd('round',[ 'rounding'],save_wallet_display)
	wallet_summary_frame.bind_combox_cmd('filter',[ 'filtering'],save_wallet_display)
	wallet_summary_frame.set_cmd('addaddr',[],wds.new_addr) #'addaddr'
	wallet_summary_frame.set_cmd('export',[],wds.export_wallet) #'addaddr'
	
	opt=wds.get_options(True)
	tmprounding=opt['rounding'] #self.get_rounding_str()
	tmpsorting=opt['sorting'] #self.get_sorting()
	tmpfiltering=opt['filtering'] #self.get_filtering()
	wallet_summary_frame.set_textvariable('round',tmprounding)
	wallet_summary_frame.set_textvariable('sort',tmpsorting)
	wallet_summary_frame.set_textvariable('filter',tmpfiltering)
	save_wallet_display('sorting' )
	wallet_details.after(500,save_wallet_display, 'sorting' )
	
	###
	### FRAME 4 - manual queue
	###
	
	queue = ttk.LabelFrame(frame01,text='Tasks queue') #, style='new.TLabelframe'
	queue.grid(row=1,column=1,sticky='nswe',padx=10,pady=5)
	queue.columnconfigure(0, weight=1)
	
	# grid_lol4=wds.queue_header()
	# queue_status=None #flexitable.FlexiTable(queue,grid_lol4,400,True)
	
	def set_queue():
		global wds #, queue_status
		grid_lol4=wds.prepare_queue_frame(True)
		queue_status=flexitable.FlexiTable(queue,grid_lol4,400,True) #params=None, grid_lol=None
		wds.queue_frame_buttons( grid_lol4,queue_status)
		addit_frames['queue_status']=queue_status
	
	queue.after(1000,set_queue)
	
	#########
	######### SUBTAB 2 - Notifications
	#########
	frame_notif=ttk.Frame(tabs1, width=200,height=200) 
	frame_notif.pack(fill='both',expand=True)
	tabs1.add( frame_notif, text = 'Notifications')
	global addrb
	addrb=addr_book.AddressBook(wds)
	
	def set_notif():
		global notif,addrb
		notif=Notifications(frame_notif,tabs1,addrb )
		addit_frames['notif']=notif
	
	frame_notif.after(2000,set_notif)
	
	#########
	######### SUBTAB 2 - History of transactions
	#########
	frame02=ttk.Frame(tabs1, width=200,height=200) 
	frame02.pack(fill='both',expand=True)
	tabs1.add( frame02, text = 'TX history')
	# filter type, command, dates: last 24h default, last week, last month, last 12 months, all

	def set_history():
		global txhi
		txhi=TransactionsHistory(frame02)
		addit_frames['txhi']=txhi
	
	frame02.after(2000,set_history)
	
	
	#########
	######### SUBTAB 2 - History of tasks 
	#########
	tt11=time.time()
	frame03=ttk.Frame(tabs1, width=200,height=200) 
	frame03.pack(fill='both',expand=True)
	tabs1.add( frame03, text = 'Tasks history')

	def set_tasks():
		global tahi
		# tahi=TransactionsHistory(frame03)
		tahi=TasksHistory(frame03)
		
		addit_frames['tahi']=tahi
		
		def _on_resize(event):
		
			sx=float(event.width)/frame01.winfo_reqwidth()
			sy=float(event.height)/frame01.winfo_reqheight()
			wallet_details.resize_canvas(sx,sy)
			
			tahi.main_table.resize_canvas(sx,sy)
		
		frame01.bind("<Configure>", _on_resize)
	
	frame03.after(3000,set_tasks)
	

	###
	### START DEAMON
	###
	
	#########
	######### SUBTAB 3 - Settings
	#########
	frame_settings=ttk.Frame(tabs1) 
	frame_settings.pack(fill='both',expand=True)
	tabs1.add( frame_settings, text = 'Settings')
	
	sett=Settings(frame_settings,wds)
	
	
	return stat_lab,bstartstop,wallet_summary_frame,wallet_details,wds,addrb  #,queue_status,tahi,txhi,notif
	
