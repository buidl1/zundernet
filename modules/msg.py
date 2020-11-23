

import tkinter as tk
from tkinter import filedialog, StringVar, ttk, messagebox, Toplevel 
import os
import datetime
import json
import time
import modules.localdb as localdb
import modules.app_fun as app_fun
import modules.flexitable as  flexitable
import modules.aes as aes

class Msg:

	def match_sign(self,fsign): 
		if len(fsign)==0:
			return -1,''
		
		idb=localdb.DB()
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
			
			flexitable.showinfo('Bad character in memo input', 'This input contains bad character ['+badc+']:\n'+mm+'\n position: '+str(bad_ii))
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
		idb=localdb.DB()
		
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
				
			
		
	def selecting_addr_from_book_set_and_destroy_sending(self,addr,uid,frame_to_destroy,*evargs ): # here also get signature!
		
		uid.set(addr)
		
		frame_to_destroy.destroy()		
		
	
	
		
		

	# def get_last_addr_from(self):
	
		# idb=localdb.DB()
		# rr=idb.select('jsons',['json_content' ],{'json_name':['=',"'last_msg_from_addr'"]} )
		
		# if len(rr)>0:
			# disp_dict=json.loads(rr[0][0])
			# return disp_dict['addr']
		# else:
			# return localdb.get_default_addr()
			
	
	# def set_last_addr_from(self,addr): 
			
		
		# if addr=='':
			# return
			
		# idb=localdb.DB()
		# table={'jsons':[{'json_content':json.dumps({'addr':addr}), 'json_name':'last_msg_from_addr'}]}
		# idb.upsert(table,['json_content','json_name' ],{'json_name':['=',"'last_msg_from_addr'"]} )

			
			
	def send_reply(self,*args):
		global tmpaddr
		selframe = Toplevel()
		selframe.title('Write message ')
		

		msg_grid=[]
		tmpdict={'from':[{'T':'LabelC', 'L':'Select own address','width':19},{'T':'Button', 'L':'...', 'uid':'selownadr', 'width':4}, {'T':'LabelV','L':'','uid':'ownaddr','width':80}]}
		msg_grid.append(tmpdict)
		
		tmpdict={'to':[{'T':'LabelC', 'L':'Select address to','width':19},{'T':'Button', 'L':'...', 'uid':'seladr', 'width':4}, {'T':'LabelV','L':'','uid':'addr','width':80}]}
		
		tmpaddr=''
		if args[0]=='r' and hasattr(self,'cur_addr'):
			tmpaddr=self.cur_addr
			tmpdict={'to':[{'T':'LabelC', 'L':'Replying to: '+tmpaddr,'width':80}, {'T':'LabelE' }, {'T':'LabelE' }]}
			
		msg_grid.append(tmpdict)
		tmpdict={'msg':[{'T':'Text','uid':'msg', 'span':3, 'height':10, 'width':80, 'L':''} ]}
		msg_grid.append(tmpdict)
		tmpdict={'send':[{'T':'Button', 'L':'Send', 'uid':'send','width':6}, {'T':'LabelE' }, {'T':'LabelE' }] }
		msg_grid.append(tmpdict)
		
		msg_table=flexitable.FlexiTable(selframe,msg_grid)
		
		last_addr=localdb.get_last_addr_from("'last_msg_from_addr'")

		if last_addr not in ['','...']:
			msg_table.set_textvariable( 'ownaddr',last_addr)
		
		def send():
			global tmpaddr
			msg=msg_table.get_value( 'msg')
			if msg.strip()=='':
				return
			
			
			to=tmpaddr
			if tmpaddr=='':
				to=msg_table.get_value( 'addr')
				
			froma=msg_table.get_value( 'ownaddr')
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
			
			idb=localdb.DB()
			idb.insert(table,['type','wait_seconds','created_time','command' ,'json','id','status' ])
			
			# self.set_last_addr_from( froma)
			localdb.set_last_addr_from( froma,"'last_msg_from_addr'")
			selframe.destroy()
			
		msg_table.set_cmd('send',[ ], send)
		msg_table.set_cmd('selownadr',[msg_table, ['ownaddr'] ], self.addr_book.get_addr_from_wallet ) # self.selecting_addr_from_book_set_and_destroy_sending, 
		
		if tmpaddr=='':
			msg_table.set_cmd('seladr',['addr', self.selecting_addr_from_book_set_and_destroy_sending ], self.addr_book.get_addr_from_book)
		

		
	
			
		
	def __init__(self,parent_frame,notebook_parent,addr_book ): # notebook_parent : in case of new msg - adj tab title 
		self.update_in_progress=False
		self.notebook_parent=notebook_parent
		self.max_block=0
		self.proc_inout()
		
		self.addr_book=addr_book
		
		frame0=ttk.LabelFrame(parent_frame,text='Options')  
		frame0.grid(row=0,column=0, sticky="nsew")
		
		tmpdict={}
		tmpdict['filters']=[{'T':'LabelC', 'L':'Threads: '}
							, {'T':'Combox', 'uid':'thr', 'V':['Last 7 days','Last 30 days','All'] }
							, {'T':'LabelC', 'L':'Messages: '}
							, {'T':'Combox', 'uid':'msg', 'V':['Last 10','Last 100', 'All'] }
							# , {'T':'Button', 'L':'Reply', 'uid':'reply'}
							, {'T':'Button', 'L':'New message', 'uid':'newmsg', 'width':13}
							]
		grid_filter=[]
		grid_filter.append(tmpdict )
		
		self.filter_table=flexitable.FlexiTable(frame0,grid_filter) # +++ update command filter after each iteration
		
		self.filter_table.bind_combox_cmd('thr',[], self.update_tread_frame )	
		self.filter_table.bind_combox_cmd('msg',[], self.update_msg_frame )	
		# send_reply
		# self.filter_table.set_cmd('reply',['r' ], self.send_reply)
		self.filter_table.set_cmd('newmsg',['s' ], self.send_reply)
		
		self.grid_threads=[]
		self.grid_threads_msg={}
		self.thr_ord=[]
				
		frame1=ttk.LabelFrame(parent_frame,text='Threads')  
		frame1.grid(row=1,column=0, sticky="nsew")
		self.frame1=frame1
		
		tmpdict={}
		tmpdict['head']=[{'T':'LabelC', 'L':'Correspondents' } #, # alias or generic name
						#{'T':'LabelC', 'L':'Action' }  # button view
						]		
						
		self.grid_threads.append(tmpdict)
		self.update_threads()
		
		self.thr_table=flexitable.FlexiTable(frame1,self.grid_threads, min_canvas_width=200,force_scroll=True)
		self.set_actions()
		
		self.update_list()
		self.main_table=None
		if len(self.thr_ord )>0:
			
			self.cur_uid=self.valid_uids[0] 
			
			self.main_table=flexitable.FlexiTable(frame1,self.grid_threads_msg[self.cur_uid], min_canvas_width=800,force_scroll=True)
			self.set_edit_alias_action(self.cur_uid)
			
		self.updating_threads=False
		self.updating_chat=False
		
	# threads : different correspondents
	def update_tread_frame(self,*evargs):
	
		while self.updating_threads:
			time.sleep(1)
	
		self.updating_threads=True
		try:
			self.proc_inout()
			self.update_threads()
			self.thr_table.update_frame(self.grid_threads)
			self.set_actions()
			self.updating_threads=False
			# when assigning - should refresh messages too !
		except:
			self.updating_threads=False
		
	
	# 2 types of update:
	# 1. clicking button: updating msg frame with clicked thread
	# 2. threads update: automatic every few seconds, also updating msg view with last / current msg selected 
	
	def update_msg_frame(self,*evargs):
	
		
		while self.updating_chat:
			time.sleep(1)
			
		self.updating_chat=True
		
		try:
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
					self.main_table=flexitable.FlexiTable(self.frame1,self.grid_threads_msg[self.cur_uid], min_canvas_width=700,force_scroll=True)
				else:
					self.main_table.update_frame(self.grid_threads_msg[ self.cur_uid ],-1)
				
				self.set_edit_alias_action(self.cur_uid)
			self.updating_chat=False
		except:
			self.updating_chat=False
	
	
	
	def update_msgs(self):
		self.update_tread_frame()
		# self.proc_inout()
		# self.update_threads()
		# self.thr_table.update_frame(self.grid_threads)
		# self.set_actions()

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
	
		idb=localdb.DB()
			
		thr_filter=self.filter_table.get_value('thr')
		wwhere={} #'Last 7 days','Last 30 days','All'
		if thr_filter=='Last 7 days':
			wwhere={'date_time':['>=',"'"+app_fun.today_add_days(-7)+"'"], 'in_sign_uid':['>',-2]} #
		elif thr_filter=='Last 30 days':
			wwhere={'date_time':['>=',"'"+app_fun.today_add_days(-30)+"'"], 'in_sign_uid':['>',-2]}
			
		adr_date=idb.select_max_val( 'msgs_inout',['in_sign_uid','date_time'],where=wwhere,groupby=['addr_ext'])
		if hasattr(self,"adr_date") and self.adr_date==adr_date:
			return 0
			
		self.adr_date=adr_date
		
		tmplen=len(self.grid_threads)
		if tmplen>1:
			del self.grid_threads[1:tmplen]
			
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
				
			threads_aa[ad[2]+'__'+str(same_date_count[ad[2]])]=[tmpaddr,tmpalias,tmpuid ] 
		
		self.threads_aa=threads_aa
		self.thr_ord=sorted(threads_aa.keys(),reverse=True)
		self.valid_uids=[]
		
		for k in self.thr_ord:
			tmpdict={k:[{'T':'Button', 'L':threads_aa[k][1], 'uid':threads_aa[k][2], 'tooltip':threads_aa[k][0]}]}
			
			self.grid_threads.append(tmpdict) 
			self.valid_uids.append(threads_aa[k][2]+'_')
		
		return 1
		
			
	

	def update_list(self ):
		idb=localdb.DB()
		msg_filter=self.filter_table.get_value('msg')
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
			
			tmpdict={threads_aa[k][1]:[{'T':'LabelV', 'L':'Correspondence with ['+threads_aa[k][1]+']', 'uid':tmpuid ,  'width':32} #,  'width':64
									,{'T':'Button', 'L':'Edit alias', 'uid':tmpuid+'_edit',  'width':8, 'style':{'bgc':'#eee','fgc':'black','fontsize':8 }}
									,{'T':'Button', 'L':'Reply', 'uid':tmpuid+'_reply',  'width':8, 'style':{'bgc':'#fff','fgc':'green','fontsize':8 }}
									,{'T':'Button', 'L':'Drop alias', 'uid':tmpuid+'_drop',  'width':8, 'style':{'bgc':'#eee','fgc':'red','fontsize':8 }} ] }
			
			if threads_aa[k][0]=='unknown':
				tmpdict[threads_aa[k][1]][1]['uid']='edit_unknown_'+str(tmp_msg[0][3])
				
			msg_flow=[]
			msg_flow.append(tmpdict)
						
			for tm in tmp_msg:
				
				sstyle2={'bgc':'#fff','fgc':'#333' } 
				tmppadx=0
				if tm[0]=='out':
					sstyle2={'bgc':'#ddd','fgc':'black' }
					tmppadx=10
				
				tmpdict={tm[2]:[{'T':'LabelV', 'L':tm[2]+' '+ tm[1], 'uid':str(tm[3]), 'width':112,'wraplength':600,'style':sstyle2, 'span':4, 'pads':[tmppadx,0] }] } #, 'pads':[tmppadx,0] 
				msg_flow.append(tmpdict)
				
			self.grid_threads_msg[tmpuid+'_']=msg_flow
			
		
	def categories_filter(self):
		all_cat_unique=[]
		
		idb=localdb.DB()
		sel_addr_book=idb.select('addr_book',[ 'Category'] )
		
		for kk in sel_addr_book:
			if kk[0] not in all_cat_unique:
				all_cat_unique.append(kk[0])
		
		if 'All' not in all_cat_unique:
			all_cat_unique=['All']+all_cat_unique 
			
		return all_cat_unique


		
	def selecting_addr_from_book_set_and_destroy(self,addr,uid,frame_to_destroy,*evargs ): # here also get signature!
		
		uid=uid.replace('_edit','')
		if addr!='':
			idb=localdb.DB()

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
			
		frame_to_destroy.destroy()
		
		
	def warning_info(self,title,label,*evargs):
		flexitable.showinfo(title,label)
		
	def edit_alias(self,uid,*evargs):
		
		self.addr_book.get_addr_from_book( uid[:-1], self.selecting_addr_from_book_set_and_destroy  )
		
		
	def set_edit_alias_action(self,thr_uid):
	
		def drop_alias(uid,*evargs):
			
			uid=uid.replace('_drop_','')
			
			if 'uid_' in uid:
				self.warning_info('No address to drop!',uid+' is not an address. There is no address/alias assigned from address book to drop it.')
				return
			
			 
			idb=localdb.DB()
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
		
		
		jj=self.grid_threads_msg[thr_uid][0]
		 
		for k,r in jj.items():
			if 'T' in r[1]:
				if r[1]['T']=='Button':
					self.main_table.set_cmd(r[1]['uid'],[r[1]['uid']+'_'  ], self.edit_alias)
					
			if 'T' in r[2]: # '_reply'
				if r[2]['T']=='Button':
					if 'uid_' in r[2]['uid']:
						
						tmpa=r[2]['uid'].replace('_reply','')
						self.main_table.set_cmd(r[2]['uid'],['Address not recognized', tmpa+' is not a correct address. First address needs to be recognized (alias assigned from address book). Click "edit alias" to do so.' ], self.warning_info)
					else:
						self.main_table.set_cmd(r[2]['uid'],['r' ], self.send_reply)
						self.cur_addr=r[2]['uid'].replace('_reply','')
					
			if 'T' in r[3]:
				if r[3]['T']=='Button':
					
					self.main_table.set_cmd(r[3]['uid'],[r[3]['uid']+'_' ], drop_alias)
					self.cur_addr=r[3]['uid'].replace('_drop','')
		
		 
	def set_actions(self):	
	
		def display_thread(uid,*evargs):
			
			self.cur_uid=uid
			self.update_msg_frame()
			
		for ii,rr in enumerate(self.grid_threads):
			if ii==0:
				continue
				
			for k,r in rr.items():
				if 'T' in r[0]:
					if r[0]['T']=='Button':
						self.thr_table.set_cmd(r[0]['uid'],[r[0]['uid']+'_' ], display_thread)
						# self.thr_table.set_cmd(r[0]['uid'],[r[0]['uid']+'_' ], display_thread)
				
				
			
