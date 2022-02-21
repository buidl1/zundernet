# frame settings

import os
# import datetime
import json
# import time
import modules.localdb as localdb
import modules.app_fun as app_fun
# import operator
# import modules.flexitable as flexitable
import modules.gui as gui
import modules.aes as aes

class Settings:


	def __init__(self, wds, initApp):
		# global idb
		self.db=wds.db
		self.grid_settings=[]
		self.parent_frame = gui.ContainerWidget(None,layout=gui.QVBoxLayout() )
		
		################ PASS CHANGE
		frame0 = gui.FramedWidgets(None,'Password change',layout=gui.QVBoxLayout())
		self.parent_frame.insertWidget(frame0) 
		def clear_change_info(*evargs):
			newpass=self.pass_table.cellWidget(0,1).text().strip()
			oldpass=self.pass_table.cellWidget(0,0).text().strip()
			
			if oldpass==wds.password:
				if oldpass==newpass:
					gui.showinfo("WARNING - Password NOT changed", "Old and new passwords are the same!",self.parent_frame )
					
					
				else:	
					wds.password=newpass
					initApp.app_password=newpass
					
					db=localdb.DB(self.db )
					cc=aes.Crypto()
					table={} 
					salttmp= cc.init_hash_seed() 
					passhashtmp= cc.hash(newpass+salttmp) 
					disp_dict={'salt':salttmp,'passhash':passhashtmp} # 
					table['jsons']=[{'json_name':"password_hash", 'json_content':json.dumps(disp_dict), 'last_update_date_time': app_fun.now_to_str(False)}]
					db.upsert(table,['json_name','json_content','last_update_date_time'],{'json_name':['=',"'password_hash'"]})

					
					# clear
					self.pass_table.cellWidget(0,0).setText('')
					self.pass_table.cellWidget(0,1).setText('')
					# info
					
					gui.showinfo("Password changed", "You have new password! Leading and trailing spaces where removed from the password to avoid mistakes.",self.parent_frame )
			else:
				gui.showinfo("WARNING - Password NOT changed", "Your old password typed incorrectly! Try again!",self.parent_frame )
		
		# self.password.setEchoMode(QLineEdit.Password)
		def toggle_pass_view( btn):
			tbl=btn.parent().parent()
			if self.pass_table.cellWidget(0,0).echoMode()==gui.QLineEdit.Password:
				self.pass_table.cellWidget(0,0).setEchoMode(gui.QLineEdit.Normal) 
				self.pass_table.cellWidget(0,1).setEchoMode(gui.QLineEdit.Normal) 
			else:
				self.pass_table.cellWidget(0,0).setEchoMode(gui.QLineEdit.Password) 
				self.pass_table.cellWidget(0,1).setEchoMode(gui.QLineEdit.Password) 
		
		colnames=['Current password','New password','','']
		grid_pass=[]
		tmpdict={}
		tmpdict['rowk']='pass_change'
		tmpdict['rowv']=[ {'T':'LineEdit','L':'',  'mode':'pass' }
							, {'T':'LineEdit','L':'', 'mode':'pass' }
							, {'T':'Button', 'L':'Preview', 'fun': toggle_pass_view}
							, {'T':'Button', 'L':'Submit', 'fun': clear_change_info}
							]
		grid_pass.append(tmpdict )	
		
		self.pass_table=gui.Table(frame0,params={'dim':[1,4], 'toContent':1} )       #flexitable.FlexiTable(frame0,grid_pass) # +++ update command filter after each iteration
		self.pass_table.updateTable(grid_pass,colnames)
		
		frame0.insertWidget(gui.Label(None,'To change password you need to have wallet synced!'))
		frame0.insertWidget(self.pass_table)
		self.updatePassChangeState()
		
		
		################ DB maintenance / clear old tasks {'total_chars':total_chars, 'total_rows':rowsii, 'older_chars':older_chars, 'old_rows':old_rows}
		
		# idb=localdb.DB(self.db)
		frame1 = gui.FramedWidgets(None,'DB maintenance',layout=gui.QHBoxLayout())
		self.parent_frame.insertWidget(frame1)
		
		def update_db_info():
			idb=localdb.DB(self.db)
			
			grid_db= []
			colnames=['Table name','Table size','' ]
			
			tmpsize_multi=idb.table_size(['jsons','tx_history','notifications','queue_done'])
			 # {'jsons': {'total_chars': 4645, 'total_rows': 6, 'older_chars': 0, 'old_rows': 0}, 'tx_history': {'total_chars': 0, 'total_rows': 0, 'older_chars': 0, 'old_rows': 0}}
			# print('tmpsize_multi',tmpsize_multi)
			
			tmpsize=tmpsize_multi['jsons'] #idb.table_size('jsons')
			tmpdict={}
			tmpdict['rowk']='json'
			tmpdict['rowv']=[{ 'T':'LabelV', 'L':'[jsons]'}, { 'T':'LabelV', 'L': str(tmpsize['total_chars'])+' chars / '+str(tmpsize['total_rows'])+' rows '}]
			# tmpdict['jsons']=[{'uid':'4','T':'LabelV', 'L':'[jsons] table size: '+str(tmpsize['total_chars'])+' chars '+str(tmpsize['total_rows'])+' rows '}]
			grid_db.append(tmpdict)
			
			tmpsize=tmpsize_multi['tx_history'] #idb.table_size('tx_history')
			tmpdict={}
			tmpdict['rowk']='tx_history'
			tmpdict['rowv']=[{ 'T':'LabelV', 'L':'[tx_history]'}, { 'T':'LabelV', 'L': str(tmpsize['total_chars'])+' chars / '+str(tmpsize['total_rows'])+' rows '}]
			grid_db.append(tmpdict)
			
			
			tmpsize=tmpsize_multi['notifications'] #idb.table_size('notifications')
			tmpdict={}
			tmpdict['rowk']='db_clear_old_notif'
			tmpdict['rowv']=[{ 'T':'LabelV', 'L':'[notifications]'}, { 'T':'LabelV', 'L': str(tmpsize['total_chars'])+' chars / '+str(tmpsize['total_rows'])+' rows '},{'T':'Button', 'L':'Delete older then 1 day','span':2  }]
			grid_db.append(tmpdict)
			
			
			
			tmpsize=tmpsize_multi['queue_done'] #idb.table_size('queue_done')
			tmpdict={}
			tmpdict['rowk']='db_clear_old_tasks'
			tmpdict['rowv']=[{ 'T':'LabelV', 'L':'[tasks]'}, { 'T':'LabelV', 'L': str(tmpsize['total_chars'])+' chars / '+str(tmpsize['total_rows'])+' rows '}]
			grid_db.append(tmpdict)
			
			tmpdict={}
			tmpdict['rowk']='db_clear_old_tasks1'
			tmpdict['rowv']=[ { 'T':'LabelV', 'L':'[tasks] older then 1 month:'}, { 'T':'LabelV', 'L': str(tmpsize['older_chars'])+' chars / '+str(tmpsize['old_rows'])+' rows '}, {'T':'Button', 'L':'Delete older then 1 month','span':2 }]
			grid_db.append(tmpdict)
			
			
			return grid_db, colnames
			
		grid_db, colnames=update_db_info()
		
		# self.db_table=flexitable.FlexiTable(frame1,grid_db)
		self.db_table=gui.Table(None,params={'dim':[5,3],'updatable':1, 'toContent':1} )       #flexitable.FlexiTable(frame0,grid_pass) # +++ update command filter after each iteration
		self.db_table.updateTable(grid_db,colnames)
		frame1.insertWidget(self.db_table)
		
		
		
		
		def delete_old(tname,datetime_colname,ddays,*evargs):
			idb=localdb.DB(self.db)
			idb.delete_old( tname,datetime_colname,ddays )
			grid_db, colnames=update_db_info()
			self.db_table.updateTable(grid_db)
			
		self.db_table.cellWidget(2,2).set_fun(True,delete_old,'queue_done','created_time',31)
		self.db_table.cellWidget(4,2).set_fun(True,delete_old,'notifications','datetime',1)
		
		# return parent_frame
		
	@gui.Slot()	
	@gui.Slot(bool)	
	def updatePassChangeState(self,enable=False):
		
		disable=True-enable

		self.pass_table.cellWidget(0,0).setReadOnly(disable)
		self.pass_table.cellWidget(0,1).setReadOnly(disable)
		if disable:
			self.pass_table.cellWidget(0,0).setStyleSheet(" QLineEdit {background-color:#ccc; border-style: solid;  border-width: 1px; border-color: #aaa;}" )
			self.pass_table.cellWidget(0,1).setStyleSheet(" QLineEdit {background-color:#ccc; border-style: solid;  border-width: 1px; border-color: #aaa;}" )
		else:
			self.pass_table.cellWidget(0,0).setStyleSheet(" QLineEdit {background-color:white; border-style: solid;  border-width: 1px; border-color: #aaa;}" )
			self.pass_table.cellWidget(0,1).setStyleSheet(" QLineEdit {background-color:white; border-style: solid;  border-width: 1px; border-color: #aaa;}" )
		
		self.pass_table.cellWidget(0,2).setEnabled(enable)
		self.pass_table.cellWidget(0,3).setEnabled(enable)
		 
			
