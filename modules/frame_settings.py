# frame settings

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

class Settings:


	def __init__(self,parent_frame,wds):
		global idb
		
		self.grid_settings=[]
	
		
		################ PASS CHANGE
		
		frame0=ttk.LabelFrame(parent_frame,text='Password change')  
		frame0.grid(row=0,column=0, sticky="nsew")
		
		tmpdict={}
		tmpdict['pass_change']=[{'T':'LabelC', 'L':'Current password: '}
							, {'T':'InputL','L':'', 'uid':'old','width':16 }
							, {'T':'LabelC', 'L':'New password: '}
							, {'T':'InputL','L':'', 'uid':'new','width':16 }
							, {'T':'Button', 'L':'Change','uid':'enter','width':8 }
							]
		grid_pass=[]
		grid_pass.append(tmpdict )
		
		self.pass_table=flexitable.FlexiTable(frame0,grid_pass) # +++ update command filter after each iteration
		
		def clear_change_info(*evargs):
			newpass=self.pass_table.get_value('new').strip()
			wds.password=newpass
			# clear
			self.pass_table.set_textvariable('new','')
			self.pass_table.set_textvariable('old','')
			# info
			
			messagebox.showinfo("Password changed", "You have new password! Leading and trailing spaces where removed from the password to avoid mistakes." )
		
		self.pass_table.set_cmd('enter',[], clear_change_info )	
		
		
		
		
		################ DB maintenance / clear old tasks {'total_chars':total_chars, 'total_rows':rowsii, 'older_chars':older_chars, 'old_rows':old_rows}
		
		idb=localdb.DB()
		
		frame1=ttk.LabelFrame(parent_frame,text='DB maintenance')  
		frame1.grid(row=0,column=1, sticky="nsew")
		
		def update_db_info():
			global idb
			
			grid_db= []
			
			tmpsize=idb.table_size('jsons')
			tmpdict={}
			tmpdict['jsons']=[{'uid':'4','T':'LabelV', 'L':'[jsons] table size: '+str(tmpsize['total_chars'])+' chars '+str(tmpsize['total_rows'])+' rows '}]
			grid_db.append(tmpdict)
			
			tmpsize=idb.table_size('tx_history')
			tmpdict={}
			tmpdict['tx_history']=[{'uid':'2','T':'LabelV', 'L':'[tx_history] table size: '+str(tmpsize['total_chars'])+' chars '+str(tmpsize['total_rows'])+' rows '}]
			grid_db.append(tmpdict)
			
			
			tmpsize=idb.table_size('notifications')
			tmpdict={}
			tmpdict['db_clear_old_notif']=[{'uid':'3','T':'LabelV', 'L':'[notifications] table size: '+str(tmpsize['total_chars'])+' chars '+str(tmpsize['total_rows'])+' rows '}]
			grid_db.append(tmpdict)
			tmpdict={}
			tmpdict['db_clear_old_notif2']=[{'T':'Button', 'L':'Delete all notifications','uid':'del_notif'  }]
			grid_db.append(tmpdict)
			
			
			
			
			tmpsize=idb.table_size('queue_done')
			tmpdict={}
			tmpdict['db_clear_old_tasks']=[{'uid':'0','T':'LabelV', 'L':'Tasks history table size: '+str(tmpsize['total_chars'])+' chars '+str(tmpsize['total_rows'])+' rows '}]
			grid_db.append(tmpdict)
			tmpdict={}
			tmpdict['db_clear_old_tasks1']=[{'uid':'1','T':'LabelV', 'L':'Older then 1 month: '+str(tmpsize['older_chars'])+' chars '+str(tmpsize['old_rows'])+' rows '}]
			grid_db.append(tmpdict)
			tmpdict={}
			tmpdict['db_clear_old_tasks2']=[{'T':'Button', 'L':'Delete old tasks','uid':'del'  }]
			grid_db.append(tmpdict)
			
			return grid_db
			
		grid_db=update_db_info()
		
		self.db_table=flexitable.FlexiTable(frame1,grid_db)
		
		def delete_old(tname,datetime_colname,ddays,*evargs):
			global idb
			idb.delete_old( tname,datetime_colname,ddays )
			self.db_table.update_frame(update_db_info())
			
			self.db_table.set_cmd('del',['queue_done','created_time',31], delete_old )	
			self.db_table.set_cmd('del_notif',['notifications','datetime',0], delete_old )	
			
		
		self.db_table.set_cmd('del',['queue_done','created_time',31], delete_old )	
		self.db_table.set_cmd('del_notif',['notifications','datetime',0], delete_old )	
	