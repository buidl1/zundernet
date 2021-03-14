
import os
# import datetime
import json
import time
import modules.localdb as localdb
import modules.app_fun as app_fun
import modules.gui as gui



class Notifications:

	
	def update_notif_frame(self,*eventargs):
	
		if not self.update_in_progress:
			self.update_in_progress=True
			self.update_list()
			self.main_table.updateTable(self.grid_notif)
			self.set_actions()
			self.update_in_progress=False
			
			
	def close_all_notif(self,*eventargs):
		
		idb=localdb.DB()
		table={}
		table['notifications']=[{'closed':'True'}]
		idb.update(table,['closed'],{} )
		self.update_notif_frame()
		

	def __init__(self, addr_book  ):
	
		self.init=True
		
		self.update_in_progress=False
		self.addr_book=addr_book
		self.parent_frame = gui.ContainerWidget(None,layout=gui.QVBoxLayout() )
		
		frame0=gui.FramedWidgets(None,'Filter')   
		frame0.setMaximumHeight(128)
		self.parent_frame.insertWidget(frame0)
		
		tmpdict={}
		tmpdict['rowk']='filters'
		tmpdict['rowv']=[{'T':'LabelC', 'L':'Category: '}
							, {'T':'Combox', 'uid':'category', 'V':['New','Closed'] }
							, {'T':'Button', 'uid':'clearall', 'L':'Close all' }
							]
		grid_filter=[]
		grid_filter.append(tmpdict )
		
		self.filter_table=gui.Table(None,params={'dim':[1,3],'updatable':1} )
		self.filter_table.updateTable(grid_filter)
		frame0.insertWidget(self.filter_table)
		
		self.filter_table.cellWidget(0,1).set_fun(self.update_notif_frame) #.bind_combox_cmd('category',[], self.update_notif_frame )	
		self.filter_table.cellWidget(0,2).set_fun(True,self.close_all_notif) #.set_cmd('clearall',[], self.close_all_notif )	
		
		self.grid_notif=[]
		
		frame1=gui.FramedWidgets(None,'Notifications list') #ttk.LabelFrame(parent_frame,text='Filter')  
		self.parent_frame.insertWidget(frame1)
		
		self.colnames=['Date time','Event','Operation details','Status','','' ]
		self.update_list()
		
		self.main_table=gui.Table(None,params={'dim':[len(self.grid_notif),len(self.colnames)],'updatable':1} )  #flexitable.FlexiTable(frame1,self.grid_notif, min_canvas_width=1200,force_scroll=True)
		frame1.insertWidget(self.main_table)     
		# print(self.grid_notif)
		self.main_table.updateTable(self.grid_notif,self.colnames)
		
		self.set_actions()
		# self.notebook_parent.tab(1,text='Notif. ('+str(len(self.grid_notif)-1)+')' )
		self.init=False

		
		
		
	def set_actions(self):	
	
		def ok_close(struid,*evargs):
			idb=localdb.DB()
			table={}
			table['notifications']=[{'closed':'True'}]
			try:
			
				idb.update(table,['closed'],where={'uid':['=',int(struid)]})
				self.update_notif_frame()
			except:
				print('notifications set_actions')
				pass
			
				
			
		def review(btn,strjson,from_name,rev_id,*evargs):
			# print('rev click')
			
			
			# formframe.title('Review payment request from '+from_name)
			todisp=app_fun.json_to_str(json.loads(strjson))
			
			grid1=[]
			grid1.append( {'request':[{'T':'LabelC', 'L':todisp, 'width':96}, {'T':'LabelE' } ]} )
			tmpfromaddr=localdb.get_last_addr_from( "'last_book_from_addr'")
			grid1.append( {'label':[   {'T':'LabelC', 'L':'Send from:' } , {'T':'LabelE' } ]} )
			grid1.append( {'selectaddr':[ {'T':'Button', 'L':tmpfromaddr,  'uid':'seladdr', 'width':96} , {'T':'LabelE' } ]} )
			grid1.append( {'decide':[{'T':'Button', 'L':'Approve and Send',  'uid':'approve', 'width':32},  {'T':'Button', 'L':'Reject',  'uid':'reject'} ]} )
			g1_table= gui.Table(formframe,params={'dim':[512,512],'updatable':1} ) #   flexitable.FlexiTable(formframe,grid1)	
			formframe.insertWidget(g1_table)
			g1_table.updateTable(grid1)
			
			def close_request( decis,*evargs):
				# print('decis',decis)
				idb=localdb.DB()
				table={}
				table['notifications']=[ {'opname':'PaymentRequest '+decis,'closed':'True' }]
				# print(rev_id)
				try:
					id=int(rev_id )
					# print('id',id)
					idb.update(table,['opname','closed'],{'uid':['=',id]} )
				except:
					print('bad id?? 141 notif')
					pass
					
				formframe.destroy()
				
			def approve(*evargs):
			
				tmpdict=json.loads(strjson)
				# print('approved ',tmpdict)
				
				tmpsignature=localdb.get_addr_to_hash(tmpdict['toaddress'])
				tmpfromaddr=g1_table.cellWidget(2,0).text() #get_value('seladdr') #localdb.get_last_addr_from( "'last_book_from_addr'")
				memotxt='Payment for '+tmpdict['title']
				if len(tmpdict['docuri'].strip())>1:
					memotxt+=' docuri: '+tmpdict['docuri']
				memotxt+=tmpsignature

				ddict={'fromaddr':tmpfromaddr, 'to':[{'z':tmpdict['toaddress'],'a':tmpdict['amount'],'m':memotxt }]	} 
				table={}
				table['queue_waiting']=[localdb.set_que_waiting('send',jsonstr=json.dumps(ddict) ) ]
				idb=localdb.DB()
				idb.insert(table,['type','wait_seconds','created_time','command' ,'json','id','status' ])
				
				# 1. send tx
				# 2. update notifications closed and opname
				
				close_request('Approved')
				gui.showinfo('Payment Request approved','Payment Request to address of amount '+str(tmpdict['amount'])+'\n'+tmpdict['toaddress']+'\nAPPROVED',evargs[0])
		
			
			g1_table.cellWidget(3,0).set_fun(True,approve) #set_cmd('approve',[ ], approve )
			# g1_table.set_cmd('seladdr',[ ], approve )
			g1_table.cellWidget(2,0).set_fun(False,self.addr_book.get_addr_from_wallet) #set_cmd('seladdr',[  g1_table, ['seladdr'] ], self.addr_book.get_addr_from_wallet )  send_from,sending_to=False
			g1_table.cellWidget(3,1).set_fun(True,close_request,'Rejected') #set_cmd('reject',[ 'Rejected'  ], close_request )
			gui.CustomDialog(btn,[g1_table], title='Review payment request from '+from_name) #Toplevel() 
			
		# print('review actin')
		
		for ii,rr in enumerate(self.grid_notif):
			if ii==0 and self.init:
				continue
				
			r=rr['rowv']
		
			# print(ii,k)
			if 'T' in r[4]:
				if r[4]['T']=='Button':
					self.main_table.cellWidget(ii,4).set_fun(True,ok_close,r[4]['tooltip']) #set_cmd(r[4]['uid'],[r[4]['tooltip'] ],ok_close)				
			
			if 'T' in r[5]:
				if r[5]['T']=='Button': #'tooltip'
					tmpfrom='Unknown'
					if 'From ' == r[2]['L'][:5]:
						tmpspli=r[2]['L'][5:].split(';')
						tmpfrom=tmpspli[0]
					# print(200,tmpfrom,r[5]['uid'],r[5]['tooltip'])
					self.main_table.cellWidget(ii,5).set_fun(False,review,r[5]['tooltip'],tmpfrom ,r[5]['uid'][3:]) #.set_cmd(r[5]['uid'],[r[5]['tooltip'],tmpfrom ,r[5]['uid'][3:] ],review)
		
		
	
	def update_list(self):
	
		self.grid_notif=[]
		idb=localdb.DB()
		
		ff=self.filter_table.cellWidget(0,1).currentText() # get_value('category')
		wwhere={}
		if ff=='New':  
			wwhere ={'closed':['<>',"'True'"]}
		else:
			wwhere ={'closed':['=',"'True'"]}
		
		task_done=idb.select('notifications', ['uid','datetime' ,'opname' ,'details' ,'status' ,'closed','orig_json'],where=wwhere,orderby=[{'uid':'desc'}])
		
		for ij,rr in enumerate(task_done):
		
			tmpdict={}
							
			# visible=True

			okclosebutton={'T':'Button', 'L':'Ok, close', 'uid':'ok'+str(rr[0]) , 'tooltip':rr[0]}
			
			if rr[5]=='True':
				okclosebutton={} #{'T':'LabelE'}
			
			review={} #{'T':'LabelE'}
			tmpdetails=rr[6]
			
			# print('orig_json',rr[3])
			
			if rr[2] =='payment request' and rr[5]!='True':
				tmp=rr[6].split('PaymentRequest;')
				tmpdetails=tmp[0]
				tmp=tmp[-1]
			
				review={'T':'Button', 'L':'Review', 'uid':'rev'+str(rr[0]) , 'tooltip':tmp}
				
				okclosebutton={'T':'LabelV','L':'','uid':'ok'+str(rr[0])}
				
			# print(okclosebutton,review)
			tmpdict['rowk']=rr[0]
			tmpdict['rowv']=[{'T':'LabelV', 'L':rr[1], 'uid':'date'+str(rr[0])  } , 
							{'T':'LabelV', 'L':rr[2], 'uid':'name'+str(rr[0]) } , 
							{'T':'LineEdit', 'V':tmpdetails, 'uid':'det'+str(rr[0])  , 'width':48} , 
							{'T':'LabelV', 'L': rr[4], 'uid':'stat'+str(rr[0]) , 'width':11  } ,
							okclosebutton,
							review
							]	
							
							
			self.grid_notif.append(tmpdict)
