



# import tkinter as tk
# from tkinter import filedialog, StringVar, ttk, messagebox, Toplevel 
import os
import datetime
import json
import time
# import modules.localdb as localdb
import modules.app_fun as app_fun
# import operator
# import modules.flexitable as flexitable
import modules.gui as gui

global global_db

class TransactionsHistory:

	def update_history_frame(self,*eventargs):
	
		if not self.update_in_progress:
			self.update_in_progress=True
			# self.grid_settings=[]
			self.update_list()
			self.main_table.updateTable(self.grid_settings,self.colnames) #update_frame(self.grid_settings)
			self.update_in_progress=False
		
		
	def __init__(self,db ):
		self.grid_settings=[]
		self.update_in_progress=False
		self.parent_frame = gui.ContainerWidget(None,layout=gui.QVBoxLayout() )
		self.db=db
		# idb=localdb.DB(self.db)
		# task_done=idb.select('tx_history', ['Category','Type','status','txid','block','date_time','from_str','to_str','amount','uid'],where=wwhere,orderby=[{'block':'desc'},{'Type':'asc'},{'timestamp':'desc'}])
		
		frame0=gui.FramedWidgets(None,'Filter') #ttk.LabelFrame(parent_frame,text='Filter')  
		frame0.setMaximumHeight(128)
		self.parent_frame.insertWidget(frame0)
		# frame0.grid(row=0,column=0, sticky="nsew")
		
		filter_colnames=['Category','Type','Last','Status']
		tmpdict={}
		tmpdict['rowk']='filters'
		tmpdict['rowv']=[ {'T':'Combox',  'V':['All','send','merge','other'] } 
							, {'T':'Combox' , 'V':['All','in','out'] } 
							, {'T':'Combox',  'V':['24h','week','month','12 months','All'] } 
							, {'T':'Combox',  'V':['All','sent','received','notarized' ] }
							]
		grid_filter=[]
		grid_filter.append(tmpdict )
		
		self.filter_table=gui.Table(None,params={'dim':[1,4],'updatable':1} )  #, 'toContent':1
		self.filter_table.updateTable(grid_filter,filter_colnames)
		frame0.insertWidget(self.filter_table)
		
		# addr book view left:
		frame1=gui.FramedWidgets(None,'Transactions list') #ttk.LabelFrame(parent_frame,text='Transactions list') 
		self.parent_frame.insertWidget(frame1)
		
		tmpdict={}
		
		self.colnames=['Category','Type','Status','Block','Date time','Amount','From','To','txid']

		self.update_list()
		
		self.main_table=gui.Table(None,params={'dim':[len(self.grid_settings),len(self.colnames)],'updatable':1,'default_sort_col':'Date time'} )
		frame1.insertWidget(self.main_table)     
		self.main_table.updateTable(self.grid_settings,self.colnames)
		
		self.filter_table.cellWidget(0,0).set_fun(self.update_history_frame )    
		self.filter_table.cellWidget(0,1).set_fun(self.update_history_frame)
		self.filter_table.cellWidget(0,3).set_fun(self.update_history_frame)	
		self.filter_table.cellWidget(0,2).set_fun(self.update_history_frame)
	
	
	
	def update_list(self):
	
		# idb=localdb.DB(self.db)
		
			# ['Category','Type','Last','Status']
		wwhere={}
		llast=self.filter_table.cellWidget(0,2).currentText() #get_value('last')
		
		if llast=='24h':  
			wwhere['timestamp']=['>=',str( (datetime.datetime.now()-datetime.timedelta(hours=24) ).timestamp() )]
		elif llast=='week':  
			wwhere['timestamp']=['>=',str( (datetime.datetime.now()-datetime.timedelta(days=7) ).timestamp() )  ]
		elif llast=='month':  
			wwhere['timestamp']=['>=',str( (datetime.datetime.now()-datetime.timedelta(days=31) ).timestamp() ) ]
		elif llast=='12 months':  
			wwhere['timestamp']=['>=',str( (datetime.datetime.now()-datetime.timedelta(days=365) ).timestamp() ) ]
		
		# ['Category','Type','Last','Status']
		ccat=self.filter_table.cellWidget(0,1).currentText() #get_value('category') {'T':'Combox' , 'V':['All','in','out'] } 
		rres=self.filter_table.cellWidget(0,3).currentText() #.get_value('result')  {'T':'Combox',  'V':['All','sent','received','notarized' ] }
		cmd=self.filter_table.cellWidget(0,0).currentText() #.get_value('command') ['All','send','merge','other']
		
		self.grid_settings=[]
		
		# print('ccat,rres,cmd',)
		if rres!='All':
			# wwhere['Type']=['=',"'"+rres+"'"]
			wwhere['status']=['=',"'"+rres+"'"]
			
		if ccat!='All':
			wwhere['Type']=['=',"'"+ccat+"'"]
			# wwhere['Category']=['=',"'"+ccat+"'"]
			# if ccat=='other':
				# wwhere['Category']=[' not in ',"('send','merge')"]
		if cmd!='All':
			# wwhere['status']=['=',"'"+cmd+"'"]
			wwhere['Category']=['=',"'"+cmd+"'"]
			if ccat=='other':
				wwhere['Category']=[' not in ',"('send','merge')"]
		
		# print('wwhere',wwhere)
		task_done=global_db.select('tx_history', ['Category','Type','status','txid','block','date_time','from_str','to_str','amount','uid'],where=wwhere,orderby=[{'block':'desc'},{'Type':'asc'},{'timestamp':'desc'}])
		
		# self.filter_table.cellWidget(0,1).set_fun(self.update_history_frame) # update filter based on this 
		dist_types=['All','in','out']
		tmp_cut_selection=self.filter_table.cellWidget(0,1).text()
		
		for ij,rr in enumerate(task_done):
		
			# print('tx_history',rr)
			if rr[1] not in dist_types: dist_types.append(rr[1])
			
			tmpdict={}
			sstyle={'bgc':'green','fgc':'#fff'}
			if 'sent' in rr[2].lower() or 'received' in rr[2].lower():
				sstyle={'bgc':'blue','fgc':'#fff'}
							
			visible=True
			tmpdict['rowk']=rr[9]
			from_str=rr[6].replace('\0','')
			tmpdict['rowv']=[{'T':'LabelV', 'L':rr[0], 'uid':'cat'+str(rr[9]), 'visible':visible } , 
							{'T':'LabelV', 'L':rr[1], 'uid':'type'+str(rr[9]) , 'visible':visible} , 
							{'T':'LabelV', 'L':rr[2], 'uid':'stat'+str(rr[9]) , 'visible':visible, 'style':sstyle} , 
							{'T':'LabelV', 'L':str(rr[4]), 'uid':'block'+str(rr[9]), 'visible':visible  } ,
							{'T':'LabelV', 'L': rr[5]  , 'uid':'ts'+str(rr[9]) , 'visible':visible} , 
							{'T':'LabelV', 'L':str(rr[8]), 'uid':'am'+str(rr[9]) , 'visible':visible} , 
							{'T':'LineEdit', 'V': from_str, 'uid':'from'+str(rr[9]), 'visible':visible, 'width':24} , 
							{'T':'LineEdit', 'V': rr[7], 'uid':'to'+str(rr[9]) , 'visible':visible, 'width':24} , 
							{'T':'LineEdit', 'V': rr[3] , 'uid':'txid'+str(rr[9]) , 'visible':visible, 'width':6} 
							]	
							
							
			self.grid_settings.append(tmpdict)
			
		self.filter_table.cellWidget(0,1).updateBox( dist_types)
		self.filter_table.cellWidget(0,1).setIndexForText(tmp_cut_selection)
