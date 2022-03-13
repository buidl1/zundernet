
import os
# import datetime
import json
import time
import modules.localdb as localdb
import modules.app_fun as app_fun

import modules.aes as aes
import modules.gui as gui

class DefChannels:

	def __init__(self):
		
		self.activation_channel_addr='zs1qds8vy37aewz0ersgnxexj3w96gs642p0d0mh3vzlschgyn9ahfrvu7lq96wmff4l8lg7a8rpg6'
	
		self.channels={ #'addr':'viewkey'
		self.activation_channel_addr:'zxviews1q0krxcg6qyqqpqqw4pupu3tlr6qcpxxk73dt969ks4xhf2lhacddyf2hqw577azksq9c84y0mq9ym7kxreut00kjkmzysjptysrh2x9yv5cne2lh46kjurudd8uklx259e3azckkj4ghh0zhlwuy0fpxph29ktz9dv5sgwtx79fcvzm2df8awj3cy8wmkdz25mn050ku04kfuneag9p3fw7dlntw8g46ru2qsg3vcvt9nvlfx06qt7srknjs32hvyvm3sd94sk7uq9q2n4df9'
		}

class Chnls(gui.QObject):
	refreshAddrBook= gui.Signal()

	# def export_channel(self):
		# print('export encrypted hannel?')

	# recognize own msg to chnl  and prev sender name to not require again
	# modify to proper chnl message ormat (select sender name signature / load if has previous and tx )
	
	
	
	
	
	
	def send_reply(self,btn,*args):		

		# tmpdict rows:
		# sending addr
		# to addr
		# msg txt
		# signature and button
		
		msg_grid=[]
		tmpdict={'rowk':'from', 'rowv':[{'T':'LabelC', 'L':'Select sending address (own):','width':19},{'T':'Button', 'L':'...', 'uid':'selownadr'}]} #, 'width':4
		msg_grid.append(tmpdict) #, {'T':'LabelV','L':'','uid':'ownaddr','width':80}
		
		tmpdict={'rowk':'to', 'rowv':[{'T':'LabelC', 'L':'Select destination address:','width':19},{'T':'Button', 'L':'...', 'uid':'seladr'}]} #, {'T':'LabelV','L':'','uid':'addr','width':80} , 'width':4
		
		tmpaddr=''
		# print(self.cur_addr)
		if args[0]=='r': # and hasattr(self,'cur_addr'):
			# if self.cur_addr!='':
			tmpaddr=self.cur_uid #args[1] #self.cur_addr
			# tmpdict={'rowk':'to', 'rowv':[{'T':'LabelC', 'L':'Replying to: '+tmpaddr,'width':80}  ]}
			tmpstr=''
			if len(args)>1:
				tmpstr=str(args[1])
			tmpdict={'rowk':'to', 'rowv':[{'T':'LabelC', 'L':'Replying to: '+tmpstr,'width':19},{'T':'LabelC', 'L':tmpaddr, 'uid':'seladr'}]} #, 'width':4
			
		msg_grid.append(tmpdict)
		tmpdict={'rowk':'msg', 'rowv':[{'T':'TextEdit','uid':'msg','span':2, 'style':'background-color:white;'} ]}
		msg_grid.append(tmpdict)
		
		# check signature exist for the addr - if not create
		mysignature=''
		idb=localdb.DB(self.db)
		 
		# db_sign=idb.select( 'channel_signatures', [ 'signature' ], {'addr':['=',  "'"+tmpaddr+"'" ] } )
		db_sign=idb.select_last_val('channel_signatures','signature')
		sign_dict={}
		if db_sign!=None: #len(db_sign)==1:
			mysignature=db_sign #[0][0]
			sign_dict={'T':'LabelC', 'L':mysignature ,'width':6}
		# if mysignature=='':
		else:
			# create and write to DB 
			cc=aes.Crypto( )
			mysignature=cc.rand_slbls( 4)
			sign_dict={'T':'LineEdit', 'L':'signature', 'V':mysignature ,'width':6}

		
		tmpdict={'rowk':'send', 'rowv':[ {'T':'LabelC', 'L':'Signature' ,'width':6}, sign_dict, {'T':'Button', 'L':'Send', 'uid':'send','width':6}  ] }
		msg_grid.append(tmpdict)
		
		# msg_table=flexitable.FlexiTable(selframe,msg_grid)
		msg_table=gui.Table(None,{'dim':[len(msg_grid),3], 'toContent':1})
		msg_table.updateTable(msg_grid)
		
		last_addr=localdb.get_last_addr_from("'last_msg_from_addr'")

		if last_addr not in ['','...']:
			msg_table.cellWidget(0,1).setToolTip(last_addr) #.set_textvariable( 'ownaddr',last_addr)
			msg_table.cellWidget(0,1).setText( self.addr_book.cat_alias( last_addr,own=True) )
		
		def send():
			# global tmpaddr
			msg=msg_table.cellWidget(2,0).toPlainText()  #get_value( 'msg')
			# print('sendng msg channel toPlainText\n',msg)
			
			if msg.strip()=='':
				# print('no msg to send')
				return
			
			
			to=self.cur_uid
			if to=='':
				to=msg_table.cellWidget(1,1).toolTip() #.get_value( 'addr')
				
			froma=msg_table.cellWidget(0,1).toolTip() #.get_value( 'ownaddr')
			if froma=='':
				return
			
			idb=localdb.DB(self.db)
			# prepare msg inner json ... 
			send_dict={'txt':msg}
			
			tmpsender=''
			if msg_table.cellWidget(3,1)!=None:
				
				tmpsender=msg_table.cellWidget(3,1).text() 
			elif msg_table.item(3,1)!=None:
				tmpsender=msg_table.item(3,1).text()
			
			# print('tmpsender', tmpsender)
			
			send_dict['sender']=tmpsender# only add sender first time later not needdidb=localdb.DB(self.db) 
			table={'channel_signatures':[{ 'signature':tmpsender}]} 
			idb.upsert( table, [ 'signature' ] )
			
			json_msg=json.dumps(send_dict)
			# print('json ready',json_msg)
			got_bad_char, msg_arr=self.prep_msg(json_msg,to)
			# print(msg_arr)
			# return
			
			if got_bad_char:
				return
			
			
			
			ddict={'fromaddr':froma,	'to':[]	} #
			for mm in msg_arr:
				ddict['to'].append({'z':to,'a':0.0001,'m':mm})
				
			# print('sending ddict\n',ddict)
			# print('temporaty return')
			# return
				
			table={}
			table['queue_waiting']=[localdb.set_que_waiting('send',jsonstr=json.dumps(ddict) ) ]
			table['queue_waiting'][0]['type']='channel'
			
			idb.insert(table,['type','wait_seconds','created_time','command' ,'json','id','status' ])
			
			# self.set_last_addr_from( froma)
			localdb.set_last_addr_from( froma,"'last_msg_from_addr'")
			msg_table.parent().close()
			
			
			
			
			
		msg_table.cellWidget(3,2).set_fun(True,send) #set_cmd('send',[ ], send)
		msg_table.cellWidget(0,1).set_fun(False,self.addr_book.get_addr_from_wallet ) 
		
		if tmpaddr=='':
			msg_table.cellWidget(1,1).set_fun(False,self.addr_book.get_addr_from_book, msg_table.cellWidget(1,1)) 
		
		gui.CustomDialog(btn,[msg_table ], title='Write message ')
		
	
	
	
	
	
	def is_channels_active(self):
	
		idb=localdb.DB(self.db)
		
		# table={'channel_signatures':[{'addr':to,'signature':tmpsender}]} 
		# print('channel_signatures\n', idb.select('channel_signatures'  ) )
		
		
		# table['addr_book']={'Category':'text', 'Alias':'text', 'Address':'text','ViewKey':'text','usage':'int','addr_verif':'int','viewkey_verif':'int' }
		xx=idb.select('addr_book', [ 'Address', 'viewkey_verif'] ,{'Address':['=',  "'"+self.defchnls.activation_channel_addr+"'" ] } )
		
		if len(xx)==0:
			print('no def channel - need to activate channels')
			return False
			
		elif xx[0][0]==None:
			print(' channel = none',xx)
			return False
		else:
			if xx[0][1]<1:
				print('is_channels_active: channels active but view key not validated',xx)
				
				return False
		
			#print('channels active',xx)
			return True 
	
	
	def updateFilter(self,*evargs):
		tmpdict={}
		
		widgetExist=False
		if self.filter_table.cellWidget(0,1)!=None: 
			if self.filter_table.cellWidget(0,1).isEnabled():
				widgetExist=True
		
		if not self.is_channels_active() and widgetExist==False: 
			# if exists and if is true do not update ?
		
			tmp_active_active=False
			tmp_active_tooltip='Sync the wallet to activate channels'
			if len(evargs)>0:
				# print('evargs',evargs)
				for ee in evargs:
					# print('ee',ee)
					if ee==True:
						# print(156)
						tmp_active_active=True
						tmp_active_tooltip='This will add common public channel (takes few minutes)'
						break
			# print('tmp_active_active',tmp_active_active)
			tmpdict['rowk']='activation'
			tmpdict['rowv']=[ {'T':'LabelC', 'L':'Activate Channels:','align':'center'} 
							, {'T':'Button', 'L':'Activate','tooltip': tmp_active_tooltip } 
							,{'T':'LabelC', 'L':''},{'T':'LabelC', 'L':''},{'T':'LabelC', 'L':''},{'T':'LabelC', 'L':''}
						]
						 
			self.filter_table.updateTable([tmpdict])  
			def activateChannels(*evargs):  
				idb=localdb.DB(self.db)
				
				tmpaddr=self.defchnls.activation_channel_addr
				tmpvk=self.defchnls.channels[tmpaddr]
				table={'addr_book':[{'Category':'Channel','Alias':'Tavern','Address':tmpaddr,'ViewKey':tmpvk,'usage':0,'addr_verif':1,'viewkey_verif':-2}]   }
				idb.upsert(table,[ 'Category','Alias','Address','ViewKey','usage','addr_verif','viewkey_verif'], {'Address':['=',  "'"+tmpaddr+"'" ] } )
				
				self.refreshAddrBook.emit() 
				tmpjson=json.dumps({'addr':tmpaddr,'viewkey':tmpvk})
				table={'queue_waiting':[localdb.set_que_waiting(command='import_view_key',jsonstr=tmpjson, wait_seconds=0)]}
				idb.insert(table,['type','wait_seconds','created_time','command' ,'json','id','status' ])
				gui.messagebox_showinfo('Channels activated','Initial public channel (Tavern) added to wallet! Syncing will take few minutes.',None) 
				self.filter_table.cellWidget(0,1).setEnabled(False) # when imported update filters !
			# print('tmp_active_active 2',tmp_active_active)	
			self.filter_table.cellWidget(0,1).setEnabled( tmp_active_active )
			self.filter_table.cellWidget(0,1).set_fun(False, activateChannels)
			
		else:
			
			tmpdict['rowk']='filters'
			tmpdict['rowv']=[ {'T':'LabelC', 'L':'Channels:','align':'center'}
							, {'T':'Combox', 'uid':'thr', 'V':['Last 7 days','Last 30 days','All'] }
							, {'T':'LabelC', 'L':'Messages:','align':'center'}
							, {'T':'Combox', 'uid':'msg', 'V':['Last 10','Last 100', 'All'] }
							# , {'T':'Button', 'L':'Import', 'tooltip':'new channel' }
							, {'T':'Button', 'L':'Export','tooltip':'current channel'  }
							, {'T':'Button', 'L':'Reply','tooltip':'to current channel'  }
						] 
			self.filter_table.updateTable([tmpdict]) 
			
			self.filter_table.cellWidget(0,1).set_fun( self.update_tread_frame) #bind_combox_cmd('thr',[], self.update_tread_frame )	
			self.filter_table.cellWidget(0,3).set_fun( self.update_msg_frame) #.bind_combox_cmd('msg',[], self.update_msg_frame )	
			# self.filter_table.cellWidget(0,4).set_fun(False,self.send_reply,'s') #.set_cmd('newmsg',['s' ], self.send_reply)
			# self.filter_table.cellWidget(0,4).set_fun(False,print,'Import') #.set_cmd('newmsg',['s' ], self.send_reply)
			
			
			if self.cur_uid in self.valid_uid_to_name:
				tmpalias=self.valid_uid_to_name[self.cur_uid] #'CHANNEL NAME!!!' #self.grid_threads_msg[curid][0]['rowv'][1]['uid'] #TO CHANGE CHANNEL
				 
				self.filter_table.cellWidget(0,4).updateButton(name='Export '+ tmpalias['name'], actionFun=self.export_channel,args=( self.cur_uid, tmpalias['vk'] ) )
				self.filter_table.cellWidget(0,5).updateButton(name='Reply to '+ tmpalias['name'], actionFun=self.send_reply,args=('r',tmpalias['name'] ) )
				 
				self.filter_table.cellWidget(0,4).setEnabled(True) 
				self.filter_table.cellWidget(0,5).setEnabled(True) 
			else:
				self.filter_table.cellWidget(0,4).set_fun(False,print,'Export')
				self.filter_table.cellWidget(0,4).setEnabled(False) #.set_cmd('newmsg',['s' ], self.send_reply)
				self.filter_table.cellWidget(0,5).set_fun(False,print,'Reply')
				self.filter_table.cellWidget(0,5).setEnabled(False) #.set_cmd('newmsg',['s' ], self.send_reply)
	
	
	#todo next:
	# add adj texedit in msg
	# create nice channel creation info on channel init
	# 
	def __init__(self, msg_obj,addr_book):
		super(Chnls, self).__init__()
		# detect channels active!
		# table['channels']={'address':'text', 'vk':'text', 'creator':'text', 'channel_name':'text', 'channel_intro':'text', 'status':'text', 'own':'text', 'channel_type':'text' }
		self.cur_uid=-1
		self.valid_uid_to_name=[]
		# print('CHANNEL INIT')
		self.defchnls=DefChannels()
		# self.activation_channel_addr='zs18mkw7d8d4ts3ctw24hmsk8auerq3r7ekhq356x8n72jfz5praez9kuh35s398lxy69zmq2snr9p'
	
		# self.channels
		
		self.get_msg_parts =msg_obj.get_msg_parts
		self.prep_msg =msg_obj.prep_msg
		
		
		self.update_in_progress=False
		self.db=addr_book.db
		
		
		
		self.max_block=0
		
		self.addr_book=addr_book
		
		self.parent_frame=gui.ContainerWidget(None,layout=gui.QVBoxLayout() )
		
		frame0=gui.FramedWidgets(None,'Filter')  
		# frame0.setMaximumHeight(128)
		self.parent_frame.insertWidget(frame0) #ttk.LabelFrame(parent_frame,text='Options')  
		
		self.filter_table=gui.Table(None,params={'dim':[1,6],'updatable':1} ) 
		self.updateFilter()
		
			
			
		frame0.insertWidget(self.filter_table) 
		frame0.setMaximumHeight(self.filter_table.height()) 
		self.grid_threads=[]
		self.grid_threads_msg={}
		self.thr_ord=[]
		
		self.msg_thrd_frame=gui.ContainerWidget(None,layout=gui.QHBoxLayout() )
		self.parent_frame.insertWidget(self.msg_thrd_frame)
				
		self.frame1= gui.FramedWidgets(None,'Threads') #ttk.LabelFrame(parent_frame,text='Threads')  
		self.frame1.setMaximumWidth(196)
		self.frame1.setMinimumWidth(128)
		self.msg_thrd_frame.insertWidget(self.frame1)
		
		# self.update_threads()
		
		self.thr_table=gui.Table(None,params={'dim':[len(self.grid_threads),2],'updatable':1,'default_sort_col': 'sorting_datetime','hideColumns':['sorting_datetime' ],'hideColNames':1} )  
		
		self.thr_table.updateTable(self.grid_threads,['buttons','sorting_datetime'])
		self.frame1.insertWidget(self.thr_table)
		# self.set_actions()
		
		self.frame2= gui.FramedWidgets(None,'Selected thread',layout=gui.QVBoxLayout())
		self.action_buttons=gui.ContainerWidget(None,layout=gui.QHBoxLayout() )
		self.frame2.insertWidget(self.action_buttons)	
		
		
		self.maxMsgColWidth=self.action_buttons.width() 
		# self.update_list()
		
		self.msg_thrd_frame.insertWidget(self.frame2)	
		 
		self.main_table=None
		self.main_table_params={ 'updatable':1,'sortable':1,'default_sort_col':'Date time' ,'rowSizeMod':1} #self.main_table_params['dim']=[len(self.grid_threads_msg[self.cur_uid]),2],
		
		
		self.updating_threads=False
		self.updating_chat=False
		
		
	 
	def export_channel(self,btn,addr,vk):
		
		automate_rowids=[ 
							[{'T':'LabelC', 'L':'Export type: ' } , {'T':'Combox', 'V':['encrypted file','display on screen','not encrypted file']  } ] ,
							[{'T':'Button', 'L':'Enter', 'uid':'enter', 'span':2  }, {}] 
						]
	
		expo=gui.Table(None,{'dim':[2,2]}) #flexitable.FlexiTable(rootframe,grid_settings)
		expo.updateTable(automate_rowids)
		# rootframe.insertWidget(expo)
		
		def enter(btn2):
			# global rootframe, expo
			expo=btn2.parent().parent()
			table={}
			ddict={'addr':addr, 
					'viewkey':vk
					}
			tmpresult=json.dumps(ddict)
			
			if expo.cellWidget(0,1).currentText()=='display on screen':
				gui.messagebox_showinfo('Channel parameters', app_fun.json_to_str(tmpresult),None)
			else:
				path=gui.set_file( None,validation_fun=None,dir=True,parent=btn2,init_path=os.getcwd(),title="Select directory to write to")
				if path==None:
					return 
				pto=os.path.join(path,'channel_viewkey_'+app_fun.now_to_str()+'.txt')
				
				
				if expo.cellWidget(0,1).currentText()=='encrypted file':
			
					cc=aes.Crypto()
					tmppass=cc.rand_password(32)
					cc.aes_encrypt_file( tmpresult, pto  , tmppass) 	

					tmptitle='Channel export. Password for file exported to:\n\n'+pto+'\n\n' #+tmppass	
					gui.output_copy_input(None,tmptitle,(tmppass,))
					
				elif expo.cellWidget(0,1).currentText()=='not encrypted file':
					
					app_fun.save_file(pto,tmpresult) 
			expo.parent().close()  
		expo.cellWidget(1,0).set_fun(False,enter) #set_cmd( 'enter',[],enter)
		rootframe =gui.CustomDialog(btn,expo, title='Exporting channel')	
		 
		 
		 
	def set_reply(self): #,curid - diff to msgs
		
		
		# self.cur_addr=curid # self.cur_uid
		tmpalias=self.valid_uid_to_name[self.cur_uid] #'CHANNEL NAME!!!' #self.grid_threads_msg[curid][0]['rowv'][1]['uid'] #TO CHANGE CHANNEL
		 
		# self.filter_table.cellWidget(0,4).setEnabled(True) 
		# self.filter_table.cellWidget(0,5).setEnabled(True) 
		 
		self.filter_table.cellWidget(0,4).updateButton(name='Export '+ tmpalias['name'], actionFun=self.export_channel,args=( self.cur_uid, tmpalias['vk'] ) )
		self.filter_table.cellWidget(0,5).updateButton(name='Reply to '+ tmpalias['name'], actionFun=self.send_reply,args=('r',tmpalias['name'] ) )
		 
		self.filter_table.cellWidget(0,4).setEnabled(True) 
		self.filter_table.cellWidget(0,5).setEnabled(True) 
		
		citems=self.action_buttons.layout().count()
		tmplen=len(tmpalias['intro'])
		tmpmsg='Channel intro: '+tmpalias['intro']
		if len(tmpalias['intro'])>64:
			tmpmsg='Channel intro: '+tmpalias['intro'][:64]+' ...'
		
		if citems>0:
			self.action_buttons.layout().itemAt(0).widget().setText( tmpmsg)
			self.action_buttons.layout().itemAt(0).widget().setToolTip( tmpalias['intro'] )
		else:
			self.action_buttons.insertWidget( gui.Label(None, tmpmsg,tooltip=tmpalias['intro'] ))			
			 
		
		
		
	# threads : different correspondents
	def update_tread_frame(self ,*args):
	
		while self.updating_threads:
			time.sleep(1)
	
		self.updating_threads=True
		try:  
		# if True:
			self.update_threads() 
			self.thr_table.updateTable(self.grid_threads)
			# self.set_actions()
			self.updating_threads=False
			# when assigning - should refresh messages too !
		except:
			
			self.updating_threads=False # print('msg update_tread_frame')
		 
		 
		 
	def update_msg_frame(self,*evargs):
		# print('updating chat')
		while self.updating_chat:
			time.sleep(1)
			print('updating chat sleep 1')
			
		self.updating_chat=True
		 
		if len(evargs)>0: 
			# print('channel changing self.cur_uid len(evargs)>0 TO:',evargs[-1],'evargs',evargs)
			self.cur_uid=evargs[-1]
		
		try:
		 
			if len(self.thr_ord )>0:
				if self.cur_uid not in self.valid_uids:
					# print('init self.cur_uid',self.cur_uid)
					# print('channel changing self.cur_uid AGAIN NOT IN ',self.cur_uid,'not in valid arr',self.valid_uids)
					self.cur_uid = self.valid_uids[0] 
					# print('\t set',self.cur_uid )
			
			# if hasattr(self,'cur_uid') and self.cur_uid>-1:
			
				if self.maxMsgColWidth<=640: self.maxMsgColWidth=self.action_buttons.width()
				self.update_list()
				 
				tmpcolnames=[]
				if self.main_table==None: 
					self.main_table_params['colSizeMod']=[80,self.maxMsgColWidth-100 ] #-80
			
					self.main_table_params['dim']=[len(self.grid_threads_msg[self.cur_uid]),2]
					self.main_table=gui.Table(None,params=self.main_table_params ) 
					self.main_table.setMinimumWidth(self.maxMsgColWidth) # increasing this does not help 
					self.frame2.insertWidget(self.main_table)	
					tmpcolnames=['Date time','Messages']
				else:
					for ii,mm in enumerate([80,self.maxMsgColWidth-100]):
						self.main_table.setColumnWidth(ii,mm)
					
					
				# BUG HERE every click changes some width ... 	
				# fix - remove colnames to tmpcolnames
				# move update list after maxcolwidth
				# add conditional maxcolwidth
					
				self.main_table.updateTable(self.grid_threads_msg[self.cur_uid],tmpcolnames,doprint=False) #+'_'
				self.set_reply( )
				 
		except:
			print('exception: update_msg_frame')
			
		self.updating_chat=False
		# print(452)
	
	
	@gui.Slot()	
	def update_channels(self):
		# time.sleep(15)
		# print('\n\nupdate_channels')
		# def tmp():
			# self.update_tread_frame()
			# self.update_msg_frame()
			
		# gui.QTimer.singleShot(15000,tmp)
		self.update_tread_frame()
		self.update_msg_frame()
		  
		
		
		
	# in msg channels = external addresses = external uids
	# in channels = registered channels 
	def update_threads(self):
		# print('\nupdate_threads')
	
		idb=localdb.DB(self.db)
		 
		thr_filter=self.filter_table.cellWidget(0,1).currentText() #get_value('thr')
		wwhere={'in_sign_uid':['>',-2],'is_channel':['=',"'True'"]} #'Last 7 days','Last 30 days','All'
		if thr_filter=='Last 7 days':
			wwhere={'date_time':['>=',"'"+app_fun.today_add_days(-7)+"'"], 'in_sign_uid':['>',-2],'is_channel':['=',"'True'"]} #
		elif thr_filter=='Last 30 days':
			wwhere={'date_time':['>=',"'"+app_fun.today_add_days(-30)+"'"], 'in_sign_uid':['>',-2],'is_channel':['=',"'True'"]}
			
		# need channel name 
		adr_date=idb.select_max_val( 'msgs_inout',['in_sign_uid','date_time'],where=wwhere,groupby=['addr_to'])
		
		print('Channel threads available\n',idb.select_max_val( 'msgs_inout',['in_sign_uid','date_time'],where={ 'is_channel':['=',"'True'"]},groupby=['addr_to']))
		# print('msgs',idb.select('msgs_inout'))
		if hasattr(self,"adr_date") and self.adr_date==adr_date:
			return 0
			
		self.adr_date=adr_date
		
		# print('latest channel addr date',adr_date)
		
		self.grid_threads=[]
			
		threads_aa={} 
		same_date_count={}
		unk_count=1
		
		for ad in adr_date:
			# print('processing for ad',ad)
			# tmpalias=''
			if ad[0]==None:
				continue
			
			tmpaddr=ad[0]
			# tmpuid= str(ad[0])
			# if ad[0]!=None and ad[0]!='': # all out + some in
				
				# chnl name :
				
				# alias_from_book
			chnl_info=idb.select('channels', [ 'vk' , 'creator' , 'channel_name' , 'channel_intro'],{'address':['=',  "'"+ad[0]+"'" ] } ) # idb.select('addr_book', [ 'Alias'],{'Address':['=',  "'"+ad[0]+"'" ] } ) ##
			# print('chnl_info',chnl_info)
			if len(chnl_info)==0:
				continue
			alias_from_book=chnl_info[0][2] # chnl name
			tmpalias=alias_from_book
				 
					
			if ad[2] not in threads_aa:
				same_date_count[ad[2]]=1
				
			else:
				same_date_count[ad[2]]=same_date_count[ad[2]]+1
				
			threads_aa[ad[2]+'__'+str(same_date_count[ad[2]])] = [tmpaddr,{'vk':chnl_info[0][0],'creator':chnl_info[0][1],'channel_name':chnl_info[0][2],'channel_intro': chnl_info[0][3] }  ] 
			# threads_aa[ad[2]+'__'+str(same_date_count[ad[2]])] = [tmpaddr,tmpalias,tmpuid ] 
		# print('threads',threads_aa)
		self.threads_aa=threads_aa
		self.thr_ord=sorted(threads_aa.keys(),reverse=True)
		self.valid_uids=[]
		self.valid_uid_to_name={}
		
		for k in self.thr_ord:
			tooltiptmp='Owner: '+threads_aa[k][1]['creator']+'\nIntro: '+threads_aa[k][1]['channel_intro']
			tmpdict={'rowk':threads_aa[k][1]['channel_name'] , 'rowv':[{'T':'Button', 'L':threads_aa[k][1]['channel_name'], 'tooltip':tooltiptmp, 'uid':threads_aa[k][0], 'fun':self.update_msg_frame, 'args':(threads_aa[k][0],) } 
									, {'T':'LabelV', 'L':k  }  ]}
			 
			self.grid_threads.append(tmpdict) 
			self.valid_uids.append( threads_aa[k][0] ) 
			self.valid_uid_to_name[threads_aa[k][0]] = {'name':threads_aa[k][1]['channel_name'],'owner':threads_aa[k][1]['creator'],'intro':threads_aa[k][1]['channel_intro'], 'vk':threads_aa[k][1]['vk']}
			
		# print(self.valid_uid_to_name)
		return 1
		
			
	

	def update_list(self ):
		# print('\nupdate_list')
		idb=localdb.DB(self.db)
		msg_filter=self.filter_table.cellWidget(0,3).currentText() #get_value('msg')
		llimit=9999
		
		if msg_filter=='Last 10':
			llimit=10
		elif msg_filter=='Last 100':
			llimit=100
			
		threads_aa=self.threads_aa		
		
		for k in self.thr_ord:
			 
			tmpuid=threads_aa[k][0]
			# print('tmpuid',tmpuid)
			
			# wwhere={}
			 
			wwhere={'proc_json':['=',"'True'"],'addr_to':['=',"'"+threads_aa[k][0]+"'"], 'in_sign_uid':['>',-2],'is_channel':['=',"'True'"], 'type':['=',"'in'"] } #, 'Type':
			# wwhere={'proc_json':['=',"'True'"],'addr_to':['=',"'"+threads_aa[k][0]+"'"], 'in_sign_uid':['>',-2],'is_channel':['=',"'True'"], 'type':[' like ',"'in%'"] } ## ' like ',"'in%'"
				
			# addr ext here is name of sender 
			tmp_msg=idb.select('msgs_inout', ['type','msg','date_time','uid','in_sign_uid','addr_ext' ],where=wwhere, orderby=[ {'date_time':'desc'}], limit=llimit)
			# print('tmp_msg\n',tmp_msg) 
			 
			msg_flow=[]
			
			ccounter=0
			for tm in tmp_msg:
				
				sstyle1=" background-color:#fff;color:#333; padding:2px "
				sstyle2=" background-color:#fff;color:#333; min-width:668px;max-width:768px;padding:2px "
				# tmppadx=0
				# writer='['+threads_aa[k][1]+']: '
				writer='['+tm[5]+']: '
				if ccounter==0: #tm[0]=='out':
					# writer='[me]: '
					ccounter=1
					sstyle1=" background-color:#ddd;color:black; padding:2px "
					sstyle2="background-color:#ddd;color:black; min-width:668px;max-width:768px;padding:2px  "
				else:
					ccounter=0
					
				# tm[1]=tm[1]+' aaa '
				tmptoinsert=writer+tm[1] #+' aaa </br> bbb <br> ccc \n ddd \\n eee '
				# {'T':'QLabel', 'L':tm[2] ,  'style':sstyle1,'ttype':gui.QDateTime  } {'T':'TextEdit', 'L': tm[2],  'style':sstyle1, 'readonly':1,'width': 80  }
				tmpdict={'rowk':tm[2], 'rowv':[{'T':'QLabel', 'L':tm[2] ,  'style':sstyle1,'ttype':gui.QDateTime  } , {'T':'TextEdit', 'L': tmptoinsert, 'uid':str(threads_aa[k][0]),  'style':sstyle2, 'readonly':1,'width': (self.maxMsgColWidth-100)  }] } # -80
				msg_flow.append(tmpdict)
				
			# print('\n\nchannel msg format')
			# print(msg_flow)
			self.grid_threads_msg[tmpuid]=msg_flow 
	

