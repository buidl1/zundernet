
import tkinter as tk
from tkinter import filedialog, StringVar, ttk, messagebox, Toplevel 
import os
import datetime
import json
import time
import modules.localdb as localdb
import modules.app_fun as app_fun
# import operator
import modules.flexitable as  flexitable



class Notifications:

	def set_que_waiting(self,command,jsonstr='', wait_seconds=0):
		
		idb=localdb.DB()
		tmparr=[0]
		latestid1=idb.select_max_val( 'queue_done','id' )
		if len(latestid1)>0: 
			
			if latestid1[0][0]!=None:
				tmparr.append(latestid1[0][0])
			
		latestid2=idb.select_max_val( 'queue_waiting','id')
		if len(latestid2)>0: 
			
			if latestid2[0][0]!=None:
				tmparr.append(latestid2[0][0])
		
		nextid=max(tmparr)+1
		
		return {"type":'manual'
				, "wait_seconds":wait_seconds # max time to wait
				, "created_time":app_fun.now_to_str(False) #datetime of creation
				, "command":command # send, new wallet, ... 
				, "json":jsonstr # if needed
				, "id":nextid # uniwue id
				, "status":'waiting' 
				}
	
	def update_notif_frame(self,*eventargs):
	
		if not self.update_in_progress:
			self.update_in_progress=True
			self.grid_notif=[]
			self.update_list()
			self.main_table.update_frame(self.grid_notif)
			self.set_actions()
			self.update_in_progress=False
			self.notebook_parent.tab(1,text='Notif. ('+str(len(self.grid_notif))+')')

			
	def close_all_notif(self,*eventargs):
		
		idb=localdb.DB()
		table={}
		table['notifications']=[{'closed':'True'}]
		idb.update(table,['closed'],{} )
		self.update_notif_frame()
		

	def __init__(self,parent_frame,notebook_parent ):
		
		self.update_in_progress=False
		self.notebook_parent=notebook_parent
		
		frame0=ttk.LabelFrame(parent_frame,text='Filter')  
		frame0.grid(row=0,column=0, sticky="nsew")
		
		tmpdict={}
		tmpdict['filters']=[{'T':'LabelC', 'L':'Category: '}
							, {'T':'Combox', 'uid':'category', 'V':['New','Closed'] }
							, {'T':'Button', 'uid':'clearall', 'L':'Close all' }
							]
		grid_filter=[]
		grid_filter.append(tmpdict )
		
		self.filter_table=flexitable.FlexiTable(frame0,grid_filter) 
		
		self.filter_table.bind_combox_cmd('category',[], self.update_notif_frame )	
		self.filter_table.set_cmd('clearall',[], self.close_all_notif )	
		
		self.grid_notif=[]
		
		frame1=ttk.LabelFrame(parent_frame,text='Notifications list') 
		frame1.grid(row=1,column=0, sticky="nsew")
	
		tmpdict={}
		tmpdict['head']=[{'T':'LabelC', 'L':'Date time' } , 
						{'T':'LabelC', 'L':'Event' } , 
						{'T':'LabelC', 'L':'Operation details' } , 
						{'T':'LabelC', 'L':'Status' },
						{ } , # ok clear
						{ }  # try again
						]		
						
		self.grid_notif.append(tmpdict)

		self.update_list()
		
		self.main_table=flexitable.FlexiTable(frame1,self.grid_notif, min_canvas_width=1000,force_scroll=True)
		self.set_actions()
		self.notebook_parent.tab(1,text='Notif. ('+str(len(self.grid_notif)-1)+')' )

	def set_actions(self):	
	
		def ok_close(struid,*evargs):
			idb=localdb.DB()
			table={}
			table['notifications']=[{'closed':'True'}]
			try:
			
				idb.update(table,['closed'],where={'uid':['=',int(struid)]})
				self.update_notif_frame()
			except:
				
				pass
			
		def queue(strjson,*evargs):
			idb=localdb.DB()
			table={}
			table['queue_waiting']=[self.set_que_waiting('send',jsonstr=strjson ) ]
			idb.insert(table,['type','wait_seconds','created_time','command' ,'json','id','status' ])
			
			messagebox.showinfo('Sending action retry',strjson)
			 
			
		
		for ii,rr in enumerate(self.grid_notif):
			if ii==0:
				continue
				
			for k,r in rr.items():
				if 'T' in r[4]:
					if r[4]['T']=='Button':
						self.main_table.set_cmd(r[4]['uid'],[r[4]['tooltip'] ],ok_close)
				
				
				if 'T' in r[5]:
					if r[5]['T']=='Button': #'tooltip'
						self.main_table.set_cmd(r[5]['uid'],[r[5]['tooltip'] ],queue)
		
		
	
	def update_list(self):
	
		idb=localdb.DB()
		
		ff=self.filter_table.get_value('category')
		wwhere={}
		if ff=='New':  
			wwhere ={'closed':['<>',"'True'"]}
		else:
			wwhere ={'closed':['=',"'True'"]}
		
		task_done=idb.select('notifications', ['uid','datetime' ,'opname' ,'details' ,'status' ,'closed','orig_json'],where=wwhere,orderby=[{'uid':'desc'}])
		
		for ij,rr in enumerate(task_done):
		
			tmpdict={}
							
			visible=True

			okclosebutton={'T':'Button', 'L':'Ok, close', 'uid':'ok'+str(rr[0]) , 'visible':visible, 'tooltip':rr[0]}
			
			if rr[5]=='True':
				okclosebutton={'T':'LabelE'}
			
			requeue={'T':'Button', 'L':'Send again', 'uid':'queue'+str(rr[0]) , 'visible':visible, 'tooltip':rr[6]}
			tmpdetails=rr[3]
			if rr[2] !='send':
				requeue={'T':'LabelE'}
				tmpdetails=rr[6]
				
			tmpdict[rr[0]]=[{'T':'LabelV', 'L':rr[1], 'uid':'date'+str(rr[0]), 'visible':visible } , 
							{'T':'LabelV', 'L':rr[2], 'uid':'name'+str(rr[0]) , 'visible':visible} , 
							{'T':'InputL', 'L':tmpdetails, 'uid':'det'+str(rr[0]) , 'visible':visible, 'width':64} , 
							{'T':'LabelV', 'L': rr[4], 'uid':'stat'+str(rr[0]), 'visible':visible, 'width':11  } ,
							okclosebutton,
							requeue
							]	
							
							
			self.grid_notif.append(tmpdict)