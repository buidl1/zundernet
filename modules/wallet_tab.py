
import os
import sys

import time
import json

import modules.deamon as deamon
import modules.localdb as localdb

from modules.tasks_history import TasksHistory
from modules.tx_history import TransactionsHistory
# from modules.frame_settings import Settings
from modules.notifications import Notifications
import modules.addr_book as addr_book

import modules.gui as gui
import traceback

class Worker(gui.QObject):
	finished = gui.Signal()
	refreshed = gui.Signal(list)
	# main_window_block_closing = gui.Signal(bool)
	
	
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
		if self.init_app.is_started:
			# print('is_started deamon')
			self.dmn.start_deamon( ) 
			
		xx=0
		while not self.init_app.close_thread:
			
			if self.queue_start_stop.qsize(): # start stop blockchain ON/OFF
				
				try:
				# if True:
					cmd = self.queue_start_stop.get(0)
					# print(48,cmd)
					if len(cmd)>0:
						if cmd['cmd']=='stop_deamon':
							
							self.block_closing=True
							self.dmn.stop_deamon()
							# un block main window closing
							self.block_closing=False
						elif cmd['cmd']=='start_deamon':
							# print('why start?',cmd)
							# self.dmn.start_stop_enable.emit(False)
							self.dmn.start_deamon(cmd['addrescan'] )
				except : #Queue.Empty:
					print('Queue exception bug?')
					traceback.print_exc()
					pass
			
			# print(87,self.dmn.started,flush=True)
			vemit=[]
			if self.dmn.started:
				# print('worker update status')
				vemit=self.dmn.update_status(xx)
				# print('after worker update status')
				vemit.append('worker_loop')
				vemit.append(xx)
				# print(63,vemit)
				if 'CONNECTED' not in vemit:
					self.block_closing=True
					print('connection problem?? vemit',vemit)
				else:
					self.block_closing=False
					# if xx<5: self.dmn.start_stop_enable.emit(True)
			else:
				vemit=['cmd_queue','worker_loop',xx]
				self.block_closing=False
				
			
			# print('before vemit',vemit)
			self.refreshed.emit(vemit)
			time.sleep(0.3) # change to 0.3
			xx+=1
			
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
			gui.output_copy_input(None,title,(to_copy,))
	
		else:
			strtitle_split=title.split('.')
			tmptitle=title  
			tmpcont=content
			
			if len(strtitle_split)>1:
				tmptitle= strtitle_split[0]
				tmpcont='.'.join(strtitle_split[1:])
			
			gui.messagebox_showinfo(tmptitle,tmpcont,None)
			
			if title=='New address(es) created':
				self.wds.update_addr_cat_map()
				self.updateWalletDisplay(['wallet'])
				self.wds.wallet_copy_progress()
	
	
	@gui.Slot(list)
	def updateStatus(self,ll):
		# print('waiting update status')
		while self.update_status_locked:
			time.sleep(1)
			
		self.update_status_locked=True
	
		# print(' update status',ll)
		if len(ll)==2:
			if ll[0]=='append':
				self.stat_lab.setText(self.stat_lab.text()+ll[1]) 
			
			elif ll[0]=='set':
				self.stat_lab.setText(ll[1])
		
		self.update_status_locked=False
		# print('done update status')
				
				
	@gui.Slot(bool)
	def enableStartStop(self,bl):
		# print('set enableStartStop',bl)
		self.bstartstop.setEnabled(bl)
		
		
	@gui.Slot(list)
	def updateWalletDisplay(self,wallet_part=[]):
	
		# print('updateWalletDisplay',wallet_part)
		cc=3
		while self.locked:
			print('waiting, locked')
			time.sleep(2)
			cc=cc-1
			if cc<0: return
		
		self.locked=True
		try:
		# if True:
		
			if  'wallet'  in wallet_part : # refreshed inside deamon / currently signal missing, and inside worke from deamon -> update_status ret_val.append('wallet')
				# print('\n\n\nupdateWalletDisplay',wallet_part)
				self.wds.set_disp_dict() #HERE OK SOMTIMES NOT REFRESHING PROPERLY ?? 
				# should take live data not from db? or update db sometimes?
				
				gridS,cols=self.wds.prepare_summary_frame()
				self.summary_frame={'grid':gridS,'columns':cols}
				# print('updating wallet prepare_byaddr_frame' )
				gridD,col3=self.wds.prepare_byaddr_frame()
				self.byaddr_frame={'grid':gridD,'columns':col3}
				# print(gridD)
				self.wallet_summary_frame.updateTable( gridS )
				if len(gridD)>0:
					# for gg in gridD:
						# print(gg['rowk'],gg['rowv'][1]['L'],gg['rowv'][2]['L'],gg['rowv'][3]['L'],gg['rowv'][5]['L'] )
					self.wallet_details.updateTable(gridD, doprint=False)
				# print('gridD updated!')
					
			if 'cmd_queue' in wallet_part :	
				
				grid_lol4,col4=self.wds.prepare_queue_frame()
				self.queue_frame={'grid':grid_lol4,'columns':col4}
				# print(grid_lol4)
				self.queue_status.updateTable(grid_lol4)
				# self.wds.queue_frame_buttons( grid_lol4,self.queue_status)
				
			if 'demon_loop' in 	wallet_part or 'worker_loop' in wallet_part:
				
				tmptt=self.tab_corner_widget.text().replace('Loops [','').replace(']','')
				stt=tmptt.split('/')
				newtt=''
				if 'demon_loop' in 	wallet_part :
					ii=wallet_part.index('demon_loop')
					
					newtt='Loops ['+str(wallet_part[ii+1])+'/'+stt[1]+']'
					
					
				if 'worker_loop' in wallet_part:
					ii=wallet_part.index('worker_loop')
					
					newtt='Loops ['+stt[0]+'/'+str(wallet_part[ii+1])+']'
				
				self.tab_corner_widget.setText(newtt)
					
			if 'task_done' in wallet_part :	
				if hasattr(self,'tahi'):
					self.tahi.update_history_frame()
					
			if 'notif_update' in wallet_part :	
				if hasattr(self,'notif'):
					self.notif.update_notif_frame()
					
			if 'tx_history_update' in wallet_part :	
				if hasattr(self,'txhi'):
					self.txhi.update_history_frame()
					
		
		except:
			print('Exception 235 wallet locked?')
			traceback.print_exc()
			
		self.locked=False
			
			
	# def updateSummaryTableValues(self):
		# value of total amount when new tx or rounding
		# try updating only first 3 columns - if works !
		# grid_lol_wallet_sum,col_names=self.wds.prepare_summary_frame( )
		# self.wallet_summary_frame.updateTable( grid_lol_wallet_sum,col_names )
		
		# value of categories in filter when categories edited ...
		# in this case needs to update the combox ... 
		# update_addr_cat_map(self)
		
	
	def __init__(self,is_deamon_started,queue_start_stop,wds  ): #autostart
	
		self.locked=False
		self.update_status_locked=False
		self.wds=wds
		self.wds.set_disp_dict()
		# print(' set_disp_dict dt',time.time()-t0)
		# t0=time.time()
		
		
		self.tabs1=gui.Tabs(None)
		
		
		pTabCornerWidget = gui.QWidget(self.tabs1)
		# pTabCornerWidget.setStyleSheet("QWidget {margin:0px;padding:0px;}")
		pHLayout = gui.QHBoxLayout()
		pHLayout.setContentsMargins(0,0,0,0)
		pTabCornerWidget.setLayout(pHLayout)
		self.tab_corner_widget=gui.Label(pTabCornerWidget,'Loops [0/0]',transparent=False)
		# self.tab_corner_widget.setMinimumHeight(32)
		self.tab_corner_widget.setStyleSheet("QLabel {font-size:9px;color:#aaa}")#;margin-top:-50px;padding-top:-50px;
		pHLayout.addWidget(self.tab_corner_widget)
		self.tabs1.setCornerWidget(pTabCornerWidget, gui.Qt.TopRightCorner)
		
		frame01=gui.ContainerWidget(self.tabs1,gui.QGridLayout())
		self.tabs1.insertTab(tab_dict={'My Balance':frame01}  )
		
		# self.tab_corner_widget=tab_corner #crnwdg=gui.Label(None,'Loops [0/0]')
		
		
		#
		# Blockchain status 
		#
		stat = gui.FramedWidgets(frame01,'Blockchain status',layout=gui.QHBoxLayout())
		frame01.insertWidget(stat,0,1 ) 
		# stat.setMaximumHeight(self.filter_table.height())
		
		self.stat_lab=gui.Label( stat, 'Blockchain off' )
		stat.insertWidget(self.stat_lab)			
		self.bstartstop=gui.Button(frame01) 
		self.bstartstop.setMaximumWidth(128)
		stat.insertWidget(self.bstartstop)
		# print('stat size',stat.height(),stat.sizePolicy())
		
		# print('autostart', autostart)
		# to distinguish started and synced ?
		if is_deamon_started :
			self.bstartstop.setText('Stop blockchain')
			self.bstartstop.setEnabled(False) #configure(state='disabled')
			# print('is_deamon_started',is_deamon_started)
		else:
			self.bstartstop.setText('Start blockchain')

			
		# why did autostart after click stop ??
		def togglestartstop(elem):
			# print('elem.text()',elem.text())
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
					# print(308,addrescan)
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
		self.queue_frame={'grid':grid_lol4,'columns':col4}
		# print(' prepare_queue_frame dt',time.time()-t0)
		
		self.queue_status=gui.Table(None,params={'dim':[0,5],'sortable':1,'updatable':1,'toContent':1})
		self.queue_status.updateTable( grid_lol4, col4 ) 
		queue.insertWidget(self.queue_status)

		# wds.queue_frame_buttons( grid_lol4,self.queue_status)
	
	
		###
		### FRAME 2 - summary
		### 
		# t0=time.time()
		opt=self.wds.get_options(True)
		self.summary_options=opt
		# print(' get_options 1 dt',time.time()-t0,opt)
		# t0=time.time()
		
		self.wds.set_format(opt['rounding']) # format used in prepare summary frame and prepare by addr frame - can be set later !
		# print(' set_format dt',time.time()-t0)
		# t0=time.time()
		
		summary = gui.FramedWidgets( frame01,'Summary' ,layout=gui.QHBoxLayout() )  #for wallet file: '+wds.data_files['wallet'] 
		# summary.setMaximumHeight(128)
		summary.setMaximumHeight(128)
		
		frame01.insertWidget(summary,0,0 )  
		grid_lol_wallet_sum,col_names= wds.prepare_summary_frame( )
		self.summary_frame={'grid':grid_lol_wallet_sum,'columns':col_names}

		self.summary_colnames=col_names
		self.wallet_summary_frame=gui.Table(summary,params={'dim':[1,6],'updatable':1,'toContent':1})  #'sortable':1, ,'rowSizeMod':['toContent']
		self.wallet_summary_frame.updateTable( grid_lol_wallet_sum, col_names )
		summary.insertWidget(self.wallet_summary_frame)

		summary.setMinimumHeight(108)
		
		
		
		###
		### FRAME 3 - wallet balances
		###
		table = gui.FramedWidgets(frame01,'Balance by address',layout=gui.QHBoxLayout())  
		frame01.insertWidget(table,1,0 ) 
		
		grid_lol3, colnames=wds.prepare_byaddr_frame()
		self.byaddr_frame={'grid':grid_lol3,'columns':colnames}
		# print(' prepare_byaddr_frame dt',time.time()-t0)
		# t0=time.time()
		self.details_colnames=colnames
		self.wallet_details=gui.Table(summary,params={'dim':[len(grid_lol3),len(colnames)],'sortable':1 ,'updatable':1,'toContent':1 }) #flexitable.FlexiTable(summary,grid_lol_wallet_sum)
		# print(len(grid_lol3) )
		# print(len(colnames),colnames)
		self.wallet_details.updateTable( grid_lol3,colnames ) #update_frame(grid_lol3)
		table.insertWidget(self.wallet_details)
		
		
		
		def save_wallet_display(btn,opt,*evnt):
			 
			vv=btn.currentText()
			if len(evnt)==0 or evnt[-1]!='init':
				idb=localdb.DB(self.wds.db)
				table={}
				table['wallet_display']=[{'option':opt, 'value':vv  }]
				idb.upsert(table,['option','value'],{'option':['=',"'"+opt+"'"]})
				
				self.summary_options[opt]=vv
			while self.wds.is_locked():
				# print('locked')
				time.sleep(1)
				
			self.wds.lock_basic_frames()
			
			if opt=='rounding':
				self.wds.set_format( format_str_value=vv)
				
			grid_lol_wallet_sum,col_names=self.wds.prepare_summary_frame( )
			self.wallet_summary_frame.updateTable( grid_lol_wallet_sum,col_names  ) #update_frame(grid_lol_wallet_sum)
			
			if opt=='filtering':
				# print('filtering ',vv)
				self.wallet_details.filtering( 'widget',0,vv )
			else:
				grid_lol3, colnames=self.wds.prepare_byaddr_frame( )
				self.byaddr_frame={'grid':grid_lol3,'columns':colnames}
				new_rows=self.wallet_details.updateTable( grid_lol3,colnames )  
				 
			self.wds.unlock_basic_frames()
			
			
		
		self.wallet_summary_frame.cellWidget(0,4).setIndexForText(opt['filtering'] )
		self.wallet_summary_frame.cellWidget(0,4).set_fun(save_wallet_display, 'filtering'  ) # only for summary to sum displayed !!! 
		
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
		
		self.wallet_summary_frame.cellWidget(0,3).setIndexForText(opt['rounding'] )
		self.wallet_summary_frame.cellWidget(0,3).set_fun(save_wallet_display, 'rounding'  )
		
		save_wallet_display(self.wallet_summary_frame.cellWidget(0,4),'filtering', 'init' )
		
	
	
	def init_additional_tabs(self,addr_book,init_app):
		
		self.notif=Notifications(addr_book)
		init_app.notif_grid=self.notif.grid_notif # pointer to object for next init ?
		
		self.tabs1.insertTab(tab_dict={'Notifications': self.notif.parent_frame}  )
		
		self.txhi=TransactionsHistory(self.wds.db)
		init_app.tx_grid=self.txhi.grid_settings # pointer to object for next init ?
		self.tabs1.insertTab(tab_dict={'TX History': self.txhi.parent_frame}  )
		
		self.tahi=TasksHistory(self.wds.db)
		init_app.task_grid=self.tahi.grid_settings # pointer to object for next init ?
		init_app.distinct_task_commands=self.tahi.distinct_task_commands # pointer to object for next init ?
		self.tabs1.insertTab(tab_dict={'Tasks History': self.tahi.parent_frame}  )
		
		# SETTINGS
		# self.grid_settings
		# self.settings=Settings( self.wds, init_app)
		# self.tabs1.insertTab(tab_dict={'Settings': self.settings.parent_frame}  )
		# print(' Settings dt',time.time()-t0) #0.74
		# t0=time.time()
		
	
