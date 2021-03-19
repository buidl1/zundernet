# check proper updating msm on events

import os
# import datetime
import json
import time
import modules.localdb as localdb
import modules.app_fun as app_fun

import modules.aes as aes
import modules.gui as gui

class Msg:

	def match_sign(self,fsign): 
		if len(fsign)==0:
			return -1,''
		
		idb=localdb.DB(self.db)
		cry=aes.Crypto(224)
		
		sign1=cry.utf8_1b2hash(fsign['sign1'])
		sign1_n=fsign['sign1_n']
		
		sign2,sign2_n=('none',-1)
		if 'sign2' in fsign:
			sign2=cry.utf8_1b2hash( fsign['sign2'] )
			sign2_n=fsign['sign2_n']
			
		ss=idb.select('in_signatures', ['hex_sign','n','uid','addr_from_book'],{'n':['>', sign1_n] },orderby=[{'n':'asc'}]) #
		
		n_init=sign1_n
		tmphash=''
		tmpsign1=sign1
		new_uid=-1
		addr_from_book=''
		
		for s in ss:
			
			ntimes=s[1]-n_init
			if ntimes>0:
				tmphash=cry.hash(tmpsign1,ntimes)
			else:
				tmphash=tmpsign1
			
			n_init=s[1]
			tmpsign1=tmphash
			
			if tmphash==s[0]:
				new_uid=s[2]
				
				if s[3]!=None:
					addr_from_book=s[3]
					
				break
			tmphash=''
			
		tuid=idb.select('in_signatures',['uid' ], {'hex_sign':['=',"'"+sign1+"'"],'n':['=',sign1_n]}   ) #
		
		if len(tuid)>0:
			return -666,''
		
		if tmphash=='': 
			
			table={}
			table['in_signatures']=[{'hex_sign':sign1,'n':sign1_n ,'uid':'auto'}]
			idb.insert(table,['hex_sign','n','uid'  ])
			
			tuid=idb.select('in_signatures',['uid','addr_from_book'], {'hex_sign':['=',"'"+sign1+"'"],'n':['=',sign1_n]}   ) #
			new_uid=tuid[0][0]
			if tuid[0][1]!=None:
				addr_from_book=tuid[0][1]
		else: 
			
			table={}
			table['in_signatures']=[{'hex_sign':sign1,'n':sign1_n}]
			idb.update(table,['hex_sign','n'   ],{'hex_sign':['=',"'"+tmphash+"'"],'n':['=',n_init]})
		
		if sign2_n>-1: 
			
			cursign=idb.select('in_signatures', ['uid','addr_from_book' ],{'hex_sign':['=', "'"+sign1+"'"], 'n':['=', sign1_n] } ) #
			tmpaddr=cursign[0][1]
			tmpuid=cursign[0][0]
			
			table={}
			table['in_signatures']=[{'hex_sign':sign2,'n':sign2_n}]
			idb.insert(table,['hex_sign','n'])
			
			table={} 
			table['in_signatures']=[{'uid':tmpuid,'addr_from_book':tmpaddr }]
			idb.update(table,['uid','addr_from_book' ],{'hex_sign':['=',"'"+sign2+"'"],'n':['=',sign2_n] })
			
		return new_uid,addr_from_book 
		
	
	
	


	def get_msg_parts(self,mm):	

		def splitutf8_512bytes(mm):

			if len(mm.encode('utf-8') )<513:
				return [mm ,len(mm.encode('utf-8') )], ''
				
			cur_ii=len(mm)//2
			cur_vv=len(mm[:cur_ii].encode('utf-8') )
			cur_step=cur_ii
			cur_diff=512-cur_vv
			tmpabs=abs(cur_diff)
			
			while cur_vv>511 or tmpabs>4:
			
				if tmpabs>cur_step:
					new_step=max(min(cur_step//2+1,tmpabs),1)
				else:
					new_step=max(min(cur_step//2,tmpabs),1)
					
				if new_step<cur_step:
					cur_step=new_step
					
				if cur_diff==0:
					break
				
				elif cur_diff<0:
					cur_ii=cur_ii-cur_step
				else:
					cur_ii=cur_ii+cur_step
					
				cur_vv=len(mm[:cur_ii].encode('utf-8') )
				new_diff=512-cur_vv
				
				cur_diff=new_diff
				tmpabs=abs(cur_diff)

			return [mm[:cur_ii],cur_vv], mm[cur_ii:]

			
		ar=[]

		while len(mm)>0:
			m1,mm=splitutf8_512bytes(mm)
			ar.append(m1)
			
		return ar
	
	
	
	
	
	def prep_msg(self,mm,addr):
			
		got_bad_char=False
		total_bytes=0
		
		try:
			total_bytes=len(mm.encode('utf-8')) #sys.getsizeof(mm.encode('utf-8'))
		
		except:
			badc=''
			bad_ii=-1
			for ii,cc in enumerate(mm):
				try:
					cc.encode('utf-8')
				except:
					badc=cc
					bad_ii=ii
					got_bad_char=True
					break
			
			gui.showinfo('Bad character in memo input', 'This input contains bad character ['+badc+']:\n'+mm+'\n position: '+str(bad_ii))
			return got_bad_char, []
			
		msg_parts=self.get_msg_parts(mm)
		tmpsignature=localdb.get_addr_to_hash(addr)
		
		if msg_parts[-1][1]+len(tmpsignature)<513:
			msg_parts[-1]=[msg_parts[-1][0]+tmpsignature , msg_parts[-1][1]+len(tmpsignature) ]
		else:
			msg_parts.append([tmpsignature,len(tmpsignature)])
			
		msg_parts=[mm[0] for mm in msg_parts]
		
		return got_bad_char, msg_parts
	
	
	
	def proc_inout(self): # goal - set addr_ext and in_sign_uid for incoming msg
		idb=localdb.DB(self.db)
		
		mio=idb.select('msgs_inout',['type','addr_ext','date_time','msg', 'in_sign_uid','uid','tx_status','txid'],{'proc_json':['=',"'False'"]},orderby=[{'date_time':'asc'}]) #
		
		if len(mio)==0:
			return
			
		for mm in mio:
		
			mm1=mm[1]
			tmpmsg=mm[3]
			
			if mm[0]=='out':
				table={'msgs_inout':[{'proc_json':'True' }]} 
				idb.update(table,['proc_json' ],{'uid':['=',mm[5]]})
				
			elif mm[0]=='in' :
				
				fsign=json.loads(mm1 )
				
				uid,addr_from_book=self.match_sign( fsign)
				
				addr_ext=''
				if uid>-1:
					tmpalias='uid_'+str(uid)
					if addr_from_book!='':
						addr_ext=addr_from_book
						
						tmpalias=idb.select('addr_book',['Alias'] , {'Address':['=',"'"+addr_from_book+"'"] } )
						tmpalias=tmpalias[0][0]
					else:
						addr_ext=tmpalias
						
					table_h={}
					uidtmp=tmpalias+';uid='+str(uid)+': '
					table_h['tx_history']=[{'from_str':uidtmp+mm[3]}]
					idb.update(table_h,['from_str' ],{'txid':['=',"'"+mm[7]+"'"]})
					
					table_n={}
					orig_json=idb.select('notifications',['orig_json'],{'details':['=',"'"+mm[7]+"'"]})
					uidtmp='From '+tmpalias+';uid='+str(uid)+': '+orig_json[0][0]
					table_n['notifications']=[{'orig_json':uidtmp }]
					idb.update(table_n,['orig_json' ],{'details':['=',"'"+mm[7]+"'"]})
					
					if tmpmsg=='':
						tmpmsg='Received '+orig_json[0][0]
						
				# 'type',
				tmptype=mm[0]
				if 'PaymentRequest' in mm[3]:
					tmptype='PaymentRequest'
					
					tmpmsg=tmpmsg.split('PaymentRequest;')
					tmpmsg=tmpmsg[-1]
					tmpmsg='Payment request '+app_fun.json_to_str(json.loads(tmpmsg),tt='')				
					
				table={'msgs_inout':[{'type':tmptype,'proc_json':'True', 'in_sign_uid':uid, 'addr_ext':addr_ext,'msg':tmpmsg}]} 
				idb.update(table,['type','proc_json', 'in_sign_uid','addr_ext','msg'],{'uid':['=',mm[5]]})
				
		
		
			
			
	def send_reply(self,btn,*args):
		

		msg_grid=[]
		tmpdict={'rowk':'from', 'rowv':[{'T':'LabelC', 'L':'Select own address','width':19},{'T':'Button', 'L':'...', 'uid':'selownadr', 'width':4}]}
		msg_grid.append(tmpdict) #, {'T':'LabelV','L':'','uid':'ownaddr','width':80}
		
		tmpdict={'rowk':'to', 'rowv':[{'T':'LabelC', 'L':'Select address to','width':19},{'T':'Button', 'L':'...', 'uid':'seladr', 'width':4}]} #, {'T':'LabelV','L':'','uid':'addr','width':80}
		
		tmpaddr=''
		# print(self.cur_addr)
		if args[0]=='r' and hasattr(self,'cur_addr'):
			if self.cur_addr!='':
				tmpaddr=self.cur_addr
				tmpdict={'rowk':'to', 'rowv':[{'T':'LabelC', 'L':'Replying to: '+tmpaddr,'width':80}  ]}
			
		msg_grid.append(tmpdict)
		tmpdict={'rowk':'msg', 'rowv':[{'T':'TextEdit','uid':'msg','span':2, 'style':'background-color:white;'} ]}
		msg_grid.append(tmpdict)
		tmpdict={'rowk':'send', 'rowv':[{'T':'Button', 'L':'Send', 'uid':'send','width':6}  ] }
		msg_grid.append(tmpdict)
		
		# msg_table=flexitable.FlexiTable(selframe,msg_grid)
		msg_table=gui.Table(None,{'dim':[len(msg_grid),2], 'toContent':1})
		msg_table.updateTable(msg_grid)
		
		last_addr=localdb.get_last_addr_from("'last_msg_from_addr'")

		if last_addr not in ['','...']:
			msg_table.cellWidget(0,1).setToolTip(last_addr) #.set_textvariable( 'ownaddr',last_addr)
			msg_table.cellWidget(0,1).setText( self.addr_book.cat_alias( last_addr,own=True) )
		
		def send():
			# global tmpaddr
			msg=msg_table.cellWidget(2,0).toPlainText()  #get_value( 'msg')
			if msg.strip()=='':
				return
			
			
			to=tmpaddr
			if tmpaddr=='':
				to=msg_table.cellWidget(1,1).toolTip() #.get_value( 'addr')
				
			froma=msg_table.cellWidget(0,1).toolTip() #.get_value( 'ownaddr')
			if froma=='':
				return
				
			got_bad_char, msg_arr=self.prep_msg(msg,to)
			
			if got_bad_char:
				return
			
			ddict={'fromaddr':froma,	'to':[]	} #
			for mm in msg_arr:
				ddict['to'].append({'z':to,'a':0.0001,'m':mm})
				
			table={}
			table['queue_waiting']=[localdb.set_que_waiting('send',jsonstr=json.dumps(ddict) ) ]
			table['queue_waiting'][0]['type']='message'
			
			idb=localdb.DB(self.db)
			idb.insert(table,['type','wait_seconds','created_time','command' ,'json','id','status' ])
			
			# self.set_last_addr_from( froma)
			localdb.set_last_addr_from( froma,"'last_msg_from_addr'")
			msg_table.parent().close()
			
		msg_table.cellWidget(3,0).set_fun(True,send) #set_cmd('send',[ ], send)
		msg_table.cellWidget(0,1).set_fun(False,self.addr_book.get_addr_from_wallet ) 
		
		if tmpaddr=='':
			msg_table.cellWidget(1,1).set_fun(False,self.addr_book.get_addr_from_book, msg_table.cellWidget(1,1)) 
		
		gui.CustomDialog(btn,[msg_table ], title='Write message ')
		
	
			
		
	def __init__(self,addr_book ): # notebook_parent : in case of new msg - adj tab title 
		self.update_in_progress=False
		self.db=addr_book.db
		
		self.max_block=0
		self.proc_inout()
		
		self.addr_book=addr_book
		
		self.parent_frame=gui.ContainerWidget(None,layout=gui.QVBoxLayout() )
		
		frame0=gui.FramedWidgets(None,'Filter')  
		frame0.setMaximumHeight(128)
		self.parent_frame.insertWidget(frame0) #ttk.LabelFrame(parent_frame,text='Options')  
		
		tmpdict={}
		tmpdict['rowk']='filters'
		tmpdict['rowv']=[ {'T':'LabelC', 'L':'Threads: '}
							, {'T':'Combox', 'uid':'thr', 'V':['Last 7 days','Last 30 days','All'] }
							, {'T':'LabelC', 'L':'Messages: '}
							, {'T':'Combox', 'uid':'msg', 'V':['Last 10','Last 100', 'All'] }
							# , {'T':'Button', 'L':'Reply', 'uid':'reply'}
							, {'T':'Button', 'L':'New message', 'uid':'newmsg', 'width':13}
						]
		grid_filter=[]
		grid_filter.append(tmpdict )
		
		self.filter_table=gui.Table(None,params={'dim':[1,5],'updatable':1} )  #, 'toContent':1
		self.filter_table.updateTable(grid_filter)
		frame0.insertWidget(self.filter_table)
		
		self.filter_table.cellWidget(0,1).set_fun( self.update_tread_frame) #bind_combox_cmd('thr',[], self.update_tread_frame )	
		self.filter_table.cellWidget(0,3).set_fun( self.update_msg_frame) #.bind_combox_cmd('msg',[], self.update_msg_frame )	
		self.filter_table.cellWidget(0,4).set_fun(False,self.send_reply,'s') #.set_cmd('newmsg',['s' ], self.send_reply)
		
		self.grid_threads=[]
		self.grid_threads_msg={}
		self.thr_ord=[]
		
		self.msg_thrd_frame=gui.ContainerWidget(None,layout=gui.QHBoxLayout() )
		self.parent_frame.insertWidget(self.msg_thrd_frame)
				
		self.frame1= gui.FramedWidgets(None,'Threads') #ttk.LabelFrame(parent_frame,text='Threads')  
		self.frame1.setMaximumWidth(256)
		self.frame1.setMinimumWidth(256)
		self.msg_thrd_frame.insertWidget(self.frame1)
		
		self.update_threads()
		
		self.thr_table=gui.Table(None,params={'dim':[len(self.grid_threads),1],'updatable':1} )  
		
		self.thr_table.updateTable(self.grid_threads)
		self.frame1.insertWidget(self.thr_table)
		self.set_actions()
		
		self.update_list()
		self.frame2= gui.FramedWidgets(None,'Selected thread',layout=gui.QVBoxLayout())
		self.action_buttons=gui.ContainerWidget(None,layout=gui.QHBoxLayout() )
		self.frame2.insertWidget(self.action_buttons)	
		
		
		
		self.msg_thrd_frame.insertWidget(self.frame2)	
		
		
		
		self.main_table=None
		if len(self.thr_ord )>0:
			
			self.cur_uid=self.valid_uids[0] 
			
			self.main_table=gui.Table(None,params={'dim':[len(self.grid_threads_msg[self.cur_uid]),2],'updatable':1,'toContent':1,'sortable':1,'default_sort_col':'Date time'} ) 
			self.main_table.updateTable(self.grid_threads_msg[self.cur_uid],['Date time','Messages']) #+'_'
			self.set_edit_drop_reply(self.cur_uid)
			
			self.frame2.insertWidget(self.main_table)	
			
		self.updating_threads=False
		self.updating_chat=False
		
		
	

	def drop_alias(self,btn,uid ):

		if 'uid_' in uid:
			self.warning_info('No address to drop!',uid+' is not an address. There is no address/alias assigned from address book to drop it.')
			return
		
		 
		idb=localdb.DB(self.db)
		if len(idb.select('msgs_inout',['uid','in_sign_uid','addr_ext'],{'addr_ext':['=', "'"+uid+"'"],'type':['=',"'in'"] }))==0:
			self.warning_info('Nothing to drop!','There is no incoming messages to unassign from this thread.')
			return
			
		in_sign_upd={'in_signatures':[{'addr_from_book':''}]}
		idb.update(in_sign_upd,['addr_from_book'],{'addr_from_book':['=',  "'"+uid+"'" ] })
		
		msg_upd={'msgs_inout':[{'addr_ext':''}]}
		idb.update(msg_upd,['addr_ext'],where={'addr_ext':['=',"'"+uid+"'"],'type':['=',"'in'"]} )
				
		self.proc_inout()
		self.update_tread_frame()
		self.cur_uid=self.valid_uids[0] #self.thr_ord[0]+'_'
		self.update_msg_frame()



	def set_edit_drop_reply(self,curid):
		
		
		self.cur_addr=curid
		if 'uid_' in self.cur_addr:
			self.cur_addr=''
		
		tmpalias=self.grid_threads_msg[curid][0]['rowv'][1]['uid']
		citems=self.action_buttons.layout().count()
		# print('citems',citems)
		if citems>0:
			self.action_buttons.layout().itemAt(0).widget().setText( 'Correspondence with ['+ tmpalias +']'  )
		else:
			self.action_buttons.insertWidget(gui.Label(None,'Correspondence with ['+ tmpalias +']'))
			
			
		if citems>1:
			self.action_buttons.layout().itemAt(1).widget().updateButton( actionFun=self.edit_alias,args=(curid,),tooltip=str(tmpalias))
		else:
			self.action_buttons.insertWidget(gui.Button(None,'Edit alias',actionFun=self.edit_alias, args=(curid,),tooltip=str(tmpalias)))
		
			
		if citems>2:
			self.action_buttons.layout().itemAt(2).widget().updateButton( actionFun=self.send_reply,args=('r',), tooltip=str(tmpalias))
		else:
			self.action_buttons.insertWidget(gui.Button(None,'Reply',actionFun=self.send_reply,args=('r',), tooltip=str(tmpalias)))
		
			
		if citems>3:
			self.action_buttons.layout().itemAt(3).widget().updateButton( actionFun=self.drop_alias,args=(curid,),tooltip=str(tmpalias))
		else:
			self.action_buttons.insertWidget(gui.Button(None,'Drop alias',actionFun=self.drop_alias, args=(curid,),tooltip=str(tmpalias)))
		
		
		
		
		
		
		
	# threads : different correspondents
	def update_tread_frame(self ):
	
		while self.updating_threads:
			time.sleep(1)
	
		self.updating_threads=True
		try:
		# print(448)
		# if True:
			self.proc_inout()
			self.update_threads()
			# print(self.grid_threads)
			self.thr_table.updateTable(self.grid_threads)
			self.set_actions()
			self.updating_threads=False
			# when assigning - should refresh messages too !
		except:
			print('msg update_tread_frame')
			self.updating_threads=False
		
	
	
	
	
	# 2 types of update:
	# 1. clicking button: updating msg frame with clicked thread
	# 2. threads update: automatic every few seconds, also updating msg view with last / current msg selected 
	
	def update_msg_frame(self,*evargs):
	
		
		while self.updating_chat:
			time.sleep(1)
			
		self.updating_chat=True
		
		try:
		# if True:
			self.proc_inout()
			self.update_list()
			
			if len(self.thr_ord )>0:
				if self.cur_uid not in self.valid_uids:
					self.cur_uid = self.valid_uids[0] 
			# if hasattr(self,'cur_uid')==False:
				# if len(self.thr_ord )>0:
					# self.cur_uid=self.valid_uids[0] 
				
			if hasattr(self,'cur_uid'):
			
				if self.main_table==None:
					self.main_table=gui.Table(None,params={'dim':[len(self.grid_threads_msg[self.cur_uid]),2],'updatable':1,'toContent':1,'sortable':1,'default_sort_col':'Date time'} ) 
					self.frame2.insertWidget(self.main_table)	
					
				self.main_table.updateTable(self.grid_threads_msg[self.cur_uid],['Date time','Messages']) #+'_'
				
				self.set_edit_drop_reply(self.cur_uid)
				
			self.updating_chat=False
		except:
			print('update_msg_frame')
			self.updating_chat=False
	
	
	
	def update_msgs(self):
		self.update_tread_frame()
		# self.proc_inout()
		# self.update_threads()
		# self.thr_table.update_frame(self.grid_threads)
		self.set_actions()

		# self.update_list()
		self.update_msg_frame()
		
		# if len(self.thr_ord )>0:
			# if self.cur_uid not in self.valid_uids:
				# self.cur_uid = self.valid_uids[0] 
			
		# if hasattr(self,'cur_uid'):
			# if self.main_table==None:
				# self.main_table=flexitable.FlexiTable(self.frame1,self.grid_threads_msg[self.cur_uid], min_canvas_width=700,force_scroll=True)
			# else:
				# self.main_table.update_frame(self.grid_threads_msg[ self.cur_uid ],-1)
				
			# self.set_edit_alias_action(self.cur_uid)
			
			
			
			
	
	def update_threads(self):
	
		idb=localdb.DB(self.db)
			
		thr_filter=self.filter_table.cellWidget(0,1).currentText() #get_value('thr')
		wwhere={} #'Last 7 days','Last 30 days','All'
		if thr_filter=='Last 7 days':
			wwhere={'date_time':['>=',"'"+app_fun.today_add_days(-7)+"'"], 'in_sign_uid':['>',-2]} #
		elif thr_filter=='Last 30 days':
			wwhere={'date_time':['>=',"'"+app_fun.today_add_days(-30)+"'"], 'in_sign_uid':['>',-2]}
			
		adr_date=idb.select_max_val( 'msgs_inout',['in_sign_uid','date_time'],where=wwhere,groupby=['addr_ext'])
		if hasattr(self,"adr_date") and self.adr_date==adr_date:
			return 0
			
		self.adr_date=adr_date
		
		self.grid_threads=[]
			
		threads_aa={} 
		same_date_count={}
		unk_count=1
		
		for ad in adr_date:
		
			tmpalias=''
			tmpaddr=ad[0]
			tmpuid= str(ad[0])
			if ad[0]!=None and ad[0]!='': # all out + some in
				
				alias_from_book=idb.select('addr_book', [ 'Alias'],{'Address':['=',  "'"+ad[0]+"'" ] } ) #
				if len(alias_from_book)>0: 
					if alias_from_book[0][0]!=None and alias_from_book[0][0]!='': 
						tmpalias=alias_from_book[0][0]
					else: # or maybe empty
						tmpalias=ad[0][3:9]
						
				else:
					if 'uid' == ad[0][:3]: # if addr may be not in a book
						tmpalias=ad[0]
					else:
						tmpalias=ad[0][3:9]
					
			else: 
				if ad[1]>-1: #got signature
					tmpalias='uid_'+str(ad[1]) # ad[1]  #'uid_'+in_sign_uid
					tmpaddr='uid_'+str(ad[1])
				else:
					tmpalias='unknown_'+str(unk_count)
					tmpaddr='unknown' #+str(unk_count)
					unk_count+=1
					tmpuid=tmpalias
					
			if ad[2] not in threads_aa:
				same_date_count[ad[2]]=1
				
			else:
				same_date_count[ad[2]]=same_date_count[ad[2]]+1
				
			threads_aa[ad[2]+'__'+str(same_date_count[ad[2]])] = [tmpaddr,tmpalias,tmpuid ] 
		
		self.threads_aa=threads_aa
		self.thr_ord=sorted(threads_aa.keys(),reverse=True)
		self.valid_uids=[]
		
		for k in self.thr_ord:
			tmpdict={'rowk':k, 'rowv':[{'T':'Button', 'L':threads_aa[k][1], 'uid':threads_aa[k][2], 'tooltip':threads_aa[k][0]}]}
			
			self.grid_threads.append(tmpdict) 
			self.valid_uids.append(threads_aa[k][2]) #+'_')
		
		return 1
		
			
	

	def update_list(self ):
		idb=localdb.DB(self.db)
		msg_filter=self.filter_table.cellWidget(0,3).currentText() #get_value('msg')
		llimit=9999
		
		if msg_filter=='Last 10':
			llimit=10
		elif msg_filter=='Last 100':
			llimit=100
			
		threads_aa=self.threads_aa		
		
		for k in self.thr_ord:
			
			
			tmpuid=threads_aa[k][2]
			
			wwhere={}
			if threads_aa[k][0]=='unknown':
				wwhere={'proc_json':['=',"'True'"],'type':['=',"'in'"],'in_sign_uid':['<',0] }				

			elif 'uid_' in threads_aa[k][1]:
			
				wwhere={'proc_json':['=',"'True'"],'in_sign_uid':['=', threads_aa[k][0].replace('uid_','') ] } # ? int()
			
			else: #if threads_aa[k][1]!='unknown':
				wwhere={'proc_json':['=',"'True'"],'addr_ext':['=',"'"+threads_aa[k][0]+"'"], 'in_sign_uid':['>',-2] }
				
			tmp_msg=idb.select('msgs_inout', ['type','msg','date_time','uid','in_sign_uid' ],where=wwhere, orderby=[ {'date_time':'desc'}], limit=llimit)
			
			msg_flow=[]
			
						
			for tm in tmp_msg:
				
				sstyle1=" background-color:#fff;color:#333; padding:5px "
				sstyle2=" background-color:#fff;color:#333; min-width:768px;max-width:768px;padding:5px "
				# tmppadx=0
				writer='['+threads_aa[k][1]+']: '
				if tm[0]=='out':
					writer='[me]: '
					sstyle1=" background-color:#ddd;color:black; padding:5px "
					sstyle2="background-color:#ddd;color:black; min-width:768px;max-width:768px;padding:5px  "
					
				tmpdict={'rowk':tm[2], 'rowv':[{'T':'QLabel', 'L':tm[2] ,  'style':sstyle1,'ttype':gui.QDateTime  }, {'T':'QLabel', 'L': writer+tm[1], 'uid':str(threads_aa[k][1]),  'style':sstyle2  }] } #, 'pads':[tmppadx,0] 
				msg_flow.append(tmpdict)
				
			self.grid_threads_msg[tmpuid]=msg_flow 
			
		
	def selecting_addr_from_book_set_and_destroy(self,addr,uid,*evargs ): # here also get signature!,frame_to_destroy
		
		if addr!='':
			idb=localdb.DB(self.db)

			if 'unknown' in uid:
				uid=uid.replace('edit_unknown_','')
				msg_upd={'msgs_inout':[{'addr_ext':addr}]}

				idb.update(msg_upd,['addr_ext'],where={'uid':['=', uid ]} )
			
			elif 'uid_' in uid: # first assignments of addr 
				uid=uid.replace('uid_','')
				in_sign_upd={'in_signatures':[{'addr_from_book':addr}]}
				idb.update(in_sign_upd,['addr_from_book'],{'uid':['=',  uid ] })
				
				msg_upd={'msgs_inout':[{'addr_ext':addr}]}

				idb.update(msg_upd,['addr_ext'],where={'in_sign_uid':['=', uid ]} )
				
			elif addr!=uid:
				
				in_sign_upd={'in_signatures':[{'addr_from_book':addr}]}
				idb.update(in_sign_upd,['addr_from_book'],{'addr_from_book':['=', "'"+uid+"'"] })
				
				msg_upd={'msgs_inout':[{'addr_ext':addr}]}

				idb.update(msg_upd,['addr_ext'],where={'addr_ext':['=',"'"+uid+"'"],'type':['=',"'in'"]} )
				
			self.proc_inout()
			self.update_tread_frame()
			self.cur_uid=self.valid_uids[0] #self.thr_ord[0]+'_'
			self.update_msg_frame()
			
	def warning_info(self,title,label,*evargs):
		gui.showinfo(title,label)
		
		
		
		
		
	def edit_alias(self, btn,uid,*evargs): 
	
		tmptxt=btn.text()
		self.addr_book.get_addr_from_book(btn,btn  ) #uid[:-1]
		if tmptxt!=btn.text():
			self.selecting_addr_from_book_set_and_destroy(btn.toolTip(),uid) #+'_' 
		
		
		
		 
	def set_actions(self):	
	
		def display_thread(uid, *evargs):
			
			self.cur_uid=uid
			self.update_msg_frame( )
			
			
		for ii,rr in enumerate(self.grid_threads):
			
			r=rr['rowv']
			if 'T' in r[0]:
				if r[0]['T']=='Button':
					self.thr_table.cellWidget(ii,0).set_fun(True,display_thread,r[0]['uid'] ) 
					
						
						
						
