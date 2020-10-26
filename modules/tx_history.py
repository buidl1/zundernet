
import tkinter as tk
from tkinter import filedialog, StringVar, ttk, messagebox, Toplevel 
import os
import datetime
import json
import time
import modules.localdb as localdb
import modules.app_fun as app_fun
# import operator
import modules.flexitable as flexitable

class TransactionsHistory:

	def update_history_frame(self,*eventargs):
	
		if not self.update_in_progress:
			self.update_in_progress=True
			self.grid_settings=[]
			self.update_list()
			self.main_table.update_frame(self.grid_settings)
			self.update_in_progress=False
		
		
	def __init__(self,parent_frame):
		self.grid_settings=[]
		self.update_in_progress=False
	
		idb=localdb.DB()
		
		frame0=ttk.LabelFrame(parent_frame,text='Filter')  
		frame0.grid(row=0,column=0, sticky="nsew")
		
		tmpdict={}
		tmpdict['filters']=[{'T':'LabelC', 'L':'Category: '}
							, {'T':'Combox', 'uid':'category', 'V':['All','send','merge','other'] }
							, {'T':'LabelC', 'L':'Type: '}
							, {'T':'Combox', 'uid':'type', 'V':['All','in','out'] }
							, {'T':'LabelC', 'L':'Last: '}
							, {'T':'Combox', 'uid':'last', 'V':['24h','week','month','12 months','All'] }
							, {'T':'LabelC', 'L':'Status: '}
							, {'T':'Combox', 'uid':'status', 'V':['All','sent','received','notarized' ] }
							]
		grid_filter=[]
		grid_filter.append(tmpdict )
		
		self.filter_table=flexitable.FlexiTable(frame0,grid_filter) 
		
		# addr book view left:
		frame1=ttk.LabelFrame(parent_frame,text='Transactions list') 
		frame1.grid(row=1,column=0, sticky="nsew")
	
		tmpdict={}
		tmpdict['head']=[{'T':'LabelC', 'L':'Category' } , 
						{'T':'LabelC', 'L':'Type' } , 
						{'T':'LabelC', 'L':'Status' } , 
						{'T':'LabelC', 'L':'Block' },
						{'T':'LabelC', 'L':'Date time' } , 
						{'T':'LabelC', 'L':'Amount' } , 
						{'T':'LabelC', 'L':'From' } , 
						{'T':'LabelC', 'L':'To' } , 
						{'T':'LabelC', 'L':'txid' } 
						]
						
		self.grid_settings.append(tmpdict)

		self.update_list()
		
		self.main_table=flexitable.FlexiTable(frame1,self.grid_settings, min_canvas_width=1200,force_scroll=True)
		
		
		self.filter_table.bind_combox_cmd('category',[], self.update_history_frame )	
		self.filter_table.bind_combox_cmd('type',[],  self.update_history_frame )	
		self.filter_table.bind_combox_cmd('status',[],  self.update_history_frame )	
		self.filter_table.bind_combox_cmd('last',[],  self.update_history_frame )
	
	
	def update_list(self):
	
		idb=localdb.DB()
		
			
		wwhere={}
		llast=self.filter_table.get_value('last')
		if llast=='24h':  
			wwhere['timestamp']=['>=',str( (datetime.datetime.now()-datetime.timedelta(hours=24) ).timestamp() )]
		elif llast=='week':  
			wwhere['timestamp']=['>=',str( (datetime.datetime.now()-datetime.timedelta(days=7) ).timestamp() )  ]
		elif llast=='month':  
			wwhere['timestamp']=['>=',str( (datetime.datetime.now()-datetime.timedelta(days=31) ).timestamp() ) ]
		elif llast=='12 months':  
			wwhere['timestamp']=['>=',str( (datetime.datetime.now()-datetime.timedelta(days=365) ).timestamp() ) ]
		
		ccat=self.filter_table.get_value('category')
		rres=self.filter_table.get_value('type')
		cmd=self.filter_table.get_value('status')
		if rres!='All':
			wwhere['Type']=['=',"'"+rres+"'"]
		if ccat!='All':
			wwhere['Category']=['=',"'"+ccat+"'"]
			if ccat=='other':
				wwhere['Category']=[' not in ',"('send','merge')"]
		if cmd!='All':
			wwhere['status']=['=',"'"+cmd+"'"]
		
		
		task_done=idb.select('tx_history', ['Category','Type','status','txid','block','date_time','from_str','to_str','amount','uid'],where=wwhere,orderby=[{'block':'desc'},{'Type':'asc'},{'timestamp':'desc'}])
		
		for ij,rr in enumerate(task_done):
			tmpdict={}
			sstyle={'bgc':'green','fgc':'#fff'}
			if 'sent' in rr[2].lower() or 'received' in rr[2].lower():
				sstyle={'bgc':'blue','fgc':'#fff'}
							
			visible=True
		
			tmpdict[rr[9]]=[{'T':'LabelV', 'L':rr[0], 'uid':'cat'+str(rr[9]), 'visible':visible } , 
							{'T':'LabelV', 'L':rr[1], 'uid':'type'+str(rr[9]) , 'visible':visible} , 
							{'T':'LabelV', 'L':rr[2], 'uid':'stat'+str(rr[9]) , 'visible':visible, 'style':sstyle} , 
							{'T':'LabelV', 'L':str(rr[4]), 'uid':'block'+str(rr[9]), 'visible':visible  } ,
							{'T':'LabelV', 'L': rr[5]  , 'uid':'ts'+str(rr[9]) , 'visible':visible} , 
							{'T':'LabelV', 'L':str(rr[8]), 'uid':'am'+str(rr[9]) , 'visible':visible} , 
							{'T':'InputL', 'L':rr[6], 'uid':'from'+str(rr[9]), 'visible':visible, 'width':24} , 
							{'T':'InputL', 'L':rr[7], 'uid':'to'+str(rr[9]) , 'visible':visible, 'width':24} , 
							{'T':'InputL', 'L': rr[3] , 'uid':'txid'+str(rr[9]) , 'visible':visible, 'width':6} 
							]	
							
							
			self.grid_settings.append(tmpdict)
			