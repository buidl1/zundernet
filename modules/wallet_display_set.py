# -- todo: add default from addr for msg
# -- detect wrong path for deamon

import tkinter as tk
from tkinter import filedialog, StringVar, ttk, messagebox, Toplevel 
import os, sys
import datetime
import json
import time
import modules.localdb as localdb
import modules.app_fun as app_fun
import operator
import modules.flexitable as flexitable
import threading
import modules.aes as aes
import shutil
from functools import partial

WAIT_S=900

class WalDispSet:

	def __init__(self,password='',queue_com=None ):
		self.password=password
		self.amount_per_address={}
		self.while_updating=False
		self.queue_com=queue_com
		
		
	def display_bills(self,id,msgstr,done):
		
		listoftxids=done[0]
		grid_settings=[]
		tmpdict={}
		tmpdict['head']=[{'T':'LabelC', 'L':'Txid' },{'T':'LabelC', 'L':'Amount' }, {'T':'LabelC', 'L':'Confirm.' } ] 
		grid_settings.append(tmpdict)
		
		for ll in listoftxids:
			ll=json.loads(ll)
			if ll==[{}]: continue
			
			for kk,vv in ll.items():
				tmpdict={}
				tmpdict[kk]=[{'T':'LabelC', 'L': kk}, {'T':'LabelC', 'L': str(vv['amount'])}, {'T':'LabelC', 'L': str(vv['conf']) }] 
				grid_settings.append(tmpdict)
			
		rootframe = Toplevel()
		rootframe.title(msgstr)
		flexitable.FlexiTable(rootframe,grid_settings)
		
		def delete_record_done():
			idb=localdb.DB()
			idb.delete_where('queue_done',{'id':['=',id]})
			
		rootframe.after(2000,delete_record_done)
		
				
				
	def show_bills(self,addr):
		table={}
		ddict={'addr':addr}
		table['queue_waiting']=[localdb.set_que_waiting('show_bills',jsonstr=json.dumps(ddict) ) ]
								
		idb=localdb.DB()
		idb.insert(table,['type','wait_seconds','created_time','command' ,'json','id','status' ])
		
		self.queue_com.put([ table['queue_waiting'][0]['id'],'Bills for '+addr, self.display_bills])
		

	def message_asap_tx_done(self,id,msgstr,done):

		done=app_fun.json_to_str(done[0][0])
		messagebox.showinfo(msgstr,done )
		


	


	def get_last_addr_from(self): # get_last_addr_from(self) set_last_addr_from(self,addr)
	
		idb=localdb.DB()
		rr=idb.select('jsons',['json_content' ],{'json_name':['=',"'last_book_from_addr'"]} )
		
		if len(rr)>0:
			disp_dict=json.loads(rr[0][0])
			return disp_dict['addr']
		else:
			return localdb.get_default_addr()
			
	
	def set_last_addr_from(self,addr):
		# print('last_book_from_addr ',addr)
		if addr=='':
			return
			
		idb=localdb.DB()
		table={'jsons':[{'json_content':json.dumps({'addr':addr}), 'json_name':'last_book_from_addr'}]}
		idb.upsert(table,['json_content','json_name' ],{'json_name':['=',"'last_book_from_addr'"]} )





	

	def send_to_addr(self,addr,exampleval=0.0001): 
		tmpsignature=localdb.get_addr_to_hash(addr)
		
		rootframe = Toplevel()
		rootframe.title('Sending...')
		# 'InputFloat'
		automate_rowids=[ [{'T':'LabelC', 'L':'Sending to address\n\n'+addr+'\n\nFrom:', 'span':4 },{},{},{}] ,
							[{'T':'LabelC', 'L':'Address' },{'T':'LabelC', 'L':'Set max','width':9 },{'T':'LabelC', 'L':'Amount','width':9 },{'T':'LabelC', 'L':'Message (max '+str(int(512-len(tmpsignature)))+' bytes)' },{}] ,
							[{'T':'Button', 'L':'Select...',  'uid':'z1', 'width':32 },{'T':'Button', 'L':'',  'uid':'setmax1', 'width':32 },{'T':'InputFloat', 'uid':'a1' },{'T':'InputL',   'uid':'m1', 'width':32 },{'T':'LabelV','L':str(int(512-len(tmpsignature)))+' bytes left','uid':'l1'}] 
						]
		
		grid_settings=[]
		for ij,ar in enumerate(automate_rowids):
			tmpdict={}
			tmpdict[ij]=ar
			grid_settings.append(tmpdict)
				

		tmpdict={}
		tmpdict[999]=[{'T':'Button', 'L':'Queue Send', 'uid':'qsend' },{'T':'Button', 'L':'ASAP Send', 'uid':'asend'},{}]
		grid_settings.append(tmpdict)

				
		send_from=flexitable.FlexiTable(rootframe,grid_settings)
		
		last_addr=self.get_last_addr_from()
		if last_addr!='':
			send_from.set_textvariable( 'z1',last_addr)
			idb=localdb.DB()
			disp_dict=idb.select('jsons',['json_content','last_update_date_time'],{'json_name':['=',"'display_wallet'"]})
			if len(disp_dict)>0:
				disp_dict=json.loads(disp_dict[0][0])
				tmpmaxv=disp_dict['addr_amount_dict'][last_addr]['confirmed']+disp_dict['addr_amount_dict'][last_addr]['unconfirmed']
				send_from.set_textvariable('setmax1',tmpmaxv)
		
		for ij,ar in enumerate(automate_rowids):
			
			if ij<2: continue
			send_from.set_valid_input_fun( ar[3]['uid'],[ij,ar[3]['uid'],ar[4]['uid'],int(512-len(tmpsignature))],self.validate_memo)
		
		
		def select_addr():
			selframe = Toplevel() #tk.Tk()
			selframe.title('Select address to send from')
			
			filter_frame=ttk.LabelFrame(selframe,text='Filter')
			filter_frame.grid(row=0,column=0)
			filtbox=ttk.Combobox(filter_frame,textvariable='All',values=self.own_wallet_categories(), state="readonly")
			filtbox.current(0)
			filtbox.pack()
			
			def refresh_add_list(*eventsargs):
				filterval=filtbox.get()
				grid_lol_select=self.prepare_byaddr_frame(True,True,filterval)
		
				list_frame=ttk.LabelFrame(selframe,text='Addresses list')
				list_frame.grid(row=1,column=0)
				select_table=flexitable.FlexiTable(list_frame,grid_lol_select,600,True) #params=None, grid_lol=None
		
				self.prepare_byaddr_button_cmd(grid_lol_select,select_table,True,send_from)
				
			refresh_add_list()
			
			filtbox.bind("<<ComboboxSelected>>",  refresh_add_list )
		
		send_from.set_cmd( 'z1',[],select_addr)
		send_from.set_textvariable('a1',str(exampleval))
		
		def setmax1(*eventsargs):
			tmpv=send_from.get_value('setmax1')
			send_from.set_textvariable('a1',tmpv)
		
		send_from.set_cmd( 'setmax1',[],setmax1)
								
		def send(asap=False):
		
			tosend=[]
			
			z=send_from.get_value('z1' ).strip()
			a=send_from.get_value('a1').strip()
			m=send_from.get_value('m1').strip()
			
			if len(z)>0:				
				if len(a)>0:
					m+=' @zUnderNet'
					
					origlen,m=self.valid_memo_len(m,512-len(tmpsignature),suggest=True)
					m+=tmpsignature
						
					tosend.append({'z':addr,'a':a,'m':m})
						
			if len(tosend)==0:
				messagebox.showinfo("Nothing to send!","Nothing to send!")
				rootframe.lift()
				return
		
			ddict={'fromaddr':z,	'to':tosend	} 
			
			table={}
			if asap:
				table['queue_waiting']=[localdb.set_que_waiting('send',jsonstr=json.dumps(ddict) ) ]
			else:
				table['queue_waiting']=[localdb.set_que_waiting('send',jsonstr=json.dumps(ddict) , wait_seconds=WAIT_S) ]
				
			idb=localdb.DB()
			idb.insert(table,['type','wait_seconds','created_time','command' ,'json','id','status' ])
			
			if table['queue_waiting'][0]['wait_seconds']==0:
				self.queue_com.put([ table['queue_waiting'][0]['id'],'Sending\n',self.message_asap_tx_done])
		
		
			self.set_last_addr_from( z)
			rootframe.destroy()
				
				
		send_from.set_cmd( 'qsend',[],send)
		send_from.set_cmd( 'asend',[True],send)		
		
		
		
	def validate_memo(self,mm_elem,output_elem,initbytes,eargs=''):
	
		if type(int(1))!=type(initbytes): 
			tmpaddrto=initbytes.get()
			initbytes=512-localdb.get_addr_to_hash(tmpaddrto,True)
	
	
		mm=mm_elem.get()
		try:
			origbytes=len(mm.encode('utf-8')) 
		
			output_elem.set(str(initbytes-origbytes)+' bytes left')
		except:
			badc=''
			for cc in mm:
				try:
					cc.encode('utf-8')
				except:
					badc=cc
					break
		
			messagebox.showinfo('Bad character in memo input', 'This input contains bad character ['+badc+']:\n'+mm)
		
	
	
	def valid_memo_len(self,mm,initbytes,suggest=False):
		origbytes=len(mm.encode('utf-8'))
		if suggest:
			iter=1
			tmpmm=mm 
			while iter<origbytes-initbytes:
				tmpmm=mm[:-1-iter]
				if len(tmpmm.encode('utf-8'))<=initbytes:
					break
				iter+=1
				
			return origbytes,tmpmm 
	
		return origbytes
		
	
	def send_from_addr(self,addr,addr_total):

		global tmpid, tmprowid

		rootframe = Toplevel()
		rootframe.title('Sending...')
		# 'InputFloat'
		automate_rowids=[ [{'T':'LabelC', 'L':'Sending from address:  '+addr+'  of total amount (minus fee): '+str(round(addr_total,8)), 'span':6 },{},{},{},{},{}] ,
							[{'T':'LabelC', 'L':'To:'},{'T':'LabelC', 'L':'Address','width':64 },{'T':'LabelC', 'L':'Set max','width':16 },{'T':'LabelC', 'L':'Amount','width':12 },{'T':'LabelC', 'L':'Message (max 512 bytes)', 'width':24},{}] ,
							[{'T':'Combox','V':['Select','Own address','Address book'],'uid':'b1'},{'T':'InputL',   'uid':'z1' },{'T':'Button', 'L':str(round(addr_total,8)),  'uid':'setmax1', 'width':16 },{'T':'InputFloat', 'uid':'a1'},{'T':'InputL',   'uid':'m1' },{'T':'LabelV','L':'512 bytes left','uid':'l1'}] ,
							[{'T':'Combox','V':['Select','Own address','Address book'],'uid':'b2'},{'T':'InputL',   'uid':'z2' },{'T':'Button', 'L':str(round(addr_total,8)),  'uid':'setmax2', 'width':16 },{'T':'InputFloat', 'uid':'a2'},{'T':'InputL',   'uid':'m2' },{'T':'LabelV','L':'512 bytes left','uid':'l2'}] ,
							[{'T':'Combox','V':['Select','Own address','Address book'],'uid':'b3'},{'T':'InputL',   'uid':'z3' },{'T':'Button', 'L':str(round(addr_total,8)),  'uid':'setmax3', 'width':16 },{'T':'InputFloat', 'uid':'a3' },{'T':'InputL',  'uid':'m3' },{'T':'LabelV','L':'512 bytes left','uid':'l3'}] 
						]
		
		grid_settings=[]
		for ij,ar in enumerate(automate_rowids):
			tmpdict={}
			tmpdict[ij]=ar
			grid_settings.append(tmpdict)
			
		tmpdict={}
		tmpdict[999]=[{'T':'Button', 'L':'+ address', 'uid':'addaddr', 'span':2},{},{'T':'Button', 'L':'Queue Send', 'uid':'qsend', 'span':2 },{},{'T':'Button', 'L':'ASAP Send', 'uid':'asend', 'span':2},{}]
		grid_settings.append(tmpdict)
										
		send_from=flexitable.FlexiTable(rootframe,grid_settings)
		
		def select_addr(elemC,elemZ, addram,evargs):
			
			booktype=elemC.get() # own or adddr book
			if booktype=='Select':
				return
			
			selframe = Toplevel() #tk.Tk()
			selframe.title('Select address to send to')
			filter_frame=ttk.LabelFrame(selframe,text='Filter')
			filter_frame.grid(row=0,column=0)
				
			if booktype=='Own address':
				
				filtbox=ttk.Combobox(filter_frame,textvariable='All',values=self.own_wallet_categories(), state="readonly")
				filtbox.current(0)
				filtbox.pack()
				
				def refresh_add_list(*eventsargs):
					filterval=filtbox.get()
					grid_lol_select=self.prepare_byaddr_frame(True,True,filterval,True)
			
					list_frame=ttk.LabelFrame(selframe,text='Addresses list')
					list_frame.grid(row=1,column=0)
					select_table=flexitable.FlexiTable(list_frame,grid_lol_select,600,True) #params=None, grid_lol=None
			
					self.prepare_byaddr_button_cmd(grid_lol_select,select_table,True,send_from,addram )
					
				refresh_add_list()
				
				filtbox.bind("<<ComboboxSelected>>",  refresh_add_list )
			else:
				# address book  categories_filter
				filtbox=ttk.Combobox(filter_frame,textvariable='All',values=self.categories_filter(), state="readonly")
				filtbox.current(0)
				filtbox.pack()
				global grid_lol_select
				grid_lol_select=[]
				tmpdict={}
				tmpdict['head']=[{ } , {'T':'LabelC', 'L':'Usage' } , {'T':'LabelC', 'L':'Category' } , {'T':'LabelC', 'L':'Alias' } , {'T':'LabelC', 'L':'Full address' }]
				grid_lol_select.append(tmpdict)

				def update_grid(*argsevnts):
					global grid_lol_select
					
					tmplen=len(grid_lol_select)
					if tmplen>1:
						del grid_lol_select[1:tmplen]
						
					idb=localdb.DB()
					sel_addr_book=idb.select('addr_book',[ 'Category','Alias','Address','usage'] ,orderby=[{'usage':'desc'},{'Category':'asc'},{'Alias':'asc' }] )
					
					if len(sel_addr_book)>0:
					
						filterv=filtbox.get()
					
						for ii,rr in enumerate(sel_addr_book):
							tmpdict={}
							visible=False
							if filterv in [rr[0],'All']:
								visible=True
							
							tmpdict[ii]=[{'T':'Button', 'L':'Select', 'uid':'select'+str(ii) , 'visible':visible}, 
									{'T':'LabelV', 'L':str(rr[3]), 'uid':'Usage'+str(ii) , 'visible':visible} , 
									{'T':'LabelV', 'L':rr[0], 'uid':'Category'+str(ii) , 'visible':visible} , 
									{'T':'LabelV', 'L':rr[1], 'uid':'Alias'+str(ii) , 'visible':visible} , 
									{'T':'LabelV', 'L':rr[2], 'uid':'Address'+str(ii) , 'visible':visible}
									]
							grid_lol_select.append(tmpdict)

				update_grid()
				list_frame=ttk.LabelFrame(selframe,text='Addresses list')
				list_frame.grid(row=1,column=0)
				select_table=flexitable.FlexiTable(list_frame,grid_lol_select)
				
				
				def set_and_destroy(addr,elemZ ): # here also get signature!
					 
					elemZ.set(addr)
					 
					selframe.destroy()
						
				for ij,ar in enumerate(grid_lol_select):
					if ij<1: continue
						
					for ki,vi in ar.items():
						select_table.set_cmd( vi[0]['uid'],[vi[4]['L'],elemZ ],set_and_destroy) # print to master and destroy ?
				
				def update_filter(*someargs):
					global grid_lol_select
					update_grid()	
					select_table.update_frame(grid_lol_select)
					
				filtbox.bind("<<ComboboxSelected>>",  update_filter )
				
		def setmax( inpout,*evargs):
			inpout.set(str(  addr_total  ))
			
		
		for ij,ar in enumerate(automate_rowids):
			if ij<2: continue
			
			send_from.set_valid_input_fun( ar[4]['uid'],[ij,ar[4]['uid'],ar[5]['uid'],ar[1]['uid']],self.validate_memo)
			# add command for buttons - open select form 
			send_from.bind_combox_cmd( ar[0]['uid'],[ ar[0]['uid'],ar[1]['uid'] , [ ar[1]['uid'], ar[3]['uid'] ] ],select_addr)
			
			send_from.set_cmd( ar[2]['uid'],[ ar[3]['uid']],setmax )
			
		tmpid=4
		tmprowid=5
		
		def addaddr():
			global tmpid, tmprowid 
			
			rr=[{'T':'Combox','V':['Select','Own address','From address book'],'uid':'b'+str(tmpid)},{'T':'InputL',   'uid':'z'+str(tmpid) },{'T':'Button', 'L':str(round(addr_total,8)),  'uid':'setmax'+str(tmpid), 'width':16 },{'T':'InputFloat', 'uid':'a'+str(tmpid) },{'T':'InputL',  'uid':'m'+str(tmpid) },{'T':'LabelV','L':'512 bytes left','uid':'l'+str(tmpid)}]
			
			for jj,vv in enumerate(rr): # column by column
				send_from.add_new_element(vv,tmprowid,jj,tmprowid)
				
			send_from.set_valid_input_fun( rr[4]['uid'],[tmprowid,rr[4]['uid'],rr[5]['uid'],rr[1]['uid']],self.validate_memo)
			send_from.bind_combox_cmd( rr[0]['uid'],[rr[0]['uid'],rr[1]['uid'] , [ rr[1]['uid'], rr[3]['uid'] ]  ],select_addr)
			
			send_from.set_cmd( rr[2]['uid'],[ rr[3]['uid']],setmax )
			
			tmprowid+=1
			tmpid+=1
		
		send_from.set_cmd( 'addaddr',[],addaddr)
				
				
		
		def send(asap=False):
			global tmpid, tmprowid #, send_from
			tosend=[]
			
			for ii in range(tmpid-1):
				tmpstr=str(ii+1)
				
				z=send_from.get_value('z'+tmpstr).strip()
				a=send_from.get_value('a'+tmpstr).strip()
				m=send_from.get_value('m'+tmpstr).strip()
				
				
				if len(z)>0:				
					if len(a)>0:
						m+=' @zUnderNet'
						tmpsignature=localdb.get_addr_to_hash(z)
						origlen,m=self.valid_memo_len(m,512-len(tmpsignature),suggest=True)
						m+=tmpsignature
						tosend.append({'z':z,'a':a,'m':m})
						
			if len(tosend)==0:
				
				messagebox.showinfo("Nothing to send!","Nothing to send!")
				rootframe.lift()
				return
		
			ddict={'fromaddr':addr,	'to':tosend	}
			table={}
			if asap:
				table['queue_waiting']=[localdb.set_que_waiting('send',jsonstr=json.dumps(ddict) ) ]
			else:
				table['queue_waiting']=[localdb.set_que_waiting('send',jsonstr=json.dumps(ddict) , wait_seconds=WAIT_S) ]
				
			idb=localdb.DB()
			idb.insert(table,['type','wait_seconds','created_time','command' ,'json','id','status' ])
			
			if table['queue_waiting'][0]['wait_seconds']==0:
				
				self.queue_com.put([ table['queue_waiting'][0]['id'],'Sending\n',self.message_asap_tx_done])
			
			rootframe.destroy()
				
				
		send_from.set_cmd( 'qsend',[],send)
		send_from.set_cmd( 'asend',[True],send)
				
				
				
	def export_wallet(self): # export encrypted wallet or encrypted priv keys and addresses
			
		rootframe = Toplevel()
		rootframe.title('Exporting wallet')
				
		automate_rowids=[ [{'T':'Button', 'L':'Select folder', 'uid':'seldir' }, {'T':'LabelV', 'L':str(os.getcwd()), 'uid':'selected' } ] ,
							[{'T':'LabelC', 'L':'Export type: ' } , {'T':'Combox', 'V':['wallet.dat','priv.keys and addresses','local_storage.db'],'uid':'opt', 'width':23 } ] ,
							[{'T':'Button', 'L':'Enter', 'uid':'enter', 'span':2  }, {}] 
						]
										
		grid_settings=[]
		for ij,ar in enumerate(automate_rowids):
			tmpdict={}
			tmpdict[ij]=ar
			grid_settings.append(tmpdict)
										
		expo=flexitable.FlexiTable(rootframe,grid_settings)
		
		def setdir_and_lift(arg):
			
			flexitable.setdir(arg)
			rootframe.lift()
		
		expo.set_cmd( 'seldir',['selected'], setdir_and_lift)
		
		def enter():
		
			ddict={'path':expo.get_value('selected'),
					'opt':expo.get_value('opt')
					}
					
			if ddict['opt']=='wallet.dat' or ddict['opt']=='local_storage.db':
				idb=localdb.DB('init.db')
				ppath=idb.select('init_settings',['datadir'] )
				pfrom=ppath[0][0]+'/wallet.dat'
				pto=ddict['path']
				
				if ddict['opt']=='local_storage.db':
					
					pfrom=os.path.join(os.getcwd(),'local_storage.db') #'/wallet.dat'
					
				cc=aes.Crypto()

				if self.password==None:
					if flexitable.msg_yes_no("Encrypt exported file with new password?", "Encrypt exported file with new password? Only hit 'no' if you really do not need encryption for this export."):
						tmppass=cc.rand_password(32)
						pto=pto+'/'+ddict['opt'].replace('.dat','.encr').replace('.db','.encr')
						cc.aes_encrypt_file( pfrom ,pto  ,tmppass ) #ppath[0][0]+'/wallet.dat' ddict['path']+'/wallet.encr'
						flexitable.output_copy_input('Password for file exported to '+ddict['path']+'/wallet.encr',tmppass)
					else:
						pto=pto+'/'+ddict['opt']
						shutil.copyfile(pfrom, pto) # ddict['path']+'/wallet.dat'
				else:
					if flexitable.msg_yes_no("Encrypt exported file with your password?", "If you make a backup for yourself 'yes' is good option. If you share or sell the file better select 'no' since sharing personal passwords is not a good practice."):
						pto=pto+'/'+ddict['opt'].replace('.dat','.encr').replace('.db','.encr')
						cc.aes_encrypt_file( pfrom, pto  , self.password) #ddict['path']+'/wallet.encr'
					
					elif flexitable.msg_yes_no("Encrypt exported file with new password?", "Encrypt exported file with new password? Only hit 'no' if you really do not need encryption for this export."):
						tmppass=cc.rand_password(32)
						pto=pto+'/'+ddict['opt'].replace('.dat','.encr').replace('.db','.encr')
						cc.aes_encrypt_file( pfrom,pto  , tmppass) #ddict['path']+'/wallet.encr'
						flexitable.output_copy_input('Password for file exported to '+ddict['path']+'/wallet.encr',tmppass)
					else:
						pto=pto+'/'+ddict['opt']
						shutil.copyfile(pfrom, pto ) #ddict['path']+'/wallet.dat'
						
				rootframe.destroy()
				return
					
					
			table={}
			table['queue_waiting']=[localdb.set_que_waiting('export_wallet',jsonstr=json.dumps(ddict) ) ]
			
			idb=localdb.DB()
			idb.insert(table,['type','wait_seconds','created_time','command' ,'json','id','status' ])
			
			rootframe.destroy()
		
		expo.set_cmd( 'enter',[],enter)
		
	def export_addr(self,addr):
	
		rootframe = Toplevel()
		rootframe.title('Exporting address')
				
		automate_rowids=[ 
							[{'T':'LabelC', 'L':'Export type: ' } , {'T':'Combox', 'V':['encrypted file','display on screen'],'uid':'opt', 'width':23 } ] ,
							[{'T':'Button', 'L':'Enter', 'uid':'enter', 'span':2  }, {}] 
						]
										
		grid_settings=[]
		for ij,ar in enumerate(automate_rowids):
			tmpdict={}
			tmpdict[ij]=ar
			grid_settings.append(tmpdict)
										
		expo=flexitable.FlexiTable(rootframe,grid_settings)
		
		
		def enter():
			# global rootframe, expo
					
			rootframe.destroy()
			if expo.get_value('opt')=='display on screen':
				flexitable.output_copy_input('Address' ,addr)
			
			else: # to file 
			
				path=filedialog.askdirectory(initialdir=os.getcwd(), title="Select directory to write to")
				if path==None:
					return 

				cc=aes.Crypto()

				tmppass=cc.rand_password(32)
				pto=path+'/addr_'+app_fun.now_to_str()+'.txt'
				# json.dumps({'addr':addr })
				cc.aes_encrypt_file( json.dumps({'addr':addr }), pto  , tmppass) #ddict['path']+'/wallet.encr'
				flexitable.output_copy_input('Password for file exported to '+pto,tmppass)

		
		expo.set_cmd( 'enter',[],enter)
		
		
		
	# encrypt with random password and present the password , save the pass in db 
	# ask where t odrop the file 
	def export_viewkey(self,addr):
		# print('enter',addr)
		rootframe = Toplevel()
		rootframe.title('Exporting view key')
				
		automate_rowids=[ 
							[{'T':'LabelC', 'L':'Export type: ' } , {'T':'Combox', 'V':['encrypted file','display on screen'],'uid':'opt', 'width':23 } ] ,
							[{'T':'Button', 'L':'Enter', 'uid':'enter', 'span':2  }, {}] 
						]
										
		grid_settings=[]
		for ij,ar in enumerate(automate_rowids):
			tmpdict={}
			tmpdict[ij]=ar
			grid_settings.append(tmpdict)
										
		expo=flexitable.FlexiTable(rootframe,grid_settings)
		
		def enter():
			# global rootframe, expo
			table={}
			rootframe.destroy()
			if expo.get_value('opt')=='display on screen':
				# flexitable.output_copy_input('Address' ,addr)
				ddict={'addr':addr,
						'path':'',
						'password':''
						}
			
			else: # to file 
			
				path=filedialog.askdirectory(initialdir=os.getcwd(), title="Select directory to write to")
				if path==None:
					return 
					
				cc=aes.Crypto()

				ddict={'addr':addr,
						'path':path,
						'password':cc.rand_password(32)
						}
					
			table['queue_waiting']=[localdb.set_que_waiting('export_viewkey',jsonstr=json.dumps(ddict)) ]
			idb=localdb.DB()
			idb.insert(table,['type','wait_seconds','created_time','command' ,'json','id','status' ])
			
					
		expo.set_cmd( 'enter',[],enter)
	
	
	
		
		
		
	def new_addr(self):
		table={}
		table['queue_waiting']=[localdb.set_que_waiting('new_addr' ) ]

		idb=localdb.DB()
		idb.insert(table,['type','wait_seconds','created_time','command' ,'json','id','status' ])
		
		self.queue_com.put([ table['queue_waiting'][0]['id'],'Creating new address\n',self.message_asap_tx_done ])

		
	
	def prepare_queue_frame(self,init=False):	

		idb=localdb.DB()
		grid_lol3=[]
		tmpdict2={}
		if init:
			tmpdict2['head']=[{'T':'LabelC', 'L':'Task'}, #, 'tooltip':'Command'
									{'T':'LabelC', 'L': 'Created time'},
									{'T':'LabelC', 'L': 'Status' },
									{'T':'LabelC', 'L': 'Wait[s]' },
									{'T':'LabelC', 'L': 'Cancell' }									
									]
		
			grid_lol3.append(tmpdict2)
		
		disp_dict=idb.select('queue_waiting', ["command","created_time","status","wait_seconds","json","id"],orderby=[{'created_time':'desc' }])
		# to have result check second table for status done 
		if len(disp_dict)>0:		
		
			for ii,rr in enumerate(disp_dict):
				tmpid=rr[5] #ii #rr[5]
				status_label={'T':'LabelV', 'L': rr[2], 'uid':"status"+str(tmpid) }
				
				if rr[2]=='awaiting_balance':
					status_label={'T':'LabelV', 'L': rr[2], 'uid':"status"+str(tmpid), 'style':{'bgc':'yellow','fgc':'brown'} }
				elif rr[2]=='processing':
					status_label={'T':'LabelV', 'L': rr[2], 'uid':"status"+str(tmpid), 'style':{'bgc':'blue','fgc':'white'} }
				elif rr[2]=='done':
					sstyle={'bgc':'white','fgc':'#aaa'}
					task_done=idb.select('queue_done', ['result'],{'id':['=',tmpid]})
					
					tmpres=' no results yet ... '
					if len(task_done)>0: 
						tmp_res=task_done[0][0].lower()
						if 'false' in tmp_res or 'failed' in tmp_res or 'error' in tmp_res :
							sstyle={'bgc':'red','fgc':'#ccc'}
							tmpres=app_fun.json_to_str(task_done[0][0]) #task_done[0][0]
						elif 'success' in tmp_res or 'true' in tmp_res :
							sstyle={'bgc':'green','fgc':'#fff'}
							tmpres='Success/True'
							
				
					status_label={'T':'LabelV', 'L': rr[2], 'uid':"status"+str(tmpid), 'style':sstyle, 'tooltip':tmpres }
				
				tmpdict2={}
				tmptooltip='' 
				if rr[0]=='send':
					ttmp=json.loads(rr[4])

					tmptooltip='From address\n'+ttmp['fromaddr']+'\nto:\n'
					for ss in ttmp['to']:
						tmptooltip+=ss['z']+' amount '+str(ss['a'])+'\n'
				else:
					tmptooltip=app_fun.json_to_str(rr[4])
				
				tmpdict2[tmpid]=[ {'T':'LabelV', 'L':rr[0], 'tooltip':tmptooltip, 'uid':"command"+str(tmpid)},
									{'T':'LabelV', 'L': rr[1], 'uid':"created_time"+str(tmpid)},
									status_label,
									{'T':'LabelV', 'L':str(int( int(rr[3])-(datetime.datetime.now()-app_fun.datetime_from_str(rr[1]) ).total_seconds() )), 'uid':"wait_seconds"+str(tmpid) },
									{'T':'Button', 'L': 'Cancell', 'uid':"Cancell"+str(tmpid) }	
								]
				grid_lol3.append(tmpdict2)
				
		return grid_lol3


	def queue_frame_buttons(self,grid,frame_table):
		idb=localdb.DB()
		
		def cancell(id):
			try:
				disp_dict=idb.select('queue_waiting', ["type","command","created_time","status","wait_seconds","json","id"],{'id':['=',id]})
				table={}	
				if disp_dict[0][3]!='done':
					
					table['queue_done']=[{"type":disp_dict[0][0]
									, "wait_seconds":disp_dict[0][4]
									, "created_time":disp_dict[0][2]
									, "command":disp_dict[0][1]
									, "json":disp_dict[0][5]
									, "id":disp_dict[0][6]
									, "result":'cancelled'
									, 'end_time':app_fun.now_to_str(False)
									} ]
					idb.insert(table,["type","wait_seconds","created_time","command","json","id","result",'end_time'])
				
				idb.delete_where('queue_waiting',{'id':['=',id]})
				time.sleep(1)
				frame_table.update_frame(self.prepare_queue_frame())
			except:
				pass # double click cancell error
		
		for x1 in grid:
		
			for kk,vv in x1.items(): # kk= head or alias 
				if kk=='head' :
					continue
					
				if type(kk)==type('asd'):
					if '_nextline' in kk:
						continue
			
				bpush_uid='Cancell'+str(kk)
				
				frame_table.set_cmd(bpush_uid,[str(kk)], cancell)
				

	def set_rounding_str(self,rstr):
		format_str=",.0f"
		if rstr=='off':
			format_str=",.8f"
		elif rstr=='0.0001':
			format_str=",.4f"
		elif rstr=='0.001':
			format_str=",.3f"
		elif rstr=='0.01':
			format_str=",.2f"
		elif rstr=='0.1':
			format_str=",.1f"
			
		return format_str

	def get_rounding_str(self,strval=False):
		format_str=",.0f"
		
		idb=localdb.DB()
		if idb.check_table_exist('wallet_display'):
			rounding=idb.select('wallet_display',['value'],{'option':['=',"'rounding'"]})
				
			if len(rounding)>0:
				rounding=rounding[0][0]
				if strval: return rounding
				
				format_str=self.set_rounding_str(rounding)
					
		if strval: return ''
		
		return format_str
		
		
	def get_options(self,strval=False):
		idb=localdb.DB()
		retdict={'sorting':'amounts','filtering': 'All','rounding':",.0f"}
		opt=idb.select('wallet_display',['option','value'],{'option':[' in ',"('sorting','filtering','rounding')"]} )
		for oo in opt:
			retdict[ oo[0] ] = oo[1]
		
		if not strval:
			retdict['rounding']=self.set_rounding_str(retdict['rounding'])
	
		return retdict
		
		
	def get_sorting(self):
		idb=localdb.DB()
		if idb.check_table_exist('wallet_display'):
			sorting=idb.select('wallet_display',['value'],{'option':['=',"'sorting'"]})
			if len(sorting)>0:
				return sorting[0][0]
		return 'amounts'

	def get_filtering(self):
		
		idb=localdb.DB()
		if idb.check_table_exist('wallet_display'):
			filtering=idb.select('wallet_display',['value'],{'option':['=',"'filtering'"]})
			if len(filtering)>0:
				return filtering[0][0]
		return 'All'
		
	
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
		
		

	def own_wallet_categories(self):
	
		all_cat_unique=[]
		idb=localdb.DB()
		all_cat=idb.select('address_category',['category'] )
		for rr in all_cat: #sorted(enumerate(self.amounts), key=lambda x:x[1], reverse=True):
			
			if rr[0] not in all_cat_unique:
				all_cat_unique.append(rr[0])
			
		if 'Excluded' not in all_cat_unique:
			all_cat_unique=['Excluded']+all_cat_unique 
			
		if 'Not hidden' not in all_cat_unique:
			all_cat_unique=['Not hidden']+all_cat_unique 
		
		if 'All' not in all_cat_unique:
			all_cat_unique=['All']+all_cat_unique 
			
		if 'Hidden' not in all_cat_unique:
			all_cat_unique=all_cat_unique + ['Hidden']
			
		if 'Edit' not in all_cat_unique:
			all_cat_unique=all_cat_unique+['Edit']
			
		return all_cat_unique


	
	def lock_basic_frames(self):
		self.while_updating=True
		
	def unlock_basic_frames(self):
		self.while_updating=False
		
	def is_locked(self):
		return self.while_updating
		
		
		
		
	def prepare_summary_frame(self,init=False):	
		
		idb=localdb.DB()
		# print(idb.select('queue_waiting' ))
		
		grid_lol_wallet_sum=[]
		
		if init:
			tmpdict={}
			tmpdict['head']=[{'T':'LabelC', 'L':'Total', 'tooltip':'Wallet total of confirmed + pending balance'}  
										, {'T':'LabelC', 'L':'Confirmed'}
										, {'T':'LabelC', 'L':'Pending'}
										, {'T':'LabelC', 'L':' '}
										, {'T':'LabelC', 'L':'Sort'}
										, {'T':'LabelC', 'L':'Round'}
										, {'T':'LabelC', 'L':'Filter'}	
										, {'T':'LabelC', 'L':'New address'}	
										, {'T':'LabelC', 'L':'Wallet'}	]
																			
			grid_lol_wallet_sum.append(tmpdict )
			
		
		disp_dict=idb.select('jsons',['json_content','last_update_date_time'],{'json_name':['=',"'display_wallet'"]})
		
			
		all_cat=self.own_wallet_categories() #all_cat_unique
		format_str=self.get_rounding_str()
					
		if len(disp_dict)>0:
			disp_dict=json.loads(disp_dict[0][0])
			# print(format_str)
			tmpdict={}
			tmpdict['summary']=[{'T':'LabelV', 'L':format(disp_dict['top']['Total'] , format_str).replace(',',"'")  , 'uid':'Total'}  , 
										{'T':'LabelV', 'L':format(disp_dict['top']['Confirmed'] , format_str).replace(',',"'")  , 'uid':'Confirmed'}, 
										{'T':'LabelV', 'L':format(disp_dict['top']['Pending'] , format_str).replace(',',"'")  , 'uid':'Pending'},
										{'T':'LabelV', 'L':' ', 'uid':'space'},
										{'T':'Combox','V':['amounts','bills','usage'], 'uid':'sort', 'width':7}, # enter this function!
										{'T':'Combox', 'uid':'round', 'V':['1','0.1','0.01','0.001','0.0001','off'], 'width':6},
										{'T':'Combox', 'uid':'filter', 'V':all_cat, 'width':6, 'tooltip':'Special categories:\nHidden - allows to hide address on the list,\n Excluded - allows to exclude address from UTXO/bills auto maintenance when it is ON.'},
										{'T':'Button', 'L':'+', 'uid':'addaddr', 'tooltip':'Create new address'},
										{'T':'Button', 'L':'Export', 'uid':'export' }
										]
			grid_lol_wallet_sum.append(tmpdict )	
			
		else:
			tmpdict={}
			tmpdict['summary']=[{'T':'LabelV', 'L':'', 'uid':'Total'}  , 
										{'T':'LabelV', 'L':'', 'uid':'Confirmed'}, 
										{'T':'LabelV', 'L':'', 'uid':'Pending'},
										{'T':'LabelV', 'L':' ', 'uid':'space'},
										{'T':'Combox','V':['amounts','bills','usage'], 'uid':'sort', 'width':7}, # enter this function!
										{'T':'Combox', 'uid':'round', 'V':['1','0.1','0.01','0.001','0.0001','off'], 'width':6},
										{'T':'Combox', 'uid':'filter', 'V':all_cat, 'width':6},
										{'T':'Button', 'L':'+', 'uid':'addaddr', 'tooltip':'Create new address'},
										{'T':'Button', 'L':'Export', 'uid':'export' }
										]
			grid_lol_wallet_sum.append(tmpdict )	
			
			
					
			
		return grid_lol_wallet_sum
		
		
		
		
	def get_header(self,selecting):
		grid_lol3=[]
		tmpdict2={}

		if selecting:
		
			tmpdict2['head']=[{'T':'LabelC', 'L':'Category', 'tooltip':'May be useful for filtering addresses in big wallets' }  , 
								{'T':'LabelC', 'L': 'Alias', 'tooltip':'Short unique address referrence', 'width':7 },
								{'T':'LabelC', 'L': 'Total' },
								{'T':'LabelC', 'L': 'Confirmed' },
								{'T':'LabelC', 'L': 'Pending' },
								{'T':'LabelC', 'L': 'Usage' },
								{'T':'LabelC', 'L': 'Select' }
								]
		else:
	
			tmpdict2['head']=[{'T':'LabelC', 'L':'Category', 'tooltip':'May be useful for filtering addresses in big wallets' }  , 
								{'T':'LabelC', 'L': 'Alias', 'tooltip':'Short unique address referrence', 'width':7 },
								{'T':'LabelC', 'L': 'Total' },
								{'T':'LabelC', 'L': 'Confirmed' },
								{'T':'LabelC', 'L': 'Pending' },
								{'T':'LabelC', 'L': 'Bills', 'tooltip':'Tota/Pending You may have the same amount in 1 bill or many bills. In cryptocurrency bill is called UTXO. It is good to have few bills at hand, because getting change make take few minutes and during changing transaction on the working address is not allowed (temporary balance is zero).' },
								{'T':'LabelC', 'L': 'Usg.', 'tooltip':'Historical incoming transactions. May be usefull to distinguish from fresh unused addresses.' },
								{'T':'LabelC', 'L': 'Addr.', 'tooltip':'Address export column' },
								{'T':'LabelC', 'L': 'V.Key' , 'tooltip':'Viewing key export column'}
								]
	
		grid_lol3.append(tmpdict2)
		
		return grid_lol3
		
		
	def prepare_byaddr_frame(self,init=False,selecting=False,selecting_filter='All',selecting_to=False):	
		
		grid_lol3=[]
		tmpdict2={}
		if init:
		
			tmphead=self.get_header(selecting)
			grid_lol3.append(tmphead[0])
		
		idb=localdb.DB()
		disp_dict=idb.select('jsons',['json_content','last_update_date_time'],{'json_name':['=',"'display_wallet'"]})
		
		opt=self.get_options()
		format_str=opt['rounding'] #self.get_rounding_str()
		sorting=opt['sorting'] #self.get_sorting()
		filtering=opt['filtering'] #self.get_filtering()
		
		if selecting:
			sorting='usage'
			filtering=selecting_filter
		
		if len(disp_dict)>0:
		
			ddict=json.loads(disp_dict[0][0])
			sorting_lol=ddict['lol']
			
			if sorting=='amounts': 
				sorting_lol=sorted(sorting_lol, key = operator.itemgetter(1, 2, 3), reverse=True )
			elif sorting=='bills':
				sorting_lol=sorted(sorting_lol, key = operator.itemgetter(2, 1, 3), reverse=True )
			elif sorting=='usage':
				sorting_lol=sorted(sorting_lol, key = operator.itemgetter(3, 1, 2), reverse=True )
				
			adr_cat=idb.select('address_category',['address','category'] )
			
			addr_cat={}
			for ac in adr_cat:
				addr_cat[ac[0]]=ac[1]
				
					
			for i in sorting_lol: 
			
				ii=i[0]
				
				self.amount_per_address[ddict['wl'][ii]['addr']]=float(ddict['wl'][ii]['confirmed'])
				
				tmpcurcat='Edit'
				if ddict['wl'][ii]['addr'] in addr_cat:
					tmpcurcat=addr_cat[ddict['wl'][ii]['addr']]
				
				visible=False
				
				if filtering in ['All',tmpcurcat]:
					visible=True
					
				if filtering=='Not hidden' and  tmpcurcat!='Hidden':
					visible=True
					
				tmp_confirmed=ddict['wl'][ii]['confirmed']
				tmp_unconfirmed=ddict['wl'][ii]['unconfirmed']
				tmp_total=tmp_confirmed+tmp_unconfirmed
				
				if selecting_to:
					visible=True
				elif selecting and tmp_total<=0.0001:
					visible=False
				
				send_state='normal'
				if tmp_total<=0:
					send_state='disabled'
					
				
				bills=int(ddict['wl'][ii]['#conf']+ddict['wl'][ii]['#unconf'])
				billsc=int(ddict['wl'][ii]['#conf'] )
				billsunc=int( ddict['wl'][ii]['#unconf'])
				
				bill_state='normal'
				if bills<=0:
					bill_state='disabled'
				
					
				tmpalias=ddict['aliasmap'][ddict['wl'][ii]['addr']]	
				tmpaddr=ddict['wl'][ii]['addr']
				
				tmpdict2={}
				
				if selecting:
					tmpdict2[tmpalias]=[ 
									{'T':'LabelV', 'L':tmpcurcat, 'visible':visible}, 
									{'T':'LabelV', 'L':tmpalias,  'visible':visible},
									{'T':'LabelV', 'L':format(tmp_total , format_str).replace(',',"'") , 'visible':visible, 'uid':'Total'+tmpalias},
									{'T':'LabelV', 'L':format(tmp_confirmed , format_str).replace(',',"'")  , 'visible':visible },
									{'T':'LabelV', 'L':format(tmp_unconfirmed , format_str).replace(',',"'") , 'visible':visible},
									
									{'T':'LabelV', 'L':str( ddict['lol'][ii][3] ),  'visible':visible},
									{'T':'Button', 'L':'Select' , 'uid':'select'+tmpalias, 'visible':visible, 'tooltip': tmpaddr }
									]
					
				else:
					tmpdict2[tmpalias]=[ 
									{'T':'Button', 'L':tmpcurcat, 'uid':'Category'+tmpalias, 'tooltip':'Edit category for address '+tmpaddr, 'visible':visible}, 
									{'T':'LabelV', 'L':tmpalias, 'uid':'Alias'+tmpalias, 'tooltip':'Alias of address '+tmpaddr, 'visible':visible},
									{'T':'LabelV', 'L':format(tmp_total , format_str).replace(',',"'") , 'uid':'Total'+tmpalias, 'visible':visible},
									{'T':'Button', 'L':format(tmp_confirmed , format_str).replace(',',"'")  , 'uid':'Send'+tmpalias, 'tooltip':'Send from this address', 'visible':visible, 'IS':send_state},
									{'T':'LabelV', 'L':format(tmp_unconfirmed , format_str).replace(',',"'") , 'uid':'Pending'+tmpalias, 'visible':visible},
									{'T':'Button', 'L':str(bills)+'/'+str(billsunc), 'uid':'Bills'+tmpalias, 'tooltip':'Show bills / UTXOs', 'visible':visible, 'IS':bill_state},
									
									{'T':'LabelV', 'L':str( ddict['lol'][ii][3] ), 'uid':'Usage'+tmpalias, 'visible':visible},

									{'T':'Button', 'L':'XA' , 'uid':'addrexp'+tmpalias, 'visible':visible, 'tooltip': 'Export address '+tmpaddr},
									{'T':'Button', 'L':'XVK' , 'uid':'viewkey'+tmpalias, 'visible':visible, 'tooltip': 'Export Viewing Key of '+tmpaddr}
									]
				grid_lol3.append(tmpdict2)

		return grid_lol3
		
		
		
		
		
	def prepare_byaddr_button_cmd(self,grid_lol3,wallet_details,selecting=False,send_from=None,addram=[]): # copy addr and edit category 

		def update_frame_display(tmpgrid):
			wallet_details.update_frame(tmpgrid)
		
		for x1 in grid_lol3:
		
			
			for kk,vv in x1.items(): # kk= head or alias 
				if kk=='head':
					continue
			
				addr=''
				addr_total=round(float(wallet_details.get_value('Total'+kk).replace("'",'')) -0.0001,8)
				
				if selecting:
					bsel_uid='select'+kk
					if 'tooltip' in vv[6] and send_from!=None:
						addr=vv[6]['tooltip']
						
						def set_and_destroy(addr,alias):
							# global addram
							amount_uid='Total'+alias
							loc_addram=addram.copy()
							if loc_addram==[]:
								loc_addram=['z1','setmax1']
								send_from.set_textvariable(loc_addram[0], addr)
								tmpv=float(wallet_details.get_value(amount_uid) )-0.0001
								send_from.set_textvariable(loc_addram[1], tmpv )
							else:
								send_from.set_textvariable(addram[0], addr)
								
							wallet_details.master.master.destroy()
						
						wallet_details.set_cmd(bsel_uid,[addr,kk],set_and_destroy)
						
				else:
					
					if 'tooltip' in vv[1]:
						addr=vv[1]['tooltip'].replace('Alias of address ','')
						
					# edit category
					bedit_uid='Category'+kk # open edit window
					curv=wallet_details.get_value(bedit_uid)
					wallet_details.set_cmd(bedit_uid,[kk,addr,curv,wallet_details], self.edit_category)
					
					# send - from this addr 
					# print('send',addr,kk)
					bsend='Send'+kk
					wallet_details.set_cmd(bsend,[addr,addr_total], self.send_from_addr) # 2h open form
					
					# bills
					bbills='Bills'+kk
					wallet_details.set_cmd(bbills,[addr], self.show_bills) # 1h open view, mark with timestamp, stays same/ not refreshed with wallet 
				
					# addrexp
					bpriv='addrexp'+kk
					wallet_details.set_cmd(bpriv,[addr], self.export_addr) # 2h open form, options: to encrypted file, to unencrypted file, just display,

					# bills
					bview='viewkey'+kk
					
					wallet_details.set_cmd(bview,[addr], self.export_viewkey) # 1h open view


	def edit_category(self,alias,addr , curv, wallet_details, json_to_update='wallet_byaddr'):

		global rootframe, tmpvar
		
		rootframe = Toplevel() #tk.Tk()
		rootframe.title('Edit category')
		ttk.Label(rootframe,text='Edit category for \n\n '+addr+' \n').grid(row=0,column=0,columnspan=3,sticky="nsew") #pack(fill='x')
		tmpvar=StringVar()
		tmpvar.set(curv.replace('Edit',''))
		
		def setmain(): tmpvar.set('Main')
		def setexcl(): tmpvar.set('Exclude')
		def sethide(): tmpvar.set('Hidden')
		
		ttk.Button(rootframe,text='Set Main',command=setmain  ).grid(row=1,column=0,columnspan=1,sticky="nsew") #pack(fill='x')
		ttk.Button(rootframe,text='Set Exclude',command=setexcl ).grid(row=1,column=1,columnspan=1,sticky="nsew") #pack(fill='x')
		ttk.Button(rootframe,text='Set Hidden',command=sethide ).grid(row=1,column=2,columnspan=1,sticky="nsew") #pack(fill='x')
		ttk.Entry(rootframe,textvariable=tmpvar).grid(row=2,column=0,columnspan=3,sticky="nsew") #pack(fill='x') #, show='*'
		
		def retv():
		
			global rootframe, tmpvar
			tmp=tmpvar.get().strip()
			
			if tmp=='':
				
				rootframe.destroy()
				return
				
			idb=localdb.DB()
			
			table={}
			
			date_str=app_fun.now_to_str(False)
			table['address_category']=[{'address':addr, 'category':tmp, 'last_update_date_time':date_str}]
			idb.upsert(table,['address','category','last_update_date_time'],{'address':['=',"'"+addr+"'"]})
			
			wallet_details.update_frame(self.prepare_summary_frame()) # update categories
			wallet_details.update_frame(self.prepare_byaddr_frame())
			rootframe.destroy()
			
		ttk.Button(rootframe,text='Enter',command=retv ).grid(row=3,column=0,columnspan=3,sticky="nsew") #pack(fill='x')
			
