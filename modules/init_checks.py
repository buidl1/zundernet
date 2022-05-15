# todo:
# activating channel not working ! 
# use in all places:
# self.db_main
# self.db_init
# off: self.db_main.init_tables( self.app_db_version)

# first write db to diff fname then if no errors - delete old and rename new 


import os
import sys
import datetime
import time
import json
import shutil
import sqlite3 #as sql
import modules.app_fun as app_fun
import modules.gui as gui
import modules.localdb as localdb
import modules.aes as aes
# import modules.gui as gui
import modules.deamon as deamon
import modules.usb as usb
import getpass

import traceback


class InitApp:

	# load_init_db(self): unload_init_db(self) unload_main_db(self,pswd) load_main_db(self,pswd ) self.db_init_conn self.db_main_conn
	# loading init db to mem
	def load_init_db(self): 
		con = sqlite3.connect('init.db')
		self.db_init_conn = sqlite3.connect( 'file:initdb?mode=memory&cache=shared', uri=True, check_same_thread=False)
		with self.db_init_conn:
			con.backup(self.db_init_conn)
			
		con.close() 
		
		
		
	
	def unload_init_db(self): # backup to  file
		# print('unloading init.db' )
		
		# add checks to block other tasks and wait current task is done 
		self.init_db.connected=False # block new operations 
		
		while self.init_db.processing!={'sql':'','fname':''}:
			print('waiting to finish',self.init_db.processing)
			time.sleep(1)
			
		os.remove('init.db') 
		con = sqlite3.connect('init.db')
		with con:
			self.db_init_conn.backup(con)
		con.close() 
		self.db_init_conn.close()
		
	
		
	 
		

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
					self.unload_init_db()
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
		self.app_db_version=3 # change when changing db tables to update 
		self.wallet ='tmpwallet.dat'
		# self.data_files['wallet']
		self.data_files={'wallet':'wallet','db':'local_storage'} # .dat/.encr or .db/.encr
		self.was_derypted_warning=False
		self.did_init_backup=False # needed cause self.was_derypted_warning also used for encr_db function
		
		self.close_thread=False
		self.chain='pirate'
		self.creating_new_wallet=False

		app_fun.check_already_running(os.path.basename(__file__)) # check app not runnin - else exit !

		
		# db_init=None
		# db_main=None
		# load_init_db(self): unload_init_db(self) unload_main_db(self,pswd) load_main_db(self,pswd )  self.db_main_conn
		# PREAPRE CONNECTIONS
		self.load_init_db() # self.db_init_conn ready 
		# print('loaded_connection')
		self.init_db=localdb.DB('init.db', -1, _connection=self.db_init_conn)
		# print('created_db init obj') 
		# localdb.init_init() # init local DB initial settings - if not exist 
		self.cc=aes.Crypto()

		
		is_deamon_working=app_fun.check_deamon_running()
		# print('is_deamon_working',is_deamon_working)
		# idb=localdb.DB('init.db')
		# db=localdb.DB( )

		# tt= self.init_db.select('init_settings',columns=["komodo","datadir",'data_files']) #,"password_on" "start_chain",
		tt= self.init_db.select('init_settings',columns=["komodo","datadir","data_files"]) 
		# print('after select tt',tt)
		
		if is_deamon_working[0]:
			if len(tt)==0:
				gui.messagebox_showinfo("init.db file missing while running - exit", "init.db file missing while running - exit")
				self.unload_init_db()
				exit()
			# print(tt)	
			tmp={}
			if tt[0][2]==None: # replace None with current file wallet in use 
				# '-wallet=wallet_Fukibu.dat'
				tmptt=is_deamon_working[3][1].replace('-wallet=wallet_','').replace('.dat','')
				tmp={ 'wallet':'wallet_'+tmptt ,'db':'local_storage_'+tmptt }
				# print('recreated',tmp)
			else:
				tmp=json.loads(tt[0][2])
				
			self.data_files={ 'wallet':tmp['wallet'],'db':tmp['db'] }

		else: # deamon starting - ask paths 
			self.paths_confirmed=False
			self.ask_paths(tt) 
			if not self.paths_confirmed:
				gui.messagebox_showinfo("Exiting app...", "Exiting app...")
				self.unload_init_db()
				exit()
			
			tt= self.init_db.select('init_settings',columns=["komodo","datadir", "data_files"])  
			if len(tt)==0 :
				gui.messagebox_showinfo("init.db file missing while running - exit", "init.db file missing while running - exit")
				self.unload_init_db()
				exit()
				
			# idb.upsert(dict_set,["lock"],{})

		# self.autostart=tt[0][2]
		# self.autostart='no'	
		# if is_deamon_working[0]:
		self.is_started=is_deamon_working[0]
			# self.autostart='yes'	
			
		# dict_set={}
		# dict_set['lock_db_threads']=[{'lock':'no'}]
		# if self.init_db.check_table_exist('lock_db_threads'):
			# self.init_db.upsert(dict_set,["lock"],{})
		
		
		
		
		
		self.first_run=False
		# if encr file not exist and .db not exist as well - assume first run ? ever ?
		# on furst run self.db_main.init_tables( self.app_db_version)
		# updateHashedPass
		
		ppath=os.getcwd()	
		init_db_file=os.path.join(ppath , self.data_files['db']+'.encr')
		# newdbfname=os.path.join(ppath ,self.data_files['db']+'.db')
		if os.path.exists(init_db_file)==False: # now no .db fie decrypted! and os.path.exists(newdbfname)==False:
			# newdbfname= self.data_files['db']+'.db' 
			# gui.messagebox_showinfo("Creating new database","Creating new database file:\n"+self.data_files['db'] )
			# self.db_main.init_tables( self.app_db_version)
			self.first_run=True

		if not os.path.exists('backups'):
			os.mkdir('backups')	
			
			
		# is lockal backup needed ? if files same - not compare file hashes 	
		# is new dir needed ?
		need_new_local_backup=False
		
		
					
		encr_wal=os.path.join(tt[0][1],self.data_files['wallet']+'.encr')
		self.cur_sess=''
		sess_dir=''
		if not self.is_started:
		
			## checking if new backup neede at all 
			last_saved_sess=self.init_db.select_last_val( 'current_session', 'datetime'  )
			# print('last_saved_sess',last_saved_sess)
			if last_saved_sess==None:
				need_new_local_backup=True
			else: #compare file hashes  
				last_sess_dir=os.path.join('backups',last_saved_sess)
				last_local_wal_back=os.path.join(last_sess_dir,self.data_files['wallet']+'.encr') 
				if os.path.exists(last_local_wal_back):
					last_local_wal_back_hash= self.cc.hash2utf8_1b( self.cc.read_bin_file( last_local_wal_back),1)
					encr_wal=os.path.join(tt[0][1],self.data_files['wallet']+'.encr') 
					if os.path.exists(encr_wal):
						cur_wal_hash= self.cc.hash2utf8_1b( self.cc.read_bin_file( encr_wal),1) 
						
						if last_local_wal_back_hash!=cur_wal_hash: 
							need_new_local_backup=True
				else:
					need_new_local_backup=True
		
			if need_new_local_backup:
				tmpdt=str(datetime.datetime.now()).replace('-','').replace(':','').replace(' ','_')
				tmpdt=tmpdt.split('.')
				self.cur_sess=tmpdt[0]
				worked=self.init_db.insert({'current_session':[{'datetime':self.cur_sess,'uid':'auto'}]},["datetime",'uid'] )
				# print('insert worked?',worked)
				# print('select\n',self.init_db.select('current_session' ) )
				sess_dir=os.path.join('backups',self.cur_sess)
				print('new backup of encr files; backed up to ', sess_dir)
				os.mkdir( sess_dir )
			
			
			
		self.app_password=None
		while self.app_password==None:
		
			tmpv=[]
			# self.ask_password( tmpv )
			# copy encr db file:
			if self.cur_sess!='' and os.path.exists(init_db_file):
				shutil.copy2(init_db_file, sess_dir )
			
			gui.PassForm(tmpv,self.first_run)
			# print(102,tmpv)
			
			if len(tmpv)==0:
				gui.messagebox_showinfo("Canceled - exiting", "Exiting app...")
				# os.rmdir(os.path.join('backups','cur_sess'))
				if self.cur_sess!='':
					shutil.rmtree( sess_dir )
					print('new session cancelled!',tmpdt[0])
				self.unload_init_db()
				exit()
			
			# print('checking pass is valid self.first_run', self.first_run)
			if self.first_run:
				self.updateHashedPass(tmpv[0])
				self.app_password=tmpv[0]

			elif self.isvalid(tmpv[0]):
				self.app_password=tmpv[0]
				# insert new session start if deamon not running:
				# table['current_session']={'uid':'int', 'ttime':'real' }
				 
				
			else:
				gui.messagebox_showinfo("Wrong password", "Password was not correct - try again.")
			
		###################### INIT DB AND DEAMON	
		t0=time.time()
		# if not self.first_run: # print('if not first run update localdb.init_tables',self.first_run)
			# self.db_main.init_tables( self.app_db_version)
			
		self.check_if_new_wallet_backup_needed()
		
		self.wallet = self.data_files['wallet']+'.dat'
		self.db = self.data_files['db']+'.db'
		
		deamon_cfg=self.deamon_setup(tt)
		# print(155,deamon_cfg)
		deamon.global_db_init=self.init_db
		deamon.global_db =self.db_main 
		self.dmn=deamon.DeamonInit(deamon_cfg,self.db)
		# print(' DeamonInit dt',time.time()-t0)
		# t0=time.time()
		self.dmn.init_clear_queue()
		
		# backup wallet.encr local
		# print(idb.select( 'current_session'  ) )
		if need_new_local_backup:
			# print('pre local backup needed',os.path.exists(encr_wal), not self.is_started, encr_wal) # OK
			if True: # these already checked above os.path.exists(encr_wal) and not self.is_started:
				# print('encr_wal',encr_wal)
				# self.cur_sess=self.init_db.select_last_val( 'current_session', 'datetime'  )
				# print(self.cur_sess)
				# sess_dir=os.path.join('backups',self.cur_sess)
				encr_wal_dest=os.path.join(sess_dir,self.data_files['wallet']+'.encr')
				# print('local backup needed',os.path.exists(encr_wal_dest), encr_wal_dest)
				if not os.path.exists(encr_wal_dest) : #self.cur_sess!='' : # to be used before wallet decryption
					
					# print('wallet off backup',encr_wal,'to',sess_dir)
					shutil.copy2(encr_wal, sess_dir )
		  
	
	def get_last_wallet_backup_data(self ):
		# required before backup	
		# idb=localdb.DB('init.db')
		if not os.path.exists(self.test_ppath):
			return [], ''
		
		cc=aes.Crypto()
		cur_dat_hash= cc.hash2utf8_1b( cc.read_bin_file( self.test_ppath),1)
		
		# db=localdb.DB(self.data_files['db']+'.db')
		# print('from db',self.data_files['db']+'.db')
		last_wallet_hash=self.db_main.select('jsons', ['json_content'],{'json_name':['=',"'backup_wallet_hash'"]})
		# print('last_wallet_hash',last_wallet_hash)
		# print('all',db.select('jsons', [] )) #'json_content'
		if len(last_wallet_hash)==0:
			return [], cur_dat_hash
			
		# print(last_wallet_hash)
		last_wallet_hash_arr=json.loads(last_wallet_hash[0][0])		
		
		return last_wallet_hash_arr, cur_dat_hash
	
	
	def make_wallet_backup(self,init_msg_info,msg2,parent,data_src,new_wallet_hash_arr ): 
	
		if not hasattr(self,'data_files'):
			print('no attribute data_files exit ')
			self.unload_init_db()
			exit()
		gui.messagebox_showinfo('Wallet backup required',init_msg_info)
									
		if not app_fun.wallet_copy_progress( src_dir=data_src, add_msg=['Please insert USB/pendrive',msg2], wallet_name=self.data_files['wallet'], gui=gui, parent_widget=parent ):
			self.unload_init_db()
			exit()
		
		
		# dat_file=src   
		# new_wallet_hash_arr= last_wallet_hash_arr.append(cur_dat_hash)
	
		# print('Inserting backup_wallet_hash at decrypted wallet found!',new_wallet_hash_arr[-1]) 
		table={}
		table['jsons']=[{'json_name':"backup_wallet_hash", 'json_content':json.dumps(new_wallet_hash_arr), 'last_update_date_time': app_fun.now_to_str(False)}]
		# db=localdb.DB(self.data_files['db']+'.db')
		self.db_main.upsert(table,['json_name','json_content','last_update_date_time'],{'json_name':['=',"'backup_wallet_hash'"]})
	
		
	# run in 2 cases:
	# if wallet was decrypted at start
	# if creating new wallet file and synced signal emited!
	# for new dat file creat wallt hash!
	@gui.Slot()	
	@gui.Slot(bool)	
	def check_if_new_wallet_backup_needed(self,synced=False ):
		if self.did_init_backup:
			# print('init backup already done')
			return
	
		# print('check_if_new_wallet_backup_needed',self.creating_new_wallet,synced,self.was_derypted_warning)
		if not hasattr(self,'test_ppath'):
			# print('\tno test path')
			return
			
		if not (self.creating_new_wallet and synced) and not self.was_derypted_warning:
			# print('neither decrypted nor new wallet?')
			return
	
		# print('test_ppath',self.test_ppath)
		# print('init checks 269 self.creating_new_wallet  or self.was_derypted_warning',self.creating_new_wallet, self.was_derypted_warning)
		# if new wallet in option selected
		# or for some reason wallet dat was decrypted on entry:
		
		last_wallet_hash_arr, cur_dat_hash = self.get_last_wallet_backup_data() #get_last_wallet_backup_data(self,test_ppath)
		# print(' last_wallet_hash_arr, cur_dat_hash',last_wallet_hash_arr, cur_dat_hash)
		
		# idb=localdb.DB('init.db') 
		data_src00=self.init_db.select('init_settings', ['datadir'])
		data_src=data_src00[0][0]
		
		tmpmsg1='New wallet created - backup required'
		tmpmsg2='Please insert USB pendrive. New wallet needs to be backed up to external memory.'
			
		if synced and self.creating_new_wallet :
			print('self.creating_new_wallet - backaup!')
			# last_wallet_hash_arr.append(cur_dat_hash)
			# self.make_wallet_backup(tmpmsg1 ,tmpmsg2,None,data_src,last_wallet_hash_arr )	

		elif self.was_derypted_warning:
			# print('self.was_derypted_warning')
			 
			 
			if cur_dat_hash in last_wallet_hash_arr: 
				print('Decrypted wallet hash consistent with history - no backup needed') # if cur_dat_hash in last_wallet_hash_arr: #==last_wallet_hash[0][0]:
				return
			else: 
				tmpmsg1='Decrypted wallet exist - backup required'
				tmpmsg2='Please insert USB pendrive. Unencrypted wallet file detected - needs to be backed up to external memory.'
			 
			 
		if os.path.exists(self.test_ppath) and cur_dat_hash!='':
			# print('making new backup')
			last_wallet_hash_arr.append(cur_dat_hash)
			self.make_wallet_backup(tmpmsg1 ,tmpmsg2,None,data_src,last_wallet_hash_arr )		
			self.did_init_backup=True			
			
			
			
			
			
			
	# if new wallet - only update file name after blockchain started!!! 
	
	def update_paths(self,deamon,data, parent ): # self.creating_new_wallet
	
		# idb=localdb.DB('init.db')
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
		self.test_ppath=os.path.join(data,self.data_files['wallet']+'.dat')
		decr_wal_exist=os.path.exists( self.test_ppath  ) #app_fun.fileExist(data,cond={'start':self.data_files['wallet'],'end':'.dat' })
		self.was_derypted_warning=(decr_wal_exist==True)
		
		# print('checked ', test_ppath ,decr_wal_exist)
		# print( decr_wal_exist,app_fun.fileExist(data,cond={'start':self.data_files['wallet'],'end':'.encr' }))
		if decr_wal_exist or app_fun.fileExist(data,cond={'start':self.data_files['wallet'],'end':'.encr' }):
			blockchain_data_ok=True
		 
		
		if komodod_ok and komodo_cli_ok  and (blockchain_data_ok or self.creating_new_wallet):  

			# if self.creating_new_wallet and app_fun.fileExist(data,cond={'start':self.data_files['wallet'] }) : 
			# dict_set={'init_settings':[{"data_files":json.dumps(self.data_files)}]}
			# self.init_db.delete_where('init_settings')
			# self.init_db.insert(dict_set,["data_files" ]) #,"data_files"
		
			ord_arr=["komodo","datadir" ]
			dict_set={ }
			dict_set['init_settings']=[]
			dict_set['init_settings'].append({
												"komodo":  deamon ,
												"datadir": data  #,
												# "data_files":json.dumps(self.data_files)
											})
											
			if not self.creating_new_wallet:
				dict_set['init_settings'][0]["data_files"]=json.dumps(self.data_files)
				ord_arr.append("data_files")
				# print('added exception',dict_set,ord_arr)
			
			self.init_db.delete_where('init_settings')
			self.init_db.insert(dict_set,ord_arr) #,"data_files"
			
		elif not komodod_ok:
			gui.messagebox_showinfo('Path for pirate deamon is wrong', deamon +'\n - no pirated file !')
			self.unload_init_db()
			exit()
		elif  not komodo_cli_ok:
			gui.messagebox_showinfo('Path for pirate-cli is wrong', data +'\n - no pirate-cli file !')
			self.unload_init_db()
			exit()
		elif not self.creating_new_wallet:
			gui.messagebox_showinfo('Path for blockchain data is wrong', data +'\n - no wallet file !')
			self.unload_init_db()
			exit()
			
	
	
	
	
	
	

	# qt dialog komodod, data dir 	
	def ask_paths(self,tt): # read from db if possible
	
		# self.data_files['wallet'], self.data_files['db']
		tmpwallet=['Create new','Select file']

		# idb=localdb.DB('init.db')
		
		preset=[]
		# tt= self.init_db.select('init_settings',columns=["komodo","datadir",'data_files']) #,"password_on" "start_chain",
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
		
			data_path=tmptw.item(2,2).text().strip()
			deamon_path=tmptw.item(1,2).text().strip()
			cbtntxt=tmptw.cellWidget(3,1).currentText()
			
			if deamon_path=='' or data_path=='':
				print('empty path')
				return
			
			if not os.path.exists(deamon_path) or not os.path.exists(data_path):
				print('bad path')
				return
		
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
			self.creating_new_wallet=newwallet # need to create backup after new wallet is synced
			self.update_paths(deamon_path,  data_path,   tmptw) #, newwallet)
			tmptw.parent().close()

		tw.cellWidget(4,0).set_fun(True, getv,tw)
		
		gui.CustomDialog(None,tw,'Enter zUnderNet', defaultij=[4,0])	
		
		
	

	def updateHashedPass(self,pas):
		# db=localdb.DB(self.data_files['db']+'.db')
		self.load_main_db(pas) #if not exist will crate in mem conn
		self.db_main=localdb.DB(self.data_files['db']+'.db', self.app_db_version, _connection=self.db_main_conn    )
		
		table={}  
		salttmp=self.cc.init_hash_seed() 
		passhashtmp=self.cc.hash(pas+salttmp)
		# print('hashed at',passhashtmp)
		disp_dict={'salt':salttmp,'passhash':passhashtmp} # 
		table['jsons']=[{'json_name':"password_hash", 'json_content':json.dumps(disp_dict), 'last_update_date_time': app_fun.now_to_str(False)}]
		self.db_main.upsert(table,['json_name','json_content','last_update_date_time'],{'json_name':['=',"'password_hash'"]})

		
		
		
	def unload_main_db(self,pswd):
	
		self.db_main.connected=False # block new operations 
		
		# wait till no sql on the queue and last one is done 
		while self.db_main.processing!={'sql':'','fname':''} or len(self.db_main.processing_list)>0:
			print('waiting to finish',self.db_main.processing)
			if len(self.db_main.processing_list)>1:
				print('sql # in the queue',len(self.db_main.processing_list) )
			time.sleep(1)
			
		encr_fname=self.data_files['db']+'.encr'
		
		larr=''
		for line in self.db_main_conn.iterdump(): 
			larr+=line+'\n' 
			
		self.cc.write_file(encr_fname,  self.cc.aes_encrypt( larr,kkey=pswd,encode=True) )
		self.db_main_conn.close()
		
		gui.messagebox_showinfo("Created new database","Created new database file:\n"+self.data_files['db']+'.encr' )
		
		
	
		
	def load_main_db(self,pswd ):
		encr_fname=self.data_files['db']+'.encr'
		rand_name=self.cc.rand_abc(16)
		# print('decrypting with',pswd)
		
		if not os.path.exists(encr_fname): # create connection and return
			self.db_main_conn = sqlite3.connect( 'file:'+rand_name+'?mode=memory&cache=shared', uri=True, check_same_thread=False)
			return True
		# dbdecr=self.cc.aes_decrypt_file( path1=encr_fname, path2=None,password=pswd)
		# print(dbdecr)
		try:
		# if True:
			dbdecr=self.cc.aes_decrypt_file( path1=encr_fname, path2=None,password=pswd) # may be false!
			# print(dbdecr[:512])
			if type(dbdecr)==type(b''):
				dest_path=encr_fname.replace('.encr','.db')
				# print('dest_path',dest_path)
				print('attempting migration and re-encryption with encoding'  )
				dbdecr=self.cc.aes_decrypt_file( path1=encr_fname, path2=dest_path,password=pswd)
				# print('dbdecr',dbdecr)
				# if len(dbdecr)<512: print(dbdecr)
				# else: print(dbdecr[:512])
				
				if dbdecr: 
					def progress(status, remaining, total):
						print(f'Copied {total-remaining} of {total} pages...')

					con = sqlite3.connect(dest_path)
					self.db_main_conn = sqlite3.connect( 'file:'+rand_name+'?mode=memory&cache=shared', uri=True, check_same_thread=False)
					with self.db_main_conn:
						con.backup(self.db_main_conn, pages=10000, progress=progress)
						
					con.close()
					
					larr=''
					for line in self.db_main_conn.iterdump(): 
						larr+=line+'\n' 
						
					os.rename(encr_fname,'old_'+encr_fname) # to keep old file 
					self.cc.write_file(encr_fname,  self.cc.aes_encrypt( larr,kkey=pswd,encode=True) )
					# print('saved',encr_fname)
					# bck.close()
					# print('remove ',dest_path)
					os.remove(dest_path) 
					return True

				else:
					print('failed to decrypt to file - corrupted db?!')
					self.db_main_conn =None
					return False
					# exit()
			elif dbdecr!=False:
				print('ok')
				# test if can load directly to memory:
				self.db_main_conn = sqlite3.connect( 'file:'+rand_name+'?mode=memory&cache=shared', uri=True, check_same_thread=False)
				cur2=self.db_main_conn.cursor() 
				cur2.executescript( dbdecr ) 
				self.db_main_conn.commit()	
				cur2.close() 
				return True
				# conn2.close()	
			else:
				print('could not decrypt')
				return False
		except:
		# else:
			print('init dbdecr failed')
			return False
		
	# self.data_files['db']
	# checking password is valid based on :
	# 1. possibility to decrypt db
	# 2. hashed password in jsons table 
	def isvalid(self,pas):

		ppath=os.getcwd()
		# print('isvalid pass main path getcwd',ppath)
		
		
		# load_init_db(self): unload_init_db(self) unload_main_db(self,pswd) load_main_db(self,pswd )  self.db_main_conn
		# PREAPRE CONNECTIONS
		# self.load_init_db() # self.db_init_conn ready 
		# self.init_db=localdb.DB('init.db', -1, _connection=)
		# self.init_db.init_init()
		
		if os.path.exists(os.path.join(ppath , self.data_files['db']+'.encr')):
			# print('encr db exist ...',self.data_files['db']+'.encr')
			# print('decr path',os.path.join(ppath , 'local_storage.encr'), os.path.join(ppath,'local_storage.db'))
			if self.load_main_db(pas): #self.cc.aes_decrypt_file( os.path.join(ppath , self.data_files['db']+'.encr'), os.path.join(ppath,self.data_files['db']+'.db') , pas):
				try:
					self.db_main=localdb.DB(self.data_files['db']+'.db', self.app_db_version, _connection=self.db_main_conn    )
					at=self.db_main.all_tables()
					# print('decrypted\n',at)
					
					# if decrypted correctly save pass hasing with different salt
					if len(at)>0:
						# app_fun.secure_delete(os.path.join(ppath , self.data_files['db']+'.encr'))
						 
						return True
				except AttributeError:
					traceback.print_exc()
					print('passing - strange expcetion')
					return True
				except:
					traceback.print_exc()
					print('wrong password 489?')
					# print('self.data_files[ db ]+ .db ',self.data_files['db']+'.db')
					return False
			else:
				return False
			
		# not possible after moving to mem 	
		# elif os.path.exists(os.path.join(ppath , self.data_files['db']+'.db')): 
			# print('decrypted db exist',self.data_files['db']+'.db') 
			
			# db=localdb.DB(self.data_files['db']+'.db')
			# last_hashed_pass=db.select('jsons', ['json_name','json_content','last_update_date_time'],{'json_name':['=',"'password_hash'"]}) 
			# if len(last_hashed_pass)>0:
				# try:
					# last_hashed_pass=last_hashed_pass[0][1] 
					# pass_dict=json.loads(last_hashed_pass) 
					# newpasshashtmp=self.cc.hash(pas+pass_dict['salt']) 
					# if newpasshashtmp==pass_dict['passhash']: 
						# return True
					# else:
					
						# print('Password hash checked - not matching previous password hash. Try again. Pass hash must be matched for consistency.')
						# return False
				# except:
					# traceback.print_exc()
					# return False
			# else:
				# print('	# save hash since not hash found - could not verify ? new db file ? ')
				# self.updateHashedPass(pas)
				# return True 
			
			# return False #True
			
		return False

	
	
	
	# not needed ?
	# def encr_db(self,parent):
		
		# if self.was_derypted_warning and self.dmn.deamon_started_ok==False: #encrypt if started with unencrypted
			# print('exceptional encryption')
			# self.dmn.encrypt_wallet_and_data()
			
		# dict_set={}
		# dict_set['lock_db_threads']=[{'lock':'yes'}]
		 
		# self.dmn.started=False # ???
		# ppath =os.getcwd()
		 
				
		# tryii=3
		# while tryii>0:
			# tryii=tryii-1
			# try: # if True:
				# self.cc.aes_encrypt_file( os.path.join(ppath ,self.data_files['db']+'.db'), os.path.join(ppath ,self.data_files['db']+'.encr') , self.app_password)
				
				# if os.path.exists(os.path.join(ppath ,self.data_files['db']+'.encr')):
					
					# app_fun.secure_delete(os.path.join(ppath ,self.data_files['db']+'.db'))
				
					# gui.messagebox_showinfo("Database encrypted", "DB secure: "+self.data_files['db']+".db -> "+self.data_files['db']+".encr ",parent)
			
					# break
			# except:
				# print('Exception in delete '+self.data_files['db']+'.db', tryii)
			
			# time.sleep(1)
			
			
			
	# to speed up init loading best to save all loaded views grids to a single json into db and then read
	# to make so need to pass all views after wallet is encrypted to this place and log to DB
	
	def on_closing(self,parent):
		# self.close_thread=True
		# db=localdb.DB(self.data_files['db']+'.db' )
		
		# on new wallet creation add new entry on exit:
		_unload_main_db=True
		if self.creating_new_wallet:
			tt= self.init_db.select('init_settings',columns=[ "datadir" ]) 
			data=tt[0][0]
			if len(data)>0 and self.creating_new_wallet and app_fun.fileExist(data,cond={'start':self.data_files['wallet'] }) : 
				dict_set={'init_settings':[{"data_files":json.dumps(self.data_files)}]} 
				self.init_db.update( dict_set, ["data_files"], {} )
				print('saved new init_settings data dir',self.init_db.select('init_settings',columns=[ ])  )
			else:
				print('# wallet file not found - not save local storage db!:')
				_unload_main_db=False
				# if os.path.exists()
		
		self.db_main.vacuum()
		is_deamon_working=app_fun.check_deamon_running()
		
		self.unload_init_db()
		
		def unload_main():
			if _unload_main_db:
				print('_unload_main_db',_unload_main_db)
				# print('encrypting with',self.app_password)
				self.unload_main_db(self.app_password)
		
		
		if is_deamon_working[0]:
			
			if gui.askokcancel("Quit", "Are you sure you want to quit? Blockchain deamon is still running. If you plan to shut down your computer it is better to STOP blockchain and quit afterwards.",parent):
			
				# self.encr_db(parent)
				unload_main()
						
				return True
			else:
				return False
		else:
			# save last views for init load 
		
			# self.encr_db(parent)	
			unload_main()
			return True
