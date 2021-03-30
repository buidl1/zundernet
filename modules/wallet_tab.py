
import os
import sys

import time
import json

import modules.deamon as deamon
import modules.localdb as localdb

from modules.tasks_history import TasksHistory
from modules.tx_history import TransactionsHistory
from modules.frame_settings import Settings
from modules.notifications import Notifications
import modules.addr_book as addr_book

import modules.gui as gui


class Worker(gui.QObject):
	finished = gui.Signal()
	refreshed = gui.Signal(list)
	
	
	def __init__(self,init_app,queue_start_stop,dmn): #init_app,wallet_display_set,queue_com,queue_start_stop,dmn,queue_status):
		super(Worker,self).__init__()

		self.queue_start_stop=queue_start_stop
		self.dmn=dmn
		self.init_app=init_app
		self.block_closing=True
		# self.queue_status=queue_status

	@gui.Slot()
	def run(self):
		"""Long-running task."""
		# print('run?',self.init_app.close_thread)
		xx=0
		while not self.init_app.close_thread:

			# if xx % 19 ==1:
				# print('thread working',xx,self.init_app.close_thread,flush=True)
			# print(45,self.queue_start_stop.qsize())
			if self.queue_start_stop.qsize(): # start stop blockchain ON/OFF
				
				try:
				# if True:
					cmd = self.queue_start_stop.get(0)
					# print(48,cmd)
					if cmd['cmd']=='stop_deamon':
						# print('stoping?')
						self.dmn.stop_deamon()
					elif cmd['cmd']=='start_deamon':
						self.dmn.start_deamon(cmd['addrescan'] )
				except : #Queue.Empty:
					print('Queue exception bug?')
					pass
			
			# print(87,self.dmn.started,flush=True)
			vemit=[]
			if self.dmn.started:
				vemit=self.dmn.update_status(xx)
				# print(63,vemit)
				if 'CONNECTED' not in vemit:
					self.block_closing=True
				else:
					self.block_closing=False
			else:
				vemit.append('cmd_queue')
				self.block_closing=False
				# print(self.init_app.autostart)
				if self.init_app.autostart!='no':
					self.init_app.autostart='no'
					self.dmn.start_deamon( )
			
			
			# print('before vemit',vemit)
			self.refreshed.emit(vemit)
			time.sleep(0.3) # change to 0.3
			xx+=1
			# print('after sleep')
			
		# print(self.init_app.close_thread)
			
		self.finished.emit()





# props:
# self.queue_status
# self.tabs1
# bstartstop
# self.stat_lab
# orig needed: stat_lab,bstartstop,wallet_summary_frame,wallet_details,wds,addrb
class WalletTab:

	# self.summary_colnames self.details_colnames
	# self.wallet_summary_frame
	# self.wallet_details
	
	@gui.Slot(str,list,list )
	def display_list(self,strtitle,colnames,listoftxids):
		grid_settings=[]
		for ll in listoftxids:
			# ll=json.loads(ll)
			if ll==[{}]: continue
			
			for kk,vv in ll.items(): 
				tmpdict=[{'T':'LabelC', 'L': str(vv['amount'])}, {'T':'LabelC', 'L': str(vv['conf']) },{'T':'LabelC', 'L': kk}]
				grid_settings.append(tmpdict)
			
		tmpgt=gui.Table(None,{'dim':[len(listoftxids),len(colnames)],'sortable':1,'toContent':1 })
		tmpgt.updateTable(grid_settings,colnames) 
		rootframe =  gui.CustomDialog(self.tabs1,tmpgt, strtitle ) #Toplevel()
		
		
		
	
	@gui.Slot(str,str,str )
	def display_message(self,title,content,to_copy):
		# print('display_message')
		if to_copy!='':
			gui.output_copy_input(self.tabs1,title,(to_copy,))
	
		else:
			strtitle_split=title.split('.')
			tmptitle=title  
			tmpcont=content
			
			if len(strtitle_split)>1:
				tmptitle= strtitle_split[0]
				tmpcont='.'.join(strtitle_split[1:])
			
			gui.messagebox_showinfo(tmptitle,tmpcont,self.tabs1)
			
			if title=='New address created':
				self.wds.wallet_copy_progress()
				self.wds.update_addr_cat_map()
				self.updateWalletDisplay(['wallet'])
	
	
	@gui.Slot(list)
	def updateStatus(self,ll):
		# print('waiting update status')
		while self.update_status_locked:
			time.sleep(1)
			
		self.update_status_locked=True
	
		# print(' update status')
		if len(ll)==2:
			if ll[0]=='append':
				self.stat_lab.setText(self.stat_lab.text()+ll[1]) 
			
			elif ll[0]=='set':
				self.stat_lab.setText(ll[1])
		
		self.update_status_locked=False
		# print('done update status')
				
				
	@gui.Slot(bool)
	def enableStartStop(self,bl):
		self.bstartstop.setEnabled(bl)
		
		
	@gui.Slot(list)
	def updateWalletDisplay(self,wallet_part=[]):
	
		# print('updateWalletDisplay',wallet_part)
		while self.locked:
			# print('waiting, locked')
			time.sleep(2)
		
		self.locked=True
		try:
		
		
			if  'wallet'  in wallet_part :
				self.wds.set_disp_dict()
				
				gridS,cols=self.wds.prepare_summary_frame()
				gridD,col3=self.wds.prepare_byaddr_frame()
				self.wallet_summary_frame.updateTable( gridS )
				if len(gridD)>0:
					self.wallet_details.updateTable(gridD)
					
			if 'cmd_queue' in wallet_part :	
				
				grid_lol4,col4=self.wds.prepare_queue_frame()
				# print(grid_lol4)
				self.queue_status.updateTable(grid_lol4)
				# self.wds.queue_frame_buttons( grid_lol4,self.queue_status)
				
			if 'task_done' in wallet_part :	
				if hasattr(self,'tahi'):
					self.tahi.update_history_frame()
					
			if 'notif_update' in wallet_part :	
				if hasattr(self,'notif'):
					self.notif.update_notif_frame()
					
			if 'tx_history_update' in wallet_part :	
				if hasattr(self,'txhi'):
					self.txhi.update_history_frame()
					
			# if 'tx_history_update' in wallet_part  or 'notif_update' in wallet_part:
				
				
			self.locked=False
			# print('updateWalletDisplay done')
		
		except:
			print('wallet locked?')
			self.locked=False
			
			
			
			
	def __init__(self,autostart,queue_start_stop,wds=None):
	
		self.locked=False
		self.update_status_locked=False
		self.wds=wds
		self.wds.set_disp_dict()
		self.wds.set_format()
		
		self.tabs1=gui.Tabs(None)
		frame01=gui.ContainerWidget(self.tabs1,gui.QGridLayout())
		self.tabs1.insertTab(tab_dict={'My Balance':frame01}  )
		
		
		#
		# Blockchain status 
		#
		stat = gui.FramedWidgets(frame01,'Blockchain status',layout=gui.QHBoxLayout())
		frame01.insertWidget(stat,0,1 ) 
		
		self.stat_lab=gui.Label( stat, 'Blockchain off' )
		stat.insertWidget(self.stat_lab)			
		self.bstartstop=gui.Button(frame01) 
		self.bstartstop.setMaximumWidth(128)
		stat.insertWidget(self.bstartstop)
		# print('autostart',autostart)
		if autostart=='yes':
			self.bstartstop.setText('Stop blockchain')
			self.bstartstop.setEnabled(False) #configure(state='disabled')
		else:
			self.bstartstop.setText('Start blockchain')

		def togglestartstop(elem):
			if elem.text()=='Stop blockchain':
				elem.setText('Start blockchain')
				# print('after start chain')
				elem.setEnabled(False)
				# print('after set enablen')
				queue_start_stop.put({'cmd':'stop_deamon'})
				# print('after que put')				
			else:
				elem.setText('Stop blockchain')	
				elem.setEnabled(False)			 
				def restart(addrescan):
					if addrescan=='No':
						addrescan=False
					else:
						addrescan=True
					
					queue_start_stop.put({'cmd':'start_deamon','addrescan':addrescan})
					
				gui.CmdYesNoDialog(elem,"Rescan wallet?",['No','Yes'],restart)
				
		self.bstartstop.set_fun(False,togglestartstop)
	
		###
		### Manual QUEUE 
		###
		queue = gui.FramedWidgets(None,'Tasks queue',layout=gui.QHBoxLayout())  
		frame01.insertWidget(queue,1,1 ) 
		
		grid_lol4, col4=wds.prepare_queue_frame(True)
		self.queue_status=gui.Table(None,params={'dim':[0,5],'sortable':1,'updatable':1,'toContent':1})
		self.queue_status.updateTable( grid_lol4, col4 ) 
		queue.insertWidget(self.queue_status)

		# wds.queue_frame_buttons( grid_lol4,self.queue_status)
	
	
		###
		### FRAME 2 - summary
		### 
		summary = gui.FramedWidgets(frame01,'Summary',layout=gui.QHBoxLayout())  
		
		summary.setMaximumHeight(128)
		frame01.insertWidget(summary,0,0 )  
		grid_lol_wallet_sum,col_names= wds.prepare_summary_frame( )
		self.summary_colnames=col_names
		self.wallet_summary_frame=gui.Table(summary,params={'dim':[1,6],'updatable':1,'toContent':1})  #'sortable':1,
		self.wallet_summary_frame.updateTable( grid_lol_wallet_sum, col_names )
		summary.insertWidget(self.wallet_summary_frame)

	
	
		
		###
		### FRAME 3 - wallet balances
		###
		table = gui.FramedWidgets(frame01,'Balance by address',layout=gui.QHBoxLayout())  
		frame01.insertWidget(table,1,0 ) 
		
		grid_lol3, colnames=wds.prepare_byaddr_frame()
		self.details_colnames=colnames
		self.wallet_details=gui.Table(summary,params={'dim':[len(grid_lol3),len(colnames)],'sortable':1 ,'updatable':1,'toContent':1 }) #flexitable.FlexiTable(summary,grid_lol_wallet_sum)
		# print(len(grid_lol3) )
		# print(len(colnames),colnames)
		self.wallet_details.updateTable( grid_lol3,colnames ) #update_frame(grid_lol3)
		table.insertWidget(self.wallet_details)
		
		# def set_summary_cmd():
		
			# opt=self.wds.get_options(True)
			# self.wallet_summary_frame.cellWidget(0,3).setIndexForText(opt['rounding'] )
			# self.wallet_summary_frame.cellWidget(0,3).set_fun(save_wallet_display,'rounding')
			
		
		
		
		def save_wallet_display(btn,opt,*evnt):
			 
			idb=localdb.DB(self.wds.db)
			table={}
			
			# vv=wallet_summary_frame.get_value(opt.replace('ing','')) # name similar to uid hence hack 
			vv=btn.currentText()
			# print(opt,vv)
			table['wallet_display']=[{'option':opt, 'value':vv  }]
			idb.upsert(table,['option','value'],{'option':['=',"'"+opt+"'"]})
			
			while self.wds.is_locked():
				# print('locked')
				time.sleep(1)
				
			self.wds.lock_basic_frames()
			
			if opt=='rounding':
				self.wds.set_format( format_str_value=vv)
				# print('rround',rround)
			
			grid_lol_wallet_sum,col_names=self.wds.prepare_summary_frame( )
			self.wallet_summary_frame.updateTable( grid_lol_wallet_sum,col_names ) #update_frame(grid_lol_wallet_sum)
			# set_summary_cmd()
			
			if opt=='filtering':
				# print('filtering ',vv)
				self.wallet_details.filtering( 'widget',0,vv )
			else:
				grid_lol3, colnames=self.wds.prepare_byaddr_frame( )
				new_rows=self.wallet_details.updateTable( grid_lol3,colnames ) #update_frame(grid_lol3)
				# print('save_wallet_display: prepare_byaddr_button_cmd',opt)
				# self.wds.prepare_byaddr_button_cmd(grid_lol3,self.wallet_details)
			
			self.wds.unlock_basic_frames()
			
			
		opt=self.wds.get_options(True)
		self.wallet_summary_frame.cellWidget(0,4).setIndexForText(opt['filtering'] )
		self.wallet_summary_frame.cellWidget(0,4).set_fun(save_wallet_display,'filtering') # only for summary to sum displayed !!! 
		
		def walletActions(cbtn):
			if cbtn.currentText()=='New address':
				self.wds.new_addr(cbtn)
			elif cbtn.currentText()=='Export':
				self.wds.export_wallet(cbtn)
			elif cbtn.currentText()=='Import priv. keys':
				self.wds.import_priv_keys(cbtn)
			elif cbtn.currentText()=='Merge':
				self.wds.merge_utxo(cbtn)
				
			cbtn.setCurrentIndex( 0 )
		
		self.wallet_summary_frame.cellWidget(0,5).set_fun( walletActions)
		
		# self.wallet_summary_frame.cellWidget(0,5).set_fun(False,self.wds.new_addr)
		# self.wallet_summary_frame.cellWidget(0,6).set_fun(False,self.wds.export_wallet)
		# set_summary_cmd()
		
		opt=self.wds.get_options(True)
		self.wallet_summary_frame.cellWidget(0,3).setIndexForText(opt['rounding'] )
		self.wallet_summary_frame.cellWidget(0,3).set_fun(save_wallet_display,'rounding')
		
		save_wallet_display(self.wallet_summary_frame.cellWidget(0,4),'filtering' )
		
		
		
	
	
	def init_additional_tabs(self,addr_book):
		
		self.notif=Notifications(addr_book)
		self.tabs1.insertTab(tab_dict={'Notifications': self.notif.parent_frame}  )
		
		# transaction history 
		self.txhi=TransactionsHistory(self.wds.db)
		self.tabs1.insertTab(tab_dict={'TX History': self.txhi.parent_frame}  )
		
		# tasks history
		self.tahi=TasksHistory(self.wds.db)
		self.tabs1.insertTab(tab_dict={'Tasks History': self.tahi.parent_frame}  )
		
		# SETTINGS
		self.settings=Settings( self.wds)
		self.tabs1.insertTab(tab_dict={'Settings': self.settings.parent_frame}  )
		
		# notifications, tasks history, transaction history 
	
