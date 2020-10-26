
import tkinter as tk
from tkinter import filedialog, StringVar, ttk, messagebox, Toplevel 
import os,sys
import datetime
import json
import time
import modules.localdb as localdb
import modules.app_fun as app_fun
# import operator
import modules.flexitable as flexitable

class TasksHistory:

	def update_filter_cmd(self):
		idb=localdb.DB()
		task_done=idb.select('queue_done', ['command'],distinct=True)
		tmpcommands=[cc[0] for cc in task_done]
		tmpdict={}
		tmpdict['filters']=[{'T':'LabelC', 'L':'Category: '}
							, {'T':'Combox', 'uid':'category', 'V':['All','manual','auto'] }
							, {'T':'LabelC', 'L':'Command: '}
							, {'T':'Combox', 'uid':'command', 'V':['All']+tmpcommands }
							, {'T':'LabelC', 'L':'Last: '}
							, {'T':'Combox', 'uid':'last', 'V':['24h','week','month','12 months','All'] }
							, {'T':'LabelC', 'L':'Result: '}
							, {'T':'Combox', 'uid':'result', 'V':['All','Failed','Success'] }
							]
		grid_filter=[]
		grid_filter.append(tmpdict )
		
		self.filter_table.update_frame(grid_filter,head_offset=-1)
		
	def update_history_frame(self,*eventargs):
		if not self.update_in_progress:
			self.update_in_progress=True
			self.grid_settings=[]
			self.update_list()
			
			self.main_table.update_frame(self.grid_settings)
			self.update_filter_cmd()
			self.update_in_progress=False
		

	def __init__(self,parent_frame):
		self.grid_settings=[]
		self.update_in_progress=False

		idb=localdb.DB()
		
		frame0=ttk.LabelFrame(parent_frame,text='Filter') #
		frame0.grid(row=0,column=0, sticky="nsew")
		
		task_done=idb.select('queue_done', ['command'],distinct=True)
		tmpcommands=[cc[0] for cc in task_done]
		tmpdict={}
		tmpdict['filters']=[{'T':'LabelC', 'L':'Category: '}
							, {'T':'Combox', 'uid':'category', 'V':['All','manual','auto'] }
							, {'T':'LabelC', 'L':'Command: '}
							, {'T':'Combox', 'uid':'command', 'V':['All']+tmpcommands }
							, {'T':'LabelC', 'L':'Last: '}
							, {'T':'Combox', 'uid':'last', 'V':['24h','week','month','12 months','All'] }
							, {'T':'LabelC', 'L':'Result: '}
							, {'T':'Combox', 'uid':'result', 'V':['All','Failed','Success','Cancelled'] }
							]
						
		grid_filter=[]
		grid_filter.append(tmpdict )
		
		self.filter_table=flexitable.FlexiTable(frame0,grid_filter) 
		# addr book view left:
		frame1=ttk.LabelFrame(parent_frame,text='Tasks list') 
		frame1.grid(row=1,column=0, sticky="nsew")
			
		tmpdict={}
		tmpdict['head']=[{'T':'LabelC', 'L':'Category' } , 
						{'T':'LabelC', 'L':'Command' } , 
						{'T':'LabelC', 'L':'Command json' } , 
						{'T':'LabelC', 'L':'Created at' } , 
						{'T':'LabelC', 'L':'Finished at' } , 
						{'T':'LabelC', 'L':'Result' } , 
						{'T':'LabelC', 'L':'wait_seconds' } , 
						{'T':'LabelC', 'L':'Result details' }
						]		
						
		self.grid_settings.append(tmpdict)
		
		self.update_list()
		
		self.main_table=flexitable.FlexiTable(frame1,self.grid_settings, min_canvas_width=1200,force_scroll=True)
		
		self.filter_table.bind_combox_cmd('category',[], self.update_history_frame )	
		self.filter_table.bind_combox_cmd('result',[],  self.update_history_frame )	
		self.filter_table.bind_combox_cmd('command',[],  self.update_history_frame )	
		self.filter_table.bind_combox_cmd('last',[],  self.update_history_frame )
	
	
	def update_list(self):
	
		idb=localdb.DB()
		
		wwhere={}
		llast=self.filter_table.get_value('last')
		if llast=='24h':  
			wwhere['datetime(created_time)']=['>=',"datetime('"+app_fun.date2str(datetime.datetime.now()-datetime.timedelta(hours=24) )+"')"]
		elif llast=='week':  
			wwhere['datetime(created_time)']=['>=',"datetime('"+app_fun.date2str(datetime.datetime.now()-datetime.timedelta(days=7) )+"')"]
		elif llast=='month':  
			wwhere['datetime(created_time)']=['>=',"datetime('"+app_fun.date2str(datetime.datetime.now()-datetime.timedelta(days=31) )+"')"]
		elif llast=='12 months':  
			wwhere['datetime(created_time)']=['>=',"datetime('"+app_fun.date2str(datetime.datetime.now()-datetime.timedelta(days=365) )+"')"]
		
		task_done=idb.select('queue_done', ['type','command','json','created_time','end_time','result','wait_seconds','id'],where=wwhere,orderby=[{'end_time':'desc'},{'created_time':'desc'}])
		
		ccat=self.filter_table.get_value('category')
		rres=self.filter_table.get_value('result')
		cmd=self.filter_table.get_value('command')
		

	
		for rr in task_done:
			tmpdict={}
			sstyle={'bgc':'green','fgc':'#fff'}
			short_result='Success/True'
			if 'error' in rr[5].lower() or 'failed' in rr[5].lower() or 'false' in rr[5].lower():
				short_result='Failed/False'
				sstyle={'bgc':'red','fgc':'black'}
			elif 'cancelled' in rr[5].lower():
				short_result='Cancelled'
				sstyle={'bgc':'blue','fgc':'white'}
				
			visible=True
			if ccat not in ['All',rr[0]]:
				continue
				# visible=False
			if cmd not in ['All',rr[1]]:
				continue
				# visible=False
			if rres!='All' and rres not in short_result:
				# print(133,short_result)
				# visible=False
				continue
				
			tmpdict[rr[7]]=[{'T':'LabelV', 'L':rr[0], 'uid':'cat'+str(rr[7]), 'visible':visible } , 
							{'T':'LabelV', 'L':rr[1], 'uid':'cmd'+str(rr[7]) , 'visible':visible} , 
							{'T':'InputL', 'L':rr[2], 'uid':'json'+str(rr[7]) , 'visible':visible, 'width':24} , 
							{'T':'LabelV', 'L':rr[3], 'uid':'ctime'+str(rr[7]) , 'visible':visible} , 
							{'T':'LabelV', 'L':rr[4], 'uid':'etime'+str(rr[7]), 'visible':visible} , 
							{'T':'LabelV', 'L':short_result, 'uid':'res'+str(rr[7]) , 'visible':visible, 'style':sstyle} , 
							{'T':'LabelV', 'L':str(rr[6]), 'uid':'wait'+str(rr[7]) , 'visible':visible} , 
							{'T':'InputL', 'L':rr[5], 'uid':'details'+str(rr[7]), 'visible':visible, 'width':32 } #app_fun.json_to_str(rr[5] )
							]	
							
			self.grid_settings.append(tmpdict)
			
		