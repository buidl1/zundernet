
import os
import time

import sys

import datetime

import subprocess
import json
import modules.app_fun as app_fun
import modules.wallet_api as wallet_api
# import modules.localdb as localdb
import modules.aes as aes

import modules.gui as gui
import traceback
	
global global_db
global global_db_init
	
	
class DeamonInit(gui.QObject):
	sending_signal = gui.Signal(list)
	msg_signal=gui.Signal(str,str,str)
	msg_signal_list=gui.Signal(str,list,list)
	start_stop_enable = gui.Signal(bool)
	wallet_status_update = gui.Signal(list)
	update_addr_book = gui.Signal()
	refresh_msgs_signal = gui.Signal()
	send_viewkey = gui.Signal(str,str )
	wallet_synced_signal= gui.Signal(bool)
	 
	def update_wallet(self,*args): # syntetic args passed auto by elem
		
		if self.started:
			# idb=localdb.DB(self.db)
			# print('refreshing wallet')
			utxo_change=self.the_wallet.refresh_wallet()
			self.update_chain_status()
			
			if 'addr_book' in self.the_wallet.to_refresh:
				self.update_addr_book.emit()
			
			# this could also be triggered by catgory or alias edit
			disp_dict=self.the_wallet.display_wallet() 
			# print('update_wallet disp_dict',disp_dict['wl'])
			date_str=app_fun.now_to_str(False)
			# print('update_wallet',47)
			table={}
			table['jsons']=[{'json_name':"display_wallet", 'json_content':json.dumps(disp_dict), 'last_update_date_time':date_str}]
			global_db.upsert(table,['json_name','json_content','last_update_date_time'],{'json_name':['=',"'display_wallet'"]})
			
			if utxo_change>0 or 'channels' in self.the_wallet.to_refresh:
				self.sending_signal.emit(['notif_update','tx_history_update' ]) #self.sending_signal.emit(['wallet'])
				self.refresh_msgs_signal.emit()
				
				
	def init_clear_queue(self):	
		# idb=localdb.DB(self.db)
		waiting=global_db.select('queue_waiting', ["type","wait_seconds","created_time","command","json","id","status"],{'command':['<>',"'automerge'"]}) # , 'command':['<>',"'process tx'"]
		
		for ii,rr in enumerate(waiting):

			if 'processing' in rr[6] or  'done' in rr[6]: # and len(idb.select('queue_done',['id'],{'id':['=',rr[5]]} ) )>0:
			
				if rr[3]!='process tx':
					table={}
					table['queue_done']=[{"type":rr[0],"wait_seconds":rr[1],"created_time":rr[2],"command":rr[3],"json":rr[4],"id":rr[5],"result":'old - forced failed on app init','end_time':app_fun.now_to_str(False)}]
					global_db.insert(table,["type","wait_seconds","created_time","command","json","id","result",'end_time'])
				
				
				global_db.delete_where('queue_waiting',{'id':['=',rr[5] ]})

				
	@gui.Slot()
	def process_queue(self):
	
		# when starting process - lock stop blockchain button return
		
		
		# idb=localdb.DB(self.db)
		 
		if not hasattr(self,'counter_15m'):
			self.counter_15m=datetime.datetime.now()
			 
			table={}
			table['queue_waiting']=[{"created_time":app_fun.now_to_str(False)}]
			 
			global_db.update( table,["created_time"],{'command':[ '=','"automerge"' ]})
		 
		history_notif_count=self.update_notarization()
		 
		waiting=global_db.select('queue_waiting', ["type","wait_seconds","created_time","command","json","id","status"])
		# print('waiting\n',waiting)
		
		if len(waiting)>0:
			# self.start_stop_enable.emit(False)
			time.sleep(1)
		else:
			self.process_queue_iter+=1 
			self.sending_signal.emit(['demon_loop',int(self.process_queue_iter)])
			return
		
		cc=aes.Crypto()	
		
		new_notif_count=0
		new_tx_history_count=0		
		count_task_done=0
		
		merged_ii=[]
		for ii,rr in enumerate(waiting):
			# print(rr)
			if ii in merged_ii:
				continue
			
			if rr[6] =='done':
				
				task_done=global_db.select('queue_done', ['end_time','result'],{'id':['=',rr[5]]})
				
				if len(task_done)>0:
					time_since_end=(datetime.datetime.now()-app_fun.datetime_from_str(task_done[0][0]) ).total_seconds()
					
					if rr[1]>=900 and time_since_end>=600 or rr[1]<900 and time_since_end>=3*60:
						global_db.delete_where('queue_waiting',{'id':['=',rr[5] ] })
				else:
					table={}
					table['queue_done']=[{"type":rr[0],"wait_seconds":rr[1],"created_time":rr[2],"command":rr[3],"json":rr[4],"id":rr[5],"result":'unknown','end_time':app_fun.now_to_str(False)}]
					global_db.insert(table,["type","wait_seconds","created_time","command","json","id","result",'end_time'])
				
				continue
			
			if rr[6] not in ['waiting','awaiting_balance'] and rr[3]!='automerge':
				continue
			
			if rr[1] - (datetime.datetime.now()-app_fun.datetime_from_str(rr[2]) ).total_seconds() - 1 >0 and rr[3]!='automerge':
				continue
			
			# 1 change status in case of task takes longer
			if rr[6]=='waiting' and rr[3]!='automerge':
				table={}
				table['queue_waiting']=[{'status':'processing'}]
				global_db.update( table,['status'],{'id':[ '=',rr[5] ]})
			
				self.sending_signal.emit(['cmd_queue'])
				time.sleep(0.3)
			
			# print('refreshing wallet before processing\n')
			# self.the_wallet.refresh_wallet()
			# print('processing\n',rr)	
			# print( 'process_queue update_wallet' )	
			self.update_wallet()
			self.sending_signal.emit(['wallet'])
				
				
				
			if rr[3]=='import_view_key': #this in addr book # {'addr':tmpaddr,'viewkey':tmpvk, 'usage_first_block':tmp_start_block}
				
				adrvk=json.loads(rr[4])
				clean_vk=adrvk['viewkey'].strip() 
				clean_addr=adrvk['addr'].strip() 
				# if nothing passed take current for speed loading / not blocking app
				start_block=self.the_wallet.getinfo()["blocks"]   #tmpblocks=self.getinfo()["blocks"]
				insert_start_block=False
				if 'usage_first_block' in adrvk:
					try: 
						start_block=int(adrvk['usage_first_block']) 
						insert_start_block=True
					except: pass
					
				# check is not already in priv keys ?
				table={}
				if clean_addr in self.the_wallet.addr_list:
					# print('view key is already aprt of the wallet priv key! - cancell')
					table['queue_done']=[{"type":rr[0],"wait_seconds":rr[1],"created_time":rr[2],"command":rr[3],"json":rr[4],"id":rr[5],"result":'cancelled - was already in prv keys','end_time':app_fun.now_to_str(False)}]
					global_db.insert(table,["type","wait_seconds","created_time","command","json","id","result",'end_time'])
					continue
					
				if clean_vk in self.the_wallet.view_key_addr_dict:
					# print('view key is already in! - cancell')
					table['queue_done']=[{"type":rr[0],"wait_seconds":rr[1],"created_time":rr[2],"command":rr[3],"json":rr[4],"id":rr[5],"result":'cancelled - was already in view keys','end_time':app_fun.now_to_str(False)}]
					global_db.insert(table,["type","wait_seconds","created_time","command","json","id","result",'end_time'])
					continue
				
				tmpresult=self.the_wallet.imp_view_key( clean_addr,clean_vk,startHeight=start_block)
				
				table['queue_done']=[{"type":rr[0],"wait_seconds":rr[1],"created_time":rr[2],"command":rr[3],"json":rr[4],"id":rr[5],"result":json.dumps(tmpresult),'end_time':app_fun.now_to_str(False)}]
				# print('inserting')
				global_db.insert(table,["type","wait_seconds","created_time","command","json","id","result",'end_time'])
				table_vk={'view_keys':[{'address':zaddr, 'vk':vkey}]}
				
				if insert_start_block:
				# vkey update cancell - only update start block on usage / actual value passed 
					table_vk['view_keys'][0]['usage_first_block']=start_block
					
				global_db.upsert(table_vk,list(kk in table_vk),where={'vk':['=',"'"+clean_vk+"'"],'address':['=',"'"+clean_addr+"'"]})
				# arrtmp=['address','vk']
				# if startHeight>1790000: # insert usage_first_block only if realistic value from init usage - not to propagate from import to import if was not yet used 
					# table_vk['view_keys'][0]['usage_first_block']= startHeight
					# arrtmp.append( 'usage_first_block')
					
				# global_db.upsert(table_vk,arrtmp,where={'vk':['=',"'"+vkey+"'"],'address':['=',"'"+zaddr+"'"]}) # separate viewkey table - was insert
		
				
				# table={}
				# if 'type' in tmpresult :
					# if tmpresult['type'].lower() in ['sapling','z-sapling','zsapling']:
						# table['addr_book']=[{ 'viewkey_verif':1 }]
						
						# table_vk={'view_keys':[{'address':clean_addr, 'vk':clean_vk,'usage_first_block': start_block}]}
						# global_db.upsert(table_vk,['address','vk'],where={'vk':['=','"'+clean_vk+"'"]}) # separate viewkey table - was insert
				# else:
					# table['addr_book']=[{ 'viewkey_verif':-1 }]
					
				# if table!={}:
					# global_db.update(table,[  'viewkey_verif'],{'Address':['=',"'"+clean_addr+"'"]}) # update addr book table 
					# self.update_addr_book.emit()
					# count_task_done+=1 
					# self.sending_signal.emit(['task_done','cmd_queue']) # print('process_queue import_view_key update_wallet')
					# self.update_wallet() # print('wallet refreshed ')
				self.update_addr_book.emit()
				count_task_done+=1 
				self.sending_signal.emit(['task_done','cmd_queue']) # print('process_queue import_view_key update_wallet')
				self.update_wallet() # print('wallet refreshed ')
				
			elif rr[3]=='import_priv_keys': #json.dumps({'addr':tmpaddr,'viewkey':tmpvk})
			
				tmpjs=json.loads(rr[4]) # ddict[addr]={pk, usage_first_block}
				ll=len(tmpjs )
				# ll=len(tmpjs['keys'])
				added_addr=[]
				
				for aa in tmpjs:#ii,kk in enumerate(tmpjs['keys']): 
					table={'queue_waiting':[{'status':'processing '+str(ii+1)+'/'+str(ll)}]}
					# table['queue_waiting']=[{'status':'processing '+str(ii+1)+'/'+str(ll)}]
					global_db.update( table,['status'],{'id':[ '=',rr[5] ]})
					self.sending_signal.emit(['cmd_queue'])
					tmpresult=''
					if 'usage_first_block' in tmpjs[aa]:
						tmpresult=self.the_wallet.imp_prv_key( tmpjs[aa]['pk'],startHeight=tmpjs[aa]['usage_first_block'] ) # now optimal 
					else:
					
						tmpresult=self.the_wallet.imp_prv_key( tmpjs[aa]['pk'],startHeight=self.the_wallet.getinfo()["blocks"]    ) #1700000
					added_addr.append(aa) #tmpresult['address'])
					
				table={}
				table['queue_done']=[{"type":rr[0],"wait_seconds":rr[1],"created_time":rr[2],"command":rr[3],"json":rr[4],"id":rr[5],"result":'new addresses: '+str(added_addr),'end_time':app_fun.now_to_str(False)}]
				
				global_db.insert(table,["type","wait_seconds","created_time","command","json","id","result",'end_time'])
				 
				count_task_done+=1
				self.sending_signal.emit(['task_done','cmd_queue'])
				
				self.update_priv_keys_table(tmpjs )
				
				# add for update ? need also start block 
				# for ii,kk in enumerate(tmpjs['keys']):
					# self.the_wallet.add_pk_for_start_block(added_addr[ii],kk)
				
			elif rr[3]=='validate_addr':
			
				adrvk=json.loads(rr[4])
				tmpresult=self.the_wallet.validate_zaddr( adrvk['addr'] )
				table={}
				table['queue_done']=[{"type":rr[0],"wait_seconds":rr[1],"created_time":rr[2],"command":rr[3],"json":rr[4],"id":rr[5],"result":tmpresult,'end_time':app_fun.now_to_str(False)}]
				
				global_db.insert(table,["type","wait_seconds","created_time","command","json","id","result",'end_time'])
				count_task_done+=1
				
				table={}
				if tmpresult=='not valid exception' or tmpresult==False:
					
					table['addr_book']=[{ 'addr_verif':-1 }]  #,'viewkey_verif' 
				else:
					table['addr_book']=[{ 'addr_verif':1 }]  #,'viewkey_verif' 
				global_db.update(table,[  'addr_verif'],{'Address':['=',global_db.qstr(adrvk['addr']) ]})
				self.update_addr_book.emit()
				self.sending_signal.emit(['task_done','cmd_queue'])
			
			elif rr[3]=='new_addr':
			
				# print('new addr',rr)
				addr_opt=json.loads(rr[4])
				addr_count= addr_opt['addr_count'] 
				addr_cat=addr_opt['addr_cat']
				addr_cat_counter=addr_opt['addr_cat_counter'] # yes / no
				new_seed=addr_opt['new_seed']
			
				# 2 create results / wallet api
				new_addr_list=[]
				date_str=app_fun.now_to_str(False)
				
				# for priv keys update
				next_id=1
				table_pk={'priv_keys':[]} #table_pk['priv_keys']=[] #{'id':next_id, 'address':aa, 'pk':pk }]
				pk=''
				if new_seed=='New':
					max_id=global_db.select_max_val('priv_keys','id' )
					if len(max_id)>0:
						if max_id[0]!=None:
							next_id=max_id[0][0]+1 
				else:
					# next_id= new_seed # str self.db_main
					_pk= global_db.select('priv_keys',['pk' ],where={'id':['=',new_seed]})
					if len(_pk)>0: pk=_pk[0][0]
					else:
						print('some error - no pk in db??',new_seed,_pk)
						return
					
				# print('pk,new_seed,next_id',pk,new_seed,next_id)	
			
			
				for nal in range(addr_count):
					# print(nal,addr_count)
					tmpresult=self.the_wallet.new_zaddr(new_seed)
					# print(tmpresult)
					new_addr_list.append(tmpresult)
					if new_seed=='New':
						pk=self.the_wallet.exp_prv_key(tmpresult)
						table_pk['priv_keys'].append({'id':next_id, 'address':tmpresult, 'pk':pk })
						next_id+=1
					else:
						# print('# get pk and id from db',new_seed,int(new_seed),pk)
						# pk=self.the_wallet.exp_prv_key(tmpresult).replace('\r','').replace('\\n','').replace('\\r','')
						table_pk['priv_keys'].append({'id':int(new_seed), 'address':tmpresult, 'pk':pk }) # pk set from _pk
					# print('after ifelse')
					# add category
					if addr_cat!='':
						tmp_cat=addr_cat
						if addr_cat_counter:
							tmp_cat+='_'+str(nal+1)
						
						table={'address_category':[{'address':tmpresult, 'category':tmp_cat, 'last_update_date_time':date_str}]}			
						# print(table)
						global_db.insert(table,['address','category','last_update_date_time']) #,{'address':['=',"'"+tmpresult+"'"]})
					
					# print('# update msg')
					table={}
					table['queue_waiting']=[{'status':'processing '+str(nal+1)+'/'+str(addr_count)}]
					global_db.update( table,['status'],{'id':[ '=',rr[5] ]})
					self.sending_signal.emit(['cmd_queue'])
					# time.sleep(0.01)
					
				# print('# if new_seed: ')
				global_db.insert(table_pk,['id','address','pk'])	
				# print('inserted',table_pk)
				# also for current seed ? as long as addr was not used ? = as long as already there ?
				
				for tpk in table_pk['priv_keys']: # tpk = {'id':int(new_seed), 'address':tmpresult, 'pk':pk }
					# add aa/pk to update stat block if new seed or if current pk already there-  then trigger for new addr too 
					# print('ckeck if ',tpk,new_seed,self.the_wallet.addr_privkey_start.values())
					if new_seed=='New' or tpk['pk'] in self.the_wallet.addr_privkey_start.values(): 
						self.the_wallet.add_pk_for_start_block(tpk['address'],tpk['pk'])
				
				
				
				# 3 insert result to queue done
				table={}
				table['queue_done']=[{"type":rr[0],"wait_seconds":rr[1],"created_time":rr[2],"command":rr[3],"json":rr[4],"id":rr[5],"result":tmpresult,'end_time':app_fun.now_to_str(False)}]
				
				global_db.insert(table,["type","wait_seconds","created_time","command","json","id","result",'end_time'])
				count_task_done+=1
				
				self.msg_signal.emit('New address(es) created','New address(es):\n\n'+'\n'.join(new_addr_list),'')
				self.sending_signal.emit(['task_done','cmd_queue'])
				# idb.select('queue_done', [ "id" ])
				
			# moved to wa disp set - dat taken from db
			elif rr[3]=='export_wallet':
						 
				tmpresult=self.the_wallet.export_wallet() 
				# print('tmpresult',tmpresult)
				path2=json.loads(rr[4])
				# print('rr',rr)
				tmppassword=path2['password']
				path2=os.path.join(path2['path'],'addrkeys_'+app_fun.now_to_str(True)+'.txt') 
				# print('path2',path2)
				if tmppassword=='current':
					cc.aes_encrypt_file( json.dumps(tmpresult),path2 ,self.wallet_display_set.password)		 
				elif tmppassword=='random':			 
					tmppassword=cc.rand_password(32)
					cc.aes_encrypt_file( json.dumps(tmpresult) , path2 , tmppassword )				
				else:
					# print('write')
					cc.write_file( path2 , json.dumps(tmpresult) , gui_copy_progr=gui.copy_progress )
					tmppassword=''
				
				tmptitle='Private keys exported. Private keys exported to\n'+path2 
				
				if tmppassword!='':
					tmptitle+='. File was encrypted with password:\n' 
				table={}
				table['queue_done']=[{"type":rr[0],"wait_seconds":rr[1],"created_time":rr[2],"command":rr[3],"json":rr[4],"id":rr[5],"result":'exported to '+path2,'end_time':app_fun.now_to_str(False)}]
				# print('insert')
				global_db.insert(table,["type","wait_seconds","created_time","command","json","id","result",'end_time'])
				count_task_done+=1
				
				table={}
				table['queue_waiting']=[{'status':'done'}]
				# print('update')
				global_db.update( table,['status'],{'id':[ '=',rr[5] ]})
				self.sending_signal.emit(['cmd_queue'])
				if tmppassword=='current':
				
					tmptitle+='Your current password'
					self.msg_signal.emit(tmptitle,'','')
				else:
					self.msg_signal.emit(tmptitle,'',tmppassword)
					
				# time.sleep(3)
				self.sending_signal.emit(['task_done','cmd_queue'])
				
			elif rr[3]=='get_viewkey': # for set channel
			
				ddict=json.loads(rr[4])
				tmpresult=self.the_wallet.exp_view_key(ddict['addr'])
			
				self.send_viewkey.emit(ddict['addr'],tmpresult)
				self.sending_signal.emit(['task_done','cmd_queue'])
			
			elif rr[3]=='export_viewkey': # make sure export view key start block as minimum from pk start block 
				ddict=json.loads(rr[4])
				tmpresult=self.the_wallet.exp_view_key(ddict['addr'])
				tmptitle='View key display'
				# print(tmpresult)
				vk_start_block=None #1700000
				# vk_start_block00= global_db.select('priv_keys',[ 'usage_first_block'],where={'address':['=','"'+ddict['addr']+'"') # 'usage_first_block'
				pk00= global_db.select('priv_keys',[ 'pk'],where={'address':['=', global_db.qstr(ddict['addr'])  ]}) # 'usage_first_block'
				# for this pk check min start block 
				# print('pk00',pk00 )
				
				if len(pk00)>0:
				# select_min_val(self,table_name,column,where={},groupby=[])
					# print('pk00[0][0]', global_db.qstr(pk00[0][0]))
					vk_start_block00= global_db.select_min_val('priv_keys', 'usage_first_block' ,where={'pk':['=',global_db.qstr(pk00[0][0]) ]}) # 'usage_first_block'
					# print('vk_start_block00 1',vk_start_block00)
					if len(vk_start_block00)>0: 
						# if vk_start_block00[0][0]!=None:
						vk_start_block=vk_start_block00[0][0]
					# print('vk_start_block00 2',vk_start_block)
				
				# if len(vk_start_block00)>0: vk_start_block00=vk_start_block00[0][0]
				# else: vk_start_block00=1700000
				
				pto='screen'
				if ddict['password']=='':
					# print(tmptitle,ddict)
					# gui.output_copy_input(None,'View key display' ,('Address  '+ddict['addr']+'\n\nView key '+tmpresult,))
					self.msg_signal.emit(tmptitle,'','Address\n\n'+ddict['addr']+'\n\nView key:\n\n'+tmpresult+'\n\nStart block: '+str(vk_start_block))
					
				else:
					tmppass=cc.rand_password(32)
					tmpdict={'addr':ddict['addr'], 'viewkey':tmpresult }
					if vk_start_block!=None: tmpdict['usage_first_block']=vk_start_block
					tmpresult=json.dumps(tmpdict)
					pto=ddict['path']+'/viewkey_'+app_fun.now_to_str()+'.txt'
					cc.aes_encrypt_file( tmpresult, pto  , tmppass) 
					tmptitle='View key exported to:\n\n'+pto+'\n\nPassword:' #+tmppass
					self.msg_signal.emit(tmptitle,'',tmppass)
					# gui.output_copy_input(None,'Password for file exported to '+pto,(tmppass,))
					
				# print('ok?')
				table={}
				table['queue_done']=[{"type":rr[0],"wait_seconds":rr[1],"created_time":rr[2],"command":rr[3],"json":rr[4],"id":rr[5],"result":'exported to '+pto,'end_time':app_fun.now_to_str(False)}]
				
				global_db.insert(table,["type","wait_seconds","created_time","command","json","id","result",'end_time'])
				count_task_done+=1
				time.sleep(1)
				self.sending_signal.emit(['task_done','cmd_queue'])
			
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
				self.sending_signal.emit(['task_done','cmd_queue'])
				
				
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
						
						global_db.insert(table,["type","wait_seconds","created_time","command","json","id","result",'end_time'])
					
					
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
						global_db.update( table,['status',"created_time"],{'id':[ '=',rr[5] ]})
					
						self.sending_signal.emit(['cmd_queue'])
						
					elif int(total_s)%5==0:
						
						table={}
						if notes_count<ddict['limit']:
							
							table['queue_waiting']=[{'status':'awaiting\nlimit '+str(notes_count)+'/'+str(ddict['limit'])} ]
						else:
							table['queue_waiting']=[{'status':'waiting 15min\ntill next check'} ]
						
						global_db.update( table,['status'],{'id':[ '=',rr[5] ]})	
						self.sending_signal.emit(['cmd_queue'])
					
			elif rr[3]=='send': # 
			
				def insert_notification(details, tmpjson):
					if type(tmpjson)==type({}):
						tmpjson=json.dumps(tmpjson)
				
					# idb=localdb.DB(self.db)
					table={}
					dt,ts=app_fun.now_to_str(False,ret_timestamp=True)
					# print('notif details',details,'dt',dt,'json',tmpjson)
					table['notifications']=[{'opname':'send','datetime':dt,'status':'Failed','details':details,'closed':'False','orig_json':tmpjson,'uid':'auto'}]
					
					global_db.insert(table,['opname','datetime','status','details', 'closed','orig_json' ,'uid'])
					new_notif_count+=1
				
			
				ddict=json.loads(rr[4])
				# print(453,ddict)
				exceptions=[]
				# better use the wallet ! self.addr_amount_dict[aa]={'confirmed'
				
				# total_conf_per_addr=self.wallet_display_set.amount_per_address[ddict['fromaddr']]
				
				sum_cur_spending=0
				total_conf_per_addr=0
				if ddict['fromaddr'] in self.the_wallet.addr_amount_dict: #self.wallet_display_set.amount_per_address: #self.the_wallet.addr_amount_dict: #self.addr_amount_dict.amount_per_address :
				
					total_conf_per_addr=self.the_wallet.addr_amount_dict[ddict['fromaddr']]['confirmed']
					# total_conf_per_addr=self.wallet_display_set.amount_per_address[ddict['fromaddr']]
					for tt in ddict['to']:
						sum_cur_spending+=float(tt['a'])
				else:
					print('addr not on the list?',ddict['fromaddr'],self.the_wallet.addr_amount_dict)
						
				# print(453,total_conf_per_addr)
				# print('sum_cur_spending',sum_cur_spending,round(sum_cur_spending,8),round(total_conf_per_addr-0.0001,8))	
				
				if round(sum_cur_spending,8)>round(total_conf_per_addr-0.0001,8): # validate amoaunt to send
					
					table={}
					table['queue_waiting']=[{'status':'awaiting_balance'}]
					global_db.update( table,['status'],{'id':[ '=',rr[5] ]}) # 
					self.sending_signal.emit(['cmd_queue'])
					# time.sleep(1)
				
				elif self.the_wallet.validate_zaddr(ddict['fromaddr']) : # first validate addr:
				
					table={}
					table['queue_waiting']=[{'status':'processing'}]
					global_db.update( table,['status'],{'id':[ '=',rr[5] ]})
					self.sending_signal.emit(['cmd_queue'])
					# time.sleep(1)
				
					merged_queue_done=[]
					msg_chnl=['message','channel'] # merging utxo sending only if not msg or chnls
					
					# merging should be only for auto sends ?
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
					
					# print('sending_summary\n',sending_summary)
					# print('from',ddict['fromaddr'])
					# print('to',tostr)
					# return 
					self.sending_signal.emit(['cmd_queue']) # more frequent queue refresh
					
					tmpres={}
					tmpres['opid']=''
					tmpres['result_details']='Bad amounts or not valid addresses.'
					tmpres["result"]='Failed - Nothing to process.'
					tmpres['exceptions']= '\n'.join(exceptions)	
					if len(sending_summary)>0:
						tostr=json.dumps(sending_summary)
						# print('SENDING',)
						tmpres['opid']=str(self.the_wallet.send(ddict['fromaddr'],tostr))
						tmpres['opid']=tmpres['opid'].strip()
						self.sending_signal.emit(['cmd_queue']) # more frequent queue refresh
						# print('tmpres\n',tmpres)
						
						cmdloc=['z_getoperationstatus','["'+tmpres['opid']+'"]']

						opstat=app_fun.run_process(self.cli_cmd,cmdloc)

						opj=''
						try:
							opj=json.loads(opstat)[0]
						except:
							opj={'error':{'message':opstat}}
						
						if 'error' in opj:
							if 'message' in opj['error']:
								tmpres['result_details']=str(opj['error']['message'].replace('shielded ','') )
							else:
								tmpres['result_details']=str(opj['error'] )
							tmpres["result"]='Failed'
							
							insert_notification(tmpres['result_details'], {'fromaddr':ddict['fromaddr'],'to':[to]})
							self.sending_signal.emit(['cmd_queue']) # more frequent queue refresh
							
						else:
							ts=7
							
							def refrsh(ts):
								tmpts=0
								while tmpts<ts: 
									self.sending_signal.emit(['cmd_queue']) # more frequent queue refresh
									tmpts+=1
									time.sleep(1)
							
							# self.sending_signal.emit(['cmd_queue']) # more frequent queue refresh
							while "result" not in opj:
							
								refrsh(ts) 
								
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
									# time.sleep(ts)
									refrsh(ts)
									if ts>1:
										ts=ts-1
									
									opstat=app_fun.run_process(self.cli_cmd,cmdloc)
									opj=json.loads(opstat)[0]
									# print('while exe',opj)
									
								if opj["status"]=="success":
									tmpres["result"]='success'
									# print('sending success')
								else:
									# print('sending failed',opstat)
									tmpres["result"]='Failed'
									exceptions.append('Failed to process tx: '+opstat)
									insert_notification(opstat, {'fromaddr':ddict['fromaddr'],'to':[to]})
									
								tmpres["result_details"]=str(opj["result"])
						
						del tmpres['opid'] # not needed later 
						
						tmpres["block"]=0 
						# print('# get block nr for confirmation notarization validation later on ')
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
							# time.sleep(5)
							refrsh(5)
							
							
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
							
							global_db.insert(table,['Category','Type','status','txid','block','timestamp', 'date_time','from_str','to_str','amount','uid'])
							new_tx_history_count+=1
							# self.tx_history.update_history_frame()
							
							txid_utf8=txid 
							if rr[0] not in ['message','channel']: # normal send / not msg
								# print(711," deamon not in ['message','channel']")
								for mmii,mm in enumerate(memo_orig):
									# print(mmii,mm,sending_summary[mmii])
									table=self.the_wallet.prep_msgs_inout(txid_utf8,mm,'out',dt,addr_to=sending_summary[mmii]["address"] ) #tostr.append({"address":to['z']
									if table['msgs_inout'][0]['msg']=='':
										table['msgs_inout'][0]['msg']='Sent amount '+str(round(sum_cur_spending,8))
									# if table=={}:
										# continue
																	 
									global_db.insert(table,['proc_json','type','addr_ext','txid','tx_status','date_time', 'msg', 'uid','in_sign_uid','addr_to'])
							else: #'message': msg_chnl
								# print('msg or channe')
								mmm=['',0,memo_orig[0][2]]
								for mmii,mm in enumerate(memo_orig):
									mmm[0]+=mm[0] # memo txt 
									mmm[1]+=mm[1] # amount
									
								# print('mmm',mmm)
								# also for channels?
								if True: #rr[0]=='message':
									# print('prep msg deamon 731')
									table=self.the_wallet.prep_msgs_inout(txid_utf8,mmm,'out',dt,addr_to=sending_summary[0]["address"])
									table['msgs_inout'][0]['is_channel']='False'
									# print('prep msg deamon 734',rr[0])
									if rr[0]=='channel':
									# table['queue_waiting'][0]['type']='channel'
										# print('prep msg deamon 737')
										table['msgs_inout'][0]['is_channel']='True'
										# print('Should mark out channel 709')
										
									if table!={}:
										# print('prep msg deamon 742\n',table)
										global_db.insert(table,['proc_json','type','addr_ext','txid','tx_status','date_time', 'msg', 'uid','in_sign_uid','addr_to','is_channel'])
									
									
						# todo: see where pre msg is used and ext_addr
						# replace 1 addr to ddict['fromaddr']						
						# self.messages.update_msgs()
						
						tmpres=json.dumps(tmpres)	
							
						table={}
						table['queue_done']=[{"type":rr[0],"wait_seconds":rr[1],"created_time":rr[2],"command":rr[3],"json":rr[4],"id":rr[5],"result":tmpres,'end_time':app_fun.now_to_str(False)}]
						global_db.insert(table,["type","wait_seconds","created_time","command","json","id","result",'end_time'])

						for ss in merged_queue_done:
							table={}
							table['queue_done']=[{"type":ss[0],"wait_seconds":ss[1],"created_time":ss[2],"command":ss[3],"json":ss[4],"id":ss[5],"result":tmpres,'end_time':app_fun.now_to_str(False)}]
						
							global_db.insert(table,["type","wait_seconds","created_time","command","json","id","result",'end_time'])
							
							table={}
							table['queue_waiting']=[{'status':'done'}]
							global_db.update( table,['status'],{'id':[ '=',ss[5] ]})
							time.sleep(0.3)
							self.sending_signal.emit(['cmd_queue'])
							time.sleep(0.3)
							
						self.update_wallet()
						# print('process_queue send update_wallet')
						time.sleep(0.3)
					
					else:
						
						tmpres=json.dumps(tmpres)# some exceptions:
						table={}
						table['queue_done']=[{"type":rr[0],"wait_seconds":rr[1],"created_time":rr[2],"command":rr[3],"json":rr[4],"id":rr[5],"result":tmpres,'end_time':app_fun.now_to_str(False)}]
						global_db.insert(table,["type","wait_seconds","created_time","command","json","id","result",'end_time'])
					
				else:
					tmpres="Wrong [from] address!"
					
					table={}
					table['queue_done']=[{"type":rr[0],"wait_seconds":rr[1],"created_time":rr[2],"command":rr[3],"json":rr[4],"id":rr[5],"result":tmpres,'end_time':app_fun.now_to_str(False)}]
						
					global_db.insert(table,["type","wait_seconds","created_time","command","json","id","result",'end_time'])
				
				count_task_done+=1
			
			if rr[3]!='automerge':
				table={}
				table['queue_waiting']=[{'status':'done'}]
				global_db.update( table,['status'],{'id':[ '=',rr[5] ], 'status':[ '=',"'processing'" ],"command":['<>',"'automerge'"]})
				self.sending_signal.emit(['cmd_queue'])
				time.sleep(1)
				
		# print('process_queue self.start_stop_enable.emit(True)')
		# self.start_stop_enable.emit(True)
		
		global_db.delete_where('queue_waiting',{ 'status':[' not in ',"('awaiting_balance','waiting')"]  }  )  #, "command":[' not in ',"('send','automerge')"]  
		global_db.delete_where('queue_waiting',{ "command":[' not in ',"('send','automerge')"]  }  )  #, "command":[' not in ',"('send','automerge')"]  
		# table['queue_done']
		# idb.delete_where('queue_waiting',{ 'status':['<>',"'awaiting_balance'"], 'status':['<>',"'waiting'"], "command":['<>',"'send'"], "command":['<>',"'automerge'"]  }) 
		# do not delete if awaiting balance or waiting or command is send (delete in another thread time based) or command is autom merge - cancelled manually
		
		self.process_queue_iter+=1
		list_emit=['cmd_queue','demon_loop',int(self.process_queue_iter)] # self.sending_signal.emit(list_emit)
		if count_task_done>0:
			list_emit.append('task_done')
			
		if new_notif_count>0:
			list_emit.append('notif_update')
		if new_tx_history_count>0:
			list_emit.append('tx_history_update')
			
		if  new_notif_count + new_tx_history_count >0:
			list_emit.append('wallet')
			
		self.sending_signal.emit(list_emit) # self.sending_signal.emit(['cmd_queue'])
		
		# print('after delete emit')	
		if 'notif_update' in list_emit or 'tx_history_update' in list_emit:
			self.refresh_msgs_signal.emit()
		
		time.sleep(1)
		
	
	def update_notarization(self): 	#time.time()
	
		if not hasattr(self , 'update_notarization_time'): # first run - create variable
			self.update_notarization_time=time.time()
			
		elif time.time() - self.update_notarization_time < 30: # next run - measure time each 30 seconds 
			# print('NOT update_notarization',time.time() - self.update_notarization_time)
			return 0
		
		else:
			self.update_notarization_time=time.time()
		
		notar=0
		try:
			y=json.loads(app_fun.run_process(self.cli_cmd,'getinfo'))		
			notar=y["notarized"]
		except:
			print(814,'demon update tx exception')
			return 0
			
		# idb=localdb.DB(self.db)	 
		count_updates=0 
		tmpwhere={'status':[' not in',"('reorged','notarized')"], 'block':['<=',notar] }
		toupdate=global_db.select('tx_history', ["txid" ],tmpwhere,distinct=True)

		if len(toupdate)>0:
		
			for tt in toupdate: #
				txidok=self.the_wallet.z_viewtransaction( tt[0] ) # if not in blocks anymore ? not valid ?
				 
				if txidok!='not valid txid':
				
					table={}
					table['tx_history']=[{'status':'notarized'}]
					global_db.update( table,['status'], { 'txid':['=',global_db.qstr(tt[0]) ] } )
					
					table={} # update notification 
					table['notifications']=[{'status':'notarized' }]
					global_db.update( table,['status'], {'details':['=',global_db.qstr(tt[0]) ] } )
					
					table={} # update msg table: 
					table['msgs_inout']=[{'tx_status':'notarized' }]
					global_db.update( table,['tx_status'  ], {'txid':['=',global_db.qstr(tt[0])  ] })
				 
				count_updates+=1
	
			if count_updates>0:
				self.sending_signal.emit([ 'tx_history_update','notif_update'])
				self.refresh_msgs_signal.emit()
	
		return count_updates
		
	def update_chain_status(self,gitmp=None,update=True):
		if self.started:
			if gitmp==None:
				gitmp=app_fun.run_process(self.cli_cmd,'getinfo')
			gi=json.loads(gitmp) 
			kv_tmp=[{"name":"Chain: "},{"synced":"\nSynced: "},{"blocks":"\nCurrent block: " }, {"longestchain":"\nLongest chain: "}, {"notarized":"\nNotarized: "}, {"connections":"\nConnections: "}]
			tmpstr=""
			for dd in kv_tmp:
				for kk,vv in dd.items():
					if kk in gi:
						tmpstr+=vv+str(gi[kk])
						
			if update:
				self.output(tmpstr)
			else:
				return tmpstr
	
	def update_status(self,xx):
		
		ret_val=[]
		if self.started:
		
			# try:
			if True:
				gitmp=app_fun.run_process(self.cli_cmd,'getinfo')
				gi=json.loads(gitmp)
				# print('\nupdate_status 700',gi)
				# kv_tmp=[{"name":"Chain: "},{"synced":"\nSynced: "},{"blocks":"\nCurrent block: " }, {"longestchain":"\nLongest chain: "}, {"notarized":"\nNotarized: "}, {"connections":"\nConnections: "}]
				# tmpstr=""
				# for dd in kv_tmp:
					# for kk,vv in dd.items():
						# if kk in gi:
							# tmpstr+=vv+str(gi[kk])
				tmpstr=self.update_chain_status(gitmp , False)
				
				
				# "Synced: "+str(gi["synced"])+"\nCurrent block: "+str(gi["blocks"])+"\nLongest chain: "+str(gi["longestchain"])+"\nNotarized: "+str(gi["notarized"])+"\nConnections: "+str(gi["connections"])
				
				if time.time()-self.insert_block_time>50: # check every 50 seconds
					self.insert_block_time=time.time()
					table={'block_time_logs':[{'uid':'auto', 'ttime':time.time(), 'block':gi["blocks"] }] }
					# idbinit=localdb.DB('init.db')
					
					# here bug hanging !!! 
					global_db_init.upsert(table,['uid', 'ttime','block'],{'block':['=',gi["blocks"]]})
				
				# print('\nupdate_status 709' )
				if xx%3==2:
					self.output(tmpstr)
				
				if int(gi["connections"])>0:
					ret_val.append('CONNECTED')
				
				# print('\nupdate_status 715' )
				modv=46 # about 15 sec
				
				if xx%modv==0 and self.started:
				# if xx%modv==modv-1 and self.started:
					# print( 'update_status update_wallet' )
					self.update_wallet()
					ret_val.append('wallet')
				# print('\nupdate_status 721',ret_val)
					
				if xx%modv==modv-1 and self.started:
					self.update_notarization()
					# self.update_incoming_tx()
					
				if xx%3==2: # and self.started: # every second
					# print('process queue')
					self.is_processing=True
					self.process_queue()
					self.is_processing=False
					# print('process queue done')
					ret_val.append('cmd_queue')
					
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
		
		self.is_processing=False
		
		
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
		
		self.started=False # tell process queue to stop
		while self.is_processing:
			time.sleep(1)
			print('waiting to stop deamon')
		# print('stopping deamon b4 outpost')
		self.output('Stopping deamon\n')
		# print('after outpost')
		self.run_subprocess(self.cli_cmd,'stop',2)
		
	def set_obj(self,obj_updateWalletDisplay):
		self.obj_updateWalletDisplay=obj_updateWalletDisplay

	@gui.Slot()
	def start_deamon(self, addrescan=False ): # if pirate-cli process exist - do not create another one !
		# print('new start deamon???')
		self.started=True
		
		tmpcond=app_fun.check_deamon_running() # ''.join(self.deamon_par) ,tmppid
		# print('tmpcond',tmpcond)
		if tmpcond[0]: # if already running
		
			# self.start_stop_enable.emit(True)
			
			gitmp=app_fun.run_process(self.cli_cmd,'getinfo')
			# print('gitmp',gitmp)
			time.sleep(1)
			while 'longestchain' not in gitmp:
				if 'Loading block index' in gitmp:
					self.output('Loading block index\n')
				else:
					self.output('Awaiting longest chain\n')
				
				for ii in range(4):
					self.wallet_status_update.emit(['append',' .'])
					time.sleep(1)
				
				gitmp=app_fun.run_process(self.cli_cmd,'getinfo')
				
			# print('self.the_wallet',self.the_wallet)
			if self.the_wallet==None: #hasattr(self,'the_wallet')==False or :
				# print('self.get_last_load()',self.get_last_load())
				self.the_wallet=wallet_api.Wallet(self.cli_cmd,self.get_last_load(),self.db)
				# print('connetcing wal api signal 1013')
				self.the_wallet.sending_signal.connect(self.obj_updateWalletDisplay) 
		
			y = json.loads(gitmp)
			# print('y:',y,"synced" in y,type(y["synced"]))
			if "synced" in y:
				if y["synced"]==True:
				# self.walletTab.bstartstop.setEnabled(True) #self.bstartstop.configure(state='normal')
					self.start_stop_enable.emit(True)
					# print('self.update_chain_status()')
					self.update_chain_status()
					# print('self.the_wallet.refresh_wallet()')
					self.the_wallet.refresh_wallet()
			elif y['longestchain']==y['blocks']:
				self.start_stop_enable.emit(True)
				self.update_chain_status()
				self.the_wallet.refresh_wallet()
			else:
				# self.walletTab.bstartstop.setEnabled(False) #self.bstartstop.configure(state='disabled')
				self.start_stop_enable.emit(False)
				
			self.wallet_synced_signal.emit(True)
		else:
			# print('start_deamon???')
			self.output('Decrypting wallet ...')
			if self.decrypt_wallet()=='Cancel':
				return
				
			self.output('Starting deamon\n usually takes few minutes ...')
			reskanopt=[] #['-salvagewallet']
			if addrescan:
				reskanopt=['-rescan']
				
			self.run_subprocess([self.deamon_par+reskanopt,self.cli_cmd],'start',8)
			
			# return
			
		self.update_priv_keys_table( )

	# for pk there may be many addr - this is checking them all 
	def update_priv_keys_table(self,with_usage_blocks=None):
		# here check if priv key table is ready ? or ?	
		# also do insert after creating new priv addr ?
		# global_db.delete_where('priv_keys' )
		all_pk= global_db.select('priv_keys',['address','id','pk']) 
		# print(all_pk,len(all_pk), len(self.the_wallet.addr_list))
		if len(all_pk)<len(self.the_wallet.addr_list):
			# self.output('Updating priv key table '+str(len(all_pk))+'<>'+str(len(self.the_wallet.addr_list)) )
			ddict=global_db.set_que_waiting('Update priv\nkey table' )
			ddict["type"]='auto'
			ddict["status"]="in progress" #table['queue_waiting']=[ddict]
			# print('ddict',ddict)
			update_id=ddict['id']
			global_db.insert({'queue_waiting':[ddict]},['type','wait_seconds','created_time','command' ,'json','id','status' ])
			# print(update_id,ddict)
			# global_db.insert( table,['status'],{'id':[ '=',rr[5] ]}) # 
			self.sending_signal.emit(['cmd_queue'])
			time.sleep(0.1)
					
			pk_not_in=[]
			for aa in self.the_wallet.addr_list:
				if aa not in all_pk:
					pk_not_in.append(aa)
					
			pkids={}
			for rr in all_pk:
				pkids[rr[2]]=rr[1] # id per pk 
			
			# print(pk_not_in,'pk_not_in')	
			max_id=global_db.select_max_val('priv_keys','id' )
			next_id=1
			if len(max_id)>0:
				if  len(max_id[0])>0 and max_id[0][0]!=None:
					# print()
					next_id=max_id[0][0]+1  
			# print(next_id,'next_id')
			table={'priv_keys':[]}
			# table['priv_keys']=[] #{'id':next_id, 'address':aa, 'pk':pk }]
			# to_add_arr=['id','address','pk']
			to_add_arr=['id','address','pk','usage_first_block' ] #,'usage_first_block'
			first_block_per_addr={}
			# if with_usage_blocks!=None: to_add_arr=['id','address','pk','usage_first_block' ]
			# else:
			# print('with_usage_blocks',with_usage_blocks)
			if with_usage_blocks==None:
				tmp_ba=global_db.select_min_val('tx_history', 'block' ,groupby=['to_str']) 
				# print('tmp_ba',tmp_ba)
				for rr in tmp_ba:
					first_block_per_addr[rr[0]]=rr[1]
					
				# print('first_block_per_addr',first_block_per_addr)
			
			for ii, aa in enumerate(pk_not_in):
				# self.output('Updating priv key table '+str(ii)+'/'+str(len(pk_not_in)-1) )
				# ddict=self.db_main.set_que_waiting('Update priv\nkey table' )
				# ddict["type"]='auto'
				# ddict["status"]="in progress" #table['queue_waiting']=[ddict]
				global_db.update( {'queue_waiting':[{'status':"in progress\n"+str(ii)+'/'+str(len(pk_not_in)-1) }]},[ 'status' ],where={'id':['=',str(update_id)]})
				self.sending_signal.emit(['cmd_queue'])
				time.sleep(0.1)
				
				
				pk=self.the_wallet.exp_prv_key(aa).replace('\r','').replace('\\n','').replace('\\r','')
				pk=pk[-8:] # for security only 8 last chars
				
				toadd={'id':next_id, 'address':aa, 'pk':pk, 'usage_first_block':None  } #, 'usage_first_block':1790000 
				
				if pk in pkids: # if pk already got id from another addr 
					toadd['id']=pkids[pk]
					# toadd={'id':pkids[pk], 'address':aa, 'pk':pk  } #, 'usage_first_block':1790000
				else:
					# print('new addr, pk',aa[:9],pk.replace('secret-extended-key-','')[:64],next_id)
					pkids[pk]=next_id
					next_id+=1
				# toadd={'id':next_id, 'address':aa, 'pk':pk , 'usage_first_block':1790000 }
				
				
				
				# here better take first tx from history ... 
				
				# print(toadd)
				if with_usage_blocks!=None :
					try:
						if 'usage_first_block' in with_usage_blocks[aa]:
							toadd['usage_first_block']=with_usage_blocks[aa]['usage_first_block']
					except:
						print('with_usage_blocks!=None but none for addr ',aa,with_usage_blocks)
						# pass
				elif aa in first_block_per_addr and first_block_per_addr[aa]>0:
					toadd['usage_first_block']=first_block_per_addr[aa]
					
				table['priv_keys'].append(toadd)
				
				# only iterate next_id if pk not yet in 
				
			# print('def update_priv_keys_table(self,with_usage_blocks=None)',table)
			global_db.insert(table,to_add_arr) 
			
			global_db.delete_where('queue_waiting',{'id':['=',str(update_id) ] })
			self.sending_signal.emit(['cmd_queue'])
			# , 'usage_first_block':'int' 
			
			
			
			
	
	def get_last_load(self):

		# idb=localdb.DB(self.db )
		last_load=0 # was -1 
		if global_db.check_table_exist( 'deamon_start_logs'):
			
			tt00=global_db.select_max_val('deamon_start_logs','loaded_block',where={'ttime':['<',time.time()-3600*24]} )
			
			if len(tt00)>0 :
				if tt00[0][0]!=None:
					last_load=tt00[0][0] #[0][0]	
					
		return last_load
		
		

		
	# @gui.Slot()	
	def output(self,ostr,ttype='set'): #self.output()
		 
		self.wallet_status_update.emit([ttype,ostr   ]) # 'Wallet synced!'
		
		# error: couldn't connect to server: timeout reached (code 0)
# (make sure server is running and you are connecting to the correct RPC port)



		
	@gui.Slot()	
	def run_subprocess(self,CLI_STR,cmd_orig,sleep_s=4 ):
		# print('cmd_orig',cmd_orig)
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
			# print('\ndeamon_start',deamon_start)

		elif type(cmd_orig)!=type([]):
			
			cmdtmp=cmd_orig.split()
			cmd=[cmdii for cmdii in cmdtmp]
			
		tmplst=deamon_start +cmd 
		# print(tmplst)
		
		pp=subprocess.Popen( tmplst ) 
		
		time.sleep(sleep_s)
		
		tsyncing=[]
		
		blocks_passed=[]
		max_n_last_iter=16
		gitmp=''
		
		while pp.poll() is None: #==None:
		
			if cmd_orig=='start':
			
				gitmp=app_fun.run_process(cli_cmd,'getinfo')
				
				if deamon_warning in gitmp:
					self.output(gitmp)
				elif 'error message:' in gitmp:
					# print(gitmp)
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
							self.wallet_synced_signal.emit(True) #init_app.check_if_new_wallet_backup_needed
                            
						break
					elif y['longestchain']>0 and y["blocks"]>0:
						
						timeleft=''
						blocksleft=y["longestchain"]-y["blocks"]
						
						if len(tsyncing)==0 and blocksleft>0: # and y["blocks"]>0
						
							tsyncing.append(time.time())
							blocks_passed.append(y["blocks"])
							
						elif blocksleft>0: # and blocksiniter>0: #y["blocks"]>0 and 
							
							tsyncing.append(time.time())
							blocks_passed.append(y["blocks"])
							# print('blocks and time',blocks_passed,tsyncing)
							tmp_time_arr=tsyncing[-max_n_last_iter:]
							tmp_blocks_arr=blocks_passed[-max_n_last_iter:]
							# print('last N',tmp_time_arr,tmp_blocks_arr)
							
							# take last max N=8 iter for estim
							# take time from aray list# take sum blocks for last N
							secpassed=tmp_time_arr[-1] - tmp_time_arr[0] #time.time()-tsyncing
							blockssynced=tmp_blocks_arr[-1] - tmp_blocks_arr[0]  #y["blocks"]-blocksinit
							
							syncspeed=(blockssynced+1)/secpassed # plus 1 to exclude zero denom
							# blocksleft=y["longestchain"]-y["blocks"]
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
								
						else:
							print('1159 ',y["blocks"],y["longestchain"] )
							
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
				
				self.wallet_status_update.emit(['append',' .']) #self.walletTab.stat_lab.setText(self.walletTab.stat_lab.text()+' .') #.set_textvariable(None,self.statustable.get()+' .')
				time.sleep(1)
				
		if cmd_orig=='start':		
			self.the_wallet=wallet_api.Wallet(self.cli_cmd,self.get_last_load(),self.db)
			# print('connetcing wal api signal 1214')
			self.the_wallet.sending_signal.connect(self.obj_updateWalletDisplay) 
			
			tend=time.time()
			tdiff=int(tend-t0)
			gitmp=app_fun.run_process(cli_cmd,'getinfo')
			y={}
			try:
				y = json.loads(gitmp)
			except:
				traceback.print_exc()
				# pass
				
			if 'error' in gitmp and 'errors' not in y:
				print('ERROR doing getinfo for CLI STR',CLI_STR)
				print('getinfo:',gitmp)
				
				self.output('Unclassified error:\n'+gitmp)
				
			else:
				
				if y["blocks"]==None:
					print('ERROR y',y)
					return
					
				loaded_block=y["blocks"]
				
				# save loading time
				# idb=localdb.DB(self.db)
				table={}
				
				table['deamon_start_logs']=[{'uid':'auto', 'time_sec':tdiff, 'ttime':tend, 'loaded_block':loaded_block }]
				global_db.insert(table,['uid','time_sec','ttime','loaded_block'])
			
			
			self.start_stop_enable.emit(True)
			self.deamon_started_ok=True
			# self.walletTab.bstartstop.setEnabled(True) #self.bstartstop.configure(state='normal')
			
		elif cmd_orig=='stop':
		
			self.started=False
			
			tmpcond =app_fun.check_deamon_running() # additiona lcheck needed for full stop
			while tmpcond[0]:
				self.wallet_status_update.emit(['append','.']) #
				# self.walletTab.stat_lab.setText(self.walletTab.stat_lab.text()+'.') #.set_textvariable(None,self.statustable.get()+' .')
				time.sleep(2)
				tmpcond =app_fun.check_deamon_running()
			
			self.the_wallet=None
			self.start_stop_enable.emit(True)
			# self.walletTab.bstartstop.setEnabled(True) #self.bstartstop.configure(state='normal')
			self.output('Blockchain stopped\nEncrypting wallet...')
			
			self.encrypt_wallet_and_data()
			
			
			
			
			
	# wallet hash vs backup_wallet_hash in init checks ... 
	# create unecessary copies ... 
	# will be switched of in ecrnypted version for pirate 
	# but still usable for other wallets ? potentially 
	# also not encrypting even when found decrypted on going off ... 
	
	# currently this is only informative ?? wallet_hash
	
	## ORIG REASON : CHECK IF DECRYPTION WAS OK
	# changed to have common with 'backup_wallet_hash'
	def check_wallet_hash(self,dat_file,insert_on_exception=False):
		cc=aes.Crypto() # regular algo
		
		last_wallet_hash=global_db.select('jsons', ['json_content'],{'json_name':['=',"'backup_wallet_hash'"]}) # 'backup_wallet_hash' 'wallet_hash'
		
		cur_dat_hash= cc.hash2utf8_1b( cc.read_bin_file( dat_file),1)
		
		def insertNewHash(tmparr): # print('Inserting hash',cur_dat_hash,'self.db',self.db)
			# tmparr.append(cur_dat_hash)
			table={}
			table['jsons']=[{'json_name':"backup_wallet_hash", 'json_content':json.dumps(tmparr), 'last_update_date_time': app_fun.now_to_str(False)}]
			 
			global_db.upsert(table,['json_name','json_content','last_update_date_time'],{'json_name':['=',"'backup_wallet_hash'"]})
			 
		# print('1518 cur_dat_hash,last_wallet_hash_arr\n',json.dumps(cur_dat_hash),last_wallet_hash)
		if len(last_wallet_hash)>0:
			last_wallet_hash_arr=json.loads(last_wallet_hash[0][0])
			# if cur_dat_hash in last_wallet_hash_arr: #==last_wallet_hash[0][0]:
				# print('Decrypted wallet hash exists in history - ok.')
			# else:
			if cur_dat_hash not in last_wallet_hash_arr:
				if insert_on_exception:
					# print('New wallet hash detected - inserting')
					last_wallet_hash_arr.append(cur_dat_hash)
					insertNewHash(last_wallet_hash_arr)
				else:
					print('Warning - wallet decryption might have been wrong - existing wallet hash does not exist in history ... ! ')
					# print(' 1530 cur_dat_hash,last_wallet_hash_arr',cur_dat_hash,last_wallet_hash_arr)
			# else:
				# print('hash matched',last_wallet_hash_arr.index(cur_dat_hash),'of',len(last_wallet_hash_arr)-1)
		else: # no last hash - save new one 
			# print('No last wallet hash - saving the new one!',cur_dat_hash)
			insertNewHash([cur_dat_hash]) # before empty

		
	def decrypt_wallet(self):
		
		# idb=localdb.DB('init.db')
		ppath=global_db_init.select('init_settings',['datadir'] )
		
		dat_file=os.path.join(ppath[0][0],self.wallet_display_set.data_files['wallet']+'.dat')
		encr_file=os.path.join(ppath[0][0],self.wallet_display_set.data_files['wallet']+'.encr')
		
		if os.path.exists(dat_file): #os.path.join(ppath[0][0],self.wallet_display_set.data_files['wallet']+'.dat') ):
			# print('wallet decrypted exist?')
			self.output('\nwallet decrypted exist?:\n'+dat_file,'append')
			return dat_file+' exists'
			
		elif os.path.exists(encr_file): #os.path.join(ppath[0][0],self.wallet_display_set.data_files['wallet']+'.encr') ):
			cc=aes.Crypto()
			 
			rv=cc.aes_decrypt_file( encr_file, dat_file , self.wallet_display_set.password)
			
			t_to_wait=int(os.path.getsize(dat_file)/1e7 )
			# print('Waiting '+str(t_to_wait)+' seconds to ensure wallet is ready ... ' )
			self.output('\nWaiting '+str(t_to_wait)+' seconds to ensure wallet is ready\n','append')
			self.counterPrint(t_to_wait)
			
			self.check_wallet_hash( dat_file )
			 
			if rv!='' and os.path.exists(rv):
				app_fun.secure_delete(encr_file) #os.path.join(ppath[0][0],self.wallet_display_set.data_files['wallet']+'.encr'))
				
			self.output('Wallet decrypted and ready' )
			 
		return 'Decrypted'
	

	def counterPrint(self,t_to_wait):
		while t_to_wait>-1:
			# print('... time left ',t_to_wait)
			self.output(' ... '+str(t_to_wait),'append')
			t_to_wait-=1
			time.sleep( 1) # 1+ t_to_wait ) # 1MB = 1s waiting
			
			
	def encrypt_wallet_and_data(self,ppath=''):
	
		if self.wallet_display_set.password==None:
			return
			
		# idb=localdb.DB('init.db')
		# print('encrypt_wallet_and_data deamon.global_db_init,deamon.global_db', global_db_init, global_db)
		# print(global_db_init.select('init_settings',[ ] ) )
		if ppath=='': # arg passed on exception signout in init check 
			ppath=global_db_init.select('init_settings',['datadir'] )
			ppath=ppath[0][0]
		else:
			print('! Emergency wallet encrypt - please wait') # for some reason does not print on the gui 
		# print(ppath) # can be empty on error - not saved init ... 
		# any option to backup init ?
		
		cc=aes.Crypto()
		path2encr=os.path.join(ppath ,self.wallet_display_set.data_files['wallet']+'.dat')
		t_to_wait=int(os.path.getsize(path2encr)/1e7 )
		# print('Waiting '+str(t_to_wait)+' seconds \nto ensure wallet \nis not working ... ' )
		self.output('\nWaiting '+str(t_to_wait)+' seconds to ensure \nwallet is not working\n','append')
		# print('encr check_wallet_hash')
		self.check_wallet_hash( path2encr, True )
		self.counterPrint(t_to_wait)
		# return
		
		path_end=os.path.join(ppath ,self.wallet_display_set.data_files['wallet']+'.encr')
		# print('Encrypting ... ' )
		self.output('\nEncrypting ... ','append')
		rv=cc.aes_encrypt_file( path2encr, path_end , self.wallet_display_set.password)
		
		self.output('done','append')
		
		encrypted_size=os.path.getsize(path_end)
		# print('encrypted_size error ',encrypted_size)
		if encrypted_size<10000:
			# print('encrypted_size error ',encrypted_size)
			self.output('\nencrypted_size error '+str(encrypted_size),'append')
		# time.sleep(1)
		
		if rv  and os.path.exists(path_end) and encrypted_size>10000: #rv!=''
			datf=os.path.join(ppath ,self.wallet_display_set.data_files['wallet']+'.dat')
			# print('Deleting .dat after encryption:',datf)
			self.output('\nDeleting .dat after encryption:\n'+datf,'append')
			app_fun.secure_delete(datf)
			
		self.output('Blockchain stopped\nWallet encrypted\nand secured (.dat deleted)')	
	
