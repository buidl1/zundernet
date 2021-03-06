

import os
import time
# import getpass
# import queue

import sys
# import psutil

import datetime

import subprocess
import json
import modules.app_fun as app_fun
import modules.wallet_api as wallet_api
import modules.localdb as localdb
import modules.aes as aes

import modules.gui as gui
	

	
	
class DeamonInit(gui.QObject):
	sending_signal = gui.Signal(list)
	msg_signal=gui.Signal(str,str,str)
	msg_signal_list=gui.Signal(str,list,list)
	start_stop_enable = gui.Signal(bool)
	wallet_status_update = gui.Signal(list)
	update_addr_book = gui.Signal()
	refresh_msgs_signal = gui.Signal()
	send_viewkey = gui.Signal(str,str )
	

	def update_wallet(self,*args): # syntetic args passed auto by elem
		
		idb=localdb.DB(self.db)
		if self.started:
			# print('update_wallet',38)
			utxo_change=self.the_wallet.refresh_wallet()
			# print('update_wallet',40,utxo_change)
			
			if True: #utxo_change>0:
			
				disp_dict=self.the_wallet.display_wallet() 
				# print('update_wallet',45)
				date_str=app_fun.now_to_str(False)
				# print('update_wallet',47)
				table={}
				table['jsons']=[{'json_name':"display_wallet", 'json_content':json.dumps(disp_dict), 'last_update_date_time':date_str}]
				idb.upsert(table,['json_name','json_content','last_update_date_time'],{'json_name':['=',"'display_wallet'"]})
				# print('update_wallet',51)
				
				# self.refreshed_results['wallet']=
			if utxo_change>0:
				self.sending_signal.emit(['notif_update','tx_history_update'])
				self.refresh_msgs_signal.emit()
				
				
	def init_clear_queue(self):	
		idb=localdb.DB(self.db)
		waiting=idb.select('queue_waiting', ["type","wait_seconds","created_time","command","json","id","status"],{'command':['<>',"'automerge'"]})
		
		for ii,rr in enumerate(waiting):

			if rr[6]=='processing': # and len(idb.select('queue_done',['id'],{'id':['=',rr[5]]} ) )>0:
				table={}
				table['queue_done']=[{"type":rr[0],"wait_seconds":rr[1],"created_time":rr[2],"command":rr[3],"json":rr[4],"id":rr[5],"result":'old - forced failed on app init','end_time':app_fun.now_to_str(False)}]
				
				idb.insert(table,["type","wait_seconds","created_time","command","json","id","result",'end_time'])
				idb.delete_where('queue_waiting',{'id':['=',rr[5] ]})

	@gui.Slot()
	def process_queue(self):
	
		idb=localdb.DB(self.db)
		
		# print('process_queue1')
		if not hasattr(self,'counter_15m'):
			self.counter_15m=datetime.datetime.now()
			
			# print('process_queue2')
			# print(idb.select('queue_waiting', ["type","wait_seconds","created_time","command","json","id","status"] ) )
			# print(idb.select('queue_waiting', ["type","wait_seconds","created_time","command","json","id","status"],{'command':['=',"'automerge'"]}) )
			
			table={}
			table['queue_waiting']=[{"created_time":app_fun.now_to_str(False)}]
			
			# print('process_queue3',table)
			idb.update( table,["created_time"],{'command':[ '=','"automerge"' ]})
		
		# print('process_queue4' )
		cc=aes.Crypto()		

		gitmp=app_fun.run_process(self.cli_cmd,'getinfo')
		# print(90,gitmp)
		
		y=json.loads(gitmp)
		notar=y["notarized"]
		
		tmpwhere={'Type':['=',"'out'"],'Category':['=',"'send'"],'status':['=',"'sent'"],'block':['<',notar] }
		toupdate=idb.select('tx_history', ["txid",'date_time'],tmpwhere,distinct=True)
		
		count_task_done=0
		new_notif_count=0
		new_tx_history_count=0
		
		# print('toupdate')

		if len(toupdate)>0:
		
			for tt in toupdate:
				txidok=self.the_wallet.z_viewtransaction( tt[0] ) # if not in blocks anymore ? not valid ?
				
				tmpwhere2={'Type':['=',"'out'"],'Category':['=',"'send'"],'status':['=',"'sent'"],'block':['<',notar], 'txid':['=',"'"+tt[0]+"'"] }
				
				if txidok=='not valid txid' and datetime.datetime.now()>app_fun.datetime_from_str(tt[1])+datetime.timedelta(hours=1):
		
					table={}
					table['tx_history']=[{'status':'reorged'}]
					idb.update( table,['status'],tmpwhere2)
					# update notification
					wwhere={'details':['=','"'+tt[0]+'"'] }
					table={}
					table['notifications']=[{'status':'reorged', 'closed':'False' }]
					idb.update( table,['status', 'closed'],wwhere)
					
					# also update msg table: 
					table={}
					table['msgs_inout']=[{'tx_status':'reorged'}] #, 'txid':''
					idb.update( table,['tx_status'  ], {'txid':['=', tt[0] ],'type':['=','sent']})
					
				elif txidok!='not valid txid':
				
					table={}
					table['tx_history']=[{'status':'notarized'}]
					idb.update( table,['status'],tmpwhere2)
					# update notification
					wwhere={'details':['=','"'+tt[0]+'"'] }
					table={}
					table['notifications']=[{'status':'notarized' }]
					idb.update( table,['status'],wwhere)
					# also update msg table: 
					table={}
					table['msgs_inout']=[{'tx_status':'notarized' }]
					idb.update( table,['tx_status'  ], {'txid':['=',  tt[0] ],'type':['=','sent']})
				
				new_notif_count+=1
				new_tx_history_count+=1
					
					
		waiting=idb.select('queue_waiting', ["type","wait_seconds","created_time","command","json","id","status"])
		
		# print('waiting',waiting)
		merged_ii=[]
		for ii,rr in enumerate(waiting):
			
			if ii in merged_ii:
				continue
			
			if rr[6] =='done':
				
				task_done=idb.select('queue_done', ['end_time','result'],{'id':['=',rr[5]]})
				
				if len(task_done)>0:
					time_since_end=(datetime.datetime.now()-app_fun.datetime_from_str(task_done[0][0]) ).total_seconds()
					
					if rr[1]>=900 and time_since_end>=600 or rr[1]<900 and time_since_end>=3*60:
						idb.delete_where('queue_waiting',{'id':['=',rr[5] ] })
				else:
					table={}
					table['queue_done']=[{"type":rr[0],"wait_seconds":rr[1],"created_time":rr[2],"command":rr[3],"json":rr[4],"id":rr[5],"result":'unknown','end_time':app_fun.now_to_str(False)}]
					idb.insert(table,["type","wait_seconds","created_time","command","json","id","result",'end_time'])
				
				continue
			
			if rr[6] not in ['waiting','awaiting_balance'] and rr[3]!='automerge':
				continue
			
			if rr[1] - (datetime.datetime.now()-app_fun.datetime_from_str(rr[2]) ).total_seconds() - 1 >0 and rr[3]!='automerge':
				continue
			
			# 1 change status in case of task takes longer
			if rr[6]=='waiting' and rr[3]!='automerge':
				table={}
				table['queue_waiting']=[{'status':'processing'}]
				idb.update( table,['status'],{'id':[ '=',rr[5] ]})
			
				self.sending_signal.emit(['cmd_queue'])
				time.sleep(0.3)
				
				
				
				
			# print(188,rr[3])
				
			if rr[3]=='import_view_key': #json.dumps({'addr':tmpaddr,'viewkey':tmpvk})
				adrvk=json.loads(rr[4])
				tmpresult=self.the_wallet.imp_view_key( adrvk['addr'],adrvk['viewkey'] )
				# print(tmpresult)
				table={}
				table['queue_done']=[{"type":rr[0],"wait_seconds":rr[1],"created_time":rr[2],"command":rr[3],"json":rr[4],"id":rr[5],"result":json.dumps(tmpresult),'end_time':app_fun.now_to_str(False)}]
				# print('inserting')
				idb.insert(table,["type","wait_seconds","created_time","command","json","id","result",'end_time'])
				
				table={}
				if 'type' in tmpresult :
					if tmpresult['type']=='sapling':
						table['addr_book']=[{ 'viewkey_verif':1 }]
						
						table_vk={'view_keys':[{'address':adrvk['addr'], 'vk':adrvk['viewkey'] }]}
						idb.insert(table_vk,['address','vk'])
				else:
					table['addr_book']=[{ 'viewkey_verif':-1 }]
					
				idb.update(table,[  'viewkey_verif'],{'Address':['=',"'"+adrvk['addr']+"'"]})
				self.update_addr_book.emit()
				count_task_done+=1
				
				
			elif rr[3]=='import_priv_keys': #json.dumps({'addr':tmpaddr,'viewkey':tmpvk})
			
			
				tmpjs=json.loads(rr[4])
				ll=len(tmpjs['keys'])
				added_addr=[]
				
				for ii,kk in enumerate(tmpjs['keys']):
					# print(ii,kk)
					table={}
					table['queue_waiting']=[{'status':'processing '+str(ii+1)+'/'+str(ll)}]
					idb.update( table,['status'],{'id':[ '=',rr[5] ]})
					self.sending_signal.emit(['cmd_queue'])
					# print(199,tmpresult['address'])
					tmpresult=self.the_wallet.imp_prv_key( kk )
					added_addr.append(tmpresult['address'])
					# print(202,added_addr)
					# self.msg_signal.emit('New address added','Address added from private key. New address:\n\n' ,'')
					# self.msg_signal.emit('New address added','Address added from private key. New address:\n\n'+tmpresult['address'],'')
					# time.sleep(1)
					
				table={}
				table['queue_done']=[{"type":rr[0],"wait_seconds":rr[1],"created_time":rr[2],"command":rr[3],"json":rr[4],"id":rr[5],"result":'new addresses: '+str(added_addr),'end_time':app_fun.now_to_str(False)}]
				
				idb.insert(table,["type","wait_seconds","created_time","command","json","id","result",'end_time'])
				 
				count_task_done+=1
				
				
			elif rr[3]=='validate_addr':
			
				adrvk=json.loads(rr[4])
				tmpresult=self.the_wallet.validate_zaddr( adrvk['addr'] )
				table={}
				table['queue_done']=[{"type":rr[0],"wait_seconds":rr[1],"created_time":rr[2],"command":rr[3],"json":rr[4],"id":rr[5],"result":tmpresult,'end_time':app_fun.now_to_str(False)}]
				
				idb.insert(table,["type","wait_seconds","created_time","command","json","id","result",'end_time'])
				count_task_done+=1
				
				table={}
				if tmpresult=='not valid exception' or tmpresult==False:
					
					table['addr_book']=[{ 'addr_verif':-1 }]  #,'viewkey_verif' 
				else:
					table['addr_book']=[{ 'addr_verif':1 }]  #,'viewkey_verif' 
				idb.update(table,[  'addr_verif'],{'Address':['=',"'"+adrvk['addr']+"'"]})
			
			elif rr[3]=='new_addr':
			
				# 2 create results / wallet api
				tmpresult=self.the_wallet.new_zaddr()
				
				# 3 insert result to queue done
				table={}
				table['queue_done']=[{"type":rr[0],"wait_seconds":rr[1],"created_time":rr[2],"command":rr[3],"json":rr[4],"id":rr[5],"result":tmpresult,'end_time':app_fun.now_to_str(False)}]
				
				idb.insert(table,["type","wait_seconds","created_time","command","json","id","result",'end_time'])
				count_task_done+=1
				
				self.msg_signal.emit('New address created','New address:\n\n'+tmpresult,'')
				# idb.select('queue_done', [ "id" ])
				
			elif rr[3]=='export_wallet':
						
				# print('exp wal',self.wallet_display_set.password)
				tmpresult=self.the_wallet.export_wallet()
				# print('tmpresult',tmpresult)
				path2=json.loads(rr[4])
				tmppassword=path2['password']
				path2=os.path.join(path2['path'],'addrkeys_'+app_fun.now_to_str(True)+'.txt')
				# print(path2)
				
				if tmppassword=='current':
					cc.aes_encrypt_file( json.dumps(tmpresult),path2 ,self.wallet_display_set.password)			
					# tmppassword='Your current password' #self.wallet_display_set.password
				elif tmppassword=='random':				
					# tmppass=cc.rand_password(32)
					tmppassword=cc.rand_password(32)
					cc.aes_encrypt_file( json.dumps(tmpresult),path2 ,tmppassword)				
				else:
					cc.write_file(path2 ,json.dumps(tmpresult))
					tmppassword=''
				
				tmptitle='Private keys exported. Private keys exported to\n'+path2
				# tmpcont='\n'+path2
				
				if tmppassword!='':
					tmptitle+='. File was encrypted with password:\n'
				 
				# print('write queue done')
				table={}
				table['queue_done']=[{"type":rr[0],"wait_seconds":rr[1],"created_time":rr[2],"command":rr[3],"json":rr[4],"id":rr[5],"result":'exported to '+path2,'end_time':app_fun.now_to_str(False)}]
				
				idb.insert(table,["type","wait_seconds","created_time","command","json","id","result",'end_time'])
				count_task_done+=1
				
				table={}
				table['queue_waiting']=[{'status':'done'}]
				idb.update( table,['status'],{'id':[ '=',rr[5] ]})
				self.sending_signal.emit(['cmd_queue'])
				if tmppassword=='current':
				
					tmptitle+='Your current password'
					self.msg_signal.emit(tmptitle,'','')
				else:
					self.msg_signal.emit(tmptitle,'',tmppassword)
					
				time.sleep(3)
				
			elif rr[3]=='get_viewkey':
			
				ddict=json.loads(rr[4])
				tmpresult=self.the_wallet.exp_view_key(ddict['addr'])
			
				self.send_viewkey.emit(ddict['addr'],tmpresult)
			
			elif rr[3]=='export_viewkey':
				ddict=json.loads(rr[4])
				tmpresult=self.the_wallet.exp_view_key(ddict['addr'])
				tmptitle='View key display'
				
				pto='screen'
				if ddict['password']=='':
					# gui.output_copy_input(None,'View key display' ,('Address  '+ddict['addr']+'\n\nView key '+tmpresult,))
					self.msg_signal.emit(tmptitle,'','Address\n\n'+ddict['addr']+'\n\nView key:\n\n'+tmpresult)
					
				else:
					tmppass=cc.rand_password(32)
					tmpresult=json.dumps({'addr':ddict['addr'], 'viewkey':tmpresult})
					pto=ddict['path']+'/viewkey_'+app_fun.now_to_str()+'.txt'
					cc.aes_encrypt_file( tmpresult, pto  , tmppass) 
					tmptitle='View key export. Password for file exported to:\n\n'+pto+'\n\n' #+tmppass
					self.msg_signal.emit(tmptitle,'',tmppass)
					# gui.output_copy_input(None,'Password for file exported to '+pto,(tmppass,))
									
				table={}
				table['queue_done']=[{"type":rr[0],"wait_seconds":rr[1],"created_time":rr[2],"command":rr[3],"json":rr[4],"id":rr[5],"result":'exported to '+pto,'end_time':app_fun.now_to_str(False)}]
				
				idb.insert(table,["type","wait_seconds","created_time","command","json","id","result",'end_time'])
				count_task_done+=1
				time.sleep(1)
			
			elif rr[3]=='show_bills': # 
				ddict=json.loads(rr[4])
				results_array=[]
				
				# tmpstr='Amount, Confirmations, TxId\n' #'Txid','Amount','Confirm.'
				if ddict['addr'] in self.the_wallet.all_unspent:
					tmpresult2=self.the_wallet.all_unspent[ddict['addr']] 
					for ii,dd in tmpresult2.items():
						tmpresult={}
						tmpresult[ii]={ 'amount':dd['amount'], 'conf':dd['conf']}
						results_array.append(tmpresult)
						
				self.msg_signal_list.emit('Bills / utxos',['Amount','Confirm.','Txid'],results_array)
				time.sleep(1)
				
				
			elif 'merge' in rr[3]: #=='show_bills': # 
				# print('merging343')
				ddict=json.loads(rr[4])
				
				def merge(once=True):
					# print('ddict',ddict)
					tmpresult2=self.the_wallet.merge(json.dumps(ddict['fromaddr']),ddict['to'],ddict['limit'])
					# print(tmpresult2)
					if once:
						self.msg_signal.emit('Merging result',tmpresult2,'')
						
						table={}
						table['queue_done']=[{"type":rr[0],"wait_seconds":rr[1],"created_time":rr[2],"command":rr[3],"json":rr[4],"id":rr[5],"result":tmpresult2,'end_time':app_fun.now_to_str(False)}]
						
						idb.insert(table,["type","wait_seconds","created_time","command","json","id","result",'end_time'])
					
					
				total_s=(datetime.datetime.now() - self.counter_15m).total_seconds()
				
				# print((int(total_s)/60 ) %3)
				if rr[3]=='merge':
					merge()
					count_task_done+=1
					
				elif  (int(total_s)/60 ) %3==0: # every 3 minutes
				
					disp_dict=self.the_wallet.display_wallet() 
					notes_count=0
					for ri in disp_dict['wl']: 
						if ri['addr'] in ddict['fromaddr']:
							notes_count+=ri['#conf']
					
					
					if total_s> 15*60:
						self.counter_15m=datetime.datetime.now()
						
						if notes_count>=ddict['limit']:
							merge(False)
						
						table={}
						table['queue_waiting']=[{'status':'waiting 15min\ntill next check',"created_time":app_fun.now_to_str(False)}]
						idb.update( table,['status',"created_time"],{'id':[ '=',rr[5] ]})
					
						self.sending_signal.emit(['cmd_queue'])
						
					elif int(total_s)%5==0:
						
						table={}
						if notes_count<ddict['limit']:
							
							table['queue_waiting']=[{'status':'awaiting\nlimit '+str(notes_count)+'/'+str(ddict['limit'])} ]
						else:
							table['queue_waiting']=[{'status':'waiting 15min\ntill next check'} ]
						
						idb.update( table,['status'],{'id':[ '=',rr[5] ]})	
						self.sending_signal.emit(['cmd_queue'])
					
			elif rr[3]=='send': # 
			
				def insert_notification(details, tmpjson):
					if type(tmpjson)==type({}):
						tmpjson=json.dumps(tmpjson)
				
					idb=localdb.DB(self.db)
					table={}
					dt,ts=app_fun.now_to_str(False,ret_timestamp=True)
					# print('notif details',details,'dt',dt,'json',tmpjson)
					table['notifications']=[{'opname':'send','datetime':dt,'status':'Failed','details':details,'closed':'False','orig_json':tmpjson,'uid':'auto'}]
					
					idb.insert(table,['opname','datetime','status','details', 'closed','orig_json' ,'uid'])
					new_notif_count+=1
				
			
				ddict=json.loads(rr[4])
				# print(453,ddict)
				exceptions=[]
				total_conf_per_addr=self.wallet_display_set.amount_per_address[ddict['fromaddr']]
				# print(453,total_conf_per_addr)
				
				sum_cur_spending=0
					
				if ddict['fromaddr'] in self.wallet_display_set.amount_per_address :
					for tt in ddict['to']:
						sum_cur_spending+=float(tt['a'])
				
				if sum_cur_spending>total_conf_per_addr-0.0001: # validate amoaunt to send
					#
				
					table={}
					table['queue_waiting']=[{'status':'awaiting_balance'}]
					idb.update( table,['status'],{'id':[ '=',rr[5] ]}) # 
					self.sending_signal.emit(['cmd_queue'])
					time.sleep(1)
				
				elif self.the_wallet.validate_zaddr(ddict['fromaddr']) : # first validate addr:
				
					table={}
					table['queue_waiting']=[{'status':'processing'}]
					idb.update( table,['status'],{'id':[ '=',rr[5] ]})
					self.sending_signal.emit(['cmd_queue'])
					time.sleep(1)
				
					merged_queue_done=[]
					msg_chnl=['message','channel']
					if rr[0] not in msg_chnl:
						for jj,ss in enumerate(waiting):
							# print(jj,ss)
							if ss[3]!='send' or jj==ii or ss[0] in msg_chnl: #=='message':
								continue 
							if ss[6]!='waiting':
								continue
							ddict2=json.loads(ss[4])
							if ddict2['fromaddr']!=ddict['fromaddr']:
								continue	
							
							#can be multiple items
							tmpsumadd=0
							for dd2 in ddict2['to']:							
								tmpsumadd+=float(dd2['a'])
								
							if sum_cur_spending+tmpsumadd>total_conf_per_addr-0.0001: # only pass that much which does not exceed total confirmed
								continue
								
							sum_cur_spending=sum_cur_spending+tmpsumadd #float(ddict2['to']['a'])
							
							merged_ii.append(jj)
							merged_queue_done.append(ss)
							ddict['to']=ddict['to']+ddict2['to']
					
					sending_summary=[]
					memo_orig=[]
					
					for to in ddict['to']:
						# validate amount, addr , memo cut 512
						table={}
						dt,ts=app_fun.now_to_str(False,ret_timestamp=True)
						if not self.the_wallet.validate_zaddr(to['z']):
							exceptions.append('Not valid destination address '+str(to['z'])+' - ignoring.')
							insert_notification('Not valid destination address '+str(to['z'])+' - ignoring.' ,{'fromaddr':ddict['fromaddr'],'to':[to]})
							 
							continue
						try:
							if float(to['a'])<0.0000001:
								exceptions.append('Too small amount '+str(to['a'])+' - ignoring.')
								
								insert_notification('Too small amount '+str(to['a'])+' - ignoring.' ,{'fromaddr':ddict['fromaddr'],'to':[to]})
								continue
						except:
							exceptions.append('Not valid amount '+str(to['a'])+' - ignoring.')
							
							insert_notification('Not valid amount '+str(to['a'])+' - ignoring.' ,{'fromaddr':ddict['fromaddr'],'to':[to]})
							continue
						
						sending_summary.append({"address":to['z'], "amount":float(to['a']), "memo":to['m'].encode('utf-8').hex() })
						
						memo_orig.append([to['m'],float(to['a']),to['z']]) 
					
					
					tmpres={}
					tmpres['opid']=''
					tmpres['result_details']='Bad amounts or not valid addresses.'
					tmpres["result"]='Failed - Nothing to process.'
					tmpres['exceptions']= '\n'.join(exceptions)	
					if len(sending_summary)>0:
						tostr=json.dumps(sending_summary)
						# print(ddict['fromaddr'],tostr)
						tmpres['opid']=str(self.the_wallet.send(ddict['fromaddr'],tostr))
						tmpres['opid']=tmpres['opid'].strip()
						
						cmdloc=['z_getoperationstatus','["'+tmpres['opid']+'"]']

						opstat=app_fun.run_process(self.cli_cmd,cmdloc)

						opj=''
						try:
							opj=json.loads(opstat)[0]
						except:
							opj={'error':{'message':opstat}}
						
						if 'error' in opj:
							tmpres['result_details']=str(opj['error']['message'].replace('shielded ','') )
							tmpres["result"]='Failed'
							
							insert_notification(tmpres['result_details'], {'fromaddr':ddict['fromaddr'],'to':[to]})
							
						else:
							ts=7
							while "result" not in opj:
								time.sleep(ts)
								if ts>1:
									ts=ts-1
								
								opstat=app_fun.run_process(self.cli_cmd,cmdloc)
								opj=json.loads(opstat)[0]
								
								if opj["status"]=="failed":
									tmpres["result"]='Failed'
									exceptions.append('Failed to process tx: '+opstat)
									insert_notification(opstat, {'fromaddr':ddict['fromaddr'],'to':[to]})
							
							if tmpres["result"]!='Failed':
								while opj["status"]=="executing":
									time.sleep(ts)
									if ts>1:
										ts=ts-1
									
									opstat=app_fun.run_process(self.cli_cmd,cmdloc)
									opj=json.loads(opstat)[0]
									# print('while exe',opj)
									
								if opj["status"]=="success":
									tmpres["result"]='success'
									
								else:
									tmpres["result"]='Failed'
									exceptions.append('Failed to process tx: '+opstat)
									insert_notification(opstat, {'fromaddr':ddict['fromaddr'],'to':[to]})
									
								tmpres["result_details"]=str(opj["result"])
						
						del tmpres['opid'] # not needed later 
						
						tmpres["block"]=0 # get block nr for confirmation notarization validation later on 

						while tmpres["block"]==0:
							tmpinfo=self.the_wallet.getinfo()
							try:
								tmpinfo=int(tmpinfo["blocks"])
								if tmpinfo>0:
									tmpres["block"]=tmpinfo
									break
							except:
								print('Network problem')
								pass
							time.sleep(5)
							
							
						# print(613,'sent',tmpres)
						if tmpres["result"]=='success': # insert tx out:
							table={}
							txid=''
							if 'txid' in opj["result"]:
								txid=opj["result"]['txid']
								
							# print(620,'memoorig',memo_orig)
							for mmii,mm in enumerate(memo_orig):
								mm0=mm[0].split('@zUnderNet')
								memo_orig[mmii][0]=mm0[0]
								
							dt,ts=app_fun.now_to_str(False,ret_timestamp=True)
							# print(630,dt,ts)
							
							# print(620,'tx_history', 'fromaddr',ddict['fromaddr'],'to_str',str(memo_orig))
							table['tx_history']=[{'Category':'send'
												, 'Type':'out'
												, 'status':'sent'
												,'txid':txid
												,'block':tmpres["block"] # estimated block sent for true nota conf estimation
												, 'timestamp':ts
												, 'date_time':dt
												,'from_str':ddict['fromaddr'] # for merge many from addr
												,'to_str':str(memo_orig)
												,'amount':sum_cur_spending
												, 'uid':'auto'
												 }]
							
							idb.insert(table,['Category','Type','status','txid','block','timestamp', 'date_time','from_str','to_str','amount','uid'])
							new_tx_history_count+=1
							# self.tx_history.update_history_frame()
							
							txid_utf8=txid 
							if rr[0]!='message':
								# print(644,'msg')
								for mmii,mm in enumerate(memo_orig):
									# print(mmii,mm,sending_summary[mmii])
									table=self.the_wallet.prep_msgs_inout(txid_utf8,mm,'out',dt,addr_to=sending_summary[mmii]["address"] ) #tostr.append({"address":to['z']
									if table['msgs_inout'][0]['msg']=='':
										table['msgs_inout'][0]['msg']='Sent amount '+str(round(sum_cur_spending,8))
									# if table=={}:
										# continue
																	 
									idb.insert(table,['proc_json','type','addr_ext','txid','tx_status','date_time', 'msg', 'uid','in_sign_uid','addr_to'])
							else: #'message': msg_chnl
								mmm=['',0,memo_orig[0][2]]
								for mmii,mm in enumerate(memo_orig):
									mmm[0]+=mm[0]
									mmm[1]+=mm[1]
									
								# also for channels?
								if True: #rr[0]=='message':
									table=self.the_wallet.prep_msgs_inout(txid_utf8,mmm,'out',dt,addr_to=sending_summary[0]["address"])
									if table!={}:
										idb.insert(table,['proc_json','type','addr_ext','txid','tx_status','date_time', 'msg', 'uid','in_sign_uid','addr_to'])
									
						# self.messages.update_msgs()
						
						tmpres=json.dumps(tmpres)	
							
						table={}
						table['queue_done']=[{"type":rr[0],"wait_seconds":rr[1],"created_time":rr[2],"command":rr[3],"json":rr[4],"id":rr[5],"result":tmpres,'end_time':app_fun.now_to_str(False)}]
						idb.insert(table,["type","wait_seconds","created_time","command","json","id","result",'end_time'])

						for ss in merged_queue_done:
							table={}
							table['queue_done']=[{"type":ss[0],"wait_seconds":ss[1],"created_time":ss[2],"command":ss[3],"json":ss[4],"id":ss[5],"result":tmpres,'end_time':app_fun.now_to_str(False)}]
						
							idb.insert(table,["type","wait_seconds","created_time","command","json","id","result",'end_time'])
							
							table={}
							table['queue_waiting']=[{'status':'done'}]
							idb.update( table,['status'],{'id':[ '=',ss[5] ]})
							self.sending_signal.emit(['cmd_queue'])
							time.sleep(1)
					
					else:
						
						tmpres=json.dumps(tmpres)# some exceptions:
						table={}
						table['queue_done']=[{"type":rr[0],"wait_seconds":rr[1],"created_time":rr[2],"command":rr[3],"json":rr[4],"id":rr[5],"result":tmpres,'end_time':app_fun.now_to_str(False)}]
						idb.insert(table,["type","wait_seconds","created_time","command","json","id","result",'end_time'])
					
				else:
					tmpres="Wrong [from] address!"
					
					table={}
					table['queue_done']=[{"type":rr[0],"wait_seconds":rr[1],"created_time":rr[2],"command":rr[3],"json":rr[4],"id":rr[5],"result":tmpres,'end_time':app_fun.now_to_str(False)}]
						
					idb.insert(table,["type","wait_seconds","created_time","command","json","id","result",'end_time'])
				
				count_task_done+=1
			
			if rr[3]!='automerge':
				table={}
				table['queue_waiting']=[{'status':'done'}]
				idb.update( table,['status'],{'id':[ '=',rr[5] ], 'status':[ '=',"'processing'" ],"command":['<>',"'automerge'"]})
				self.sending_signal.emit(['cmd_queue'])
				time.sleep(1)
				# self.task_history.update_history_frame()
		
		# print('b4 delete')			
		idb.delete_where('queue_waiting',{'status':['<>',"'awaiting_balance'"],'status':['<>',"'waiting'"],"command":['<>',"'send'"],"command":['<>',"'automerge'"]  }) 
		# do not delete if awaiting balance or waiting or command is send (delete in another thread time based) or command is autom merge - cancelled manually
		
		# print('after delete')	
		self.process_queue_iter+=1
		list_emit=['cmd_queue','demon_loop',int(self.process_queue_iter)]
		if count_task_done>0:
			list_emit.append('task_done')
		if new_notif_count>0:
			list_emit.append('notif_update')
		if new_tx_history_count>0:
			list_emit.append('tx_history_update')
			
			
		self.sending_signal.emit(list_emit) # self.sending_signal.emit(['notif_update'])
		
		if 'notif_update' in list_emit or 'tx_history_update' in list_emit:
			self.refresh_msgs_signal.emit()
		
		# print('b4 sleep')
		# if count_task_done>0:
			# self.task_done.emit()
			
		time.sleep(1)
		
	
	
	
	
	
	
	def update_incoming_tx(self):
	
		if not hasattr(self.the_wallet, 'z_viewtransaction'):
			return
	
		try:
			y=json.loads(app_fun.run_process(self.cli_cmd,'getinfo'))
		
			notar=y["notarized"]
		except:
			print(626,'demon update tx exception')
			return
			
		tmpwhere={'status':[' not in',"('reorged','notarized')"], 'Type':['=',"'in'"],'block':['<=',notar] }
		
		idb=localdb.DB(self.db)	
		toupdate=idb.select('tx_history', ["txid",'date_time'],tmpwhere) #
		
		if len(toupdate)>0: # check if update required ()
		
			for tt in toupdate:
		
				txidok=self.the_wallet.z_viewtransaction( tt[0] ) # if not in blocks anymore ? not valid ?
				tmpwhere2={'status':[' not in',"('reorged','notarized')"], 'Type':['=',"'in'"],'block':['<=',notar], 'txid':['=',"'"+tt[0]+"'"] }
				
				if txidok=='not valid txid' and datetime.datetime.now()>app_fun.datetime_from_str(tt[1])+datetime.timedelta(hours=1):
				
					table={}
					table['tx_history']=[{'status':'reorged'}]
					idb.update( table,['status'],tmpwhere2)
					
					table={}
					table['msgs_inout']=[{'tx_status':'reorged' }]
					idb.update( table,['tx_status' ], {'txid':['=', "'"+tt[0]+"'" ],'type':['=',"'received'"]})
					
				elif txidok!='not valid txid':
					table={}
					table['tx_history']=[{'status':'notarized'}]
					idb.update( table,['status'],tmpwhere2) # updating all, no matter outindex 
					
					table={}
					table['msgs_inout']=[{'tx_status':'notarized' }]
					idb.update( table,['tx_status'  ], {'txid':['=', "'"+tt[0]+"'" ],'type':['=',"'received'"]})
				# else wait
			# self.tx_history.update_history_frame()
			self.sending_signal.emit([ 'tx_history_update'])
			self.refresh_msgs_signal.emit()
			
	
	
	
	
	
	
	
	
	def update_status(self,xx):
	
	
		ret_val=[]
		if self.started:
		
			# try:
			if True:
				gitmp=app_fun.run_process(self.cli_cmd,'getinfo')
				gi=json.loads(gitmp)
				# print('\nupdate_status 700',gi)
				kv_tmp=[{"name":"Chain: "},{"synced":"\nSynced: "},{"blocks":"\nCurrent block: " }, {"longestchain":"\nLongest chain: "}, {"notarized":"\nNotarized: "}, {"connections":"\nConnections: "}]
				tmpstr=""
				for dd in kv_tmp:
					for kk,vv in dd.items():
						if kk in gi:
							tmpstr+=vv+str(gi[kk])
				
				
				# "Synced: "+str(gi["synced"])+"\nCurrent block: "+str(gi["blocks"])+"\nLongest chain: "+str(gi["longestchain"])+"\nNotarized: "+str(gi["notarized"])+"\nConnections: "+str(gi["connections"])
				
				if time.time()-self.insert_block_time>50: # check every 50 seconds
					self.insert_block_time=time.time()
					table={'block_time_logs':[{'uid':'auto', 'ttime':time.time(), 'block':gi["blocks"] }] }
					idbinit=localdb.DB('init.db')
					idbinit.upsert(table,['uid', 'ttime','block'],{'block':['=',gi["blocks"]]})
				
				# print('\nupdate_status 709' )
				self.output(tmpstr)
				
				if int(gi["connections"])>0:
					ret_val.append('CONNECTED')
				
				# print('\nupdate_status 715' )
				modv=46 # about 15 sec
				
				if xx%modv==modv-1 and self.started:
					# print(818,'modv',xx)
					self.update_wallet()
					ret_val.append('wallet')
				# print('\nupdate_status 721',ret_val)
					
				if xx%modv==modv-1 and self.started:
					self.update_incoming_tx()
					
				
				# print('\nupdate_status 727' )
					
				if xx%3==2: # and self.started: # every second
					# print('process queue')
					self.process_queue()
					# print('process queue done')
					ret_val.append('cmd_queue')
					
				# print('\nupdate_status 732' )
					
		return 	ret_val
		

	def set_wallet_widgets(self,wds): #,wata,task_history=None,txhi=None,notif=None,messages=None):
		
		self.wallet_display_set=wds
		# self.db=wds.db
		
		

	def __init__(self, deamon_cfg ,db): 
	
		super(DeamonInit, self).__init__()
		self.db=db
		self.started=False
		self.insert_block_time=0
		self.the_wallet=None
		self.deamon_started_ok=False
		self.process_queue_iter=0
		
		# self.msg_queue = queue.Queue()	
		# self.refreshed_results={}
		
		if deamon_cfg==None:
			return
			
		FULL_DEAMON_PARAMS=[]
		CLI_STR=[]
		if "ac_name" in deamon_cfg:
			FULL_DEAMON_PARAMS=[ deamon_cfg['deamon-path'] ,"-wallet="+deamon_cfg["wallet"] ,"-ac_name="+deamon_cfg["ac_name"]]
			CLI_STR=[deamon_cfg['cli-path'], "-ac_name="+deamon_cfg["ac_name"] ]
		else:
			FULL_DEAMON_PARAMS=[ deamon_cfg['deamon-path'] ,"-wallet="+deamon_cfg["wallet"]  ]
			CLI_STR=[deamon_cfg['cli-path'] ]
			
		ac_params_add_node=''
		if "ac_params" in deamon_cfg:
			if deamon_cfg["ac_params"].strip()!='':
				ac_params_add_node=deamon_cfg["ac_params"]
			
		if "addnode" in deamon_cfg:
			if len(deamon_cfg["addnode"])>0:
			
				for an in deamon_cfg["addnode"]:
					ac_params_add_node+=' -addnode='+an
			
		if len(ac_params_add_node.strip())>1:
			FULL_DEAMON_PARAMS+= ac_params_add_node.split(" ")  

		
		if deamon_cfg["datadir"].strip()!='': # adjust data dir
			FULL_DEAMON_PARAMS+=['-datadir='+deamon_cfg["datadir"] ] 
			CLI_STR+=['-datadir='+deamon_cfg["datadir"] ] 

		self.cli_cmd=CLI_STR
		self.deamon_par=FULL_DEAMON_PARAMS
		# print(self.deamon_par,self.cli_cmd)
	
	
	
	def stop_deamon(self):
	
		self.started=False
		# print('b4 outpost')
		self.output('Stopping deamon\n')
		# print('after outpost')
		self.run_subprocess(self.cli_cmd,'stop',2)
		

	@gui.Slot()
	def start_deamon(self, addrescan=False ):
	
		self.started=True
		
		tmpcond,tmppid=app_fun.check_deamon_running() # ''.join(self.deamon_par)
		
		if tmpcond:
		
			# self.walletTab.bstartstop.setEnabled(True) #.configure(state='normal')
			self.start_stop_enable.emit(True)
				# self.msg_queue.put({'cmd_queue':''})
			
			gitmp=app_fun.run_process(self.cli_cmd,'getinfo')
			while 'longestchain' not in gitmp:
				time.sleep(4)
				gitmp=app_fun.run_process(self.cli_cmd,'getinfo')
				self.output('Awaiting longest chain')
				
			if self.the_wallet==None: #hasattr(self,'the_wallet')==False or :
				self.the_wallet=wallet_api.Wallet(self.cli_cmd,self.get_last_load(),self.db)
		
			y = json.loads(gitmp)
			if "synced" in y:
				if y["synced"]==True:
				# self.walletTab.bstartstop.setEnabled(True) #self.bstartstop.configure(state='normal')
					self.start_stop_enable.emit(True)
			elif y['longestchain']==y['blocks']:
				self.start_stop_enable.emit(True)
			else:
				# self.walletTab.bstartstop.setEnabled(False) #self.bstartstop.configure(state='disabled')
				self.start_stop_enable.emit(False)
				
			return 

		else:
			if self.decrypt_wallet()=='Cancel':
				return
				
			self.output('Starting deamon usually takes few minutes ...')
			reskanopt=[]
			if addrescan:
				reskanopt=['-rescan']
				
			# print([self.deamon_par+reskanopt,self.cli_cmd])
			self.run_subprocess([self.deamon_par+reskanopt,self.cli_cmd],'start',8)
			
			return
			
	
	def get_last_load(self):

		idb=localdb.DB(self.db )
		last_load=-1
		if idb.check_table_exist( 'deamon_start_logs'):
			tt=idb.select_last_val( 'deamon_start_logs','loaded_block')

			if tt!=None:
				last_load=tt #[0][0]	
					
		return last_load
		
	# @gui.Slot()	
	def output(self,ostr): #self.output()
		
		self.wallet_status_update.emit(['set',ostr]) #
		# self.walletTab.stat_lab.setText(ostr)
	
		# error: couldn't connect to server: timeout reached (code 0)
# (make sure server is running and you are connecting to the correct RPC port)
		
	@gui.Slot()	
	def run_subprocess(self,CLI_STR,cmd_orig,sleep_s=2 ):

		if cmd_orig in ['start','stop']:
			self.start_stop_enable.emit(False)
			# self.walletTab.bstartstop.setEnabled(False) #self.bstartstop.configure(state='disabled')
	
		deamon_start=CLI_STR.copy()
		cli_cmd=CLI_STR.copy()
		cmd=cmd_orig
		deamon_warning="make sure server is running and you are connecting to the correct RPC port"
		
		t0=time.time()

		if cmd_orig=='start':
			deamon_start=CLI_STR[0]
			cli_cmd=CLI_STR[1]
			cmd=[]

		elif type(cmd_orig)!=type([]):
			
			cmdtmp=cmd_orig.split()
			cmd=[cmdii for cmdii in cmdtmp]
			
		tmplst=deamon_start +cmd 
		# print(tmplst)
		
		pp=subprocess.Popen( tmplst ) 
		
		time.sleep(sleep_s)
		
		tsyncing=None
		blocksinit=None
		
		while pp.poll()==None:
		
			# print('deamon  while')
		
			if cmd_orig=='start':
			
				gitmp=app_fun.run_process(cli_cmd,'getinfo')
				
				# print(1010,gitmp)
				
				if deamon_warning in gitmp:
					self.output(gitmp)
				elif 'error message:' in gitmp:
					tmps=gitmp.split('error message:')
					self.output(tmps[1].strip()+'\n')
					
				elif 'is not recognized' in gitmp or 'exe' in gitmp:
					self.output('Command ['+cli_cmd+" getinfo"+'] not recognized - wrong path ? Exiting.')
					exit()
				elif 'longestchain' in gitmp:
				
					y = json.loads(gitmp)
					
					kv_tmp=[{"synced":"Synced: "},{"blocks":"\nCurrent block: " }, {"longestchain":"\nLongest chain: "}, {"notarized":"\nNotarized: "}, {"connections":"\nConnections: "}]
					gtmpstr=""
					for dd in kv_tmp:
						for kk,vv in dd.items():
							if kk in y:
								gtmpstr+=vv+str(y[kk])
					
					# gtmpstr="Synced: "+str(y["synced"])+"\nCurrent block: "+str(y["blocks"])+"\nLongest chain: "+str(y["longestchain"])+"\nConnections: "+str(y["connections"])
				
					if y['longestchain']==y["blocks"] and y['longestchain']>0:
						if cmd_orig=='start':
							self.output('Wallet synced!')
							
						break
					elif y['longestchain']>0:
						
						timeleft=''
						if tsyncing==None and y["blocks"]>0 and y["longestchain"]-y["blocks"]>0:
						
							tsyncing=time.time()
							blocksinit=y["blocks"]
							
						elif y["blocks"]>0 and y["longestchain"]-y["blocks"]>0:
							secpassed=time.time()-tsyncing
							blockssynced=y["blocks"]-blocksinit
							syncspeed=blockssynced/secpassed
							blocksleft=y["longestchain"]-y["blocks"]
							timeleft=int(blocksleft/syncspeed)
							hoursleft=0
							minutesleft=0
							secondsleft=int(timeleft)
							if timeleft>3600:
								hoursleft=int(timeleft/3600)
								secondsleft=int(timeleft-hoursleft*3600)
							if secondsleft>60:
								minutesleft=int(secondsleft/60)
								secondsleft=int(secondsleft-minutesleft*60)
									
							timeleft='Estimated time left: '+str(hoursleft)+' h '+str(minutesleft)+' m '+str(secondsleft)+' s'
							
							if hoursleft>1:
								timeleft+='\nConsider downloading bootstrap for faster sync.'
							
						tmpstr='Syncing ... \nLoaded blocks: '+str(y["blocks"])+' of '+str(y["longestchain"])+' ('+str(int(100*y["blocks"]/y["longestchain"]))+'%)' +'\nBlocks left: '+str(y["longestchain"]-y["blocks"])+'\n'+timeleft+'\n'
						
						
						self.output(tmpstr)
						
					else:
						self.output(gtmpstr)
						
				else:
					self.output('1074 getinfo output: '+gitmp)
					
			if sleep_s>4:
				sleep_s=int(sleep_s-2)
				
			if sleep_s<4: # can be for 3 reason, hence separate
				sleep_s=4
					
			# if not hasattr(self.walletTab,'stat_lab'): printsleep(sleep_s)
			# else: 
			for ti in range(int(sleep_s)):
				# tmptmptmp=self.walletTab.stat_lab.text()
				
				self.wallet_status_update.emit(['append',' .']) #self.walletTab.stat_lab.setText(self.walletTab.stat_lab.text()+' .') #.set_textvariable(None,self.statustable.get()+' .')
				time.sleep(1)
		 
		
		if cmd_orig=='start':		
			self.the_wallet=wallet_api.Wallet(self.cli_cmd,self.get_last_load(),self.db)
			
			tend=time.time()
			tdiff=int(tend-t0)
			gitmp=app_fun.run_process(cli_cmd,'getinfo')
			# print(1100,gitmp)
			y = json.loads(gitmp)
			
			loaded_block=y["blocks"]
			
			# save loading time
			idb=localdb.DB(self.db)
			table={}
			
			table['deamon_start_logs']=[{'uid':'auto', 'time_sec':tdiff, 'ttime':tend, 'loaded_block':loaded_block }]
			idb.insert(table,['uid','time_sec','ttime','loaded_block'])
			self.start_stop_enable.emit(True)
			self.deamon_started_ok=True
			# self.walletTab.bstartstop.setEnabled(True) #self.bstartstop.configure(state='normal')
			
		elif cmd_orig=='stop':
		
			self.started=False
			
			tmpcond,tmppid=app_fun.check_deamon_running() # additiona lcheck needed for full stop
			while tmpcond:
				self.wallet_status_update.emit(['append','.']) #
				# self.walletTab.stat_lab.setText(self.walletTab.stat_lab.text()+'.') #.set_textvariable(None,self.statustable.get()+' .')
				time.sleep(2)
				tmpcond,tmppid=app_fun.check_deamon_running()
			
			self.the_wallet=None
			self.start_stop_enable.emit(True)
			# self.walletTab.bstartstop.setEnabled(True) #self.bstartstop.configure(state='normal')
			self.output('Blockchain stopped')
			
			self.encrypt_wallet_and_data()
		
	def decrypt_wallet(self):
		
		idb=localdb.DB('init.db')
		ppath=idb.select('init_settings',['datadir'] )
		
		# print(self.wallet_display_set.password,os.path.join(ppath[0][0],self.wallet_display_set.data_files['wallet']+'.dat'))
		
		# if self.wallet_display_set.password==None:
			# print(1004)
		
		if os.path.exists(os.path.join(ppath[0][0],self.wallet_display_set.data_files['wallet']+'.dat') ):
			return self.wallet_display_set.data_files['wallet']+'.dat exists'
			
		elif os.path.exists(os.path.join(ppath[0][0],self.wallet_display_set.data_files['wallet']+'.encr') ):
			cc=aes.Crypto()
			rv=cc.aes_decrypt_file( os.path.join(ppath[0][0],self.wallet_display_set.data_files['wallet']+'.encr'), os.path.join(ppath[0][0],self.wallet_display_set.data_files['wallet']+'.dat') , self.wallet_display_set.password)
			time.sleep(1)
			# print( rv)
			# os.remove(ppath[0][0]+'/wallet.encr')
			if rv!='' and os.path.exists(rv):
				app_fun.secure_delete(os.path.join(ppath[0][0],self.wallet_display_set.data_files['wallet']+'.encr'))
			time.sleep(1)
			
			
			
		# if not os.path.exists(os.path.join(ppath[0][0],self.wallet_display_set.data_files['wallet']+'.dat') ):
			# addstr=''
			# if os.path.exists(os.path.join(ppath[0][0],self.wallet_display_set.data_files['wallet']+'.encr') ):
				# addstr=' However '+self.wallet_display_set.data_files['wallet']+'.encr EXISTS - MAYBE YOU SHOULD RUN WITH PASSWORD OPTION? '
			
			# if gui.msg_yes_no("Wallet file missing!", 'There is no '+self.wallet_display_set.data_files['wallet']+'.dat file in the directory \n\n'+ppath[0][0]+'\n'+addstr+'\n\n ARE YOU SURE YOU WANT TO PROCEEED?? A NEW WALLET WILL BE CREATED!'):
							
				# return 'New wallet accepted'
			# else:
				# return 'Cancel'
		# else:
			# return self.wallet_display_set.data_files['wallet']+'.dat exists'
			
		
		
		
		# elif os.path.exists(os.path.join(ppath[0][0],self.wallet_display_set.data_files['wallet']+'.encr') ):
			# cc=aes.Crypto()
			# rv=cc.aes_decrypt_file( os.path.join(ppath[0][0],self.wallet_display_set.data_files['wallet']+'.encr'), os.path.join(ppath[0][0],self.wallet_display_set.data_files['wallet']+'.dat') , self.wallet_display_set.password)
			# time.sleep(1)
			
			# if rv!='' and os.path.exists(rv):
				# app_fun.secure_delete(os.path.join(ppath[0][0],self.wallet_display_set.data_files['wallet']+'.encr'))
			# time.sleep(1)
		# else:
			# print(1033)
			# gui.messagebox_showinfo('Wallet file missing!', 'There is no '+self.wallet_display_set.data_files['wallet']+'. file in the directory \n\n'+ppath[0][0]+'\n\n Will create new wallet file!')
		
		return 'Decrypted'
			
			
			
	def encrypt_wallet_and_data(self):
		
		if self.wallet_display_set.password==None:
			return
			
		idb=localdb.DB('init.db')
		ppath=idb.select('init_settings',['datadir'] )
		
		cc=aes.Crypto()
		path2encr=os.path.join(ppath[0][0],self.wallet_display_set.data_files['wallet']+'.dat')
		path_end=os.path.join(ppath[0][0],self.wallet_display_set.data_files['wallet']+'.encr')
		rv=cc.aes_encrypt_file( path2encr, path_end , self.wallet_display_set.password)
		time.sleep(1)
		# print('encrypted wallet',path2encr,path_end,rv)
		
		encrypted_size=os.path.getsize(path_end)
		# print('encrypted_size error ',encrypted_size)
		
		if rv  and os.path.exists(path_end) and encrypted_size>10000: #rv!=''
			app_fun.secure_delete(os.path.join(ppath[0][0],self.wallet_display_set.data_files['wallet']+'.dat'))
			
		if encrypted_size<10000:
			print('encrypted_size error ',encrypted_size)
		time.sleep(1)
	
