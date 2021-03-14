
import os
import sys
import datetime
import time
import json
import shutil
import modules.app_fun as app_fun
import modules.gui as gui
import modules.localdb as localdb
import modules.aes as aes
import modules.gui as gui
import modules.deamon as deamon
import modules.usb as usb

# props:
# self.cc=aes.Crypto()
# self.autostart
 
# self.first_run
# self.app_password
# self.dmn
class InitApp:

	def deamon_setup(self,tt):
		
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


		
		
		
		
	def __init__(self):
	
		self.close_thread=False

		app_fun.check_already_running(os.path.basename(__file__)) # check app not runnin - else escape !

		localdb.init_init() # init local DB initial settings - if not exist 
		self.cc=aes.Crypto()

		
		is_deamon_working=app_fun.check_deamon_running()
		idb=localdb.DB('init.db')
		db=localdb.DB( )

		tt= idb.select('init_settings',columns=["komodo","datadir","start_chain"]) 
		
		if is_deamon_working[0]:
			if len(tt)==0:
				gui.messagebox_showinfo("init.db file missing while running - exit", "init.db file missing while running - exit")
				exit()

		else: # deamon starting - ask paths 
			self.paths_confirmed=False
			self.ask_paths() 
			if not self.paths_confirmed:
				gui.messagebox_showinfo("Exiting app...", "Exiting app...")
				exit()
			
			tt= idb.select('init_settings',columns=["komodo","datadir","start_chain"])  
			if len(tt)==0 :
				gui.messagebox_showinfo("init.db file missing while running - exit", "init.db file missing while running - exit")
				exit()

		self.autostart=tt[0][2]
		if is_deamon_working[0]:
			self.autostart='yes'	

			
		deamon_cfg=self.deamon_setup(tt)
		dict_set={}
		dict_set['lock_db_threads']=[{'lock':'no'}]
		if idb.check_table_exist('lock_db_threads'):
			idb.upsert(dict_set,["lock"],{})
		
		self.first_run=False
		
		ppath=os.getcwd()	
		if os.path.exists(os.path.join(ppath , 'local_storage.encr'))==False and os.path.exists(os.path.join(ppath , 'local_storage.db'))==False:
			gui.messagebox_showinfo("Creating new local_storage.db","Creating new local_storage.db")
			localdb.init_tables()
			self.first_run=True

		self.app_password=None
		while self.app_password==None:
		
			tmpv=[]
			# self.ask_password( tmpv )
			gui.PassForm(tmpv,self.first_run)
			# print(102,tmpv)
			
			if len(tmpv)==0:
				gui.messagebox_showinfo("Canceled - exiting", "Exiting app...")
				exit()
			
			if self.isvalid(tmpv[0]): # checks if decryption is correct 
				self.app_password=tmpv[0]
			else:
				gui.messagebox_showinfo("Wrong password", "Password was not correct - try again.")
			
		###################### INIT DB AND DEAMON	
		if not self.first_run:
			localdb.init_tables()
		
		self.dmn=deamon.DeamonInit(deamon_cfg)
		self.dmn.init_clear_queue()	
		
		
		
		
		
	
	def update_paths(self,deamon,data,chain,parent):
		idb=localdb.DB('init.db')
		komodod_ok=False
		if os.path.exists( os.path.join(deamon,'komodod.exe') ) or os.path.exists(deamon+'/komodod'):
			komodod_ok=True
			
		komodo_cli_ok=False
		if os.path.exists( os.path.join(deamon,'komodo-cli.exe') ) or os.path.exists(deamon+'/komodo-cli'):
			komodo_cli_ok=True
			
		blockchain_data_ok=False
		decr_wal_exist=os.path.exists( os.path.join(data,'wallet.dat'))
		if decr_wal_exist or os.path.exists( os.path.join(data,'wallet.encr') ):
			blockchain_data_ok=True
			
			
			
			
		if decr_wal_exist: # backup!
		
			uu=usb.USB()
			
			while len(uu.locate_usb())==0:
				gui.messagebox_showinfo('Please insert USB pendrive','Please insert USB pendrive. Unencrypted wallet.dat file detected - needs to be backed up to external memory.')
				
			path=uu.locate_usb()
			path=path[0]
			path2=''
			while path2=='':
				tmpinitdir=os.getcwd()
				
				if sys.platform=='win32':
					if os.path.exists(path):
						tmpinitdir=path
						
				elif sys.platform!='win32':
					curusr=getpass.getuser()
					if os.path.exists('/media/'+curusr+'/'):
						tmpinitdir='/media/'+curusr+'/'
				
				# path=filedialog.askdirectory(initialdir=tmpinitdir, title="Select directory on your USB drive") # was 
				path2=gui.set_file( None,None,True,parent,init_path=tmpinitdir,title="Select directory on your USB drive" )
				
				if uu.verify_path_is_usb(path2):
					# gui.messagebox_showinfo('Starting backup','Please wait untill backup is finished and relevant message is displayed.' )
					dest=os.path.join(path2,'wallet_'+app_fun.now_to_str()+'.dat')  
					src= os.path.join(data,'wallet.dat')
					
					path2=gui.copy_progress(path2, 'Wallet backup to '+path2+'\n',src,dest)
					
					# try:
						# shutil.copy(src, dest)
						# path2=''
						# gui.messagebox_showinfo('Backup done','Your wallet is safe now at \n'+dest )
						# break
					# except:
						# exit()
				else:
					gui.messagebox_showinfo('Wrong path','Selected path is not USB drive, please try again.' )
					path2=''
		
		
		
		
		
		if komodod_ok and komodo_cli_ok and blockchain_data_ok:  

			dict_set={}
			dict_set['init_settings']=[]
			dict_set['init_settings'].append({
												"komodo":  deamon ,
												"datadir": data ,
												"start_chain":chain
											})
			
			idb.delete_where('init_settings')
			idb.insert(dict_set,["komodo","datadir","start_chain"]) #,"password_on"
			
		elif not komodod_ok:
			gui.messagebox_showinfo('Path for komodo deamon is wrong', deamon +'\n - no komodod file !')
		elif  not komodo_cli_ok:
			gui.messagebox_showinfo('Path for komodo-cli is wrong', data +'\n - no komodo-cli file !')
		else:
			gui.messagebox_showinfo('Path for blockchain data is wrong', data +'\n - no wallet file !')
			
	
	
	
	
	
	

	# qt dialog komodod, data dir 	
	def ask_paths(self): # read from db if possible

		idb=localdb.DB('init.db')
		
		preset=[]
		tt= idb.select('init_settings',columns=["komodo","datadir","start_chain"]) #,"password_on"
		if len(tt)>0:  

			for t in tt[0]: # single row only
				preset.append(t)
		else:

			preset=['','', 'no'] # preset win path
			
			curusr=getpass.getuser()
			curpath=os.getcwd().split('\\') #C:\Users\zxcv\AppData\Roaming\Komodo\PIRATE
			templatepath=curpath[0]+'/'+'/'.join(['Users',curusr,'AppData','Roaming','Komodo','PIRATE'])
			
			if sys.platform=='win32' and os.path.exists(templatepath):
				preset[1]=templatepath
			elif os.path.exists('/home/'+curusr+'/.komodo/PIRATE'):
				preset[1]='/home/'+curusr+'/.komodo/PIRATE'
			
		automate_rowids=[ [{'T':'LabelV', 'L':'Set proper paths, otherwise the deamon may freeze and you may need to kill the process manually.', 'span':3, 'width':120, 'style':{'bgc':'#eee','fgc':'red'}, 'uid':'none'},{  }, {  } ] ,
						[{'T':'LabelC', 'L':'Select deamon and cli path \n(komodod and komodo-cli inside)', 'width':32}, {'T':'Button','L':'Komodo path:','uid':'p1', 'width':15}, {'T':'LabelV', 'L':preset[0],'uid':'deamon', 'width':60} ],
						[{'T':'LabelC', 'L':'Select data directory', 'width':32}, {'T':'Button','L':'Data dir path:','uid':'p2', 'width':15}, {'T':'LabelV', 'L':preset[1],'uid':'data', 'width':60} ] ,
						[{'T':'LabelC', 'L':'Start blockchain', 'width':32}, {'T':'Combox','V':['no','yes'],'uid':'cs2', 'width':15 }, { } ],
						[{'T':'Button','L':'Confirm','uid':'conf', 'span':3, 'width':120}, {   }, { } ]	] #, 'width':128
			
		tw=gui.Table( params={'dim':[5,3],"show_grid":False, 'colSizeMod':[256,'toContent','stretch'], 'rowSizeMod':['toContent','toContent','toContent','toContent','toContent']})		
		tw.updateTable(automate_rowids)
		
		tw.cellWidget(1,1).set_fun(True,gui.set_file,tw.item(1,2),None,True,tw)
		tw.cellWidget(2,1).set_fun(True,gui.set_file,tw.item(2,2),None,True,tw)
		
		def getv(tmptw):
			self.paths_confirmed=True
			self.update_paths(tmptw.item(1,2).text(),  tmptw.item(2,2).text(), tmptw.cellWidget(3,1).currentText() ,tmptw)
			tmptw.parent().close()

		tw.cellWidget(4,0).set_fun(True, getv,tw)
		# tw.cellWidget(4,0).setFocus()
		# tw.cellWidget(4,0).setDefault(True)
		
		gui.CustomDialog(None,tw,'Enter zUnderNet', defaultij=[4,0])	
		
		
	

	
	
	def isvalid(self,pas):

		ppath=os.getcwd()
		
		if os.path.exists(os.path.join(ppath , 'local_storage.encr')):
			# print(256,pas)
			# print('decr path',os.path.join(ppath , 'local_storage.encr'), os.path.join(ppath,'local_storage.db'))
			self.cc.aes_decrypt_file( os.path.join(ppath , 'local_storage.encr'), os.path.join(ppath,'local_storage.db') , pas)
			
			db=localdb.DB( )
			at=db.all_tables()
			# print(at)
			if len(at)>0:
				app_fun.secure_delete(os.path.join(ppath , 'local_storage.encr'))

				return True
				
		elif os.path.exists(os.path.join(ppath , 'local_storage.db')):
			return True
			
		return False

	
	
	
		
	def encr_db(self,parent):
		
		dict_set={}
		dict_set['lock_db_threads']=[{'lock':'yes'}]
		idb=localdb.DB('init.db')
		if idb.check_table_exist('lock_db_threads'):
			idb.upsert(dict_set,["lock"],{})
			
		self.dmn.started=False # ???
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
			try:
			# if True:
				self.cc.aes_encrypt_file( os.path.join(ppath ,'local_storage.db'), os.path.join(ppath ,'local_storage.encr') , self.app_password)
				
				if os.path.exists(os.path.join(ppath ,'local_storage.encr')):
					
					app_fun.secure_delete(os.path.join(ppath ,'local_storage.db'))
				
					gui.messagebox_showinfo("local_storage.db encrypted", "DB secure: local_storage.db -> local_storage.encr ",parent)
			
					break
			except:
				print('Exception in delete local_storage.db', tryii)
			
			time.sleep(1)
			
			
			
			

	def on_closing(self,parent):
		# self.close_thread=True
		db=localdb.DB( )
		db.vacuum()
		is_deamon_working=app_fun.check_deamon_running()
		if is_deamon_working[0]:

			if gui.askokcancel("Quit", "Are you sure you want to quit? Blockchain deamon is still running. If you plan to shut down your computer it is better to STOP blockchain and quit afterwards.",parent):
			
				self.encr_db(parent)
				return True
			else:
				return False
		else:
			self.encr_db(parent)	
			return True
