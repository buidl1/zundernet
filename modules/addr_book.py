# show button for not validated addresses to validate again 
# there should be id validation if cancelled - show button

# fix send to 
# if addr not valid after > 1h - set button to  validate again?

import os

import json
import time
import modules.localdb as localdb
import modules.app_fun as app_fun
import modules.gui as gui

import modules.aes as aes


# import operator

class AddressBook:

	def __init__(self,wds):
		self.wds=wds
		self.db=wds.db
		self.addr_book_view_grid=[]
		
	def prepare_own_addr_frame(self,  selecting_to=False):
		# print('addrbook byaddr frame')
		return self.wds.prepare_byaddr_frame(False, True,selecting_to )

		
	# add amount {'confirmed':amount_init,'unconfirmed':am_unc,'#conf':cc_conf,'#unconf':cc_unc}
	def cat_alias(self,selz,own=True):
		cat1=''
		alia1=''
		am1=''
		if own:
			if selz in self.wds.addr_cat_map:
				cat1=self.wds.addr_cat_map[selz]
			if selz in self.wds.alias_map:
				alia1=self.wds.alias_map[selz]
			if selz in self.wds.addr_amount_dict:
				am1=', available amount: '+str(round(self.wds.addr_amount_dict[selz]['confirmed']+self.wds.addr_amount_dict[selz]['unconfirmed'],8))
		else:
			if selz in self.wds.addr_book_category_alias:
				cat1=self.wds.addr_book_category_alias[selz]['category']
			if selz in self.wds.addr_book_category_alias:
				alia1=self.wds.addr_book_category_alias[selz]['alias']
		
		if cat1!='' or alia1!='':
			return alia1+','+cat1+am1 #cat1+','+alia1
			
		return selz
		
		
	
	def set_values(self,btn3,send_from,selz,own=True):

		send_from.setToolTip(selz)
		
			
		send_from.setText(self.cat_alias(selz,own)) #cat1+','+alia1)
		
		btn3.parent().parent().parent().parent().close()				
					
							
	#sendfrom = lineedit
	def get_addr_from_wallet(self,  send_from,sending_to=False): #,*evargs

		# selframe = Toplevel() #tk.Tk()
		filter_frame=gui.FramedWidgets(None ,'Filter') 
		filtbox=gui.Combox(None,self.wds.own_wallet_categories())
		filtbox.setMaximumHeight(128)
		filter_frame.insertWidget(filtbox)	
			
		
		addr_list_frame=gui.FramedWidgets(None,'Addresses list')  
		grid_lol_select,colnames= self.prepare_own_addr_frame( sending_to) # 4 sec 

		select_table=gui.Table(None,{'dim':[len(grid_lol_select),len(colnames)], 'toContent':1})
		select_table.updateTable(grid_lol_select,colnames)
		
		
		for bii in range( select_table.rowCount()):	
			select_table.cellWidget(bii,6).set_fun(False,self.set_values, send_from, select_table.item(bii,7).text() ) 
			#, select_table.item(bii,0).text(), select_table.item(bii,1).text() )
		
		addr_list_frame.insertWidget(select_table)

		
		def refresh_add_list(btn4,*eventsargs):
			
			list_frame_tmp=btn4.parent().parent().widgetAt(1) #listframe
			tbltmp=list_frame_tmp.widgetAt(0)
			
			tbltmp.filtering( 'item',0,btn4.currentText() )

		
		filtbox.set_fun(refresh_add_list)  
		
		gui.CustomDialog(send_from,[filter_frame,addr_list_frame], title='Select address')


		
	def get_addr_from_book(self,btn,elemZ,*evargs):

		filter_frame=gui.FramedWidgets(None ,'Filter') 
		filtbox=gui.Combox(None,self.wds.categories_filter())
		filter_frame.insertWidget(filtbox)	
			

		
		list_frame=gui.FramedWidgets(None,'Addresses list') #ttk.LabelFrame(selframe,text='Addresses list')
		
		grid_lol_select,colnames=self.wds.addr_book_select()
		select_table=gui.Table(None,{'dim':[len(grid_lol_select),5], 'toContent':1} ) #flexitable.FlexiTable(list_frame,grid_lol_select)
		select_table.updateTable(grid_lol_select,colnames)
		for bii in range( select_table.rowCount()):
			select_table.cellWidget(bii,0).set_fun( False, self.set_values,  elemZ, select_table.item(bii,4).text(), False )
			
		list_frame.insertWidget(select_table)
		 
		def update_filter(btn5,*someargs):
			
			list_frame_tmp=btn5.parent().parent().widgetAt(1) #listframe
			tbltmp=list_frame_tmp.widgetAt(0)
			
			tbltmp.filtering( 'item',2,btn5.currentText() )
			
		filtbox.set_fun(update_filter )
		
		gui.CustomDialog(btn,[filter_frame,list_frame], title='Select address to send to')
			
			
			
			# idb.select('msgs_inout',['type','addr_ext','date_time','msg', 'in_sign_uid','uid','tx_status','txid','is_channel'],{'proc_json':['=',"'False'"]},orderby=[{'date_time':'asc'}])
			
	def displayHistoricalTXs(self,btn,alias,addr):
		# print('displayHistoricalTXs',alias,addr)
		# get from msg table - all incl channel
		# display
		colnames=['Date Time', 'Message' ]
		grid_lol_msg=[]
		
		idb=localdb.DB(self.db)
		
		sel_view=idb.select('msgs_inout',[ 'date_time', 'msg' ],{'addr_to':['=',"'"+addr+"'"]}, orderby=[{'date_time':'desc'}] )
		
		if len(sel_view)>0:
			# print(sel_view)
		
			for ii,rr in enumerate(sel_view):  
				tmpdict={'rowk':str(ii), 'rowv':[{'T':'LabelV', 'L':str(rr[0]) } , 
										{'T':'LabelV', 'L':rr[1] }  
										]}
				grid_lol_msg.append(tmpdict)
	
			tx_tbl=gui.Table(None,{'dim':[len(grid_lol_msg),len(colnames)],'updatable':1, 'toContent':1}) #flexitable.FlexiTable(rootframe,grid_settings)
			tx_tbl.updateTable(grid_lol_msg,colnames)
	
			gui.CustomDialog(btn,tx_tbl, title='View key messages')
		else:
			gui.messagebox_showinfo('No transactions ...','No transactions yet for this view key.',btn)
	
	
	
	
	def addr_book_view(self):
	
		# print('refresh addr book')
		colnames=[ 'Usage','Category','Alias','Full address','Valid','View Key','Valid','','','','','']
		grid_lol_select=[]
					
		idb=localdb.DB(self.db)
		
		sel_addr_book=idb.select('addr_book',[ 'Category','Alias','Address','ViewKey','usage','addr_verif','viewkey_verif'], orderby=[{'usage':'desc'},{'Category':'asc'},{'Alias':'asc' }] )
		
		# print(170,sel_addr_book)
		
		cur_addr=[]
		if len(sel_addr_book)>0:
		
			for ii,rr in enumerate(sel_addr_book):
			
				# print(rr)
				tmpdict={}
				uid_tmp=rr[2]
				tmpdict['rowk']=str(uid_tmp)
						
				
				cur_addr.append(rr[2])
				
				tmphasvk=False
				uid_tmp=rr[2]
				# fsize=24
				tmpnott={'T':'QLabel', 'L':'-',   'tooltip':'No view key', 'style':' text-align:center;padding-left:10px;margin:3px;' } #u"\u2612" , 'fontsize':fsize
				
				# print(190,rr )
				if rr[3].strip()!='':
					tmphasvk=True
					
					# tmpnott={'T':'Button', 'L':"\U0001F441", 'fun':self.displayHistoricalTXs,'args':(rr[1],rr[2]),  'tooltip':rr[3].strip(), 'style':'background-color:lightgreen;color:white;text-align:center; font-size:22px;' } #u"\u2611"
					tmpnott={'T':'QLabel', 'L':'+',  'tooltip':rr[3].strip(), 'style':'background-color:lightgreen;color:white;text-align:center;padding-left:10px;margin:3px; font-size:22px;font-weight:bold;' } #u"\u2611"
					
				addrvalid='...' #	u"\U0001F550" #'Waiting'
				addr_valid_tt='Waiting for validation'
				addr_color=' color:blue;text-align:center;padding-left:10px'
				if rr[5]==-1:
					addrvalid='N' #u"\u2612" #'No'
					addr_valid_tt='Not valid'
					addr_color='background-color:red;color:yellow;text-align:center; margin:3px;font-size:22px;font-weight:bold;'
				elif rr[5]==1:
					addrvalid='Y' #u"\u2611" #'Yes'
					addr_valid_tt='Address valid'
					addr_color='background-color:lightgreen;color:white;text-align:center; margin:3px;font-size:22px;font-weight:bold;'
					
				
				viewk_valid='-'
				viewk_valid_tt=''
				viewk_color=' color:grey;text-align:center;padding-left:10px;margin:3px;'
				if rr[6]==-1:
					viewk_valid=='N' #u"\u2612" #'No'
					viewk_valid_tt='Not valid'
					viewk_color='background-color:red;color:yellow;text-align:center; margin:3px;font-size:22px;font-weight:bold;'
				elif rr[6]==1:
					viewk_valid='Y' #u"\u2611" #'Yes'
					viewk_valid_tt='Valid'
					viewk_color='background-color:lightgreen;color:white;text-align:center; margin:3px;font-size:22px;font-weight:bold;'
					
					tmpnott={'T':'Button', 'L':"\U0001F441", 'fun':self.displayHistoricalTXs,'args':(rr[1],rr[2]),  'tooltip':rr[3].strip(), 'style':'background-color:lightgreen;color:white;text-align:center; font-size:22px;' } #u"\u2611"
					
				elif rr[6]==0:
					viewk_valid='...' #	u"\U0001F550" #'Waiting'
					viewk_valid_tt='Waiting for validation'
					viewk_color=' color:blue;text-align:center;padding-left:10px;margin:3px;'
				 # , 'tooltip': uid_tmp rr[2][:7]+'...'
				bstyle='padding:1px;font-size:18px;'
				tmpdict['rowv']=[{'T':'LabelV', 'L':str(rr[4]) } , #, 'uid':'Usage'+str(uid_tmp)
							{'T':'LabelV', 'L':rr[0] } , #, 'uid':'Category'+str(uid_tmp)
							{'T':'LabelV', 'L':rr[1]} , #, 'uid':'Alias'+str(uid_tmp)
							{'T':'LabelV', 'L':rr[2][:7]+'...'  , 'tooltip': uid_tmp } , # , 'tooltip': uid_tmp rr[2][:7]+'...' , 'uid':'Address'+str(uid_tmp) 
							{'T':'QLabel', 'L':addrvalid, 'tooltip':addr_valid_tt, 'style':addr_color } , 
							tmpnott , 
							{'T':'QLabel', 'L':viewk_valid, 'tooltip':viewk_valid_tt, 'style':viewk_color} , 
							
							{'T':'Button', 'L':u"\U0001F4CB"  , 'tooltip':'Edit record', 'style':bstyle } ,  #'Edit'
							{'T':'Button', 'L':u"\U0001F5D1" , 'tooltip':'Delete record', 'style':bstyle } ,  #'Del.'
							{'T':'Button', 'L':u"\u2398"  , 'tooltip':'Copy address', 'style':'padding:0px;font-size:22px;' } , 
							{'T':'Button', 'L':u"\U0001F585"  , 'tooltip':'Send to', 'style':'padding:0px;font-size:22px;' } ,
							{'T':'Button', 'L':u"\U0001F9FE" , 'tooltip':'Request payment from this address', 'style':bstyle }
							]
				grid_lol_select.append(tmpdict)
	
		return grid_lol_select,colnames,cur_addr
					
					
	
	def update_buttons(self):
		# global idb, form_grid, grid_settings
		
		def delete_addr(btn,addr,alias ):			
			
			tf=gui.msg_yes_no('Delete from address book?','Please confirm to delete address\n\n'+addr+'\n\nof alias\n\n'+alias+'\n',btn)
			
			if tf:
				idb=localdb.DB(self.db)
				idb.delete_where('addr_book',{'Address':['=',"'"+addr+"'"]})
				grid_settings,colnames,cur_addr=self.addr_book_view()
				self.main_table.updateTable(grid_settings,colnames)
				
				self.cur_addr.remove(addr)
				
			
		def subcopy( addr ):
			
			# gui.copy(main_table,addr)
			gui.copy(None,addr)
			self.increment_usage(addr )
			
		def subsendto(btn,addr , sendto_fun):
			# print(addr)
			sendto_fun(btn,addr)
			self.increment_usage(addr )
			
		def edit_addr(addr,alias,category,viewkey): # load data to form
						
			self.form_table.cellWidget(1,1).setText( category)
			self.form_table.cellWidget(2,1).setText( alias)
			self.form_table.cellWidget(3,1).setText( addr)
			self.form_table.cellWidget(4,1).setText(viewkey)
			 
		
		def request_payment(btn,alias,addr ,  sendto_fun):
			
			grid1=[]
			grid1.append( [{'T':'LabelC', 'L':'Obligatory:', 'span':2}] )
			grid1.append( [{'T':'LabelC', 'L':'Request amount'}, {'T':'LineEdit','V':'0.0001', 'L':'amount', 'width':32, 'valid':{'ttype':float,'rrange':[0.0001, 1000000]}} ]  )
			
			select=localdb.get_last_addr_from("'last_payment_to_addr'")
			# print(self.wds.addr_cat_map)
			cat1=''
			if select in self.wds.addr_cat_map:
				cat1=self.wds.addr_cat_map[select]
			alia1=''
			if select in self.wds.alias_map:
				alia1=self.wds.alias_map[select] #'L':cat1+','+alia1
			# disp_dict['aliasmap']=self.alias_map
			grid1.append(  [{'T':'LabelC', 'L':'Payment to address'}, {'T':'Button', 'L':cat1+','+alia1, 'tooltip':select, 'fun':self.get_addr_from_wallet  } ] )
			grid1.append( [{'T':'LabelC', 'L':'Optional:','span':2}  ] )
			grid1.append( [{'T':'LabelC', 'L':'Title'}, {'T':'LineEdit', 'L':'Payment request for invoice nr ', 'uid':'title' } ] )
			grid1.append(  [{'T':'LabelC', 'L':'Document URI'}, {'T':'LineEdit', 'uid':'docuri', 'width':32} ] )
			
			select=localdb.get_last_addr_from("'last_book_from_addr'")
			
			cat2=''
			if select in self.wds.addr_cat_map:
				cat2=self.wds.addr_cat_map[select]
			alia2=''
			if select in self.wds.alias_map:
				alia2=self.wds.alias_map[select]
			grid1.append( [{'T':'LabelC', 'L':'Send using'}, {'T':'Button', 'L':cat2+','+alia2, 'tooltip':select, 'fun':self.get_addr_from_wallet } ] )
			grid1.append(  [{'T':'Button', 'L':'Send request', 'span':2, 'uid':'submit'} ] )
			
			
			g1_table=gui.Table(None,params={'dim':[len(grid1),2] } ) # flexitable.FlexiTable(obligatory,grid1)			
			g1_table.updateTable(grid1 )
			
			def send_request(btn7):
				tw=btn7.parent().parent()
				ii=btn7.property('rowii')
				tmptoaddr=tw.cellWidget(2,1).toolTip() #g1_table.get_value('toaddr')
				tmpfromaddr=tw.cellWidget(6,1).toolTip() #g1_table.get_value('sendfromaddr')
			
				localdb.set_last_addr_from(tmpfromaddr,"'last_book_from_addr'")  #g1_table.get_value('sendfromaddr')
				localdb.set_last_addr_from(tmptoaddr ,"'last_payment_to_addr'") #g1_table.get_value('toaddr')
			
				tmpam=round(float(tw.cellWidget(1,1).text() ),8) #g1_table.get_value('amount')
				
				if tmpam>100000000 or tmpam<0.0001:
					gui.showinfo('Amount not valid, please correct','Amount '+str(tmpam)+' is not realistic, please correct.',btn7)
					return
				
				if tmptoaddr in ['','...']:
					gui.showinfo('Address missing','Please enter valid [Payment to address]',btn7)
					return
				
				if tmpfromaddr in ['','...']:
					gui.showinfo('Address missing','Please enter valid [Send using] address',btn7)
					return
					
				if len(tw.cellWidget(4,1).text())>64: #g1_table.get_value('title')
					gui.showinfo('Title too long','Please correct request title to be less then 64 characters long.',btn7)
					return
				
				tmpsignature=localdb.get_addr_to_hash(addr)
				
				memo_json={'amount':tmpam
							,'toaddress':tmptoaddr
							,'title':tw.cellWidget(4,1).text()
							,'docuri':tw.cellWidget(5,1).text()}
			
				# add sign 
				ddict={'fromaddr':tmpfromaddr, 'to':[{'z':addr,'a':0.0001,'m':'PaymentRequest;'+json.dumps(memo_json)+tmpsignature }]	} 
				table={}
				table['queue_waiting']=[localdb.set_que_waiting('send',jsonstr=json.dumps(ddict) ) ]
				idb=localdb.DB(self.db)
				idb.insert(table,['type','wait_seconds','created_time','command' ,'json','id','status' ])
				# print(table)
				tw.parent().close() #.destroy()
				
			
			g1_table.cellWidget(7,0).set_fun(False,send_request)
			gui.CustomDialog(btn,[g1_table ], title='Request payment from '+alias)


			
		for kk in range(self.main_table.rowCount()):
		

			addr=self.main_table.item(kk,3 ).toolTip()
			alias=self.main_table.item(kk,2  ).text()
			categ=self.main_table.item(kk,1).text()
			viewk=''
			
			if self.main_table.cellWidget(kk,5).text() in ['+',"\U0001F441"] : #u"\u2611"  : #'True': #'tooltip' in vv[5]:
				viewk=self.main_table.cellWidget(kk,5).toolTip() 
				
			self.main_table.cellWidget(kk,7).set_fun(True,edit_addr, addr,alias,categ,viewk ) 
			
			self.main_table.cellWidget(kk,8).set_fun(False,delete_addr, addr,alias ) #
			
			self.main_table.cellWidget(kk,9).set_fun(True,subcopy, addr ) #
			
			self.main_table.cellWidget(kk,10).set_fun(False,subsendto, addr,  self.wds.send_to_addr ) #
			
			self.main_table.cellWidget(kk,11).set_fun(False,request_payment, alias,addr ,  self.wds.send_to_addr ) #
								

								
								
								
								
			
	def increment_usage(self,addr): # when copy or sendto
		idb=localdb.DB(self.db)
		sel_addr_book=idb.select('addr_book',[ 'usage'],{'Address':['=',"'"+addr+"'"]} )
		table={}
		table['addr_book']=[{'usage':int(sel_addr_book[0][0])+1}]  
		idb.upsert(table,['usage'],{'Address':['=',"'"+addr+"'"]})
		
		grid_settings,colnames,cur_addr=self.addr_book_view()
		self.main_table.updateTable(grid_settings,colnames)
		
	@gui.Slot()		
	def refresh_addr_book(self):
	
		self.filter_table.updateBox( new_items_list=self.wds.categories_filter())
		
		grid_settings,colnames,cur_addr=self.addr_book_view()
		self.cur_addr=cur_addr
		self.main_table.updateTable(grid_settings,colnames)
		
		self.update_buttons()

	def setaddrbook(self ): 
				
		# global idb, grid_settings, form_grid, cur_addr 
		frame0=gui.FramedWidgets(None,'Filter') #ttk.LabelFrame(parent_frame,text='Filter') 
		
		self.filter_table=gui.Combox(None,self.wds.categories_filter())
		frame0.insertWidget(self.filter_table)
		
		# addr book view left:
		frame1=gui.FramedWidgets(None,'Addresses list') #ttk.LabelFrame(parent_frame,text='Addresses list') 
		
		grid_settings,colnames,cur_addr=self.addr_book_view()
		self.addr_book_view_grid=grid_settings
		
		self.cur_addr=cur_addr
		
		self.main_table=gui.Table(None,params={'dim':[len(grid_settings),len(colnames)],'updatable':1, 'toContent':1} )  #, 'toContent':1
		self.main_table.updateTable(grid_settings,colnames)
		frame1.insertWidget(self.main_table)
		
		
		c_left=gui.ContainerWidget(None,gui.QVBoxLayout(),widgets=[frame0,frame1])
		
		def update_filter(btn,*someargs):
			
			self.main_table.filtering( cellType='item',colnum=1,fopt=btn.currentText() )
			
		self.filter_table.set_fun(update_filter)	
		self.update_buttons()
		
		
		frame2=gui.FramedWidgets(None,'Add/edit form') 
		
		init_form=[ [{'T':'Button','L':'Import','uid':'import','span':2}],
					[{'T':'LabelC', 'L':'Category'} ,	{'T':'LineEdit','uid':'cat','width':32} ],
					[{'T':'LabelC', 'L':'Alias' } , {'T':'LineEdit','uid':'alia'} ],
					[{'T':'LabelC', 'L':'Full address' } , 	{'T':'LineEdit','uid':'addr','width':32} ],
					[{'T':'LabelC', 'L':'View key' } , 	{'T':'LineEdit','uid':'viewkey','width':32} ],
					[{'T':'Button','L':'Save','uid':'enter', 'span':2}]
						]	
		form_grid=[]
		for ii,inf in enumerate(init_form):
			tmpdict={}
			tmpdict['rowk']=str(ii)
			tmpdict['rowv']=inf
						
			form_grid.append(tmpdict)
		
		# form_table=flexitable.FlexiTable(frame2,form_grid)
		self.form_table=gui.Table(None,params={'dim':[len(init_form),2],'updatable':1, 'toContent':1} )  #, 'toContent':1
		self.form_table.updateTable(form_grid)
		frame2.insertWidget(self.form_table)
		frame2.setMinimumWidth(256) # +32
		
		
		
		# vk_valid=-2 not processesd vk_valid=0 empty no need to process 
		def save_new():
			# global idb, form_grid, grid_settings
			# table={}
			idb=localdb.DB(self.db)
			tmpaddr=self.form_table.cellWidget(3,1).text().strip() #.get_value('addr').strip()
			# print(468,tmpaddr)
			if tmpaddr=='':
				return
				
			tmpvk=self.form_table.cellWidget(4,1).text().strip() #.get_value('viewkey').strip()
			tmpcat=self.form_table.cellWidget(1,1).text().strip() #.get_value('cat').strip()
			tmpalia=self.form_table.cellWidget(2,1).text().strip() #.get_value('alia').strip()
			
			sel_addr_book=idb.select('addr_book',[ 'ViewKey','addr_verif','viewkey_verif'],{'Address':['=',"'"+tmpaddr+"'"]})
			# print(477,sel_addr_book)
			# print(tmpvk)
			
			tmpaddr_valid=0
			tmpvk_valid=-2
			if len(sel_addr_book)>0:
				if tmpvk=='':# no need for validation
					tmpvk_valid=0
				# elif sel_addr_book[0][0]!=tmpvk : #not empty and new - need t ovalidate
					# tmpvk_valid=-2
				else:
					tmpaddr_valid=sel_addr_book[0][1]
					tmpvk_valid=-2 #sel_addr_book[0][2]
			
			
			table={}
			# print('self.cur_addr',self.cur_addr,tmpvk_valid,tmpvk)
			if tmpaddr in self.cur_addr: # = editing addr already in 
				table['addr_book']=[{'Category':tmpcat,'Alias':tmpalia,'Address':tmpaddr,'ViewKey':tmpvk,'addr_verif':tmpaddr_valid,'viewkey_verif':tmpvk_valid }] 
				idb.upsert(table,[ 'Category','Alias','Address','ViewKey','addr_verif','viewkey_verif' ],{'Address':['=',"'"+tmpaddr+"'"]})
				
				if tmpvk_valid==-2: # if not valid add validation 
					table={}
					tmpjson=json.dumps({'addr':tmpaddr,'viewkey':tmpvk})
					table['queue_waiting']=[localdb.set_que_waiting(command='import_view_key',jsonstr=tmpjson, wait_seconds=0)]
					idb.upsert(table,['type','wait_seconds','created_time','command' ,'json','id','status' ],{'command':['=',"'import_view_key'"],'json':['=',"'"+tmpjson+"'"] })
			else: # new 
				table['addr_book']=[{'Category':tmpcat,'Alias':tmpalia,'Address':tmpaddr,'ViewKey':tmpvk,'usage':0,'addr_verif':tmpaddr_valid,'viewkey_verif':tmpvk_valid}]  
				idb.insert(table,[ 'Category','Alias','Address','ViewKey','usage','addr_verif','viewkey_verif'])
				
				table={} # valid addr
				table['queue_waiting']=[localdb.set_que_waiting(command='validate_addr',jsonstr=json.dumps({'addr':tmpaddr }), wait_seconds=0)]
				idb.insert(table,['type','wait_seconds','created_time','command' ,'json','id','status' ])
				
				if tmpvk!='':
					table={}
					tmpjson=json.dumps({'addr':tmpaddr,'viewkey':tmpvk})
					table['queue_waiting']=[localdb.set_que_waiting(command='import_view_key',jsonstr=tmpjson, wait_seconds=0)]
					idb.insert(table,['type','wait_seconds','created_time','command' ,'json','id','status' ])
				
				# idb.upsert(table,[ 'Category','Alias','Address','ViewKey','usage'],{'Address':['=',"'"+tmpaddr+"'"]})
			
			self.form_table.cellWidget(1,1).setText( '')
			self.form_table.cellWidget(2,1).setText( '')
			self.form_table.cellWidget(3,1).setText( '')
			self.form_table.cellWidget(4,1).setText('')
			
			self.refresh_addr_book()
			
			# update_filter_values()
			
			
		self.form_table.cellWidget(5,0).set_fun(True,save_new)
		
		
		
		
		
		# open dialog to select file
		# 2 types : zaddr or viewkey strtitle ,init_path=os.getcwd(),parent=None,name_filter=''
		def import_z(): 
			# global zpath
			zpath=gui.get_file_dialog( "Select file with z-address or view key", parent=self.form_table   ) #
			# print(zpath)
			if zpath==None or zpath[0]=='':
				return
				
			zpath=zpath[0]				
			tmpval=[]
			cc=aes.Crypto()
			
			# 1. try read file as decrypted containing addr or viewkey keyword json
			# if failed try password
			isjok=False
			
			def load_values(ddi):
				isjok=False
				if 'addr' in ddi:
					self.form_table.cellWidget(3,1).setText(ddi['addr'])
					isjok=True
					# print(isjok)
				if 'viewkey' in ddi:
					self.form_table.cellWidget(4,1).setText(ddi['viewkey']) 
					self.form_table.cellWidget(1,1).setText('ViewKey')
			
				return isjok
				
			try:
				testjson=json.loads(cc.read_file( zpath))
				isjok=load_values(testjson)
				
			except:
				print('err testjson')  
				isjok=False
			
			if not isjok:
				def whilewaiting(tmpval2,zpath):
					# global zpath
					# print(547,zpath,tmpval2)
					if tmpval2[0]==' ':
						return					
				
					try:
						decr_val=cc.aes_decrypt_file(path1=zpath,path2=None,password=tmpval2 ) #
						
						if decr_val==False:
							1/0
						
						ddi=json.loads(decr_val)	

						load_values(ddi)						
				
						# if 'viewkey' in ddi:
							# self.form_table.cellWidget(1,1).setText('ViewKey') #self.form_table.set_textvariable('cat','ViewKey')
							# self.form_table.cellWidget(3,1).setText( ddi['addr'])
							# self.form_table.cellWidget(4,1).setText(ddi['viewkey'])
						# else:							
							# self.form_table.cellWidget(3,1).setText(ddi['addr'])	 # self.form_table.set_textvariable('addr',ddi['addr'])		
						
					except:
						gui.showinfo('Could not decrypt file','File '+zpath+' does not contain encrypted address or view key or you have wrong password!', self.form_table)
				
				gui.PassForm(tmpval, first_time=False, parent = self.form_table,  title="Enter password to decrypt file")
				if len(tmpval)>0:
					# flexitable.ask_password(tmpval,'Decrypting file','\n Decrypting file '+zpath+'\n\nEnter password\n',whilewaiting) # set password if needed ?
					whilewaiting(tmpval[0],zpath)
		
		
		self.form_table.cellWidget(0,0).set_fun(True,import_z) #.set_cmd('import',[ ],import_z)
		
		
		return gui.ContainerWidget(None,gui.QHBoxLayout(),widgets=[c_left,frame2])
		
