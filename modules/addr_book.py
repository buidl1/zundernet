

import tkinter as tk
from tkinter import filedialog, StringVar, ttk, messagebox, Toplevel 
import os

import json
import time
import modules.localdb as localdb
import modules.app_fun as app_fun

import modules.flexitable as flexitable

import modules.aes as aes


import operator

class AddressBook:

	def __init__(self,wds):
		self.wds=wds

	def own_wallet_categories(self):

		all_cat_unique=[]
		idb=localdb.DB()
		all_cat=idb.select('address_category',['category'] )
		for rr in all_cat: 
			
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
			
			
	


	
	def prepare_own_addr_frame(self, selecting_filter='All',selecting_to=False):	

		grid_lol3=[]
		tmpdict2={}
		
		tmpdict2['head']=[{'T':'LabelC', 'L':'Category', 'tooltip':'May be useful for filtering addresses in big wallets' }  , 
									{'T':'LabelC', 'L': 'Alias', 'tooltip':'Short unique address referrence', 'width':7 },
									{'T':'LabelC', 'L': 'Total' },
									{'T':'LabelC', 'L': 'Confirmed' },
									{'T':'LabelC', 'L': 'Pending' },
									{'T':'LabelC', 'L': 'Usage' },
									{'T':'LabelC', 'L': 'Select' }
									]
			
		grid_lol3.append(tmpdict2)
		

		idb=localdb.DB()

		disp_dict=idb.select('jsons',['json_content','last_update_date_time'],{'json_name':['=',"'display_wallet'"]})

		format_str=",.8f"
		
		sorting='usage'
		filtering=selecting_filter
		
		if len(disp_dict)>0:
		
			ddict=json.loads(disp_dict[0][0])
			
			sorting_lol=ddict['lol']
			
			sorting_lol=sorted(sorting_lol, key = operator.itemgetter(3, 1, 2), reverse=True )
			adr_cat=idb.select('address_category',['address','category'] )
			addr_cat={}
			for ac in adr_cat:
				addr_cat[ac[0]]=ac[1]
			
			for i in sorting_lol: 
			
				ii=i[0]
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
				
				if tmp_total<=0.0001 and selecting_to==False:
					visible=False
				
				send_state='normal'
				if tmp_total<=0:
					send_state='disabled'
				
				bills=int(ddict['wl'][ii]['#conf']+ddict['wl'][ii]['#unconf'])
				billsc=int(ddict['wl'][ii]['#conf'] )
				billsunc=int( ddict['wl'][ii]['#unconf'])
				
				tmpalias=ddict['aliasmap'][ddict['wl'][ii]['addr']]	
				tmpaddr=ddict['wl'][ii]['addr']
				
				tmpdict2={}
				
				
				tmpdict2[tmpalias]=[ 
								{'T':'LabelV', 'L':tmpcurcat, 'visible':visible, 'uid':'tmpcurcat'+tmpalias}, 
								{'T':'LabelV', 'L':tmpalias,  'visible':visible, 'uid':'tmpalias'+tmpalias},
								{'T':'LabelV', 'L':format(tmp_total , format_str).replace(',',"'") , 'visible':visible, 'uid':'Total'+tmpalias},
								{'T':'LabelV', 'L':format(tmp_confirmed , format_str).replace(',',"'")  , 'visible':visible , 'uid':'tmp_confirmed'+tmpalias},
								{'T':'LabelV', 'L':format(tmp_unconfirmed , format_str).replace(',',"'") , 'visible':visible, 'uid':'tmp_unconfirmed'+tmpalias},									
								{'T':'LabelV', 'L':str( ddict['lol'][ii][3] ),  'visible':visible, 'uid':'usage'+tmpalias},
								{'T':'Button', 'L':'Select' , 'uid':'select'+tmpalias, 'visible':visible, 'tooltip': tmpaddr }
								]
					
				grid_lol3.append(tmpdict2)
				
		return grid_lol3
			

	def prepare_own_addr_button_cmd(self, grid_lol3,wallet_details,send_from=None,addram=[]): # copy addr and edit category 

		for x1 in grid_lol3:
			for kk,vv in x1.items(): # kk= head or alias 
				if kk=='head':
					continue
			
				addr=''
				bsel_uid='select'+kk
				
				if 'tooltip' in vv[6] and send_from!=None:
					addr=vv[6]['tooltip']
					
					def set_and_destroy(addr,alias):
						amount_uid='Total'+alias
						loc_addram=addram.copy()
						if loc_addram==[]:
							loc_addram=['z1','setmax1']
							send_from.set_textvariable(loc_addram[0], addr) # addr
							tmpv=float(wallet_details.get_value(amount_uid) )-0.0001
							send_from.set_textvariable(loc_addram[1], tmpv ) # amount 
						else:
							send_from.set_textvariable(addram[0], addr)
							
						wallet_details.master.master.destroy()
					
					wallet_details.set_cmd(bsel_uid,[addr,kk],set_and_destroy)
							

	def get_addr_from_wallet(self,set_and_destroy,send_from,addram,sending_to=False,*evargs):

		selframe = Toplevel() #tk.Tk()
		selframe.title('Select address ')
		filter_frame=ttk.LabelFrame(selframe,text='Filter')
		filter_frame.grid(row=0,column=0)
			
			
		filtbox=ttk.Combobox(filter_frame,textvariable='All',values=self.own_wallet_categories(), state="readonly")
		filtbox.current(0)
		filtbox.pack()
		
		
		grid_lol_select= self.prepare_own_addr_frame('All',sending_to) # 4 sec 

		list_frame=ttk.LabelFrame(selframe,text='Addresses list')
		list_frame.grid(row=1,column=0)
		select_table=flexitable.FlexiTable(list_frame,grid_lol_select,600,True) #params=None, grid_lol=None

		self.prepare_own_addr_button_cmd(grid_lol_select,select_table, send_from,addram )

		def refresh_add_list(*eventsargs):
			filterval=filtbox.get()
			
			grid_lol_select= self.prepare_own_addr_frame(filterval,sending_to)
			select_table.update_frame(grid_lol_select)
			
		
		filtbox.bind("<<ComboboxSelected>>",  refresh_add_list )





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
		
		
		
		
		

	# address book  categories_filter
	def get_addr_from_book(self,uid,set_and_destroy,*evargs):

		print('# get_last_addr_from(self) set_last_addr_from(self,addr)')
		selframe = Toplevel() #tk.Tk()
		selframe.title('Select address '+str(uid))
		filter_frame=ttk.LabelFrame(selframe,text='Filter')
		filter_frame.grid(row=0,column=0)

		filtbox=ttk.Combobox(filter_frame,textvariable='All',values= self.categories_filter(), state="readonly")
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
		
				
		for ij,ar in enumerate(grid_lol_select):
			if ij<1: continue
			for ki,vi in ar.items():
				
				select_table.set_cmd( vi[0]['uid'],[vi[4]['L'],uid,selframe ],set_and_destroy) # print to master and destroy ?
		
		def update_filter(*someargs):
			global grid_lol_select
			update_grid()	
			select_table.update_frame(grid_lol_select)
			
		filtbox.bind("<<ComboboxSelected>>",  update_filter )
					



		
		

	def setaddrbook(self,parent_frame): 
				
		global idb, grid_settings, form_grid, cur_addr 
		
		frame0=ttk.LabelFrame(parent_frame,text='Filter') 
		frame0.grid(row=0,column=0, sticky="nsew")
		tmpdict={}
		tmpdict['summary']=[{'T':'Combox', 'uid':'filter', 'V':self.categories_filter() }]
		grid_filter=[]							
		grid_filter.append(tmpdict )
		
		filter_table=flexitable.FlexiTable(frame0,grid_filter)
		
		
		# addr book view left:
		frame1=ttk.LabelFrame(parent_frame,text='Addresses list') 
		frame1.grid(row=1,column=0, sticky="nsew")
			
		grid_settings=[]
		tmpdict={}
		tmpdict['head']=[{'T':'LabelC', 'L':'Usage' } , 
						{'T':'LabelC', 'L':'Category' } , 
						{'T':'LabelC', 'L':'Alias' } , 
						{'T':'LabelC', 'L':'Full address' } , 
						{'T':'LabelC', 'L':'Valid' } , 
						{'T':'LabelC', 'L':'View Key' } , 
						{'T':'LabelC', 'L':'Valid' } , 
						{'T':'LabelC', 'L':' ' } , 
						{'T':'LabelC', 'L':' ' } , 
						{'T':'LabelC', 'L':' ' } 
						]		
						
		grid_settings.append(tmpdict)
		
		idb=localdb.DB()
		cur_addr=[]
		
		def update_grid(*argsevnts):
			global idb, grid_settings
			
			tmplen=len(grid_settings)
			if tmplen>1:
				del grid_settings[1:tmplen]
				del cur_addr[0:]
			
			sel_addr_book=idb.select('addr_book',[ 'Category','Alias','Address','ViewKey','usage','addr_verif','viewkey_verif'], orderby=[{'usage':'desc'},{'Category':'asc'},{'Alias':'asc' }] )
			if len(sel_addr_book)>0:
			
				filterv=filter_table.get_value('filter')
			
				for ii,rr in enumerate(sel_addr_book):
					tmpdict={}
					visible=False
					if filterv in [rr[0],'All']:
						visible=True
						
					cur_addr.append(rr[2])
					
					tmphasvk=False
					tmpnott={'T':'LabelV', 'L':str(tmphasvk), 'uid':'View'+str(ii) , 'visible':visible }
					if rr[3].strip()!='':
						tmphasvk=True
						tmpnott={'T':'LabelV', 'L':str(tmphasvk), 'uid':'View'+str(ii) , 'visible':visible, 'tooltip':rr[3].strip() }
						
					addrvalid='Waiting'
					if rr[5]==-1:
						addrvalid='No'
					elif rr[5]==1:
						addrvalid='Yes'
						
					
					viewk_valid='None'
					if rr[6]==-1:
						viewk_valid=='No'
					elif rr[6]==-1:
						viewk_valid='Yes'
					elif rr[6]==0:
						viewk_valid='Waiting'
						
					tmpdict[ii]=[{'T':'LabelV', 'L':str(rr[4]), 'uid':'Usage'+str(ii) , 'visible':visible} , 
							{'T':'LabelV', 'L':rr[0], 'uid':'Category'+str(ii) , 'visible':visible} , 
							{'T':'LabelV', 'L':rr[1], 'uid':'Alias'+str(ii) , 'visible':visible} , 
							{'T':'InputL', 'L':rr[2], 'uid':'Address'+str(ii) , 'visible':visible,'width':32} , 
							{'T':'LabelV', 'L':addrvalid, 'uid':'AddressValid'+str(ii) , 'visible':visible} , 
							tmpnott , 
							{'T':'LabelV', 'L':viewk_valid, 'uid':'ViewKeyValid'+str(ii) , 'visible':visible} , 
							{'T':'Button', 'L':'edit', 'uid':'edit'+str(ii), 'visible':visible } , 
							{'T':'Button', 'L':'delete', 'uid':'delete'+str(ii), 'visible':visible } , 
							{'T':'Button', 'L':'copy', 'uid':'copy'+str(ii), 'visible':visible } , 
							{'T':'Button', 'L':'sendto', 'uid':'sendto'+str(ii) , 'visible':visible} 
							]
					grid_settings.append(tmpdict)
			
		update_grid()
			
		main_table=flexitable.FlexiTable(frame1,grid_settings)
		
		def update_filter(update_fun,*someargs):
			global grid_settings
			update_grid()	
			main_table.update_frame(grid_settings)
			update_fun()
			
			
		# form for edit and add:
		frame2=ttk.LabelFrame(parent_frame,text='Add/edit form') #.grid(row=0,column=0,columnspan=3,sticky="nsew") #pack(fill='x')
		frame2.grid(row=1,column=1, sticky="nsew")
		form_grid=[]
		init_form=[{'T':'Button','L':'Import','uid':'import'},
						{'T':'LabelC', 'L':'Category'} , 
						{'T':'InputL','uid':'cat','width':32},
						{'T':'LabelC', 'L':'Alias' } , 
						{'T':'InputL','uid':'alia'},
						{'T':'LabelC', 'L':'Full address' } , 
						{'T':'InputL','uid':'addr','width':32},
						{'T':'LabelC', 'L':'View key' } , 
						{'T':'InputL','uid':'viewkey','width':32},
						{'T':'Button','L':'Save','uid':'enter'}
						]	
		
		for ii,inf in enumerate(init_form):
			tmpdict={}
			tmpdict[ii]=[inf]	
						
			form_grid.append(tmpdict)
		
		form_table=flexitable.FlexiTable(frame2,form_grid)
			
		# button functions:
		
		def delete_addr(uid,addr,alias,update_fun):
			global idb, grid_settings
			
			tf=flexitable.msg_yes_no('Delete from address book?','Please confirm to delete address\n\n'+addr+'\n\nof alias\n\n'+alias+'\n')
			
			if tf:
				idb.delete_where('addr_book',{'Address':['=',"'"+addr+"'"]})
				update_grid()
				main_table.update_frame(grid_settings)
				update_fun()		
			
			
		def edit_addr(uid,addr,alias,category,viewkey): # load data to form
			global idb, form_grid
			
			form_table.set_textvariable('cat',category)
			form_table.set_textvariable('alia',alias)
			form_table.set_textvariable('addr',addr)
			form_table.set_textvariable('viewkey',viewkey)
			
			
			
		def increment_usage(addr , update_fun): # when copy or sendto
			global idb, grid_settings
			sel_addr_book=idb.select('addr_book',[ 'usage'],{'Address':['=',"'"+addr+"'"]} )
			table={}
			table['addr_book']=[{'usage':int(sel_addr_book[0][0])+1}]  
			idb.upsert(table,['usage'],{'Address':['=',"'"+addr+"'"]})
			
			update_grid()	
			main_table.update_frame(grid_settings)
			update_fun()		
			
			
			
		def subcopy(main_table,addr , update_fun):
			
			flexitable.copy(main_table,addr)
			increment_usage(addr , update_fun)
			
		def subsendto(addr , update_fun, sendto_fun):
			sendto_fun(addr)
			increment_usage(addr , update_fun)
		
			
		# buttons commands for main grid:
		def update_buttons():
			global idb, form_grid, grid_settings
			for x1 in grid_settings:
			
				for kk,vv in x1.items():  
					if kk=='head':
						continue
				
					addr=main_table.get_value('Address'+str(kk) )
					alias=main_table.get_value('Alias'+str(kk) )
					categ=main_table.get_value('Category'+str(kk) )
					viewk=''
					
					if 'tooltip' in vv[5]:
						viewk=vv[5]['tooltip'] #main_table.get_value('View'+str(kk) )
				
					edit_uid='edit'+str(kk)
					main_table.set_cmd(edit_uid,[kk,addr,alias,categ,viewk],edit_addr)
					
					del_uid='delete'+str(kk) # remove from db and update view
					main_table.set_cmd(del_uid,[kk,addr,alias,update_buttons],delete_addr)
					
					
					copy_uid='copy'+str(kk) # remove from db and update view
					main_table.set_cmd(copy_uid,[main_table,addr,update_buttons ],  subcopy)
					
					send_uid='sendto'+str(kk)
					main_table.set_cmd(send_uid,[ addr,update_buttons,self.wds.send_to_addr ], subsendto )
					
		update_buttons()
				
			
		filter_table.bind_combox_cmd('filter',[update_buttons], update_filter )	
		
		
		def update_filter_values():
			# global wds
			tmpdict={}
			tmpdict['summary']=[{'T':'Combox', 'uid':'filter', 'V': self.categories_filter() }]
			grid_filter=[]							
			grid_filter.append(tmpdict )		
			filter_table.update_frame(grid_filter)
		
		

		def save_new():
			global idb, form_grid, grid_settings
			table={}
			tmpaddr=form_table.get_value('addr').strip()
			
			if tmpaddr=='':
				return
				
			tmpvk=form_table.get_value('viewkey').strip()
			tmpcat=form_table.get_value('cat').strip()
			tmpalia=form_table.get_value('alia').strip()
			
			sel_addr_book=idb.select('addr_book',[ 'ViewKey','addr_verif','viewkey_verif'],{'Address':['=',"'"+tmpaddr+"'"]})
			tmpaddr_valid=0
			tmpvk_valid=-2
			if len(sel_addr_book)>0:
				if sel_addr_book[0][0]!=tmpvk and tmpvk!='':
					tmpvk_valid=0
				else:
					tmpaddr_valid=sel_addr_book[0][1]
					tmpvk_valid=sel_addr_book[0][2]
			
			
			if tmpaddr in cur_addr:
				table={}
				table['addr_book']=[{'Category':tmpcat,'Alias':tmpalia,'Address':tmpaddr,'ViewKey':tmpvk,'addr_verif':tmpaddr_valid,'viewkey_verif':tmpvk_valid }] 
				idb.upsert(table,[ 'Category','Alias','Address','ViewKey','addr_verif','viewkey_verif' ],{'Address':['=',"'"+tmpaddr+"'"]})
				
				if tmpvk_valid==0: # upsert to prevent double action
					table={}
					tmpjson=json.dumps({'addr':tmpaddr,'viewkey':tmpvk})
					table['queue_waiting']=[localdb.set_que_waiting(command='import_view_key',jsonstr=tmpjson, wait_seconds=0)]
					idb.upsert(table,['type','wait_seconds','created_time','command' ,'json','id','status' ],{'command':['=',"'"+import_view_key+"'"],'json':['=',"'"+tmpjson+"'"] })
			else:
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
			
			form_table.set_textvariable('cat','')
			form_table.set_textvariable('alia','')
			form_table.set_textvariable('addr','')
			form_table.set_textvariable('viewkey','')
			update_grid()
			main_table.update_frame(grid_settings)
			update_buttons()
			
			update_filter_values()
			
			
		form_table.set_cmd('enter',[ ],save_new)
		
		# open dialog to select file
		# 2 types : zaddr or viewkey
		def import_z(): 
			global zpath
			zpath=flexitable.get_file_dialog("Select file with z-address or view key")
			if zpath==None:
				return
				
			tmpval=[]
			
			# if len(tmpval)>0:
			def whilewaiting(tmpval2):
				global zpath
				
				if tmpval2[0]==' ':
					return
				cc=aes.Crypto()
				
				decr_val=cc.aes_decrypt_file(path1=zpath,path2=None,password=tmpval2[0])
			
				try:
					ddi=json.loads(decr_val)
					
					if 'viewkey' in ddi:
						form_table.set_textvariable('cat','ViewKey')
						form_table.set_textvariable('addr',ddi['addr'])
						form_table.set_textvariable('viewkey',ddi['viewkey'])
					else:
						form_table.set_textvariable('addr',ddi['addr'])			 
					
				except:
					flexitable.showinfo('Could not decrypt file','File '+zpath+' does not contain encrypted address or view key or you have wrong password!')
			
			
			flexitable.ask_password(tmpval,'Decrypting file','\n Decrypting file '+zpath+'\n\nEnter password\n',whilewaiting) # set password if needed ?
			
		
		
		form_table.set_cmd('import',[ ],import_z)
