######### LATER
# show only current categories

import os, sys
import datetime
import json
import time
# import modules.localdb as localdb
import modules.app_fun as app_fun
import modules.usb as usb
import operator

import modules.aes as aes

import modules.gui as gui
import traceback

WAIT_S=900

class WalDispSet(gui.QObject):
	sending_signal = gui.Signal(list)

	def __init__(self,password=[''], data_files={}, _db_main=None, _db_init=None ):
	
		# self.wallet=wallet
		self.db_main=_db_main
		self.db_init=_db_init
		self.db=data_files['db']+'.db'
		self.wallet=data_files['wallet']+'.dat'
		self.data_files=data_files #self.data_files['db']
	
		super(WalDispSet, self).__init__()
		self.password=password[0]
		self.amount_per_address={}
		self.while_updating=False
			
		self.addr_cat_map={}
		self.update_addr_cat_map()
		self.alias_map={}
		self.grid_lol_select=[]
		self.addr_book_data_refresh()
		self.disp_dict=[]
		self.addr_book_category_alias={}
		self.addr_amount_dict={}
		
		self.is_synced=False
	
	def setSynced(self,bb):
		# print('set wds synced',bb)
		self.is_synced=bb
		
	def update_addr_cat_map(self):
		# idb=localdb.DB(self.db)
		addr_cat=self.db_main.select('address_category',['address','category'] )
		self.addr_cat_map={}
		for rr in addr_cat:
			self.addr_cat_map[rr[0].strip()]=rr[1]
			
		# print('self.addr_cat_map',self.addr_cat_map)
			
			
				
	def show_bills(self,btn,addr):
		table={}
		ddict={'addr':addr}
		table['queue_waiting']=[self.db_main.set_que_waiting('show_bills',jsonstr=json.dumps(ddict) ) ]
								
		# idb=localdb.DB(self.db)
		self.db_main.insert(table,['type','wait_seconds','created_time','command' ,'json','id','status' ])
		
		# self.queue_com.put([ table['queue_waiting'][0]['id'],'Bills for '+addr, self.display_bills])
		
		
		
		
		
		
	# run after new addr created !
	def wallet_copy_progress(self ):
	
		# idb=localdb.DB('init.db')
		tt=self.db_init.select('init_settings',columns=[ "datadir" ])  
		src=os.path.join(tt[0][0],self.wallet)
		
		if app_fun.wallet_copy_progress( src_dir=tt[0][0], add_msg=['Please insert USB/pendrive','To create new address wallet backup to pendrive is required. '], wallet_name=self.data_files['wallet'], gui=gui ):
			# save new hash 
			dat_file=src
			cc=aes.Crypto()
			# db=localdb.DB(self.db)
			last_wallet_hash=self.db_main.select('jsons', ['json_content'],{'json_name':['=',"'backup_wallet_hash'"]})
			last_wallet_hash_arr=json.loads(last_wallet_hash[0][0])
			cur_dat_hash= cc.hash2utf8_1b( cc.read_bin_file( dat_file),1)
			last_wallet_hash_arr.append(cur_dat_hash)
		
			# print('Inserting hash at addr creation after backup',cur_dat_hash) 
			table={}
			table['jsons']=[{'json_name':"backup_wallet_hash", 'json_content':json.dumps(last_wallet_hash_arr), 'last_update_date_time': app_fun.now_to_str(False)}]
			self.db_main.upsert(table,['json_name','json_content','last_update_date_time'],{'json_name':['=',"'backup_wallet_hash'"]})
		 

		

		
	def send_to_addr(self,btn,addr,exampleval=0.0001): 
	
		tmpsignature=self.db_main.get_addr_to_hash(addr)
		
		tmpcat=''
		tmpalia=''
		if hasattr(self,'addr_book_category_alias'):
			if addr in self.addr_book_category_alias:
				tmpcat=self.addr_book_category_alias[addr]['category']
				tmpalia=self.addr_book_category_alias[addr]['alias']
			
		tmp_to=''
		if tmpcat!='':
			tmp_to=tmpcat+', '
		if tmpalia!='':
			tmp_to+=tmpalia
				
		initlabel=gui.Label(None,'Sending to '+tmp_to+'\nAddress: '+addr+'\n')
		
		automate_rowids=[ #[{},{},{},{}] ,
							[{'T':'LabelC', 'L':'From address' },{'T':'LabelC', 'L':'Set max','width':9 },{'T':'LabelC', 'L':'Amount','width':9 },{'T':'LabelC', 'L':'Message (max '+str(int(512-len(tmpsignature)))+' bytes)' },{}] ,
							[{'T':'Button', 'L':'Select...',  'uid':'z1', 'width':32 },{'T':'Button', 'L':'',  'uid':'setmax1', 'width':32 },{'T':'LineEdit','V':'0.0001', 'uid':'a1' , 'valid':{'ttype':float,'rrange':[0,1000000]}},{'T':'LineEdit',   'uid':'m1', 'width':32 },{'T':'LabelV','L':str(int(512-len(tmpsignature)))+' bytes left','uid':'l1'}] 
						]
		
		grid_settings=[]
		for ij,ar in enumerate(automate_rowids):
			tmpdict={}
			tmpdict['rowk']=str(ij)
			tmpdict['rowv']=ar
			grid_settings.append(tmpdict)
			
				
		send_from=gui.Table(None,{'dim':[2,4],'updatable':1, 'toContent':1}) #flexitable.FlexiTable(rootframe,grid_settings)
		send_from.updateTable(grid_settings)
		
		last_addr=self.db_main.get_last_addr_from("'last_book_from_addr'")
		if last_addr not in ['','...']:
			send_from.cellWidget(1,0).setText(last_addr) #set_textvariable( 'z1',last_addr)
			# idb=localdb.DB(self.db)
			disp_dict=self.disp_dict[0][0] #idb.select('jsons',['json_content','last_update_date_time'],{'json_name':['=',"'display_wallet'"]})
			if len(disp_dict)>0:
				disp_dict=json.loads(disp_dict )
				tmpmaxv=disp_dict['addr_amount_dict'][last_addr]['confirmed']+disp_dict['addr_amount_dict'][last_addr]['unconfirmed']-0.0001
				
				send_from.cellWidget(1,1).setText( str(round(tmpmaxv,8)))
				send_from.cellWidget(1,0).setToolTip(last_addr)

				# print(last_addr)
				# print(self.alias_map)
				# print(self.addr_cat_map)
				tmpcat=''
				if last_addr in self.addr_cat_map :
					tmpcat=self.addr_cat_map[last_addr]
				send_from.cellWidget(1,0).setText(tmpcat +','+self.alias_map[last_addr] )
		

		
		
		
		
		
		def select_addr(btn2):
		
			def set_values(btn3,selz,categ,alias,total_amount):
				newtxt= ', '.join([categ,alias])
				
				total_amount=float(total_amount)-0.0001
				send_from.cellWidget(1,0).setText(newtxt)
				send_from.cellWidget(1,0).setToolTip(selz)
				send_from.cellWidget(1,1).setText(str(total_amount))
				# table_frame_tmp.adjustSize()
				btn3.parent().parent().parent().parent().close()
				
			filter_frame=gui.FramedWidgets(None,'Filter')
			filtbox=gui.Combox(None,self.own_wallet_categories()) # #ttk.LabelFrame(selframe,text='Filter')
			filter_frame.insertWidget(filtbox)

			
			addr_list_frame=gui.ContainerWidget(None,layout=gui.QVBoxLayout()) #,'Addresses list')
			print('prepare_byaddr_frame 199' )
			
			grid_lol_select,colnames=self.prepare_byaddr_frame( True,True)
			 
			select_table=gui.Table(None,{'dim':[len(grid_lol_select),len(colnames)], 'toContent':1})
			select_table.updateTable(grid_lol_select,colnames)
			for bii in range( select_table.rowCount()):
				# print('values',select_table.item(bii,7).text())
				select_table.cellWidget(bii,6).set_fun( False, set_values, select_table.item(bii,7).text(), select_table.item(bii,0).text(), select_table.item(bii,1).text(), select_table.item(bii,2).text()  )
			
			addr_list_frame.insertWidget(select_table)
			
			def refresh_add_list(btn4,*eventsargs):
				
				list_frame_tmp=btn4.parent().parent().widgetAt(1) #listframe
				tbltmp=list_frame_tmp.widgetAt(0)
				
				tbltmp.filtering( 'item',0,btn4.currentText() )

			
			filtbox.set_fun(refresh_add_list)  
			gui.CustomDialog(btn2,[filter_frame,addr_list_frame ], title='Select address to send from')
		
		send_from.cellWidget(1,0).set_fun(False,select_addr) #set_cmd( 'z1',[],select_addr)
		send_from.cellWidget(1,2).setText( str(exampleval))
		
		def setmax1(btn,*eventsargs):
			try:
				tmpv=float(send_from.cellWidget(1,1).text())
				send_from.cellWidget(1,2).setText( str(round(tmpv,8)))
			except:
				gui.showinfo("Max amount missing","Please first select sending address!",btn)
		
		send_from.cellWidget(1,1).set_fun(False, setmax1)
								
		def send(btn,asap=False):
		
			tosend=[]
			
			z=send_from.cellWidget(1,0).toolTip().strip() #get_value('z1' ).strip()
			a=send_from.cellWidget(1,2).text().strip() #.get_value('a1').strip()
			m=send_from.cellWidget(1,3).text().strip() #.get_value('m1').strip()
			
			if len(z)>0:				
				if len(a)>0:
					m+=' @zUnderNet'
					
					origlen,m=self.valid_memo_len(m,512-len(tmpsignature),suggest=True)
					m+=tmpsignature
						
					tosend.append({'z':addr,'a':a,'m':m})
						
			if len(tosend)==0:
				gui.showinfo("Nothing to send!","Nothing to send!",btn)
				# rootframe.lift()
				return
		
			ddict={'fromaddr':z,	'to':tosend	} 
			
			table={}
			if asap:
				table['queue_waiting']=[self.db_main.set_que_waiting('send',jsonstr=json.dumps(ddict) ) ]
			else:
				table['queue_waiting']=[self.db_main.set_que_waiting('send',jsonstr=json.dumps(ddict) , wait_seconds=WAIT_S) ]
				
			# idb=localdb.DB(self.db)
			self.db_main.insert(table,['type','wait_seconds','created_time','command' ,'json','id','status' ])
			
			self.db_main.set_last_addr_from( z,"'last_book_from_addr'")
			btn.parent().parent().close() #destroy()
				
	 
		last_buttons=gui.ContainerWidget(None,layout=gui.QHBoxLayout() )
		# last_buttons.insertWidget(gui.Button(None,'+ More rows +',actionFun=more_rows, args=(send ,)) )
		last_buttons.insertWidget(gui.Button(None,'Queue Send',actionFun=send, args=(False, ))   )
		last_buttons.insertWidget(gui.Button(None,'ASAP Send',actionFun=send, args=( True, ) ) )		
		
		gui.CustomDialog(btn,[initlabel,send_from,last_buttons ], title='Sending...', wihi=[512+256,256])
				
		
		
		
		
		
		
		
	# initbytes is address element
	def validate_memo(self,mm_elem,output_elem,initbytes):
	# def validate_memo(self,mm_elem,output_elem,initbytes,eargs=''):
	
		if type(int(1))!=type(initbytes): 
			tmpaddrto=initbytes.text()
			initbytes=512-self.db_main.get_addr_to_hash(tmpaddrto,True)
	
		mm=mm_elem.text() #get()
		try:
		# if True:
			origbytes=len(mm.encode('utf-8')) 
		
			output_elem.setText(str(initbytes-origbytes)+' bytes left')
		except:
			badc=''
			for cc in mm:
				try:
					# print(cc)
					cc.encode('utf-8')
				except:
					badc=cc
					break
			if len(badc)>0:
				gui.showinfo('Bad character in memo input', 'This input contains bad character ['+badc+']:\n'+mm,mm_elem)
			else:
				print('memo validation error?')
		
	
	
	
	
	
	
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
		
	@gui.Slot()	
	def addr_book_data_refresh(self):
		self.addr_book_colnames=['','Usage','Category','Alias','Full address']
		# idb=localdb.DB(self.db)
		sel_addr_book=self.db_main.select('addr_book',[ 'Category','Alias','Address','usage'] ,orderby=[{'usage':'desc'},{'Category':'asc'},{'Alias':'asc' }] )
		
		# print('\n\n\n addr_book_data_refresh',sel_addr_book)
		
		self.grid_lol_select=[]
		self.addr_book_unique_categories=['All']
		if len(sel_addr_book)>0:
			self.addr_book_category_alias={}
			for ii,rr in enumerate(sel_addr_book):
			
				self.addr_book_category_alias[rr[2]]={'category':rr[0], 'alias':rr[1] }
				if rr[0] not in self.addr_book_unique_categories:
					self.addr_book_unique_categories.append(rr[0])
					
				tmpdict={}
				tmpdict['rowk']=str(ii)
				tmpdict['rowv']=[{'T':'Button', 'L':'Select', 'uid':'select'+str(ii)  }, 
						{'T':'LabelV', 'L':str(rr[3]), 'uid':'Usage'+str(ii)  } , 
						{'T':'LabelV', 'L':rr[0], 'uid':'Category'+str(ii)  } , 
						{'T':'LabelV', 'L':rr[1], 'uid':'Alias'+str(ii)  } , 
						{'T':'LabelV', 'L':rr[2], 'uid':'Address'+str(ii)  }
						]
				self.grid_lol_select.append(tmpdict)
				
		# print('self.grid_lol_select',self.grid_lol_select)
		
	def addr_book_select(self):
		
		self.addr_book_data_refresh()
		# print('\n\nreturning',self.grid_lol_select, self.addr_book_colnames)
		return self.grid_lol_select, self.addr_book_colnames
	


	def categories_filter(self):
		
		return self.addr_book_unique_categories
		
			
			
			
			
			
	
	def send_from_addr(self,btn,addr,addr_total):
		# 
		addr_total=round(  addr_total -0.0001,8 )
		
		tmplbl='Sending from address:\n\n'+addr+'\n\nMax. amount (0.0001 fee discounted) '+str(round(addr_total,8))+'\n'
		
		def select_addr(btn2):
			
			def set_values(btn3,selz,categ,alias):
				newtxt= ', '.join([categ,alias])

				table_frame_tmp=btn2.parent().parent()
				crow=btn2.property("rowii")
				table_frame_tmp.cellWidget(crow,1).setText(selz)				# addram=table_frame_tmp.cellWidget(crow,3) # amount 
				# table_frame_tmp.adjustSize()
				btn3.parent().parent().parent().parent().close()
				jj=btn2.count()
				btn2.addItem(newtxt,newtxt)
				btn2.setItemData(jj, newtxt, gui.Qt.ToolTipRole)
				btn2.setCurrentIndex(jj)
			
			booktype=btn2.currentText() #get() # own or adddr book
			if booktype=='Select':
				return
			# print('select_addr',booktype)
			
			filter_frame=gui.FramedWidgets(None ,'Filter') #ttk.LabelFrame(selframe,text='Filter') ,layout=gui.QHBoxLayout()
			
				
			if booktype=='Own address':
				
				filtbox=gui.Combox(None,self.own_wallet_categories()) #ttk.Combobox(filter_frame,textvariable='All',values=self.own_wallet_categories(), state="readonly")
				# print('parent1',filtbox.parent())
				filter_frame.insertWidget(filtbox)
				# print('parent2',filtbox.parent())
				
				addr_list_frame=gui.ContainerWidget(None,layout=gui.QVBoxLayout()) #,'Addresses list')
				# print('parent3',filtbox.parent())
				
				# print('prepare_byaddr_frame 411' )
				grid_lol_select,colnames=self.prepare_byaddr_frame( True,True, True)
				 
				select_table=gui.Table(None,{'dim':[len(grid_lol_select),len(colnames)], 'toContent':1})
				select_table.updateTable(grid_lol_select,colnames)
				for bii in range( select_table.rowCount()):
					# print('values',select_table.item(bii,7).text())
					select_table.cellWidget(bii,6).set_fun( False, set_values, select_table.item(bii,7).text(), select_table.item(bii,0).text(), select_table.item(bii,1).text())
				 
				addr_list_frame.insertWidget(select_table)
				
				def refresh_add_list(btn4,*eventsargs):
					
					list_frame_tmp=btn4.parent().parent().widgetAt(1) #listframe
					tbltmp=list_frame_tmp.widgetAt(0)
					
					tbltmp.filtering( 'item',0,btn4.currentText() )

				
				filtbox.set_fun(refresh_add_list)  
				gui.CustomDialog(btn2,[filter_frame,addr_list_frame ], title='Select address to send to')
				# del filter_frame
				# print('parent4',filtbox.parent())
				
			else:
				# print('# address book  categories_filter')
				filtbox=gui.Combox(None,self.categories_filter()) #ttk.Combobox(filter_frame,textvariable='All',values=self.categories_filter(), state="readonly")
				filter_frame.insertWidget(filtbox)
				
				# tmpdict={}
				# colnames=['','Usage','Category','Alias','Full address']	
				
				list_frame=gui.FramedWidgets(None,'Addresses list') #ttk.LabelFrame(selframe,text='Addresses list')
				
				
				grid_lol_select,colnames=self.addr_book_select()
				
				select_table=gui.Table(None,{'dim':[len(grid_lol_select),5], 'toContent':1} ) #flexitable.FlexiTable(list_frame,grid_lol_select)
				select_table.updateTable(grid_lol_select,colnames)
				for bii in range( select_table.rowCount()):
					select_table.cellWidget(bii,0).set_fun( False, set_values, select_table.item(bii,4).text(),select_table.item(bii,2).text(),select_table.item(bii,3).text())
					
				list_frame.insertWidget(select_table)
				 
				def update_filter(btn5,*someargs):
					
					list_frame_tmp=btn5.parent().parent().widgetAt(1) #listframe
					tbltmp=list_frame_tmp.widgetAt(0)
					
					tbltmp.filtering( 'item',2,btn5.currentText() )
					
				filtbox.set_fun(update_filter )
				
				gui.CustomDialog(btn2,[filter_frame,list_frame], title='Select address to send to')
			
		#
		# TOTO SENDING 
		#		
			
		def setmin(btn2):
			rowii=btn2.property('rowii')
			tbl=btn2.parent().parent()
			tbl.cellWidget(rowii,3).setText(str( 0.0001))	
			
			
			
			
			
		def setmax(btn2):
			rowii=btn2.property('rowii')
			tbl=btn2.parent().parent()
			# print('setmax',tbl,tmprr)
			tbl.cellWidget(rowii,3).setText(str(  addr_total  ))
			
			
			
			
		def send(btn2,asap=False,send_from=None):
			# print('send')
			# global tmpid, tmprowid #, send_from
			tosend=[]
			sending_amount=0
			for ii in range(send_from.rowCount()):
				# tmpstr=str(ii+1)
				
				z=send_from.cellWidget(ii ,1).text().strip()  #get_value('z'+tmpstr).strip()
				a=send_from.cellWidget(ii ,3).text().strip()  #.get_value('a'+tmpstr).strip()
				m=send_from.cellWidget(ii ,4).text().strip()  #.get_value('m'+tmpstr).strip()
				
				
				
				if len(z)>0:				
					if len(a)>0:
						sending_amount+=float(a)
						m+=' @zUnderNet'
						tmpsignature=self.db_main.get_addr_to_hash(z)
						origlen,m=self.valid_memo_len(m,512-len(tmpsignature),suggest=True)
						m+=tmpsignature
						tosend.append({'z':z,'a':a,'m':m})
						
			if sending_amount>addr_total:
				gui.showinfo("Wrong total amount!","Total amount to send is exceeding address balance: "+str(sending_amount)+' > '+str(addr_total)+'\nPlease correct!',send_from)
				return
						
			if len(tosend)==0:
				
				gui.showinfo("Nothing to send!","Nothing to send!",send_from)
				btn2.parent().parent().close() 
				return
		
			ddict={'fromaddr':addr,	'to':tosend	}
			table={}
			if asap:
				table['queue_waiting']=[self.db_main.set_que_waiting('send',jsonstr=json.dumps(ddict) ) ]
			else:
				table['queue_waiting']=[self.db_main.set_que_waiting('send',jsonstr=json.dumps(ddict) , wait_seconds=WAIT_S) ]
				
			# idb=localdb.DB(self.db)
			self.db_main.insert(table,['type','wait_seconds','created_time','command' ,'json','id','status' ])
			
			btn2.parent().parent().close()  
			self.sending_signal.emit(['cmd_queue'])
			
		colnames=['Book type','Address to','Set max/min','Amount','Message (max 512 bytes)','Bytes left (with signature)']
	
		automate_rowids=[ 
							{'rowk':'from0', 'rowv':[{'T':'Combox','V':['Select','Own address','Address book'],'uid':'b1', 'fun':select_addr,'every_click':1 },{'T':'LineEdit',   'uid':'z1' },{'T':'Button', 'L':str(round(addr_total,8)), 'fun':setmax, 'width':16 },{'T':'LineEdit','L':'Amount', 'valid':{'ttype':float,'rrange':[0,addr_total]} },{'T':'LineEdit', 'L':'Message','valid':{'ttype':'custom','rrange':[self.validate_memo,5,1]} },{'T':'LabelV','L':'473 bytes left','uid':'l1'}] } ,
							
							{'rowk':'from1', 'rowv':[{'T':'Combox','V':['Select','Own address','Address book'],'uid':'b2', 'fun':select_addr,'every_click':1 },{'T':'LineEdit',   'uid':'z2' },{'T':'Button', 'L':str(0.0001), 'fun':setmin, 'width':16 },{'T':'LineEdit','L':'Amount', 'valid':{'ttype':float,'rrange':[0,addr_total]} },{'T':'LineEdit', 'L':'Message','valid':{'ttype':'custom','rrange':[self.validate_memo,5,1]} },{'T':'LabelV','L':'473 bytes left','uid':'l2'}] } ,
							{'rowk':'from2', 'rowv':[{'T':'Combox','V':['Select','Own address','Address book'],'uid':'b3', 'fun':select_addr,'every_click':1 },{'T':'LineEdit',   'uid':'z3' },{'T':'Button', 'L':str(0.0001), 'fun':setmin, 'width':16 },{'T':'LineEdit','L':'Amount', 'valid':{'ttype':float,'rrange':[0,addr_total]}  },{'T':'LineEdit','L':'Message', 'valid':{'ttype':'custom','rrange':[self.validate_memo,5,1]} },{'T':'LabelV','L':'473 bytes left','uid':'l3'}] } ,
							
						]
						
		send_from=gui.Table(None,{'dim':[3,6],'updatable':1, 'toContent':1}) #flexitable.FlexiTable(rootframe,grid_settings)
		send_from.updateTable(automate_rowids,colnames)
		
		def more_rows(btn2,send_from):
			widgets_dict=[]
			tmpcc=send_from.rowCount()
			defrr={'rowk':'fromii', 'rowv':[{'T':'Combox','V':['Select','Own address','Address book'], 'fun':select_addr,'every_click':1 },{'T':'LineEdit' },{'T':'Button', 'L':str(0.0001), 'fun':setmin, 'width':16 },{'T':'LineEdit','L':'Amount', 'valid':{'ttype':float,'rrange':[0,addr_total]} },{'T':'LineEdit', 'L':'Message','valid':{'ttype':'custom','rrange':[self.validate_memo,5,1]} },{'T':'LabelV','L':'473 bytes left' }] }
			for ii in range(5):
				defrr['rowk']='from'+str(ii+tmpcc)
				widgets_dict.append(defrr.copy())
		
			# print()
			send_from.updateTable( widgets_dict, insert_only=True)
	 
		last_buttons=gui.ContainerWidget(None,layout=gui.QHBoxLayout() )
		last_buttons.insertWidget(gui.Button(None,'+ More rows +',actionFun=more_rows, args=(send_from,)) )
		last_buttons.insertWidget(gui.Button(None,'Queue Send',actionFun=send, args=(False, send_from ))   )
		last_buttons.insertWidget(gui.Button(None,'ASAP Send',actionFun=send, args=( True,  send_from ) ) )
		
		
		rootframe =gui.CustomDialog(btn,[gui.Label(None,tmplbl) , send_from, last_buttons ], title='Sending...', wihi=[1024,512])
		
		
		
		
		
		
	# from def exported file / might be encrypted
	# from other source file
	# manual entry - text area 
	def import_priv_keys(self,btn):
		# [{'T':'Button', 'L':'Load from file' }, {'T':'LabelV', 'L':''  } ] ,
							# [{'T':'LineEdit', 'span':2 } , { } ] , # 
		w0=gui.Button(None,'Load from file')
		w0.setMaximumWidth(128)
		w1=gui.Label(None,'...')
		w2=gui.LineEdit(None)
		w2.setMaximumWidth(256)
		
		w3=gui.Table(None,{'dim':[1,1],'toContent':1 })
		w3.updateTable([[{'T':'LabelV' }]])
		# w3.setMaximumWidth(512)
		# w3=gui.Label(None,'')
		w4=gui.Button(None,'Import')
		w4.setMaximumWidth(128)
			
		
		def setfile(btn2,lbl,lblk):	
			gui.set_file( lbl , dir=False,parent=btn2 , title="Select file with private keys")
			
			def trysplit(tmpstr):
				try:
					tmpstr2=json.loads(tmpstr)
					retv=''
					for kk,vv in tmpstr2.items():
						retv+=vv.replace('\r','').replace('\\n','').replace('\\r','')
					# print(retv)
					return retv
				except:
					pass
			
				c=[',',';','\r'] #separators
				best=1
				ci='\n'
				for cc in c:
					tmp=tmpstr.split(cc)
					if len(tmp)>best:
						best=len(tmp)
						ci=cc
				if ci!='\n':
					return tmpstr.replace(ci,'\n')
				else:
					return tmpstr
			
			# try to unpack or read
			# 1. encrypted - aks password json.dumps({'iv':iv, 'ct':ct})
			path1=lbl.text()
			if len(path1)>1:
				if os.path.exists(path1):
					rstr=''
					with open(path1, "r", encoding="utf-8") as f:
						rstr = f.read()
					keys=''	
					if 'iv' in rstr and 'ct' in rstr:
						# print('decrypt')
						
						try:
							# print('set LabelV')
							tmpval=[]
							gui.PassForm(tmpval, first_time=False, parent = btn2,  title="Enter password to decrypt file")
							if len(tmpval)>0:
								cc=aes.Crypto()
								keys=cc.aes_decrypt_file( path1,None,tmpval[0])
								if keys==False:
									1/0
									
								keys=trysplit(keys)
								lblk.setText(keys)		
								# lblk.setToolTip(keys)	
							else:
								1/0
						except:
							gui.showinfo('Could not decrypt file','File '+path1+' does not contain encrypted address or view key or you have wrong password!', btn2)
							lblk.setText('')		
							lbl.setText('')
					else:
						keys=trysplit(rstr)
						lblk.setText(keys)
			
		w0.set_fun(False,setfile,w1,w3.item(0,0))
				
		w2.setEventFilter(w3.item(0,0))
				
		# \n \r problem 		
				
		def import_keys(btn3,lbl):
			tmpstr=lbl.text().split('\n')
			keys=[]
			for kk in tmpstr:
				if len(kk)>50:
					keys.append(kk)
					
			# print('importing',keys)		
			ddict={'keys': keys	}
			table={}
			table['queue_waiting']=[self.db_main.set_que_waiting('import_priv_keys',jsonstr=json.dumps(ddict) ) ]
			
			# idb=localdb.DB(self.db)
			self.db_main.insert(table,['type','wait_seconds','created_time','command' ,'json','id','status' ])
			
			expo=btn3.parent().parent()
			expo.close() #.parent()
				
		w4.set_fun(False,import_keys,w3.item(0,0))
		
		gui.CustomDialog(btn,[w0,w1,w2,w3,w4], title='Import Private keys',wihi=[512,256])

		
		
		
		
		
		
	def merge_utxo(self,btn):

		def set_to(btn3,selz,categ,alias):
			ttable=btn3.parent().parent()
			btn3.setText(u"\u2611")
			for bii in range( ttable.rowCount()):
				if ttable.cellWidget(bii,6)==btn3:
					continue
					
				ttable.cellWidget(bii,6).setText(u"\u2610")
			
			# print(selz,categ,alias)
			
		def set_values(btn3,selz,categ,alias):
			if btn3.text()==u"\u2610":
				btn3.setText(u"\u2611")
			else:
				btn3.setText(u"\u2610")
			# print(selz,categ,alias)

		filter_frame=gui.FramedWidgets(None ,'Filter addresses to merge FROM') #ttk.LabelFrame(selframe,text='Filter') ,layout=gui.QHBoxLayout()
		filtbox=gui.Combox(None,self.own_wallet_categories()) 
		filter_frame.insertWidget(filtbox)
		
		
		filter_to=gui.FramedWidgets(None ,'Filter address to merge TO') #ttk.LabelFrame(selframe,text='Filter') ,layout=gui.QHBoxLayout()
		filtbox2=gui.Combox(None,self.own_wallet_categories()) 
		filter_to.insertWidget(filtbox2)
		
		addr_list_frame=gui.FramedWidgets(None,'Select addresses to merge FROM',layout=gui.QVBoxLayout()) 
		
		# print('prepare_byaddr_frame 726' )
		grid_lol_select,colnames=self.prepare_byaddr_frame( True,True, True)
		 
		select_table=gui.Table(None,{'dim':[len(grid_lol_select),len(colnames)], 'toContent':1})
		select_table.updateTable(grid_lol_select,colnames)
		
		
		select_to=gui.Table(None,{'dim':[len(grid_lol_select),len(colnames)], 'toContent':1})
		select_to.updateTable(grid_lol_select,colnames)
		
		# btn actions 
		for bii in range( select_table.rowCount()):
			select_table.cellWidget(bii,6).set_fun( False, set_values, select_table.item(bii,7).text(), select_table.item(bii,0).text(), select_table.item(bii,1).text())
			select_table.cellWidget(bii,6).setText(u"\u2610")
			select_table.cellWidget(bii,6).setStyleSheet('QPushButton {padding:0px;font-size:22px;}')
			
			
			select_to.cellWidget(bii,6).set_fun( False, set_to, select_table.item(bii,7).text(), select_table.item(bii,0).text(), select_table.item(bii,1).text())
			select_to.cellWidget(bii,6).setText(u"\u2610")
			select_to.cellWidget(bii,6).setStyleSheet('QPushButton {padding:0px;font-size:22px;}')
		 
		addr_list_frame.insertWidget(select_table)
		
		
		def select_all(btn,args):
			# print(args)
			tmpico=u"\u2611"
			if btn.text()=='Select all':
				btn.setText('Deselect all')
			else:
				tmpico=u"\u2610"
				btn.setText('Select all')
				
			for bii in range( args.rowCount()):
				if args.isRowHidden(bii):
					continue
				args.cellWidget(bii,6).setText(tmpico)
			
		buttons=gui.ContainerWidget(None,layout=gui.QHBoxLayout() )
		
		btn_all=gui.Button(None,'Select all',actionFun=select_all,args=[select_table])
		buttons.insertWidget(btn_all)
		
		lbllimit=gui.Label(None,'Input limit: ','20 for slow machines, 200 for very fast')
		# lbllimit.setStyleSheet('QWidget QLabel {text-align:right;float:right;color:red;}')
		lbllimit.setAlignment(gui.Qt.AlignRight | gui.Qt.AlignVCenter);
		llimit=gui.Combox(None,['20','50','100','200'])
		buttons.insertWidget(lbllimit)
		buttons.insertWidget(llimit)
		
		addr_list_frame.insertWidget(buttons)
		
		
		def refresh_add_list(btn4,tmp_table):
			tmp_table.filtering( 'item',0,btn4.currentText() )
		
		filtbox.set_fun(refresh_add_list,select_table)  
		filtbox2.set_fun(refresh_add_list,select_to)  
		# 
		grid=gui.ContainerWidget(None)
		grid.insertWidget( filter_frame, 0, 0)
		grid.insertWidget( addr_list_frame, 1, 0)
		grid.insertWidget( filter_to, 0, 1)
		
		addr_list_frame_to=gui.FramedWidgets(None,'Select addresses to merge TO',layout=gui.QVBoxLayout()) 
		addr_list_frame_to.insertWidget(select_to)
		
		def merge(btn5,t1,li,t2):
			from_addr=[]
			to_addr=''
			for bii in range( t1.rowCount()):
				if t1.cellWidget(bii,6).text()==u"\u2611":
					from_addr.append(t1.item(bii,7).text())
				
				if t2.cellWidget(bii,6).text()==u"\u2611":
					to_addr=t2.item(bii,7).text()
					
			if len(from_addr)==0:
				gui.messagebox_showinfo('Merge canceled','Missing FROM addresses - none was selected.',btn5)
				return
				
			if to_addr=='':
				gui.messagebox_showinfo('Merge canceled','Missing TO addresses - none was selected.',btn5)
				return
				
			lim=li.currentText()
		
			# print(from_addr,from_addr,lim)
			merge_type='merge'
			wait_seconds_tmp=0
			if 'Auto' in btn5.text():
				merge_type='automerge'
				wait_seconds_tmp=900
			
			ddict={'fromaddr':from_addr, 'limit':int(lim)	,'to': to_addr 	} #,'to':'"'+to_addr+'"'	}
			table={}
			# if asap:
			table['queue_waiting']=[self.db_main.set_que_waiting(merge_type,jsonstr=json.dumps(ddict), wait_seconds=wait_seconds_tmp ) ]
			# else:
				# table['queue_waiting']=[localdb.set_que_waiting('send',jsonstr=json.dumps(ddict) , wait_seconds=WAIT_S) ]
			# print(table)
			# idb=localdb.DB(self.db)
			self.db_main.insert(table,['type','wait_seconds','created_time','command' ,'json','id','status' ])
			self.sending_signal.emit(['cmd_queue'])
			
			btn5.parent().parent().parent().parent().close()
		
		btn_merge=gui.Button(None,'Merge once',actionFun=merge,args=[select_table,llimit,select_to],tooltip='It will take number of inputs not bigger then limit set.')
		btn_merge_auto=gui.Button(None,'Auto-merge',actionFun=merge,args=[select_table,llimit,select_to],tooltip='Merging will work each time limit threshold is reached, but not sooner then 15 min after GUI is ON and not more often then every 15 minutes.\nYou can cancel it in the task queue.')
		buttons2=gui.ContainerWidget(None,layout=gui.QHBoxLayout() )
		buttons2.insertWidget( btn_merge)
		buttons2.insertWidget( btn_merge_auto)
		addr_list_frame_to.insertWidget(buttons2)
		
		grid.insertWidget( addr_list_frame_to, 1, 1)
		
		gui.CustomDialog(btn,[grid  ], title='Merging setup')
		# todo: deamon side -
		# test
		# add automation 
		
		
		
		
		
		
		
		
				
				
	def export_wallet(self,btn): # export encrypted wallet or encrypted priv keys and addresses
			
		automate_rowids=[ [{'T':'Button', 'L':'Select folder' }, {'T':'LabelV', 'L':str(os.getcwd()) } ] ,
							[{'T':'LabelC', 'L':'Export type: ' } , {'T':'Combox', 'V':['Wallet','Database','Private keys']  } ] , # 
							[{'T':'Button', 'L':'Enter',  'span':2  }, {}] 
						]
						
		expo=gui.Table(None,{'dim':[3,2]}) #flexitable.FlexiTable(rootframe,grid_settings)
		expo.updateTable(automate_rowids)
		# rootframe.insertWidget(expo)
		
		def setdir_and_lift(btn2,arg):
			
			gui.set_file( arg , dir=True,parent=btn2 , title="Select folder to export wallet")
			
		expo.cellWidget(0,0).set_fun(False,setdir_and_lift,expo.item(0,1))
		
		def enter(btn3):
			expo=btn3.parent().parent()
			ddict={'path':expo.item(0,1).text( ), #get_value('selected'),
					'opt':expo.cellWidget(1,1).currentText( ) #expo.get_value('opt')
					}
				
			# print(ddict)	
			if ddict['opt']=='Wallet' or ddict['opt']=='Database' :
			
				# idb=localdb.DB('init.db')
				ppath=self.db_init.select('init_settings',['datadir'] )
				
					
				pfrom=os.path.join(ppath[0][0],self.wallet)
				
				if ddict['opt']=='Database':				
					pfrom=os.path.join(os.getcwd(),self.db) #'/wallet.dat'
					ddict['opt']=self.db
					if not os.path.exists(pfrom):
						gui.messagebox_showinfo('Error - file missing ...','Failed! Database file missing - '+self.data_files['db']+'.db',expo)
						expo.parent().close()
						return 
				else:
					ddict['opt']=self.wallet
					
					if not os.path.exists(pfrom):
						
						ddict['opt']=self.data_files['wallet']+'.encr'
						pfrom=os.path.join(ppath[0][0],ddict['opt'])
				
				
				tmp_to=ddict['opt'].replace('.dat','.encr').replace('.db','.encr').replace('.','_'+app_fun.now_to_str(True)+'.')
				pto=os.path.join(ddict['path'], tmp_to)
				# pto=ddict['path']
				
				cc=aes.Crypto()

				if ddict['opt']==self.data_files['wallet']+'.encr' or gui.msg_yes_no("Encrypt exported file with your password?", "If you make a backup for yourself 'yes' is good option. If you share or sell the file better select 'no' since sharing personal passwords is not a good practice.",btn3):
					# pto=os.path.join(pto, tmp_to)
					cc.aes_encrypt_file( pfrom, pto  , self.password) #ddict['path']+'/wallet.encr'
					gui.messagebox_showinfo('File exported to ',pto,expo)
				
				elif gui.msg_yes_no("Encrypt exported file with new password?", "Encrypt exported file with new password? Only hit 'no' if you really do not need encryption for this export.",btn3):
					tmppass=cc.rand_password(32)
					# pto=os.path.join(pto, tmp_to ) #replace('.','_'+app_fun.now_to_str(True)+'.')
					cc.aes_encrypt_file( pfrom,pto  , tmppass) #ddict['path']+'/wallet.encr'
					gui.output_copy_input(btn3,'Password for file exported to \n'+pto,(tmppass,))
				else:
					# pto=os.path.join(pto,ddict['opt']).replace('.','_'+app_fun.now_to_str(True)+'.')
					# shutil.copyfile(pfrom, pto ) #ddict['path']+'/wallet.dat'
					gui.copy_progress(pfrom,'Exporting file to '+pto,pfrom,pto)
					# gui.messagebox_showinfo('File exported to ',pto,expo)
						
				expo.parent().close()
				return
			else: #export priv keys 

				if gui.msg_yes_no("Encrypt private keys with your password?", "If you make a backup for yourself 'yes' is good option. If you share or sell the wallet better select 'no' since sharing personal passwords is not good practice."):
					ddict['password']='current'
					
				elif gui.msg_yes_no("Encrypt private keys with new random password?", "Encrypt private keys with new random password? Only hit 'no' if you really do not need security for this export."):
					ddict['password']='random'
					
				else:
					ddict['password']='no'
					
					
			table={}
			table['queue_waiting']=[self.db_main.set_que_waiting('export_wallet',jsonstr=json.dumps(ddict) ) ]
			
			# idb=localdb.DB(self.db)
			self.db_main.insert(table,['type','wait_seconds','created_time','command' ,'json','id','status' ])
			
			# rootframe.destroy()
			expo.parent().close() #.destroy()
		
		# expo.set_cmd( 'enter',[],enter)
		expo.cellWidget(2,0).set_fun(False,enter )
		rootframe =gui.CustomDialog(btn,expo, title='Exporting wallet')
		
		
		
		
		
		
		
		
		
		
		
	def export_addr(self,btn,addr):
	
		automate_rowids=[ 
							[{'T':'LabelC', 'L':'Export type: ' } , {'T':'Combox', 'V':['display on screen','encrypted file'],'width':23 } ] ,
							[{'T':'Button', 'L':'Enter','span':2  }, {}] 
						]

										
		expo=gui.Table(None,{'dim':[2,2]}) #flexitable.FlexiTable(rootframe,grid_settings)
		expo.updateTable(automate_rowids)
		# rootframe.insertWidget(expo)
		
		def enter(btn2):
			# global rootframe, expo
			expo=btn2.parent().parent()
			# print(btn2.parent(),btn2.parent().parent())
			if expo.cellWidget(0,1).currentText()=='display on screen': #expo.get_value('opt')=='display on screen':
				gui.output_copy_input(btn2,'Address' ,(addr,))
			
			else: # to file 
			
				# path=filedialog.askdirectory(initialdir=os.getcwd(), title="Select directory to write to")
				path=gui.set_file( None,validation_fun=None,dir=True,parent=btn2,init_path=os.getcwd(),title="Select directory to write to")
				if path==None:
					return 

				cc=aes.Crypto()

				tmppass=cc.rand_password(32)
				pto=os.path.join(path,'addr_'+app_fun.now_to_str()+'.txt') #path+'/addr_'+app_fun.now_to_str()+'.txt'
				# json.dumps({'addr':addr })
				cc.aes_encrypt_file( json.dumps({'addr':addr }), pto  , tmppass) #ddict['path']+'/wallet.encr'
				gui.output_copy_input(btn2,'Password for file exported to '+pto,(tmppass,) )
				
			expo.parent().close() #.destroy()

		
		expo.cellWidget(1,0).set_fun(False,enter) #set_cmd( 'enter',[],enter)
		
		rootframe =gui.CustomDialog(btn,expo, title='Exporting address')
		
		
		
	# encrypt with random password and present the password , save the pass in db 
	# ask where t odrop the file 
	def export_viewkey(self,btn,addr):
		
		automate_rowids=[ 
							[{'T':'LabelC', 'L':'Export type: ' } , {'T':'Combox', 'V':['encrypted file','display on screen']  } ] ,
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
					'path':'',
					'password':''
					}
				
			if expo.cellWidget(0,1).currentText()=='encrypted file':
				# path=filedialog.askdirectory(initialdir=os.getcwd(), title="Select directory to write to")
				path=gui.set_file( None,validation_fun=None,dir=True,parent=btn2,init_path=os.getcwd(),title="Select directory to write to")
				if path==None:
					return 
					
				cc=aes.Crypto()

				ddict={'addr':addr,
						'path':path,
						'password':cc.rand_password(32)
						}
					
			table['queue_waiting']=[self.db_main.set_que_waiting('export_viewkey',jsonstr=json.dumps(ddict)) ]
			# idb=localdb.DB(self.db)
			self.db_main.insert(table,['type','wait_seconds','created_time','command' ,'json','id','status' ])
			expo.parent().close() #.destroy()
			
					
		# expo.set_cmd( 'enter',[],enter)
		expo.cellWidget(1,0).set_fun(False,enter) #set_cmd( 'enter',[],enter)
		rootframe =gui.CustomDialog(btn,expo, title='Exporting view key')
		
	
	
		
		
		
	def new_addr(self,btn):
		
		uu=usb.USB()
		
		while len(uu.locate_usb())==0:
			if not gui.msg_yes_no('Please insert USB pendrive','To create new address wallet backup to pendrive is required. Click [yes] when you are read or [no] to cancel.',btn):
				return
		
		############### new addr setup
		
		
		automate_rowids=[ [{'T':'LabelV', 'L':'Number of addresses to create: ',  'style':{'bgc':'#eee','fgc':'red'} },{'T':'LineEdit', 'V':'1','valid':{'ttype':int, 'rrange':[1,9999]}} ] ,
						[{'T':'LabelV', 'L':'Category for new addresses: ', 'style':{'bgc':'#eee','fgc':'red'} },{'T':'LineEdit', 'V':''} ],
						[{'T':'LabelV', 'L':'Set category counter' },{'T':'Combox','V':['No','Yes'] } ] ,
						[{'T':'LabelV', 'L':'Address from new seed' },{'T':'Combox','V':['No (better for wallet performance)','Yes (better for privacy when sharing a viewing key)'] } ] ,
						[{'T':'Button', 'L':'Create', 'span':2}   ] 
						]
		
		tw=gui.Table( params={'dim':[5,2],"show_grid":False, 'colSizeMod':[ 'toContent','toContent'], 'rowSizeMod':['toContent','toContent' ]})		
		tw.updateTable(automate_rowids)
		
		
		def create_addr(btn_c,addr_num,addr_cat,addr_cat_counter, new_seed):
			# print ('create_addr wds ')
			addr_num, addr_cat, addr_cat_counter, new_seed =addr_num.text().strip(), addr_cat.text().strip(), addr_cat_counter.currentText(), new_seed.currentText()
		
			# idb=localdb.DB(self.db)
			
			if addr_cat_counter=='No': 	addr_cat_counter=False
			else: addr_cat_counter=True
			
			if 'No' in new_seed: new_seed=False
			else: new_seed=True 
				
			table={}
			table['queue_waiting']=[global_db.set_que_waiting('new_addr', json.dumps({'addr_count':int(addr_num),'addr_cat':addr_cat,'addr_cat_counter':addr_cat_counter, 'new_seed':new_seed}) ) ]
 
			self.db_main.insert(table,['type','wait_seconds','created_time','command' ,'json','id','status' ])

			btn_c.parent().parent().parent().close() #.destroy()
			
		tw.cellWidget(4,0).set_fun(False, create_addr, tw.cellWidget(0,1), tw.cellWidget(1,1), tw.cellWidget(2,1), tw.cellWidget(3,1)) 
		
		gui.CustomDialog(btn,tw, title='New address setup', defaultij=[4,0])
		
		
		
	
	def prepare_queue_frame(self,init=False):	

		
		# print('preparing prepare_queue_frame' )
		# idb=localdb.DB(self.db)
		grid_lol3=[]
		tmpdict2={}
		colnames=['Task','Created time','Status','Wait[s]','Cancel']
		
		# print('22 os.path.exists(self.db)',os.path.exists(self.db) )
		disp_dict=self.db_main.select('queue_waiting', ["command","created_time","status","wait_seconds","json","id"],orderby=[{'created_time':'desc' }])
		# print(disp_dict)
		
		
		def cancell(btn,id):
		
			# print(btn,id)
			# if True:
			try:
				disp_dict=self.db_main.select('queue_waiting', ["type","command","created_time","status","wait_seconds","json","id"],{'id':['=',id]})
				# print('disp_dict',disp_dict)
				if len(disp_dict)>0:
					table={}	
					if disp_dict[0][3]!='done':
						
						table['queue_done']=[{"type":disp_dict[0][0]
										, "wait_seconds":disp_dict[0][4]
										, "created_time":disp_dict[0][2]
										, "command":disp_dict[0][1]
										, "json":disp_dict[0][5]
										, "id":disp_dict[0][6]
										, "result":'canceled'
										, 'end_time':app_fun.now_to_str(False)
										} ]
						self.db_main.insert(table,["type","wait_seconds","created_time","command","json","id","result",'end_time'])
				
				# print('before delete',idb.select('queue_waiting'))
				self.db_main.delete_where('queue_waiting',{'id':['=',id]})
				# self.sending_signal.emit(['cmd_queue']) # dead loop
				
			except:
				traceback.print_exc()
				print(792,'cancel exception')
				pass # double click cancell error
		
		# to have result check second table for status done 
		if len(disp_dict)>0:		
		
			for ii,rr in enumerate(disp_dict):
			
				# print(ii,rr)
			
				tmpid=rr[5] #ii #rr[5]
				status_label={'T':'LabelV', 'L': rr[2] }
				
				if rr[2]=='awaiting_balance':
					status_label={'T':'LabelV', 'L': rr[2] , 'style':{'bgc':'yellow','fgc':'brown'} }
				elif rr[2]=='processing':
					status_label={'T':'LabelV', 'L': rr[2] , 'style':{'bgc':'blue','fgc':'white'} }
				elif rr[2]=='done':
					sstyle={'bgc':'white','fgc':'#aaa'}
					task_done=self.db_main.select('queue_done', ['result'],{'id':['=',tmpid]})
					
					tmpres=' no results yet ... '
					if len(task_done)>0: 
						tmp_res=task_done[0][0].lower()
						if 'false' in tmp_res or 'failed' in tmp_res or 'error' in tmp_res :
							sstyle={'bgc':'red','fgc':'#ccc'}
							tmpres=app_fun.json_to_str(task_done[0][0]) #task_done[0][0]
						elif 'success' in tmp_res or 'true' in tmp_res :
							sstyle={'bgc':'green','fgc':'#fff'}
							tmpres='Success/True'
							
				
					status_label={'T':'LabelV', 'L': rr[2] , 'style':sstyle, 'tooltip':tmpres }
				
				tmpdict2={}
				tmptooltip='' 
				if rr[0]=='send':
					ttmp=json.loads(rr[4])

					tmptooltip='From address\n'+ttmp['fromaddr']+'\nto:\n'
					for ss in ttmp['to']:
						tmptooltip+=ss['z']+' amount '+str(ss['a'])+'\n'
				else:
					tmptooltip=app_fun.json_to_str( rr[4] )
					
				total_s=str(int( int(rr[3])-(datetime.datetime.now()-app_fun.datetime_from_str(rr[1]) ).total_seconds() ))
				# if rr[0]=='automerge':
					# total_s='0'
				
				tmpdict2['rowk']=str(tmpid)
				tmpdict2['rowv']=[ {'T':'LabelV', 'L':rr[0], 'tooltip':tmptooltip },
									{'T':'LabelV', 'L': rr[1].replace(' ','\n') , 'width':12},
									status_label,
									{'T':'LabelV', 'L':total_s  },
									{'T':'Button', 'L': 'Cancel', 'fun':cancell, 'args':(str(tmpid),) }	
									# , 'fun':self.edit_category, 'args':(tmpalias,tmpaddr)
								]
				grid_lol3.append(tmpdict2)
				
		# print('DONE preparing prepare_queue_frame' )
		
		return grid_lol3,colnames


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

		
	# set_format->	get_rounding_str -> idb -> set_rounding_str
	def set_format(self,format_str_value=''):
		# print('setting format',format_str_value)
		self.format_str=self.get_rounding_str(direct_value=format_str_value)
		# print('setting format',self.format_str)
	
			
		
		
	def get_rounding_str(self,strval=False,direct_value=''): # if direct value dont take from db 
		format_str=",.0f"
		
		if direct_value!='':
			# print('get_rounding_str',self.set_rounding_str(direct_value))
			return self.set_rounding_str(direct_value)
		
		# idb=localdb.DB(self.db)
		if self.db_main.check_table_exist('wallet_display'):
			rounding=self.db_main.select('wallet_display',['value'],{'option':['=',"'rounding'"]})
				
			if len(rounding)>0:
				rounding=rounding[0][0]
				if strval: return rounding
				
				format_str=self.set_rounding_str(rounding)
					
		if strval: return ''
		
		return format_str
		
		
		
		
	def get_options(self,strval=False):
		# idb=localdb.DB(self.db)
		retdict={'sorting':'amounts','filtering': 'All','rounding':'0.0001' } #",.4f"
		opt=self.db_main.select('wallet_display',['option','value'],{'option':[' in ',"('sorting','filtering','rounding')"]} )
		# print('opt',opt)
		for oo in opt:
			retdict[ oo[0] ] = oo[1]
		
		if not strval:
			retdict['rounding']=self.set_rounding_str(retdict['rounding'])
	
		# print('retdict',retdict)
	
		return retdict
		
		
		
	

		

	def own_wallet_categories(self):
	
		all_cat_unique=['Excluded','Not hidden','All','Hidden','Edit']
		all_cat=list(set(self.addr_cat_map.values() ))
		# print(all_cat)
		for rr in all_cat: 
			if rr not in all_cat_unique:
				
				all_cat_unique.append(rr )
			 
			
		return sorted(all_cat_unique)


	
	def lock_basic_frames(self):
		self.while_updating=True
		
	def unlock_basic_frames(self):
		self.while_updating=False
		
	def is_locked(self):
		return self.while_updating
		
		
		
		
	def set_disp_dict(self):
		# idb=localdb.DB(self.db)
		self.disp_dict=self.db_main.select('jsons',['json_content','last_update_date_time'],{'json_name':['=',"'display_wallet'"]})
		if len(self.disp_dict)==0: return
		tmp_disp_dict=json.loads(self.disp_dict[0][0])
		self.alias_map=tmp_disp_dict['aliasmap']
		
		self.addr_amount_dict=tmp_disp_dict['addr_amount_dict'] #=self.addr_amount_dict #self.addr_amount_dict[aa]={'confirmed':amount_init,'unconfirmed':am_unc,'#conf':cc_conf,'#unconf':cc_unc}
	
		
		
	def prepare_summary_frame(self ):	
		
		# idb=localdb.DB(self.db)
		
		grid_lol_wallet_sum=[]
		col_names=['Total','Confirmed','Pending','Round','Filter','Wallet']
		# col_names=['Total','Confirmed','Pending','Round','Filter','New address','Wallet']
		
		all_cat=self.own_wallet_categories() #all_cat_unique
		
		wallet_opt=['Select:','New address','Export','Import priv. keys','Merge']
				
		if len(self.disp_dict)>0:
			disp_dict=json.loads(self.disp_dict[0][0])
			
			tmpdict={}
			tmpdict['rowk']='summary'
			tmpdict['rowv']=[{'T':'LabelV', 'L':format(disp_dict['top']['Total'] , self.format_str).replace(',',"'")  , 'uid':'Total'}  , 
										{'T':'LabelV', 'L':format(disp_dict['top']['Confirmed'] , self.format_str).replace(',',"'")  , 'uid':'Confirmed'}, 
										{'T':'LabelV', 'L':format(disp_dict['top']['Pending'] , self.format_str).replace(',',"'")  , 'uid':'Pending'}, 
										{'T':'Combox', 'uid':'round', 'V':['1','0.1','0.01','0.001','0.0001','off'], 'width':6},
										{'T':'Combox', 'uid':'filter', 'V':all_cat, 'width':6, 'tooltip':'Special categories:\nHidden - allows to hide address on the list,\n Excluded - allows to exclude address from UTXO/bills auto maintenance when it is ON.'},
										{'T':'Combox', 'V':wallet_opt } 
										]
			# if part=='Numbers':
				# for ii,vv in enumerate(tmpdict['rowv']):
					# if ii>2: tmpdict['rowv'][ii]['T']='excludeupdate-'+tmpdict['rowv'][ii]['T']
					
			# elif part=='Categries':
				# for ii,vv in enumerate(tmpdict['rowv']):
					# if ii<>4: tmpdict['rowv'][ii]['T']='excludeupdate-'+tmpdict['rowv'][ii]['T']
					
			grid_lol_wallet_sum.append(tmpdict )	
			
		else:
			tmpdict={}
			tmpdict['rowk']='summary'
			tmpdict['rowv']=[{'T':'LabelV', 'L':'', 'uid':'Total'}  , 
										{'T':'LabelV', 'L':'', 'uid':'Confirmed'}, 
										{'T':'LabelV', 'L':'', 'uid':'Pending'}, 
										{'T':'Combox', 'uid':'round', 'V':['1','0.1','0.01','0.001','0.0001','off'], 'width':6},
										{'T':'Combox', 'uid':'filter', 'V':all_cat, 'width':6},
										{'T':'Combox', 'V':wallet_opt } 
										]
			grid_lol_wallet_sum.append(tmpdict )	
			
			
					
			
		return grid_lol_wallet_sum, col_names
		
		
		
		
		
		
		
# 1. insert into channel table:
			# owner nickname, owner init hash, title, channel name, init content
	@gui.Slot(str,str)
	def set_channel(self,addr,vkey):
		# check if channels active:
		# idb=localdb.DB(self.db)
		xx=self.db_main.select_max_val( 'channels',['address' ], groupby=[ ])
		
		if len(xx)==0 or xx[0][0]==None:
			gui.messagebox_showinfo('Channels not yet active','Please activate channels in Channels tab!\n Will be active after view key is validated.',None)
			return
	
		# print('set_channel',addr,vkey)
		select_addr_str='Select address to send initial tx from'
		automate_rowids=[ 
							[{'T':'LabelC', 'L':'Channel for address: ','span':2  } , { } ] ,
							[{'T':'LabelC', 'L':addr ,'span':2} , { } ] ,
							[{'T':'LabelC', 'L':'Your nickname: ' } , {'T':'LineEdit' } ] ,
							[{'T':'LabelC', 'L':'Channel name: ' } , {'T':'LineEdit' } ] ,
							[{'T':'LabelC', 'L':'Channel type: ' } , {'T':'Combox', 'V':['Forum' ] } ] ,
							[{'T':'LabelC', 'L':'Introduction: ' } , {'T':'LineEdit' } ] ,
							[{'T':'Button', 'L':select_addr_str,'span':2  }, {}] ,
							[{'T':'Button', 'L':'Enter','span':2}, {}] 
						]
# {'T':'Combox', 'V':['Select:','address','view key','set channel'],'fun':self.export_or_create_channel,'args':(tmpaddr,), 'every_click':1  }
									
										
		expo=gui.Table(None,{'dim':[8,2], 'toContent':1}) #flexitable.FlexiTable(rootframe,grid_settings)
		expo.updateTable(automate_rowids)
		# rootframe.insertWidget(expo)
		
		
		
		def select_addr(btn2):
		
			def set_values(btn3,selz,categ,alias,total_amount):
				newtxt= ', '.join([categ,alias])
				
				total_amount=float(total_amount)-0.0001
				
				expo.cellWidget(6,0).setText(selz) 
				btn3.parent().parent().parent().parent().close()
				
			filter_frame=gui.FramedWidgets(None,'Filter')
			filtbox=gui.Combox(None,self.own_wallet_categories()) # #ttk.LabelFrame(selframe,text='Filter')
			filter_frame.insertWidget(filtbox)

			
			addr_list_frame=gui.ContainerWidget(None,layout=gui.QVBoxLayout()) #,'Addresses list')
			# print('parent3',filtbox.parent())
			
			# print('prepare_byaddr_frame 1446' )
			grid_lol_select,colnames=self.prepare_byaddr_frame( True,True)
			 
			select_table=gui.Table(None,{'dim':[len(grid_lol_select),len(colnames)], 'toContent':1})
			select_table.updateTable(grid_lol_select,colnames)
			for bii in range( select_table.rowCount()):
				# print('values',select_table.item(bii,7).text())
				select_table.cellWidget(bii,6).set_fun( False, set_values, select_table.item(bii,7).text(), select_table.item(bii,0).text(), select_table.item(bii,1).text(), select_table.item(bii,2).text()  )
			
			addr_list_frame.insertWidget(select_table)
			
			def refresh_add_list(btn4,*eventsargs):
				
				list_frame_tmp=btn4.parent().parent().widgetAt(1) #listframe
				tbltmp=list_frame_tmp.widgetAt(0)
				
				tbltmp.filtering( 'item',0,btn4.currentText() )

			
			filtbox.set_fun(refresh_add_list)  
			gui.CustomDialog(btn2,[filter_frame,addr_list_frame ], title='Select address to send from')
		
		# send_from.cellWidget(1,0).set_fun(False,select_addr)s
		
		
		expo.cellWidget(6,0).set_fun(False,select_addr) #set_cmd( 'enter',[],enter)
		
		
		# steps:
		# 1. send msg with channel params
		# 2. save channel to channels table
		# 3. update addr category (infrmative!)
		def enter(btn2): 
			# print('save data')
			
			creator=expo.cellWidget(2,1).text().strip()
			if creator=='':
				gui.messagebox_showinfo('Your nickname must not be empty','Your nickname must not be empty',btn2)
				return
				
			chname=expo.cellWidget(3,1).text().strip()
			if chname=='':
				gui.messagebox_showinfo('Channel name must not be empty','Channel name must not be empty',btn2)
				return
				
			if expo.cellWidget(6,0).text()==select_addr_str:
				gui.messagebox_showinfo('You must select address','You must select address for init transaction of the channel',btn2)
				return
				
			# addr,vkey
			# table['channels']={'address':'text', 'vk':'text', 'creator':'text', 'channel_name':'text', 'status':'text', 'own':'text' }
			
			
			# sending INIT TX 
			z=expo.cellWidget(6,0).text()
			# a='0.0001'
			initcontent=expo.cellWidget(5,1).text().strip()
			
			# print(expo.cellWidget(4,1))
			ch_type=expo.cellWidget(4,1).text().strip() #.currentText()
			
			msg=json.dumps({'channel_name':chname,'channel_owner':creator, 'channel_intro':initcontent, 'channel_type':ch_type })
			got_bad_char, msg_arr=global_db.prep_msg(msg,addr)
			
			if got_bad_char:
				gui.showinfo(msg_arr[0], msg_arr[1])
				return
				
			ddict={'fromaddr':z,	'to':[]	} #
			for mm in msg_arr:
				ddict['to'].append({'z':addr,'a':0.0001,'m':mm})
				
			table={}
			table['queue_waiting']=[global_db.set_que_waiting('send',jsonstr=json.dumps(ddict) ) ]
			table['queue_waiting'][0]['type']='channel'
			
			# idb=localdb.DB(self.db)
			self.db_main.insert(table,['type','wait_seconds','created_time','command' ,'json','id','status' ])	
			
			# all went through - save channel
			# table['channels']={'address':'text', 'vk':'text', 'creator':'text', 'channel_name':'text', 'channel_intro':'text', 'status':'text', 'own':'text', 'channel_type':'text' }
			table={'channels':[{'address':addr, 'vk':vkey, 'creator':creator, 'channel_name':chname, 'status':'active', 'own':'True',   'channel_intro':initcontent , 'channel_type':ch_type}]}	
			# print('1507 CREATING CHANNEL\n',table)
			# idb=localdb.DB(self.db)
			self.db_main.insert(table,['address' , 'vk' , 'creator' , 'channel_name' , 'status' , 'own',   'channel_intro' , 'channel_type' ])
			gui.showinfo('Channel created','Channel created.\nTo start using it - export channel view key and share with others.')
			
			# update addr category
			
			date_str=app_fun.now_to_str(False)
			table={'address_category':[{'address':addr, 'category':'Channel '+chname, 'last_update_date_time':date_str}]}			
			self.db_main.upsert(table,['address','category','last_update_date_time'],{'address':['=',"'"+addr+"'"]})
			
			# wallet_details.update_frame(self.prepare_summary_frame()) # update categories
			# grid1,col1=self.prepare_byaddr_frame()
			
			self.update_addr_cat_map()
			self.sending_signal.emit(['wallet'])
			
			table={'channel_signatures':[{'addr':addr,'signature':creator}]} 
			self.db_main.upsert( table, [ 'addr' ,'signature' ], {'addr':['=',  "'"+addr+"'" ] } )
			
				
			expo.parent().close() 


		expo.cellWidget(7,0).set_fun(False,enter) #set_cmd( 'enter',[],enter)

		gui.CustomDialog(None,expo, title='Creating channel')
		
		


				






		
		
									
	def export_or_create_channel(self,btn,addr ):
		if btn.currentText()=='Select:':
			return
		elif btn.currentText()=='address':
			self.export_addr(btn,addr)
		elif btn.currentText()=='view key':
			if self.is_synced:
				self.export_viewkey(btn,addr)
			else:
				# print('must be synced to export view key')
				gui.showinfo('Cannot export view key','Must be synced to export view key!')
		elif btn.currentText()=='set channel':
			# print(btn.currentText())
			if self.is_synced:
				ddict={'addr':addr} #,
							# 'path':'',
							# 'password':''
							# }
				table={}	
				table['queue_waiting']=[self.db_main.set_que_waiting('get_viewkey',jsonstr=json.dumps(ddict)) ]
				# idb=localdb.DB(self.db)
				self.db_main.insert(table,['type','wait_seconds','created_time','command' ,'json','id','status' ])
			else:
				# print('must be synced to set channel')
				gui.showinfo('Cannot create Channel','Must be synced to set up a channel!')
			
			
		btn.setIndexForText('Select:')
		
		
		
		
		
	def get_header(self,selecting):
		
		if selecting:
			return ['Category','Alias','Total','Confirmed','Pending','Usage','Select','Full address']
		else:
			return  ['Category','Alias','Total','Confirmed',' ','Pending','Bills','Usage','Export']
			# return  ['Category','Alias','Total','Confirmed',' ','Pending','Bills','Usage','Addr.','V.Key']
		
		
	def prepare_byaddr_frame(self,init=False,selecting=False,selecting_to=False):	
	
		# print('prepare_byaddr_frame')
	
		colnames=self.get_header(selecting)
		grid_lol3=[]
		tmpdict2={}
		
		# opt=self.get_options() # ??? need getoption every time ??
		# sorting=opt['sorting'] #self.get_sorting()
		# if selecting:
			# sorting='usage'
			
		if len(self.disp_dict)>0:
			# print('len(self.disp_dict)>0')
		
			uu=usb.USB()
			
			send_style='padding:-6px;font-size:28px;'
			if uu.os!='windows':
				send_style='padding-top:-4px;padding-bottom:0px;font-size:28px;'
		# if ddict['wl'][ii]['addr'] in addr_cat:
					# tmpcurcat=addr_cat[ddict['wl'][ii]['addr']]
			ddict=json.loads(self.disp_dict[0][0])
			sorting_lol=ddict['lol'] # not needed with qt
			
			sorting_lol=sorted(sorting_lol, key = operator.itemgetter(1, 2, 3), reverse=True )
			
			# if sorting=='amounts': 
				# sorting_lol=sorted(sorting_lol, key = operator.itemgetter(1, 2, 3), reverse=True )
			# elif sorting=='bills':
				# sorting_lol=sorted(sorting_lol, key = operator.itemgetter(2, 1, 3), reverse=True )
			# elif sorting=='usage':
				# sorting_lol=sorted(sorting_lol, key = operator.itemgetter(3, 1, 2), reverse=True )
			
			addr_cat=self.addr_cat_map 
			
			# print('1593 addr_cat',addr_cat)
					
			for i in sorting_lol: 
			
				ii=i[0]
				
				tmp_confirmed=0
				if 'confirmed' in ddict['wl'][ii]:
					tmp_confirmed=float(ddict['wl'][ii]['confirmed'])
				if tmp_confirmed==None:
					tmp_confirmed=0
					
				# print('updating',ii,ddict['wl'][ii]['addr'],tmp_confirmed, ddict['wl'][ii]['confirmed'])
				self.amount_per_address[ddict['wl'][ii]['addr']]=tmp_confirmed
				
				tmpcurcat='Edit'
				# print('testing',ddict['wl'][ii]['addr'],' in addr cat')
				if ddict['wl'][ii]['addr'] in addr_cat:
					tmpcurcat=addr_cat[ddict['wl'][ii]['addr']]
					
				# print( 'addr/cat',ddict['wl'][ii]['addr'] , tmpcurcat )
				
				tmp_unconfirmed=0
				if 'unconfirmed' in ddict['wl'][ii]:			
					tmp_unconfirmed=float(ddict['wl'][ii]['unconfirmed'])
				if tmp_unconfirmed==None:
					tmp_unconfirmed=0
					
				tmp_total=tmp_confirmed+tmp_unconfirmed
				
				
				b_enabled=True
				
				bills=int(ddict['wl'][ii]['#conf']+ddict['wl'][ii]['#unconf'])
				billsc=int(ddict['wl'][ii]['#conf'] )
				billsunc=int( ddict['wl'][ii]['#unconf'])
				
				bill_state=True
				if bills<=0:
					bill_state=False
				
					
				tmpalias=ddict['aliasmap'][ddict['wl'][ii]['addr']]	
				tmpaddr=ddict['wl'][ii]['addr']
				
				tmpdict2={}
				tmpdict2['rowk']=tmpalias
				
				if selecting:
				
					if tmp_total<=0.0001:
						b_enabled=False	
						
					if selecting_to:
						b_enabled=True
						
					tmpdict2['rowv']=[ 
									{'T':'LabelV', 'L':tmpcurcat }, 
									{'T':'LabelV', 'L':tmpalias },
									{'T':'LabelV', 'L':format(tmp_total , self.format_str).replace(',',"'")  , 'uid':'Total'+tmpalias},
									{'T':'LabelV', 'L':format(tmp_confirmed , self.format_str).replace(',',"'")    },
									{'T':'LabelV', 'L':format(tmp_unconfirmed , self.format_str).replace(',',"'")  },
									
									{'T':'LabelV', 'L':str( ddict['lol'][ii][3] ) },
									{'T':'Button', 'L':'Select' , 'uid':'select'+tmpalias , 'tooltip': tmpaddr , 'IS':b_enabled},
									{'T':'LabelV', 'L':tmpaddr  }
									]
					
				else:
					if tmp_total<=0:
						b_enabled=False
				
					tmpdict2['rowv']=[ 
									{'T':'Button', 'L':tmpcurcat,  'tooltip':'Edit category for address '+tmpaddr, 'fun':self.edit_category, 'args':(tmpalias,tmpaddr) }, 
									{'T':'LabelV', 'L':tmpalias,  'tooltip':'Alias of address '+tmpaddr },
									{'T':'LabelV', 'L':format(tmp_total , self.format_str).replace(',',"'")  },
									{'T':'LabelV', 'L':format(tmp_confirmed , self.format_str).replace(',',"'") },
									{'T':'Button', 'L':u"\u25B6"   , 'tooltip':'Send from this address' , 'IS':b_enabled, 'fun':self.send_from_addr, 'args':(tmpaddr, tmp_total), 'style':send_style},
									{'T':'LabelV', 'L':format(tmp_unconfirmed , self.format_str).replace(',',"'")  },
									{'T':'Button', 'L':str(bills)+'/'+str(billsunc) , 'tooltip':'Show bills / UTXOs' , 'IS':bill_state, 'fun':self.show_bills, 'args':(tmpaddr,) },
									
									{'T':'LabelV', 'L':str( ddict['lol'][ii][3] ) },
									{'T':'Combox', 'V':['Select:','address','view key','set channel'],'fun':self.export_or_create_channel,'args':(tmpaddr,), 'every_click':1  }
									
									# {'T':'Button', 'L':u"\u2398" , 'tooltip': 'Export address '+tmpaddr, 'fun':self.export_addr, 'args':(tmpaddr,), 'style':'padding:-4px;font-size:24px; ' },
									# {'T':'Button', 'L':u"\u2398" , 'tooltip': 'Export Viewing Key of '+tmpaddr, 'fun':self.export_viewkey, 'args':(tmpaddr,), 'style':'padding:-4px;font-size:24px;' }
									]
				grid_lol3.append(tmpdict2) 

		# print('1724 ,grid_lol3\n',self.amount_per_address)
				
		return grid_lol3, colnames
		
		
		
	def edit_category(self,btn,alias,addr  ): #, json_to_update='wallet_byaddr'):

		# global rootframe, tmpvar
		curv= btn.text()
		
		automate_rowids=[ [{'T':'LabelV', 'L':'Edit category for \n\n '+addr+' \n', 'span':3, 'width':120, 'style':{'bgc':'#eee','fgc':'red'}, 'uid':'none'},{  }, {  } ] ,
						[{'T':'LineEdit', 'V':curv.replace('Edit',''), 'width':32, 'span':3}, { }, { } ],
						[{'T':'Button', 'L':'Set Main', 'width':32},{'T':'Button', 'L':'Set Exclude', 'width':32},{'T':'Button', 'L':'Set Hidden', 'width':32} ] ,
						[{'T':'Button', 'L':'Enter', 'width':32},{ },{ }  ] ,
						]
		
		tw=gui.Table( params={'dim':[4,3],"show_grid":False, 'colSizeMod':[256,'toContent','stretch'], 'rowSizeMod':['toContent','toContent','toContent' ]})		
		tw.updateTable(automate_rowids)
		
		def setV(le,vv):
			le.setText(vv)
			le.setFocus(gui.Qt.PopupFocusReason)
		
		tw.cellWidget(2,0).set_fun(True,setV,tw.cellWidget(1,0),'Main')
		tw.cellWidget(2,1).set_fun(True,setV,tw.cellWidget(1,0),'Excluded') 
		tw.cellWidget(2,2).set_fun(True,setV,tw.cellWidget(1,0),'Hidden') 
		
		
		def retv(btn,tmpvar):
		
			# global rootframe, tmpvar
			tmp= tmpvar.text().strip()
			
			if tmp=='':
				
				# btn.parent().close()
				tmpvar.parent().parent().parent().close()
				return
				
			# idb=localdb.DB(self.db)
			
			table={}
			
			date_str=app_fun.now_to_str(False)
			table['address_category']=[{'address':addr, 'category':tmp, 'last_update_date_time':date_str}]
			self.db_main.upsert(table,['address','category','last_update_date_time'],{'address':['=',"'"+addr+"'"]})
			
			## wallet_details.update_frame(self.prepare_summary_frame()) # update categories
			# wallet_details=btn.parent().parent()
			# grid1,col1=self.prepare_byaddr_frame()			
			# wallet_details.updateTable(grid1)
			self.update_addr_cat_map()
			self.sending_signal.emit(['wallet'])
			tmpvar.parent().parent().parent().close() #.destroy()
			
		tw.cellWidget(3,0).set_fun(True,retv,btn,tw.cellWidget(1,0)) 
		
		gui.CustomDialog(btn,tw, title='Edit category', defaultij=[3,0])
		
		

