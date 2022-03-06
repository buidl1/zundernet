
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
# import modules.gui as gui
import modules.deamon as deamon
import modules.usb as usb
import getpass

import traceback

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
		# self.autostart='no'	
		# if is_deamon_working[0]:
		self.is_started=is_deamon_working[0]
			# self.autostart='yes'	
			
		dict_set={}
		dict_set['lock_db_threads']=[{'lock':'no'}]
		if idb.check_table_exist('lock_db_threads'):
			idb.upsert(dict_set,["lock"],{})
		
		self.first_run=False
		
		ppath=os.getcwd()	
		init_db_file=os.path.join(ppath , self.data_files['db']+'.encr')
		if os.path.exists(init_db_file)==False and os.path.exists(os.path.join(ppath ,self.data_files['db']+'.db'))==False:
			newdbfname= self.data_files['db']+'.db' 
			gui.messagebox_showinfo("Creating new database","Creating new database file:\n"+newdbfname)
			localdb.init_tables(newdbfname,self.app_db_version)
			self.first_run=True

		if not os.path.exists('backups'):
			os.mkdir('backups')	
			
		self.cur_sess=''
		if not self.is_started:
			tmpdt=str(datetime.datetime.now()).replace('-','').replace(':','').replace(' ','_')
			tmpdt=tmpdt.split('.')
			self.cur_sess=tmpdt[0]
			idb.insert({'current_session':[{'datetime':self.cur_sess,'uid':'auto'}]},["datetime",'uid'] )
			sess_dir=os.path.join('backups',self.cur_sess)
			print('new session started! encr files backed up to ', sess_dir)
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
				exit()
			
			# print('checking pass is valid self.first_run', self.first_run)
			if self.first_run:
				self.updateHashedPass(tmpv[0])
				self.app_password=tmpv[0]

			elif self.isvalid(tmpv[0]):
				self.app_password=tmpv[0]
				# insert new session start if deamon not running:
				# table['current_session']={'uid':'int', 'ttime':'real' }
				
				
			# if self.isvalid(tmpv[0]) and not self.first_run : # checks if decryption is correct 
				# self.app_password=tmpv[0]
				
			else:
				gui.messagebox_showinfo("Wrong password", "Password was not correct - try again.")
			
		###################### INIT DB AND DEAMON	
		t0=time.time()
		if not self.first_run:
			# print('if not first run update localdb.init_tables',self.first_run)
			localdb.init_tables(self.data_files['db']+'.db',self.app_db_version)
			
		self.check_if_new_wallet_backup_needed()
		
		self.wallet = self.data_files['wallet']+'.dat'
		self.db = self.data_files['db']+'.db'
		
		deamon_cfg=self.deamon_setup(tt)
		# print(155,deamon_cfg)
		self.dmn=deamon.DeamonInit(deamon_cfg,self.db)
		# print(' DeamonInit dt',time.time()-t0)
		# t0=time.time()
		self.dmn.init_clear_queue()
		
		# backup wallet.encr local
		# print(idb.select( 'current_session'  ) )
		encr_wal=os.path.join(tt[0][1],self.data_files['wallet']+'.encr')
		if os.path.exists(encr_wal) and not self.is_started:
			# print('encr_wal',encr_wal)
			self.cur_sess=idb.select_last_val( 'current_session', 'datetime'  )
			# print(self.cur_sess)
			sess_dir=os.path.join('backups',self.cur_sess)
			encr_wal_dest=os.path.join(sess_dir,self.data_files['wallet']+'.encr')
			if not os.path.exists(encr_wal_dest) : #self.cur_sess!='' : # to be used before wallet decryption
				
				# print('wallet off backup',encr_wal)
				shutil.copy2(encr_wal, sess_dir )
		  
	
	def get_last_wallet_backup_data(self ):
		# required before backup	
		# idb=localdb.DB('init.db')
		if not os.path.exists(self.test_ppath):
			return [], ''
		
		cc=aes.Crypto()
		cur_dat_hash= cc.hash2utf8_1b( cc.read_bin_file( self.test_ppath),1)
		
		db=localdb.DB(self.data_files['db']+'.db')
		# print('from db',self.data_files['db']+'.db')
		last_wallet_hash=db.select('jsons', ['json_content'],{'json_name':['=',"'backup_wallet_hash'"]})
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
			exit()
		gui.messagebox_showinfo('Wallet backup required',init_msg_info)
									
		if not app_fun.wallet_copy_progress( src_dir=data_src, add_msg=['Please insert USB/pendrive',msg2], wallet_name=self.data_files['wallet'], gui=gui, parent_widget=parent ):
			exit()
		
		
		# dat_file=src   
		# new_wallet_hash_arr= last_wallet_hash_arr.append(cur_dat_hash)
	
		# print('Inserting backup_wallet_hash at decrypted wallet found!',new_wallet_hash_arr[-1]) 
		table={}
		table['jsons']=[{'json_name':"backup_wallet_hash", 'json_content':json.dumps(new_wallet_hash_arr), 'last_update_date_time': app_fun.now_to_str(False)}]
		db=localdb.DB(self.data_files['db']+'.db')
		db.upsert(table,['json_name','json_content','last_update_date_time'],{'json_name':['=',"'backup_wallet_hash'"]})
	
		
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
		
		idb=localdb.DB('init.db') 
		data_src00=idb.select('init_settings', ['datadir'])
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
		self.test_ppath=os.path.join(data,self.data_files['wallet']+'.dat')
		decr_wal_exist=os.path.exists( self.test_ppath  ) #app_fun.fileExist(data,cond={'start':self.data_files['wallet'],'end':'.dat' })
		self.was_derypted_warning=(decr_wal_exist==True)
		
		# print('checked ', test_ppath ,decr_wal_exist)
		# print( decr_wal_exist,app_fun.fileExist(data,cond={'start':self.data_files['wallet'],'end':'.encr' }))
		if decr_wal_exist or app_fun.fileExist(data,cond={'start':self.data_files['wallet'],'end':'.encr' }):
			blockchain_data_ok=True
		 
		
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
			self.update_paths(deamon_path,  data_path,   tmptw,newwallet)
			tmptw.parent().close()

		tw.cellWidget(4,0).set_fun(True, getv,tw)
		
		gui.CustomDialog(None,tw,'Enter zUnderNet', defaultij=[4,0])	
		
		
	

	def updateHashedPass(self,pas):
		db=localdb.DB(self.data_files['db']+'.db')
		table={}  
		salttmp=self.cc.init_hash_seed() 
		passhashtmp=self.cc.hash(pas+salttmp)
		# print('hashed at',passhashtmp)
		disp_dict={'salt':salttmp,'passhash':passhashtmp} # 
		table['jsons']=[{'json_name':"password_hash", 'json_content':json.dumps(disp_dict), 'last_update_date_time': app_fun.now_to_str(False)}]
		db.upsert(table,['json_name','json_content','last_update_date_time'],{'json_name':['=',"'password_hash'"]})

	# self.data_files['db']
	# checking password is valid based on :
	# 1. possibility to decrypt db
	# 2. hashed password in jsons table 
	def isvalid(self,pas):

		ppath=os.getcwd()
		# print('isvalid pass main path getcwd',ppath)
		
		
		
		if os.path.exists(os.path.join(ppath , self.data_files['db']+'.encr')):
			# print('encr db exist ...',self.data_files['db']+'.encr')
			# print('decr path',os.path.join(ppath , 'local_storage.encr'), os.path.join(ppath,'local_storage.db'))
			if self.cc.aes_decrypt_file( os.path.join(ppath , self.data_files['db']+'.encr'), os.path.join(ppath,self.data_files['db']+'.db') , pas):
				try:
					db=localdb.DB(self.data_files['db']+'.db')
					at=db.all_tables()
					# print('decrypted\n',at)
					
					# if decrypted correctly save pass hasing with different salt
					if len(at)>0:
						app_fun.secure_delete(os.path.join(ppath , self.data_files['db']+'.encr'))
						 
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
			
				
		elif os.path.exists(os.path.join(ppath , self.data_files['db']+'.db')):
			# print('Provided pass: ',pas,' Write it down if it was not correct.')
			print('decrypted db exist',self.data_files['db']+'.db')
			# if first run: password just created, no hashes, should backup wallet dat after wallet created and after sync!
			# if consecutive run: check hash!
			
			db=localdb.DB(self.data_files['db']+'.db')
			last_hashed_pass=db.select('jsons', ['json_name','json_content','last_update_date_time'],{'json_name':['=',"'password_hash'"]})
			# print('last_hashed_pass',last_hashed_pass)
			if len(last_hashed_pass)>0:
				try:
					last_hashed_pass=last_hashed_pass[0][1]
					# print('last_hashed_pass',last_hashed_pass)
					pass_dict=json.loads(last_hashed_pass)
					# print('testing',pas,pass_dict['salt'])
					newpasshashtmp=self.cc.hash(pas+pass_dict['salt'])
					# print('testing',newpasshashtmp,pass_dict['passhash'])
					if newpasshashtmp==pass_dict['passhash']:
						# print('hashed pass ok ')
						return True
					else:
					
						print('Password hash checked - not matching previous password hash. Try again. Pass hash must be matched for consistency.')
						return False
				except:
					traceback.print_exc()
					return False
			else:
				print('	# save hash since not hash found - could not verify ? new db file ? ')
				self.updateHashedPass(pas)
				return True
			# instead verify is password matched hashed:
			
			return False #True
			
		return False

	
	
	
		
	def encr_db(self,parent):
		
		if self.was_derypted_warning and self.dmn.deamon_started_ok==False: #encrypt if started with unencrypted
			print('exceptional encryption')
			self.dmn.encrypt_wallet_and_data()
			
		dict_set={}
		dict_set['lock_db_threads']=[{'lock':'yes'}]
		# print('locking db')
		idb=localdb.DB('init.db')
		if idb.check_table_exist('lock_db_threads'):
			# print('locking db -> upsert')
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
			
			
			
	# to speed up init loading best to save all loaded views grids to a single json into db and then read
	# to make so need to pass all views after wallet is encrypted to this place and log to DB
	
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
			# save last views for init load 
		
			self.encr_db(parent)	
			return True
