

import os,sys
import datetime
import json
import time
# import modules.localdb as localdb
import modules.app_fun as app_fun

import modules.gui as gui

global global_db

class TasksHistory:

	def update_filter_cmd(self,from_update_list=[]):
		tmpcommands=self.distinct_task_commands.copy()
		if len(self.distinct_task_commands)==0:
			# idb=localdb.DB(self.db)
			task_done=global_db.select('queue_done', ['command'],distinct=True)
			tmpcommands=[cc[0] for cc in task_done]
			
		colnames=['Category','Command','Last','Result']
		tmpdict={}
		tmpdict['rowk']='filters'
		tmpdict['rowv']=[ {'T':'Combox',  'V':['All','manual','auto'] }
							, {'T':'Combox', 'V':['All']+tmpcommands }
							, {'T':'Combox', 'V':['24h','week','month','12 months','All'] }
							, {'T':'Combox',  'V':['All','Failed','Success'] }
							]
		grid_filter=[]
		grid_filter.append(tmpdict )
		
		self.filter_table.updateTable(grid_filter,colnames)    #update_frame(grid_filter,head_offset=-1)
		
		
		
	def update_history_frame(self,*eventargs):
		if not self.update_in_progress:
			self.update_in_progress=True
			# self.grid_settings=[]
			self.update_list()
			
			# self.main_table.update_frame(self.grid_settings)
			self.main_table.updateTable(self.grid_settings,self.colnames)
			self.update_filter_cmd()
			self.update_in_progress=False
		
		
		
		

	def __init__(self,db ):
		self.db=db
		self.grid_settings=[]
		self.distinct_task_commands=[]
		self.update_in_progress=False
		self.parent_frame = gui.ContainerWidget(None,layout=gui.QVBoxLayout() )

		frame0=gui.FramedWidgets(None,'Filter') #ttk.LabelFrame(parent_frame,text='Filter') # 
		frame0.setMaximumHeight(128)
		self.parent_frame.insertWidget(frame0)
		
		
		self.filter_table=gui.Table(None,params={'dim':[1,4],'updatable':1} )  #flexitable.FlexiTable(frame0,grid_filter) 
		frame0.insertWidget(self.filter_table)
		self.update_filter_cmd()
		
		frame1=gui.FramedWidgets(None,'Tasks list')    
		self.parent_frame.insertWidget(frame1)
		# frame1.grid(row=1,column=0, sticky="nsew")
			
		tmpdict={}
		
		self.colnames=['Category','Command','Command json','Created at','Finished at','Result','wait_seconds','Result details']
			
		self.update_list()
		
		self.main_table=gui.Table(None,params={'dim':[len(self.grid_settings),len(self.colnames)],'updatable':1,'default_sort_col':'Created at'} )  #flexitable.FlexiTable(frame0,grid_filter) 
		frame1.insertWidget(self.main_table)    #flexitable.FlexiTable(frame1,self.grid_settings, min_canvas_width=1200,force_scroll=True)
		self.main_table.updateTable(self.grid_settings,self.colnames)
		
		self.filter_table.cellWidget(0,0).set_fun(self.update_history_frame )    
		self.filter_table.cellWidget(0,1).set_fun(self.update_history_frame) #.bind_combox_cmd('result',[],  self.update_history_frame )	
		self.filter_table.cellWidget(0,2).set_fun(self.update_history_frame) #.bind_combox_cmd('command',[],  self.update_history_frame )	
		self.filter_table.cellWidget(0,3).set_fun(self.update_history_frame) #.bind_combox_cmd('last',[],  self.update_history_frame )
	
	
	def update_list(self):
	
		# idb=localdb.DB(self.db)
		
		wwhere={}
		llast=self.filter_table.cellWidget(0,2).currentText() #.get_value('last')
		if llast=='24h':  
			wwhere['datetime(created_time)']=['>=',"datetime('"+app_fun.date2str(datetime.datetime.now()-datetime.timedelta(hours=24) )+"')"]
		elif llast=='week':  
			wwhere['datetime(created_time)']=['>=',"datetime('"+app_fun.date2str(datetime.datetime.now()-datetime.timedelta(days=7) )+"')"]
		elif llast=='month':  
			wwhere['datetime(created_time)']=['>=',"datetime('"+app_fun.date2str(datetime.datetime.now()-datetime.timedelta(days=31) )+"')"]
		elif llast=='12 months':  
			wwhere['datetime(created_time)']=['>=',"datetime('"+app_fun.date2str(datetime.datetime.now()-datetime.timedelta(days=365) )+"')"]
		
		task_done=global_db.select('queue_done', ['type','command','json','created_time','end_time','result','wait_seconds','id'],where=wwhere,orderby=[{'end_time':'desc'},{'created_time':'desc'}])
		
		ccat=self.filter_table.cellWidget(0,0).currentText() #get_value('category')
		rres=self.filter_table.cellWidget(0,3).currentText() #.get_value('result')
		cmd=self.filter_table.cellWidget(0,1).currentText() #.get_value('command')
		
		self.grid_settings=[]
		
		self.distinct_task_commands=[]
	
		for rr in task_done:
		
			if rr[1] not in self.distinct_task_commands: self.distinct_task_commands.append(rr[1])
				
			tmpdict={}
			sstyle={'bgc':'green','fgc':'#fff'}
			short_result='Success/True'
			if 'error' in rr[5].lower() or 'failed' in rr[5].lower() or 'false' in rr[5].lower():
				short_result='Failed/False'
				sstyle={'bgc':'red','fgc':'black'}
			elif 'canceled' in rr[5].lower():
				short_result='Canceled'
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
				
			tmpdict['rowk']=rr[7]
			tmpdict['rowv']=[{'T':'LabelV', 'L':rr[0], 'uid':'cat'+str(rr[7]), 'visible':visible } , 
							{'T':'LabelV', 'L':rr[1], 'uid':'cmd'+str(rr[7]) , 'visible':visible} , 
							{'T':'LineEdit', 'V': rr[2], 'uid':'json'+str(rr[7]) , 'visible':visible, 'width':24} , 
							{'T':'LabelV', 'L':rr[3], 'uid':'ctime'+str(rr[7]) , 'visible':visible} , 
							{'T':'LabelV', 'L':rr[4], 'uid':'etime'+str(rr[7]), 'visible':visible} , 
							{'T':'LabelV', 'L':short_result, 'uid':'res'+str(rr[7]) , 'visible':visible, 'style':sstyle} , 
							{'T':'LabelV', 'L':str(rr[6]), 'uid':'wait'+str(rr[7]) , 'visible':visible} , 
							{'T':'LineEdit', 'V': rr[5], 'uid':'details'+str(rr[7]), 'visible':visible, 'width':32 } #app_fun.json_to_str(rr[5] )
							]	
							
			self.grid_settings.append(tmpdict)
			
		# return distinct_task_commands
