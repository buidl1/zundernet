# todo: check tavern duplicity reason
# check why not nice channel display ? channel display in api ro msgs ?

import os
# import datetime
import json
import time
# import modules.localdb as localdb
import modules.app_fun as app_fun

import modules.aes as aes
import traceback
import modules.gui as gui
global global_db

class Msg(gui.QObject):
	refreshChannels= gui.Signal()
	refreshTxHistory= gui.Signal()
	refreshNotifications= gui.Signal()
	refreshAddrBook= gui.Signal()
	sending_signal = gui.Signal(list)
	
# checking hash for
 # ('in', '{"sign1": "\\u00066Y\\u001eN2.2\\u0012*t,M(>\\u007ftd<gU+g?h_&bv\\u000f7l", "sign1_n": 15865}', '2022-03-13 20:48:59', '{"channel_name": "ii", "channel_owner": "i", "channel_intro": "iii", "channel_type": "Forum"}', -2, 357, 'received', '3bfb4b14474387ba8af717133f953c224b9b373df86c77d6f31b9cc29f15b598', 'True', 'zs1avkprmlsaumw9kymq2fjhshv0umpqmhx6va4qrx6jz4vylje3fekhn9dcd5pghzdtdg3w60h2lx')
# ERR dupli detected - already in ! 82a35b7da594c242f3316555d52cb6e75ae87dacae61b043ecaa32f0 15865


# found match -666
# check if uid is good iwth init channel definition
	def match_sign(self,fsign,sender=''): 
	
		# print('starting match_sign',sender)
		
		if len(fsign)==0:
			# print('len(fsign)==0')
			return -1,''
		
		# idb=localdb.DB(self.db)
		cry=aes.Crypto(224)
		
		sign1=cry.utf8_1b2hash(fsign['sign1'])
		sign1_n=fsign['sign1_n']
		
		sign2,sign2_n=('none',-1)
		if 'sign2' in fsign:
			sign2=cry.utf8_1b2hash( fsign['sign2'] )
			sign2_n=fsign['sign2_n']
			
		# print('\n\nentering sign',sign1_n,sign1)
		ss=global_db.select('in_signatures', ['hex_sign','n','uid','addr_from_book'],{'n':['>', sign1_n] },orderby=[{'n':'asc'}]) #
		# print('searching sign in ',ss)
		
		n_init=sign1_n
		tmphash=''
		tmpsign1=sign1
		new_uid=-1
		addr_from_book=''
		
		for s in ss:
			
			# print('\t n_init tmpsign1',n_init,tmpsign1)
			ntimes=s[1]-n_init
			# print('\tchecking s ntimes',s,ntimes)
			if ntimes>0:
				tmphash=cry.hash(tmpsign1,ntimes)
			else:
				tmphash=tmpsign1
				
			# print('\ttmphash',tmphash)
			
			n_init=s[1] # saving to speed up some calculation and utilize already calculated hashes 
			tmpsign1=tmphash
			
			if tmphash==s[0]:
				# print('\t found ',tmphash,s[0],'uid',s[2])
				new_uid=s[2]
				
				if s[3]!=None:
					addr_from_book=s[3]
					# print('\t addr from book',addr_from_book)
					
				break
			tmphash=''
			
		tuid=global_db.select('in_signatures',['uid' ], {'hex_sign':['=',global_db.qstr(sign1)   ],'n':['=',sign1_n]}   ) #
		# print('#match_sign found addr_from_book',addr_from_book)
		
		if len(tuid)>0: # this should be new hash - should be no other before like this one - if other detected - return 
			# print('tuid',tuid)
			print('ERR dupli detected - already in !',sign1,sign1_n)
			return -666,''
		
		hex2alpha=cry.hex2alpha(sign1)
		if tmphash=='': # new sender 
			
			table={}
			table['in_signatures']=[{'hex_sign':sign1,'n':sign1_n ,'uid':'auto' }]
			insert_arr=['hex_sign','n','uid'  ]
			
			if True: #sender!='': # for channels exception: insert addr book here as incoming name 
				# print('hcannel ')
				insert_arr.append('addr_from_book')
				
				addr_from_book=sender+'-'+hex2alpha[:6] # channel sender name = sender nickname + init hash 4 chars
				# print('new sender addr_from_book',addr_from_book)
				table['in_signatures'][0]['addr_from_book']=addr_from_book
				
			global_db.insert(table,insert_arr)
			# print('#match_sign new sender addr_from_book',addr_from_book)
			tuid=global_db.select('in_signatures',['uid','addr_from_book'], {'hex_sign':['=',global_db.qstr(sign1)  ],'n':['=',sign1_n]}   ) #getting the new uid 
			new_uid=tuid[0][0]
			# print('new uid',new_uid)
			# if tuid[0][1]!=None:
				# addr_from_book=tuid[0][1]
		else: 
			
			table={}
			# table['in_signatures']=[{'hex_sign':sign1,'n':sign1_n }]
			if addr_from_book=='-'+hex2alpha[:6]: # correcting signature  
				addr_from_book=sender+'-'+hex2alpha[:6] # table['in_signatures'][0]['addr_from_book']=addr_from_book
			# print('#match_sign update addr_from_book',addr_from_book)
				
			table['in_signatures']=[{'hex_sign':sign1,'n':sign1_n, 'addr_from_book':addr_from_book }]
			global_db.update(table,['hex_sign','n','addr_from_book'   ],{'hex_sign':['=',global_db.qstr(tmphash) ],'n':['=',n_init]})
			
		# print('#match_sign in_signatures',idb.select('in_signatures',[ ]  ),'sign2_n',sign2_n)	
		
		if sign2_n>-1: # if exchanging signature to new one 
			# print('in if sign2_n>-1')
			cursign=global_db.select('in_signatures', ['uid','addr_from_book' ],{'hex_sign':['=', global_db.qstr(sign1)  ], 'n':['=', sign1_n] } ) #
			tmpaddr=cursign[0][1]
			tmpuid=cursign[0][0]
			
			table={}
			table['in_signatures']=[{'hex_sign':sign2,'n':sign2_n}]
			# print('in inserting')
			global_db.insert(table,['hex_sign','n'])
			
			table={} 
			table['in_signatures']=[{'uid':tmpuid,'addr_from_book':tmpaddr }]
			# print('updating')
			global_db.update(table,['uid','addr_from_book' ],{'hex_sign':['=',global_db.qstr(sign2)  ],'n':['=',sign2_n] })
			
			# addr_from_book=tmpaddr # not needed - already done in the loop
		# print('retugning return new_uid,addr_from_book ',new_uid,addr_from_book )
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
		tmpsignature=global_db.get_addr_to_hash(addr)
		
		if msg_parts[-1][1]+len(tmpsignature)<513:
			msg_parts[-1]=[msg_parts[-1][0]+tmpsignature , msg_parts[-1][1]+len(tmpsignature) ]
		else:
			msg_parts.append([tmpsignature,len(tmpsignature)])
			
		msg_parts=[mm[0] for mm in msg_parts]
		
		return got_bad_char, msg_parts
	
	
	
	# def check_is_channel(tmpmsg,test_json=['channel_name' , 'channel_owner', 'channel_intro','channel_type']):
		# channel_json=None
		# try:
			# channel_json=json.loads(tmpmsg)
			# cc=0
			# for tt in test_json:
				# if tt in tmpmsg:
					# cc=cc+1
					
			# return cc==len(test_json),channel_json
			
		# except:
			# return False,channel_json
	
	# main purpose - recognize sender
	# to change:
	# - every msg in defined channel is channel msg and do not display in msg table
	# test recalcing signatures 
	
	def proc_inout(self): # goal - set addr_ext and in_sign_uid for incoming msg removed ,'addr_to'
	
		debug_msg= False
	
		if self.update_in_progress:
			# print('already processing msgs - check next time')
			return
			
		self.update_in_progress=True
	
		# idb=localdb.DB(self.db)
		
		mio=global_db.select('msgs_inout',['type','addr_ext','date_time','msg', 'in_sign_uid','uid','tx_status','txid','is_channel','addr_to'],{'proc_json':['=',"'False'"]},orderby=[{'date_time':'asc'}]) #
		if debug_msg:
			print('all msgs to processing msg \n\n',mio,'\n\n')	
		
		mm_count=len(mio)
		if mm_count==0:
			self.update_in_progress=False
			return
			
			
		queue_table={}
		queue_table['queue_waiting']=[global_db.set_que_waiting(command='process msgs' )] #,jsonstr=json.dumps({'left':'0 of N'})
		queue_table['queue_waiting'][0]['status']='processing\n'+str(mm_count)+' msgs'
		queue_table['queue_waiting'][0]["type"]='auto'
		queue_id=queue_table['queue_waiting'][0]['id']
		
		global_db.insert(queue_table,['type','wait_seconds','created_time','command' ,'json','id','status' ])
		self.sending_signal.emit(['cmd_queue'])	
		# print('queue_table',queue_table)
		# time.sleep(0.3)
			
			
		refrsh_hist,refrsh_notif,refrsh_chnl =0,0,0
		
		def split_simple_signature(tmpmsg): #tmpmsg, tmp_sender
			tmp_arr=tmpmsg.split('\nFrom:')
			tmpmsg=tmp_arr[0]
			if len(tmp_arr)>2: tmpmsg='\nFrom:'.join(tmp_arr[:-1]) 
			tmp_sender=tmp_arr[-1] 
			return tmpmsg, tmp_sender
			
		for iind, mm in enumerate(mio):
			if debug_msg: print('\n\n\nmm processing:\n', mm[3][:128])
			
			if (iind+1)%max([20,int(mm_count/100) ])==0:
				working_on_tx='msgs done: '+str((iind+1))+'/' +str(mm_count) 
				# print('working_on_msg',working_on_tx)
				global_db.update( {'queue_waiting':[{'status':'processing\n'+working_on_tx }]} ,['status'],{'id':[ '=',queue_id ]})
				self.sending_signal.emit(['cmd_queue'])
				# time.sleep(0.1)
		
			mm1=mm[1]
			tmpmsg=mm[3]
			tmp_sender=''
			tmp_channel_update=False
			init_ch_id=[]
			
			# unfinished ?
			if mm[8]=='True': # if channel 
				# print('\nanalizing msg for channel',mm)
				refrsh_chnl+=1
				if ('txt' in tmpmsg or 'channel_name' in tmpmsg): # and 'CHANNEL ABUSE DETECTED SPOOFING CHANNEL INFO' not in tmpmsg:	
					try:  
						tmp_str=json.loads(tmpmsg) #'channel_name':chname,'channel_owner':creator, 'channel_intro'
							
						if 'channel_name' in tmp_str: # channel creation
							tmp_sender=tmp_str['channel_owner'] 
							tmpmsg='#Channel created#\nChannel name: '+tmp_str['channel_name']+'\nOwner: '+tmp_str['channel_owner']+'\nType: '+tmp_str['channel_type']+'\nIntro: '+tmp_str['channel_intro']
						
							# ensure there is channel to update or it is init insert?
							# and it is not related to current but historical entry!
							init_ch_id=global_db.select_min_val( 'msgs_inout','uid',where={'is_channel':['=',"'True'"] , 'addr_to': ['=',global_db.qstr(mm[9])  ],  'type': ['=',"'in'"]  } )  														
							
							if len(init_ch_id)>0 and init_ch_id[0][0]!=mm[5]:# and it is not related to current but historical entry!																								 
								tmp_channel_update=True
								tmpmsg='Channel info update\nChannel name: '+tmp_str['channel_name']+'\nOwner: '+tmp_str['channel_owner']+'\nType: '+tmp_str['channel_type']+'\nIntro: '+tmp_str['channel_intro']
							
							if debug_msg: print('channel_name',tmp_str)
						elif 'txt' in tmp_str:				
						
							if debug_msg: print('txt',tmp_str)
							tmpmsg=tmp_str['txt']
							
							# sender recognition needed ?
							if 'sender' in tmp_str:
								tmp_sender=tmp_str['sender'].strip()
								
							if tmp_sender=='':
								tmp_sender='@'
								
								
					except: # OR print channel init  
						tmpmsg='BAD MSG FORMAT, SEE TERMINAL '
						tmp_sender='Unknown' 
						if debug_msg: print('\n\n\nBAD MSG FORMAT '+mm[3])
						traceback.print_exc()
				else:
					print('msg::not proper channel json - simple text msg',tmpmsg)
			############## unfinished ?
			else:
				if debug_msg: print('NOT CHANNEL ' )
				# print('check if msg is reg msg to channel to not write into regular msgs ?')
				test_addr=global_db.select('channels',['address'], {'address':['=',"'"+mm[9]+"'"]}  ) #
				
				if len(test_addr)>0:
					if test_addr[0][0]==mm[9]:
						if debug_msg: print('*\n correcting channel type optional ') 
						mm[8]='True'
						refrsh_chnl+=1
				else:
					if debug_msg: print('\n\nsplit_simple_signature') 
					tmpmsg, tmp_sender=split_simple_signature(tmpmsg) #tmpmsg, tmp_sender
					
				# print('\n\nREG MSG',tmpmsg)
				# print('SENDER',tmp_sender)
				 
			# confusing out and in msgs ... ?
			if mm[0]=='out': 
				if debug_msg: print('outgoing msg\n',mm) 
				table={'msgs_inout':[{'proc_json':'True','msg': tmpmsg}]} 
				global_db.update(table,['proc_json','msg' ],{'uid':['=',mm[5]]})
				
			elif mm[0]=='in' :
				if debug_msg:  print('incoming msg\n',mm)
				
				fsign=json.loads(mm1 )
				
				# if channel update: tmp_sender must match!
				# must recognized the signature comes from the same as orig msg signature owner!
				
				if debug_msg:  print('\nchecking hash for ',tmp_sender)
				uid,addr_from_book=self.match_sign( fsign, tmp_sender ) #mio
				if debug_msg:  print('\n found match',uid,addr_from_book)
				
				if tmp_channel_update:
					if debug_msg:   print('tmp_channel_update',mm[9])
					# print('all\n',idb.select('msgs_inout',[ 'uid','in_sign_uid','msg' ],where={'is_channel':['=',"'True'"] , 'addr_to': ['=',"'"+mm[9]+"'"],  'type': ['=',"'in'"]   } ))
					# why spoofing when first time ?
					
					# init_ch_id=idb.select_min_val( 'msgs_inout','uid',where={'is_channel':['=',"'True'"] , 'addr_to': ['=',"'"+mm[9]+"'"],  'type': ['=',"'in'"]  } ) # find first id for the channel
					
					if True: #tmp_channel_update: #len(init_ch_id)>0:
						in_sign_uid=global_db.select('msgs_inout',[ 'in_sign_uid' ],{'uid':['=',init_ch_id[0][0] ]} ) #
						
						# BUG? when channel recognized first time uid =-2 before updated ... 
						# additional condition? first msg in channel ?
						# print(in_sign_uid,uid)
						if len(in_sign_uid)>0 and in_sign_uid[0][0]==uid:
							tmp_str['channel_name']=tmp_str['channel_name']+'-'+mm[9][3:6]
							table={'channels':[{ 'creator':tmp_str['channel_owner'], 'channel_name':tmp_str['channel_name'], 'channel_intro':tmp_str['channel_intro'] , 'channel_type':tmp_str['channel_type']  }]}	
							# print('updating channel  ',table) 
							global_db.update(table,[ 'creator','channel_name','channel_intro' , 'channel_type' ],{'address':['=',"'"+mm[9]+"'"]})  
							# print('updated?',idb.select('channels',[  ], {'address':['=',"'"+mm[9]+"'"]} ) )
							
							table={}
							table['addr_book']=[{'Category':'Channel: '+tmp_str['channel_type'],'Alias': tmp_str['channel_name'] }]  
							# print(' addr book',table) 
							global_db.update(table,[ 'Category','Alias'  ],{'Address':['=',"'"+mm[9]+"'"]})
							
							# refresh   addr book view
							self.refreshAddrBook.emit()	
							# print('channel updated?')
						else:
							tmpmsg='CHANNEL SPOOFING DETECTED 1 '+tmpmsg
							print(init_ch_id,uid,in_sign_uid)
					# else:
						# tmpmsg='CHANNEL SPOOFING DETECTED 2 '+tmpmsg
							
					# select 'in_sign_uid' from 'msgs_inout' where 'proc_json':'True'  'in_sign_uid':uid ,'is_channel':mm[8] and 'msg': like ... and ,'addr_to': mm[9]
					# table={'msgs_inout':[{'type':tmptype,'proc_json':'True', 'in_sign_uid':uid, 'addr_ext':addr_ext,'msg':tmpmsg,'is_channel':mm[8]}]}
				
				# TODO FOR CHANNLE:
				# if externa l channel detected link with addr book zaddr
				# ELSE ?? channel message first time - new sender otherwise detect uid 
				
				addr_ext=''
				if uid>-1:
					tmpalias='uid_'+str(uid)
					if debug_msg:   print('tmpalias',tmpalias)
					if mm[8]=='True': # if channel 	
						if debug_msg:   print("mm[8]=='True'")
						tmpalias=addr_from_book
						# tmpmsg=tmpmsg #json.dumps({'sender':addr_from_book, 'txt':tmpmsg}) #addr_from_book+':\n'+tmpmsg
						addr_ext=addr_from_book
						# tmpalias=addr_from_book
					
					elif addr_from_book!='':
						if debug_msg:   print("addr_from_book!=''")
						addr_ext=addr_from_book
						
						tmpalias=global_db.select('addr_book',['Alias'] , {'Address':['=',"'"+addr_from_book+"'"] } )
						
						if tmp_sender!='': 
							tmpalias=tmp_sender
						elif len(tmpalias)<1:
							tmpalias=addr_from_book
						else:
							# print(tmpalias)
							tmpalias=tmpalias[0][0]
					else:
						if debug_msg:   print("addr_ext=tmpalias")
						addr_ext=tmpalias
						if tmp_sender!='': tmpalias=tmp_sender
							
					if debug_msg:   print("tmpalias",tmpalias)
					table_h={}
					uidtmp=tmpalias+';uid='+str(uid)+': '
					table_h['tx_history']=[{'from_str':uidtmp+mm[3]}]
					# one more condition - addr to/from ... 
					# if addr t ois self do not change
					# print('update(table_h')
					global_db.update(table_h,['from_str' ], {'txid':['=',"'"+mm[7]+"'"],'Type':[' not in ',"('in/change','out')"]} )
					refrsh_hist+=1
					# print('update history ok')
					
					
					# print("select('notifications'")
					orig_json=global_db.select('notifications',['orig_json'],{'details':['=',"'"+mm[7]+"'"]})
					# print(orig_json)
					if len(orig_json)>0:
						table_n={}
						uidtmp='From '+tmpalias+';uid='+str(uid)+': '+orig_json[0][0]
						table_n['notifications']=[{'orig_json':uidtmp }]
						# print("update(table_n")
						global_db.update(table_n,['orig_json' ],{'details':['=',"'"+mm[7]+"'"]})
						refrsh_notif+=1
					
					if tmpmsg=='' :
						if len(orig_json)>0: 
							tmpmsg='Received '+orig_json[0][0]
						else : 
							tmp_amount=global_db.select('tx_history',['amount' ],{'txid':['=',"'"+mm[7]+"'"], 'Type':[' like ',"'in%'"] } ) 
							if len(tmp_amount)>0:
								tmpmsg='Received '+str(tmp_amount[0][0])
						
				# 'type',
				tmptype=mm[0]
				if 'PaymentRequest' in mm[3]:
					tmptype='PaymentRequest'
					
					tmpmsg=tmpmsg.split('PaymentRequest;')
					tmpmsg=tmpmsg[-1]
					tmpmsg='Payment request '+app_fun.json_to_str(json.loads(tmpmsg),tt='')		
			
					
				table={'msgs_inout':[{'type':tmptype,'proc_json':'True', 'in_sign_uid':uid, 'addr_ext':addr_ext,'msg':tmpmsg,'is_channel':mm[8]}]} #,'is_channel':"False"
				
				# print('final msg update\n\t',uid,addr_ext,'\n\t',tmpmsg)
				# if is_channel:
					# table['msgs_inout'][0]['is_channel']='True'
				
				# correcting channel type optional
				if debug_msg:    print("\n\nupdating processed mm\n",table)
				global_db.update(table,['type','proc_json', 'in_sign_uid','addr_ext','msg','is_channel' ],{'uid':['=',mm[5]]})
			# self.refresh_msgs_signal.emit()	
		if refrsh_chnl>0:
			self.refreshChannels.emit()	
		if refrsh_hist>0: 
			self.refreshTxHistory.emit()	
		if refrsh_notif>0: 
			self.refreshNotifications.emit()	
			
		global_db.update( {'queue_waiting':[{'status':'processing\nmsgs done'}]} ,['status'],{'id':[ '=',queue_id ]})
		self.sending_signal.emit(['cmd_queue'])
		
		self.update_in_progress=False
		
			
			
	def send_reply(self,btn,*args):
		

		msg_grid=[]
		tmpdict={'rowk':'from', 'rowv':[{'T':'LabelC', 'L':'Select own address','width':19},{'T':'Button', 'L':'...', 'uid':'selownadr', 'width':4}]}
		msg_grid.append(tmpdict) #, {'T':'LabelV','L':'','uid':'ownaddr','width':80}
		
		tmpdict={'rowk':'to', 'rowv':[{'T':'LabelC', 'L':'Select address to','width':19},{'T':'Button', 'L':'...', 'uid':'seladr', 'width':4}]} #, {'T':'LabelV','L':'','uid':'addr','width':80}
		
		# tmpaddr=''
		# print(self.cur_addr)
		if args[0]=='r': # and hasattr(self,'cur_addr'):
			if self.cur_addr!='':
				# tmpaddr=self.cur_addr
				tmpdict={'rowk':'to', 'rowv':[{'T':'LabelC', 'L':'Replying to: '+self.cur_addr,'width':80}  ]}
			
		msg_grid.append(tmpdict)
		tmpdict={'rowk':'msg', 'rowv':[{'T':'TextEdit','uid':'msg','span':2, 'style':'background-color:white;'} ]}
		msg_grid.append(tmpdict)
		
		
		
		
		
		# check signature exist for the addr - if not create
		mysignature=''
		# idb=localdb.DB(self.db)
		 
		# db_sign=idb.select( 'channel_signatures', [ 'signature' ], {'addr':['=',  "'"+tmpaddr+"'" ] } )
		db_sign=global_db.select_last_val('channel_signatures','signature')
		if db_sign==None:
			# db_sign
			tmp=global_db.select_max_val( 'channel_signatures','signature')
			if len(tmp)>0:
				if tmp[0][0]!=None:
					db_sign=tmp[0][0]
					
		# print('db_sign',db_sign)
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
		 
		
		
		# tmpdict={'rowk':'send', 'rowv':[{'T':'Button', 'L':'Send', 'uid':'send','width':6}  ] }
		# msg_grid.append(tmpdict)
		
		# msg_table=flexitable.FlexiTable(selframe,msg_grid)
		msg_table=gui.Table(None,{'dim':[len(msg_grid),3], 'toContent':1})
		msg_table.updateTable(msg_grid)
		
		last_addr=global_db.get_last_addr_from("'last_msg_from_addr'")

		if last_addr not in ['','...']:
			msg_table.cellWidget(0,1).setToolTip(last_addr) #.set_textvariable( 'ownaddr',last_addr)
			msg_table.cellWidget(0,1).setText( self.addr_book.cat_alias( last_addr,own=True) )
		
		def send():
			# global tmpaddr
			msg=msg_table.cellWidget(2,0).toPlainText()  #get_value( 'msg')
			if msg.strip()=='':
				return
			
			
			to= self.cur_addr
			if to=='':
				to=msg_table.cellWidget(1,1).toolTip() #.get_value( 'addr')
			 
				
			froma=msg_table.cellWidget(0,1).toolTip() #.get_value( 'ownaddr')
			if froma=='':
				return
			
			# idb=localdb.DB(self.db)
			
			tmpsender=''
			if msg_table.cellWidget(3,1)!=None: 
				tmpsender=msg_table.cellWidget(3,1).text() 
			elif msg_table.item(3,1)!=None:
				tmpsender=msg_table.item(3,1).text() 
			
			table={'channel_signatures':[{ 'signature':tmpsender}]} 
			global_db.upsert( table, [ 'signature' ] )
			msg+='\nFrom:'+tmpsender
			
			got_bad_char, msg_arr=self.prep_msg(msg,to)
			
			if got_bad_char:
				return
			
			ddict={'fromaddr':froma,	'to':[]	} #
			for mm in msg_arr:
				ddict['to'].append({'z':to,'a':0.0001,'m':mm})
				
			table={}
			table['queue_waiting']=[global_db.set_que_waiting('send',jsonstr=json.dumps(ddict) ) ]
			table['queue_waiting'][0]['type']='message'
			global_db.insert(table,['type','wait_seconds','created_time','command' ,'json','id','status' ])
			
			
			
			# self.set_last_addr_from( froma)
			global_db.set_last_addr_from( froma,"'last_msg_from_addr'")
			msg_table.parent().close()
			
		msg_table.cellWidget(3,2).set_fun(True,send) #set_cmd('send',[ ], send)
		msg_table.cellWidget(0,1).set_fun(False,self.addr_book.get_addr_from_wallet ) 
		
		if self.cur_addr=='':
			msg_table.cellWidget(1,1).set_fun(False,self.addr_book.get_addr_from_book, msg_table.cellWidget(1,1)) 
		
		gui.CustomDialog(btn,[msg_table ], title='Write message ')
		
	
			
	# TODO: test live new sorting and msgs_inout
	
	def __init__(self,addr_book ): # notebook_parent : in case of new msg - adj tab title 
		super(Msg, self).__init__()
		self.update_in_progress=False
		self.db=addr_book.db
		self.cur_addr=''
		self.max_block=0
		# self.proc_inout()
		
		self.addr_book=addr_book
		
		self.parent_frame=gui.ContainerWidget(None,layout=gui.QVBoxLayout() )
		
		frame0=gui.FramedWidgets(None,'Filter')  
		# frame0.setMaximumHeight(128)
		self.parent_frame.insertWidget(frame0) #ttk.LabelFrame(parent_frame,text='Options')  
		
		tmpdict={}
		tmpdict['rowk']='filters'
		tmpdict['rowv']=[ {'T':'LabelC', 'L':'Threads: '}
							, {'T':'Combox', 'uid':'thr', 'V':['Last 10','Last 100', 'All'] } #['Last 7 days','Last 30 days','All']
							, {'T':'LabelC', 'L':'Messages: '}
							, {'T':'Combox', 'uid':'msg', 'V':['Last 10','Last 100', 'All'] }
							# , {'T':'Button', 'L':'Reply', 'uid':'reply'}
							, {'T':'Button', 'L':'New message', 'uid':'newmsg', 'width':13}
						]
		grid_filter=[]
		grid_filter.append(tmpdict )
		
		self.filter_table=gui.Table(None,params={'dim':[1,5],'updatable':1, 'toContent':1} )  #, 'toContent':1
		self.filter_table.updateTable(grid_filter)
		frame0.insertWidget(self.filter_table)
		frame0.setMaximumHeight(self.filter_table.height())
		
		self.filter_table.cellWidget(0,1).set_fun( self.update_tread_frame) #bind_combox_cmd('thr',[], self.update_tread_frame )	
		self.filter_table.cellWidget(0,3).set_fun( self.update_msg_frame) #.bind_combox_cmd('msg',[], self.update_msg_frame )	
		self.filter_table.cellWidget(0,4).set_fun(False,self.send_reply,'s') #.set_cmd('newmsg',['s' ], self.send_reply)
		
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
		self.thr_table=gui.Table(None,params={'dim':[len(self.grid_threads),2],'updatable':1,'default_sort_col': 'sorting_datetime','hideColumns':['sorting_datetime' ],'hideColNames':1} )  #['sorting_datetime']
		 
		# self.thr_table.updateTable(self.grid_threads,['buttons','sorting_datetime'])
		self.frame1.insertWidget(self.thr_table)
		# self.set_actions()
		
		self.frame2= gui.FramedWidgets(None,'Selected thread',layout=gui.QVBoxLayout())
		self.action_buttons=gui.ContainerWidget(None,layout=gui.QHBoxLayout() )
		self.frame2.insertWidget(self.action_buttons)	
		self.maxMsgColWidth=self.action_buttons.width()
		
		# self.update_list()
		
		
		self.msg_thrd_frame.insertWidget(self.frame2)	
		
		
		
		self.main_table=None
		self.main_table_params={ 'updatable':1,'sortable':1,'default_sort_col':'Date time' ,'rowSizeMod':1} 
		self.cur_uid=-1
		# if len(self.thr_ord )>0:
			
			# self.cur_uid=self.valid_uids[0] 
			# self.main_table_params['dim']=[len(self.grid_threads_msg[self.cur_uid]),2] # print('init b4 change self.maxMsgColWidth',self.maxMsgColWidth)
			# if self.maxMsgColWidth<=640: self.maxMsgColWidth=self.action_buttons.width() 	# print('init after change self.maxMsgColWidth',self.maxMsgColWidth)
			
			# self.main_table_params['colSizeMod']=[80,self.maxMsgColWidth-100]
			
			# self.main_table=gui.Table(None,params=self.main_table_params) #{'dim':[len(self.grid_threads_msg[self.cur_uid]),2],'updatable':1,'toContent':1,'sortable':1,'default_sort_col':'Date time'} ) 
			# self.main_table.updateTable(self.grid_threads_msg[self.cur_uid],['Date time','Messages']) #+'_'
			# self.set_edit_drop_reply(self.cur_uid)
			
			# self.frame2.insertWidget(self.main_table)	
			# self.main_table.setMinimumWidth(self.maxMsgColWidth)
			
		self.updating_threads=False
		self.updating_chat=False
		
		
	

	def drop_alias(self,btn,uid ):

		if 'uid_' in uid:
			self.warning_info('No address to drop!',uid+' is not an address. There is no address/alias assigned from address book to drop it.')
			return
		
		 
		# idb=localdb.DB(self.db)
		if len(global_db.select('msgs_inout',['uid','in_sign_uid','addr_ext'],{'addr_ext':['=', "'"+uid+"'"],'type':['=',"'in'"] }))==0:
			self.warning_info('Nothing to drop!','There is no incoming messages to unassign from this thread.')
			return
			
		in_sign_upd={'in_signatures':[{'addr_from_book':''}]}
		global_db.update(in_sign_upd,['addr_from_book'],{'addr_from_book':['=',  "'"+uid+"'" ] })
		
		msg_upd={'msgs_inout':[{'addr_ext':''}]}
		global_db.update(msg_upd,['addr_ext'],where={'addr_ext':['=',"'"+uid+"'"],'type':['=',"'in'"]} )
				
		self.proc_inout()
		self.update_tread_frame()
		self.cur_uid=self.valid_uids[0] #self.thr_ord[0]+'_'
		self.update_msg_frame()



	def set_edit_drop_reply(self,curid):
		
		
		self.cur_addr=curid
		if 'uid_' in self.cur_addr:
			self.cur_addr=''
		
		# print(curid,self.grid_threads_msg)
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
		
		
		self.frame2.setTitle('Selected thread '+tmpalias) #['name']
		
		
		
		
		
	# threads : different correspondents
	def update_tread_frame(self,*args ):
	
		while self.updating_threads:
			time.sleep(1)
	
		self.updating_threads=True
		try:
		# print(448)
		# if True:
			self.proc_inout()
			self.update_threads()
			# print(self.grid_threads)
			tmpcolumns=[]
			if not hasattr(self.thr_table,'col_names'):
				tmpcolumns=['buttons','sorting_datetime']
				
			self.thr_table.updateTable(self.grid_threads, tmpcolumns, doprint=False)
			# self.set_actions()
			self.updating_threads=False
			# when assigning - should refresh messages too !
		except:
			# print('msg update_tread_frame')
			self.updating_threads=False
		
	
	
	
	
	# 2 types of update:
	# 1. clicking button: updating msg frame with clicked thread
	# 2. threads update: automatic every few seconds, also updating msg view with last / current msg selected 
	
	def update_msg_frame(self,*evargs):
	
		# print('update msg chat')
		while self.updating_chat:
			time.sleep(1)
			
		self.updating_chat=True
		
		if len(evargs)>0:
			# print('updating cur uid',evargs[-1])
			self.cur_uid=evargs[-1]
		
		try:
		# if True:
			self.proc_inout()
			
			
			if len(self.thr_ord )>0:
				if self.cur_uid not in self.valid_uids:
					self.cur_uid = self.valid_uids[0] 
			# if hasattr(self,'cur_uid')==False:
				# if len(self.thr_ord )>0:
					# self.cur_uid=self.valid_uids[0] 
				
			# if hasattr(self,'cur_uid'): # and self.cur_uid>-1:
				# print('has attr cur id',self.cur_uid)
				# self.set_edit_drop_reply(self.cur_uid)
				# print('b4 change self.maxMsgColWidth',self.maxMsgColWidth)
				if self.maxMsgColWidth<=640: self.maxMsgColWidth=self.action_buttons.width()
				# print('after change self.maxMsgColWidth',self.maxMsgColWidth)
				self.update_list()
				tmpcolnames=[]
				if self.main_table==None:
				
					# self.maxMsgColWidth=self.action_buttons.width()
					self.main_table_params['colSizeMod']=[80,self.maxMsgColWidth-100]
					self.main_table_params['dim']=[len(self.grid_threads_msg[self.cur_uid]),2]
					self.main_table=gui.Table(None,params=self.main_table_params ) 
					self.main_table.setMinimumWidth(self.maxMsgColWidth) # increasing this does not help 
					# self.main_table=gui.Table(None,params={'dim':[len(self.grid_threads_msg[self.cur_uid]),2],'updatable':1,'toContent':1,'sortable':1,'default_sort_col':'Date time'} ) 
					self.frame2.insertWidget(self.main_table)	
					tmpcolnames=['Date time','Messages']
				else:
					for ii,mm in enumerate([80,self.maxMsgColWidth-100]):
						self.main_table.setColumnWidth(ii,mm)
					
				# print('update msg chat with cur id ',self.cur_uid,self.grid_threads_msg[self.cur_uid])
				self.main_table.updateTable(self.grid_threads_msg[self.cur_uid],tmpcolnames) #+'_'
				
				self.set_edit_drop_reply(self.cur_uid)
				
			self.updating_chat=False
		except:
			print('update_msg_frame exception')
			traceback.print_exc()
			self.updating_chat=False
	
	
	@gui.Slot()	
	def update_msgs(self):
		self.update_tread_frame() # grid ready 
		 
		self.update_msg_frame() 
			
		

	def update_threads(self):
		# print('\n\n\n\n update_threads msg')
		
		
		# idb=localdb.DB(self.db)
		
		
		# mio=idb.select('msgs_inout',['type','addr_ext','date_time','msg', 'in_sign_uid','uid','tx_status','txid','is_channel'],{'date_time':['>=',"'"+app_fun.today_add_days(-30)+"'"],'proc_json':['=',"'True'"]},orderby=[{'date_time':'asc'}]) #
		# print('processing msg ',mio)	
			
		thr_filter=self.filter_table.cellWidget(0,1).currentText() #get_value('thr')
		wwhere={'in_sign_uid':['>',-2],'is_channel':[['=',"'False'"],[' is ',"null"]]} #'Last 7 days','Last 30 days','All'
		llimit=0
		if thr_filter=='Last 10': 
			llimit=10
		elif thr_filter=='Last 100': 
			llimit=100
		# if thr_filter=='Last 7 days':
			# wwhere={'date_time':['>=',"'"+app_fun.today_add_days(-7)+"'"], 'in_sign_uid':['>',-2],'is_channel':[['=',"'False'"],[' is ',"null"]]} #
		# elif thr_filter=='Last 30 days':
			# wwhere={'date_time':['>=',"'"+app_fun.today_add_days(-30)+"'"], 'in_sign_uid':['>',-2],'is_channel':[['=',"'False'"],[' is ',"null"]]}
			
		# aliases known:
		# can send to using addr book / defined situation or tx to any / undefined ...
		
		# when sending to - show under alias from send to addr, show "me" msgs 
		# when receiving - show under alias from my addr
		# should be:
		# when addr from book - show both in out msgs under alias from book / merged ?
		#
		# when no addr in book connected:
		# show outgoing under  from addr i sent to ?
		# when receiving from unknown? should stay unknown until connected ?
		# in this approach  is ok - sending to , it's me so it is outgoing!
			
		adr_date=global_db.select_max_val( 'msgs_inout',['in_sign_uid','date_time' ],where=wwhere,groupby=['addr_ext'],_limit=llimit, _ord_by=[1])
		if hasattr(self,"adr_date") and self.adr_date==adr_date:
			return 0
			
		# print(adr_date) # hcannel address will be here ! why external address is known ??
			
		self.adr_date=adr_date
		
		self.grid_threads=[]
			
		threads_aa={} 
		same_date_count={}
		unk_count=1
		
		for ad in adr_date:
			# print('ad',ad)
			tmpalias=''
			tmpaddr=ad[0]
			tmpuid= str(ad[0])
			if ad[0]!=None and ad[0]!='': # all out + some in
				# print('ad note empty',ad[0])
				alias_from_book=global_db.select('addr_book', [ 'Alias'],{'Address':['=',  "'"+ad[0]+"'" ] } ) #
				# print('alias_from_book',alias_from_book)
				if len(alias_from_book)>0: 
					if alias_from_book[0][0]!=None and alias_from_book[0][0]!='': 
						# print('alias_from_book',alias_from_book[0][0])
						tmpalias=alias_from_book[0][0]
					else: # or maybe empty
						tmpalias=ad[0][3:9]
						# print('ad[0][3:9]',ad[0][3:9])
						
				else:
					# print('preping tmpalias') 
					if 'uid' == ad[0][:3]: # if addr may be not in a book
						tmpalias=ad[0]
						# print('ad[0]',ad[0] )# here uid1
					else:
						tmpalias=ad[0][3:9]
						# print('2 ad[0][3:9]',ad[0][3:9])  
					# print('preping tmpalias',tmpalias)
					
			else: 
				# print(' thrd else',ad[0][3:9])
				if ad[1]>-1: #got signature
					tmpalias='uid_'+str(ad[1]) # ad[1]  #'uid_'+in_sign_uid
					tmpaddr='uid_'+str(ad[1])
					# print('ad[1]>-1',ad[1])
				else:
					tmpalias='unknown_'+str(unk_count)
					tmpaddr='unknown' #+str(unk_count)
					unk_count+=1
					tmpuid=tmpalias
					
			if ad[2] not in threads_aa:
				same_date_count[ad[2]]=1
				
			else:
				same_date_count[ad[2]]=same_date_count[ad[2]]+1
				
			# threads_aa[ad[2] ] = [tmpaddr,tmpalias,tmpuid ] 
			threads_aa[ad[2]+'__'+str(same_date_count[ad[2]])] = [tmpaddr,tmpalias,tmpuid ] 
		
		self.threads_aa=threads_aa
		self.thr_ord=sorted(threads_aa.keys(),reverse=True)
		self.valid_uids=[]
		
		for k in self.thr_ord:
			tmpdict={'rowk':threads_aa[k][1], 'rowv':[ {'T':'Button', 'L':threads_aa[k][1], 'uid':threads_aa[k][2], 'tooltip':threads_aa[k][0] , 'fun':self.update_msg_frame, 'args':(threads_aa[k][2],)} 
										, {'T':'LabelV', 'L':k  } #'sorting_by_datetime' , 'ttype':gui.QDateTime
										] }
			# self.thr_table.cellWidget(ii,0).set_fun(True,display_thread,r[0]['uid'] )  # self.update_msg_frame(uid )
			# {'T':'Button', 'L':tmpcurcat,  'tooltip':'Edit category for address '+tmpaddr, 'fun':self.edit_category, 'args':(tmpalias,tmpaddr) }, 
			self.grid_threads.append(tmpdict) 
			self.valid_uids.append(threads_aa[k][2]) #+'_')
			
		# print('updating threads',self.grid_threads)
		# print('self.valid_uids',self.valid_uids)
		
		return 1
		
			
	

	def update_list(self ):
		# idb=localdb.DB(self.db)
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
				# wwhere={'proc_json':['=',"'True'"],'type':[' like ',"'in%'"],'in_sign_uid':['<',0],'is_channel':[['=',"'False'"],[' is ',"null"]] }		
				wwhere={'proc_json':['=',"'True'"],'type':['=',"'in'"],'in_sign_uid':['<',0],'is_channel':[['=',"'False'"],[' is ',"null"]] }			

			elif 'uid_' in threads_aa[k][1]:
			
				wwhere={'proc_json':['=',"'True'"],'in_sign_uid':['=', threads_aa[k][0].replace('uid_','') ],'is_channel':[['=',"'False'"],[' is ',"null"]] } # ? int()
			
			else: #if threads_aa[k][1]!='unknown':
				wwhere={'proc_json':['=',"'True'"],'addr_ext':['=',"'"+threads_aa[k][0]+"'"], 'in_sign_uid':['>',-2],'is_channel':[['=',"'False'"],[' is ',"null"]] }
				
			# print('wwhere',wwhere)
			tmp_msg=global_db.select('msgs_inout', ['type','msg','date_time','uid','in_sign_uid','is_channel' ],where=wwhere, orderby=[ {'date_time':'desc'}], limit=llimit)
			# print('tmp_msg',tmp_msg)
			msg_flow=[]
			
						
			for tm in tmp_msg:
				
				# sstyle1=" background-color:#fff;color:#333; padding:5px "
				# sstyle2=" background-color:#fff;color:#333; min-width:768px;max-width:768px;padding:5px "
				sstyle1=" color:green; padding:2px; min-height:40px;"
				sstyle2=" color:green; min-width:668px;max-width:768px;padding:2px "
				# tmppadx=0
				writer='['+threads_aa[k][1]+']: '
				if tm[0]=='out':
					writer='[me]: '
					# sstyle1=" background-color:#ddd;color:black; padding:5px "
					# sstyle2="background-color:#ddd;color:black; min-width:768px;max-width:768px;padding:5px  "
					sstyle1=" color:blue; padding:2px ; min-height:40px;"
					sstyle2=" color:blue; min-width:668px;max-width:768px;padding:2px  "
					
					
				# tmpdict={'rowk':tm[2], 'rowv':[{'T':'QLabel', 'L':tm[2] ,  'style':sstyle1,'ttype':gui.QDateTime  }, {'T':'TextEdit', 'L': writer+tm[1], 'uid':str(threads_aa[k][1]),  'style':sstyle2, 'readonly':1,'width': (self.maxMsgColWidth-100)  }] } #, 'pads':[tmppadx,0] 
				tmpdict={'rowk':tm[2], 'rowv':[{'T':'QLabel', 'L':tm[2] ,  'style':sstyle1,'ttype':gui.QDateTime , 'align':['AlignTop'] }, {'T':'LabelV', 'L': writer+tm[1], 'uid':str(threads_aa[k][1]) ,  'style':sstyle2  }] } #, 'pads':[tmppadx,0] 
				
				msg_flow.append(tmpdict)
				
			self.grid_threads_msg[tmpuid]=msg_flow 
			
		
	def selecting_addr_from_book_set_and_destroy(self,addr,uid,*evargs ): # here also get signature!,frame_to_destroy
		
		if addr!='':
			# idb=localdb.DB(self.db)

			if 'unknown' in uid:
				uid=uid.replace('edit_unknown_','')
				msg_upd={'msgs_inout':[{'addr_ext':addr}]}

				global_db.update(msg_upd,['addr_ext'],where={'uid':['=', uid ]} )
			
			elif 'uid_' in uid: # first assignments of addr 
				uid=uid.replace('uid_','')
				in_sign_upd={'in_signatures':[{'addr_from_book':addr}]}
				global_db.update(in_sign_upd,['addr_from_book'],{'uid':['=',  uid ] })
				
				msg_upd={'msgs_inout':[{'addr_ext':addr}]}

				global_db.update(msg_upd,['addr_ext'],where={'in_sign_uid':['=', uid ]} )
				
			elif addr!=uid:
				
				in_sign_upd={'in_signatures':[{'addr_from_book':addr}]}
				global_db.update(in_sign_upd,['addr_from_book'],{'addr_from_book':['=', "'"+uid+"'"] })
				
				msg_upd={'msgs_inout':[{'addr_ext':addr}]}

				global_db.update(msg_upd,['addr_ext'],where={'addr_ext':['=',"'"+uid+"'"],'type':['=',"'in'"]} )
				
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
		


	# def set_actions(self):	
	
		# def display_thread(uid, *evargs): # bad uid for new entry 
			# print('clicked uid',uid)
			# self.cur_uid=uid
			# self.update_msg_frame( )
			
			
		# for ii,rr in enumerate(self.grid_threads):
			
			# r=rr['rowv']
			# if 'T' in r[0]:
				# if r[0]['T']=='Button':
					# print('thr assing button action',ii,r[0]['uid'],self.thr_table.cellWidget(ii,0).text())
					# self.thr_table.cellWidget(ii,0).set_fun(True,display_thread,r[0]['uid'] )  # self.update_msg_frame(uid )
					
						
						
						
