
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
import getpass

# props:
# self.cc=aes.Crypto()
# self.autostart
 
# self.first_run
# self.app_password
# self.dmn
class InitApp:

	def correctWin(self,p1,p2):
		if sys.platform=='win32':
			p1+='.exe'
			p2+='.exe'
			
		return p1,p2

	def deamon_setup(self,tt):
		
		self.chain='pirate'
		
		verus=False
		pirated=False
		dpath=os.path.join(tt[0][0],'komodod')
		cpath=os.path.join(tt[0][0],'komodo-cli')
		
		dpath,cpath=self.correctWin(dpath,cpath)
		
		# if sys.platform=='win32':
			# dpath+='.exe'
			# cpath+='.exe'
			
		# print(dpath,os.path.exists(dpath))
		if not os.path.exists(dpath):
			dpath=os.path.join(tt[0][0],'pirated')
			cpath=os.path.join(tt[0][0],'pirate-cli')
			
			dpath,cpath=self.correctWin(dpath,cpath)
			# if sys.platform=='win32':
				# dpath+='.exe'
				# cpath+='.exe'
			if not os.path.exists(dpath):	
				dpath=os.path.join(tt[0][0],'verusd')
				cpath=os.path.join(tt[0][0],'verus')
				dpath,cpath=self.correctWin(dpath,cpath)
				verus=True
				if not os.path.exists(dpath):
					print('Wrong path, file does not exist: ',dpath)
					exit()
			else:
				pirated=True
		
		ddatap=tt[0][1]
		
		

		deamon_cfg={
			"deamon-path":dpath, 
			"cli-path":cpath, 
			"wallet":self.wallet,
			"ac_name": "PIRATE",
			"ac_params":"-ac_supply=0 -ac_reward=25600000000 -ac_halving=77777 -ac_private=1", # -rescan if needed
			"datadir":ddatap, 
			"fee":"0.0001"# "addnode":["136.243.102.225", "78.47.205.239"],
		}	
		
		if pirated:
			
			deamon_cfg={
				"deamon-path":dpath, 
				"cli-path":cpath, 
				"wallet":self.wallet,
				"datadir":ddatap, 
				"fee":"0.0001"# "addnode":["136.243.102.225", "78.47.205.239"],
			}
		elif verus:
			self.chain='verus'
			deamon_cfg={
				"deamon-path":dpath, 
				"cli-path":cpath, 
				"wallet":self.wallet,
				"datadir":ddatap, 
				"fee":"0.0001"
			}
		
			
		# print(deamon_cfg)
		
		return deamon_cfg


		
		
		
	# need to generate name here for config and save it 	
	def __init__(self):
		self.wallet ='tmpwallet.dat'
		# self.data_files['wallet']
		self.data_files={'wallet':'wallet','db':'local_storage'} # .dat/.encr or .db/.encr
		self.was_derypted_warning=False
		self.close_thread=False
		self.chain='pirate'

		app_fun.check_already_running(os.path.basename(__file__)) # check app not runnin - else escape !

		localdb.init_init() # init local DB initial settings - if not exist 
		self.cc=aes.Crypto()

		
		is_deamon_working=app_fun.check_deamon_running()
		idb=localdb.DB('init.db')
		# db=localdb.DB( )

		tt= idb.select('init_settings',columns=["komodo","datadir","data_files"]) 
		
		if is_deamon_working[0]:
			if len(tt)==0:
				gui.messagebox_showinfo("init.db file missing while running - exit", "init.db file missing while running - exit")
				exit()
			# print(tt)	
			tmp=json.loads(tt[0][2])
			self.data_files={ 'wallet':tmp['wallet'],'db':tmp['db'] }

		else: # deamon starting - ask paths 
			self.paths_confirmed=False
			self.ask_paths() 
			if not self.paths_confirmed:
				gui.messagebox_showinfo("Exiting app...", "Exiting app...")
				exit()
			
			tt= idb.select('init_settings',columns=["komodo","datadir", "data_files"])  
			if len(tt)==0 :
				gui.messagebox_showinfo("init.db file missing while running - exit", "init.db file missing while running - exit")
				exit()
				
			# idb.upsert(dict_set,["lock"],{})

		# self.autostart=tt[0][2]
		self.autostart='no'	
		if is_deamon_working[0]:
			self.autostart='yes'	
			
		dict_set={}
		dict_set['lock_db_threads']=[{'lock':'no'}]
		if idb.check_table_exist('lock_db_threads'):
			idb.upsert(dict_set,["lock"],{})
		
		self.first_run=False
		
		ppath=os.getcwd()	
		if os.path.exists(os.path.join(ppath , self.data_files['db']+'.encr'))==False and os.path.exists(os.path.join(ppath ,self.data_files['db']+'.db'))==False:
			newdbfname= self.data_files['db']+'.db' 
			gui.messagebox_showinfo("Creating new database","Creating new database file:\n"+newdbfname)
			localdb.init_tables(newdbfname)
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
			localdb.init_tables(self.data_files['db']+'.db')
		
		self.wallet = self.data_files['wallet']+'.dat'
		self.db = self.data_files['db']+'.db'
		
		deamon_cfg=self.deamon_setup(tt)
		# print(155,deamon_cfg)
		self.dmn=deamon.DeamonInit(deamon_cfg,self.db)
		self.dmn.init_clear_queue()	
		# self.data_files={ 'wallet':tmp['wallet'],'db':tmp['local_storage'] }
		
		
		
		
		
		
	
	def update_paths(self,deamon,data, parent,new_wallet):
	
		idb=localdb.DB('init.db')
		komodod_ok=False
		allowed_deamons=['komodod.exe','komodod','pirated','pirated.exe','verusd','verusd.exe']
		for ad in allowed_deamons:
			if os.path.exists( os.path.join(deamon,ad) ):
				komodod_ok=True
				break
				
		komodo_cli_ok=False
		allowed_cli=['komodo-cli.exe','komodo-cli','pirate-cli','pirate-cli.exe','verus','verus.exe']
		for ac in allowed_cli:
			if os.path.exists( os.path.join(deamon,ac) ):
				komodo_cli_ok=True
				break		
				
		
		# if os.path.exists( os.path.join(deamon,'komodod.exe') ) or os.path.exists(deamon+'/komodod') or os.path.exists( os.path.join(deamon,'pirated.exe') ) or os.path.exists(deamon+'/pirated'):
			# komodod_ok=True
			
		# if os.path.exists( os.path.join(deamon,'komodo-cli.exe') ) or os.path.exists(deamon+'/komodo-cli'):
			# komodo_cli_ok=True
			
		blockchain_data_ok=False
		test_ppath=os.path.join(data,self.data_files['wallet']+'.dat')
		decr_wal_exist=os.path.exists( test_ppath  ) #app_fun.fileExist(data,cond={'start':self.data_files['wallet'],'end':'.dat' })
		self.was_derypted_warning=(decr_wal_exist==True)
		
		# print('checked ', test_ppath ,decr_wal_exist)
		# print( decr_wal_exist,app_fun.fileExist(data,cond={'start':self.data_files['wallet'],'end':'.encr' }))
		if decr_wal_exist or app_fun.fileExist(data,cond={'start':self.data_files['wallet'],'end':'.encr' }):
			blockchain_data_ok=True
		
		# decr_wal_exist=os.path.exists( os.path.join(data,self.data_files['wallet']+'.dat'))
		# if decr_wal_exist or os.path.exists( os.path.join(data,self.data_files['wallet']+'.encr') ):
			# blockchain_data_ok=True
			
		# print('blockchain_data_ok',blockchain_data_ok,new_wallet,str_data_files)
			
			
		if decr_wal_exist: # backup!
			
			gui.messagebox_showinfo('Wallet backup required','Decrypted wallet exist - backup required')
			
			uu=usb.USB()
			
			while len(uu.locate_usb())==0:
				gui.messagebox_showinfo('Please insert USB pendrive','Please insert USB pendrive. Unencrypted wallet file detected - needs to be backed up to external memory.')
				
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
				# print(path2)
				if path2!=None:
					if uu.verify_path_is_usb(path2):
						# gui.messagebox_showinfo('Starting backup','Please wait untill backup is finished and relevant message is displayed.' )
						dest=os.path.join(path2,self.data_files['wallet']+ '_'+app_fun.now_to_str()+'.dat')  
						src= os.path.join(data,self.data_files['wallet']+'.dat')
						
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
				else:
					# path2=''
					exit()
		
		
		
		# print(254,deamon,data,self.data_files)
		
		if komodod_ok and komodo_cli_ok  and (blockchain_data_ok or new_wallet):  

			# wallet name = wallet_ABECUP.dat local_storage_ABECUP.dat
		
			# data_files=json.dumps()
		
			dict_set={}
			dict_set['init_settings']=[]
			dict_set['init_settings'].append({
												"komodo":  deamon ,
												"datadir": data  ,
												"data_files":json.dumps(self.data_files)
											})
			
			idb.delete_where('init_settings')
			idb.insert(dict_set,["komodo","datadir","data_files" ]) #,"password_on"
			
		elif not komodod_ok:
			gui.messagebox_showinfo('Path for pirate deamon is wrong', deamon +'\n - no pirated file !')
			exit()
		elif  not komodo_cli_ok:
			gui.messagebox_showinfo('Path for pirate-cli is wrong', data +'\n - no pirate-cli file !')
			exit()
		elif not new_wallet:
			gui.messagebox_showinfo('Path for blockchain data is wrong', data +'\n - no wallet file !')
			exit()
			
	
	
	
	
	
	

	# qt dialog komodod, data dir 	
	def ask_paths(self): # read from db if possible
	
		# self.data_files['wallet'], self.data_files['db']
		tmpwallet=['Create new','Select file']

		idb=localdb.DB('init.db')
		
		preset=[]
		tt= idb.select('init_settings',columns=["komodo","datadir",'data_files']) #,"password_on" "start_chain",
		if len(tt)>0:  

			for t in tt[0]: # single row only
				preset.append(t)
				
			if preset[2]!=None:
				tmpj=json.loads(preset[2])
				tmpwallet=[tmpj['wallet'] , 'Create new','Select file']
		else:

			preset=['','', 'New' ] # preset win path "{'wallet':'wallet','db':'local_storage'}"
			
			curusr=getpass.getuser()
			curpath=os.getcwd().split('\\') #C:\Users\zxcv\AppData\Roaming\Komodo\PIRATE
			templatepath=os.path.join(curpath[0],'Users',curusr,'AppData','Roaming','Komodo','PIRATE')
			# curpath[0]+'/'+'/'.join(['Users',curusr,'AppData','Roaming','Komodo','PIRATE'])
			
			if sys.platform=='win32' and os.path.exists(templatepath):
				preset[1]=templatepath
			elif os.path.exists('/home/'+curusr+'/.komodo/PIRATE'):
				preset[1]='/home/'+curusr+'/.komodo/PIRATE'
				
		# combobox actions:
		# new - generate name
		# select file - open dialog and select -> generate db name relevant
		# other - select value 
		# END: update 
			
			
			
		automate_rowids=[ [{'T':'LabelV', 'L':'Set proper paths, otherwise the deamon may freeze and you may need to kill the process manually.', 'span':3},{  }, {  } ] ,
						[{'T':'LabelC', 'L':'Select deamon and cli path \n(pirated and pirate-cli inside)', 'width':32}, {'T':'Button','L':'Pirated path:','uid':'p1', 'width':15}, {'T':'LabelV', 'L':preset[0],'uid':'deamon', 'width':60} ],
						[{'T':'LabelC', 'L':'Select data directory', 'width':32}, {'T':'Button','L':'Data dir path:','uid':'p2', 'width':15}, {'T':'LabelV', 'L':preset[1],'uid':'data', 'width':60} ] ,
						[{'T':'LabelC', 'L':'Select wallet', 'width':32}, {'T':'Combox','V':tmpwallet,'uid':'cs2', 'width':15 }, { } ],
						# [{'T':'LabelC', 'L':'Start blockchain', 'width':32}, {'T':'Combox','V':['no','yes'],'uid':'cs2', 'width':15 }, { } ],
						[{'T':'Button','L':'Confirm','uid':'conf', 'span':3, 'width':120}, {   }, { } ]	] #, 'width':128
			
		tw=gui.Table( params={'dim':[5,3],"show_grid":False, 'colSizeMod':[256,'toContent','stretch'], 'rowSizeMod':['toContent','toContent','toContent','toContent','toContent']})		
		tw.updateTable(automate_rowids)
		
		# on data dir change default to new wallet file 
		def setDefWalOnDatadirChange():
			tw.cellWidget(3,1).setIndexForText('Create new') 
			
		tw.cellWidget(1,1).set_fun(True,gui.set_file,tw.item(1,2),None,True,tw)
		tw.cellWidget(2,1).set_fun(True,gui.set_file,tw.item(2,2),None,True,tw,os.getcwd(), "Select relevant file", setDefWalOnDatadirChange)
		
		
		def combox(cbtn,tw):
			if cbtn.currentText()=='Select file':
				sel_file=gui.get_file_dialog('Select wallet file' ,init_path=tw.item(2,2).text(),parent=tw,name_filter="Data (*.dat *.encr)") #preset[1]
				sel_file=sel_file[0]
				if sel_file=='':
					return
					
				h,t=os.path.split(sel_file)	
				
				if len(t.split())>1:
					gui.messagebox_showinfo('Wrong wallet file name', 'Wallet file name cannot contain spaces or white characters!')
					return
				
				cbtn.addItem( t , t )
				cbtn.setIndexForText( t)
				
		tw.cellWidget(3,1).every_click=True
		tw.cellWidget(3,1).set_fun( combox,tw)
		
		
		
		
		def getv(tmptw):#self.data_files={'wallet':'wallet','db':'local_storage'}
		
			cbtntxt=tmptw.cellWidget(3,1).currentText()
			data_path=tmptw.item(2,2).text()
			# print(data_path)
			
			tmp_wal=''
			newwallet=False
		
			if cbtntxt=='Create new':
				tmprand=''
				while True:
					tmprand=self.cc.rand_slbls(3)
					tmp_wal='wallet_'+tmprand+'.dat'
					tmp_db='local_storage_'+tmprand+'.db'
					if not os.path.exists(os.path.join(data_path,tmp_wal)) and not os.path.exists( os.path.join(os.getcwd(),tmp_db) ):
						# print(os.path.join(data_path,tmp_wal), os.path.join(data_path,tmp_db) )
						# with open(os.path.join(data_path,tmp_wal),'wb'):
							# print('created new wallet file: ',os.path.join(data_path,tmp_wal))
						break
				self.data_files['db']='local_storage_'+tmprand
				self.data_files['wallet']='wallet_'+tmprand
				newwallet=True
			
			elif 'wallet_'==cbtntxt[:7] :
				tmp=cbtntxt[7:].split('.')
				self.data_files['db']='local_storage_'+tmp[0]
				self.data_files['wallet']='wallet_'+tmp[0]
			else:
				tmp=cbtntxt.split('.')
				self.data_files['wallet']=tmp[0]
				
				cbtntxt=cbtntxt.replace('wallet','')
				tmp=cbtntxt.split('.')
				if tmp[0]=='':
					self.data_files['db']= 'local_storage'
				else:
					self.data_files['db']= 'local_storage_'+tmp[0] 
				
			# print(self.data_files)
				
			self.paths_confirmed=True
			self.update_paths(tmptw.item(1,2).text(),  tmptw.item(2,2).text(),   tmptw,newwallet)
			tmptw.parent().close()

		tw.cellWidget(4,0).set_fun(True, getv,tw)
		# tw.cellWidget(4,0).setFocus()
		# tw.cellWidget(4,0).setDefault(True)
		
		gui.CustomDialog(None,tw,'Enter zUnderNet', defaultij=[4,0])	
		
		
	

	
	# self.data_files['db']
	def isvalid(self,pas):

		ppath=os.getcwd()
		
		if os.path.exists(os.path.join(ppath , self.data_files['db']+'.encr')):
			# print(256,pas)
			# print('decr path',os.path.join(ppath , 'local_storage.encr'), os.path.join(ppath,'local_storage.db'))
			if self.cc.aes_decrypt_file( os.path.join(ppath , self.data_files['db']+'.encr'), os.path.join(ppath,self.data_files['db']+'.db') , pas):
				try:
					db=localdb.DB(self.data_files['db']+'.db')
					at=db.all_tables()
					# print(at)
					if len(at)>0:
						app_fun.secure_delete(os.path.join(ppath , self.data_files['db']+'.encr'))

						return True
				except:
					print('wrong password 489?')
					return False
			else:
				return False
			
				
		elif os.path.exists(os.path.join(ppath , self.data_files['db']+'.db')):
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
				self.cc.aes_encrypt_file( os.path.join(ppath ,self.data_files['db']+'.db'), os.path.join(ppath ,self.data_files['db']+'.encr') , self.app_password)
				
				if os.path.exists(os.path.join(ppath ,self.data_files['db']+'.encr')):
					
					app_fun.secure_delete(os.path.join(ppath ,self.data_files['db']+'.db'))
				
					gui.messagebox_showinfo("Database encrypted", "DB secure: "+self.data_files['db']+".db -> "+self.data_files['db']+".encr ",parent)
			
					break
			except:
				print('Exception in delete '+self.data_files['db']+'.db', tryii)
			
			time.sleep(1)
			
		if self.was_derypted_warning and self.dmn.deamon_started_ok==False: #encrypt if started with unencrypted
			print('exceptional encryption')
			self.dmn.encrypt_wallet_and_data()
			
			

	def on_closing(self,parent):
		# self.close_thread=True
		db=localdb.DB(self.data_files['db']+'.db' )
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
