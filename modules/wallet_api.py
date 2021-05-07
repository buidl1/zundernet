
import os
import time
import sys
import datetime

# import subprocess
import json
# import modules.deamon as deamon
# import re
import modules.localdb as localdb
import modules.app_fun as app_fun
# import modules.aes as aes
# save in db last block nr, last time loaded, last loading time

class Wallet: # should store last values in DB for faster preview - on preview wallt commands frozen/not active


	def prep_msgs_inout(self,txid_utf8,mm,ttype,dt,tx_status='sent' ,in_sign_uid=-1,addr_to='' ):

		tmpmsg,sign1,sign1_n,sign2,sign2_n =app_fun.split_memo(mm[0],False)
		
		# if tmpmsg=='':
			# return {}
		 
			
		tmpaddr=mm[2] # for incoming save full sign info
		if tmpaddr=='':
			tmpdict={}
			if sign2!='none':
				tmpdict={'sign1':sign1,'sign1_n':sign1_n,'sign2':sign2,'sign2_n':sign2_n}
			elif sign1!='none':
				tmpdict={'sign1':sign1,'sign1_n':sign1_n}
				
			tmpaddr=json.dumps(tmpdict) #.replace(',',';')
			 
		table={}
		table['msgs_inout']=[{'proc_json':'False'
							,'type':ttype
							,'addr_ext':tmpaddr #tostr[mmii]["address"]
							,'txid':txid_utf8
							,'tx_status':tx_status
							,'date_time':dt
							,'msg':tmpmsg
							,'uid':'auto'
							,'in_sign_uid':in_sign_uid
							,'addr_to':addr_to }]
		return table #table['msgs_inout'][0]['msg']
	


	def __init__(self,CLI_STR,last_load,db):
		self.db=db
		self.first_block=None
		self.min_conf=1
		self.cli_cmd=CLI_STR

		self.last_block=0
		self.addr_amount_dict={}
		self.amounts=[]
		self.amounts_conf=[]
		self.amounts_unc=[]

		self.addr_list=[]
		self.alias_map={}
		self.total_balance=0
		self.total_conf=0
		self.total_unconf=0
		self.wl=[]
		
		
		self.unconfirmed={}
		self.confirmed={}
		self.all_unspent={}
		self.utxids={}
		
		idb=localdb.DB(self.db)	
		 
		disp_dict=idb.select('jsons',['json_content','last_update_date_time'],{'json_name':['=',"'display_wallet'"]})
		if len(disp_dict)>0:
			disp_dict=json.loads(disp_dict[0][0])
		 
			if "blocks" in disp_dict: self.last_block=disp_dict["blocks"]
			if "addr_amount_dict" in disp_dict: self.addr_amount_dict=disp_dict['addr_amount_dict']
			if "amounts" in disp_dict: self.amounts=disp_dict['amounts']
			if "amounts_conf" in disp_dict: self.amounts_conf=disp_dict['amounts_conf']
			if "amounts_unc" in disp_dict: self.amounts_unc=disp_dict['amounts_unc']	
			if "unconfirmed" in disp_dict: self.unconfirmed=disp_dict['unconfirmed']
			if "confirmed" in disp_dict: self.confirmed=disp_dict['confirmed']
			if "all_unspent" in disp_dict: 
				self.all_unspent=disp_dict['all_unspent']	
				for aa,rr in self.all_unspent.items():
					for utxo,vv in rr.items():
						if utxo not in self.utxids:
							self.utxids[utxo]=vv['amount']
				
				
			if "addr_list" in disp_dict: self.addr_list=disp_dict['addr_list']
			
			if "external_addr" in disp_dict: self.external_addr=disp_dict['external_addr']

			# if "historical" in disp_dict: self.historical_txs=disp_dict['historical']
			if "aliasmap" in disp_dict: self.alias_map=disp_dict['aliasmap']	
			if "top" in disp_dict: 
				self.total_balance=disp_dict['top']['Total']
				self.total_conf=disp_dict['top']['Confirmed']
				self.total_unconf=disp_dict['top']['Pending']
			if "wl" in disp_dict: self.wl=disp_dict['wl']
		
		
		tx_in_sql=idb.select('tx_history',['Category','Type','status','txid','block','timestamp','date_time','from_str','to_str','amount','uid'],{'Type':['=',"'in'"]})
		
		self.historical_txs={}
		self.history_update_counter=0
		
		for ti in tx_in_sql:
			aa=ti[8]
			txid=ti[3]
			outindex=int(ti[0].replace('outindex_',''))
			if aa not in self.historical_txs:
				self.historical_txs[aa]={}
			
			if txid not in self.historical_txs[aa]:
				self.historical_txs[aa][txid]={}
				
				
			if outindex not in self.historical_txs[aa][txid]:
				self.historical_txs[aa][txid][outindex]	= { "amount":ti[9]} #,"conf": self.last_block-ti[4],"memo":ti[7]  }
				
		
		
		
		
		
		
		
		
		
	
	def refresh_wallet(self): # once a 1-2 minutes?
		
		# print(self.getinfo())
		tmpblocks=self.getinfo()["blocks"]
		self.last_block=tmpblocks
		# print(141)
		self.update_all_addr()
		# print(143)
		self.address_aliases()
		# print(145)
		freshutxo=self.update_unspent() #init=False,maxconf=str(blocks_div) )
		# print(147)
		tmptotal_balance=self.total_balance
		self.wallet_summary()
		# print(150)
		total_change=round(self.total_balance-tmptotal_balance,8)
		# if total_change!=0:
			# print(168,'total change diff 0 wal api ',total_change)
			# total_change=1
		# print('b4 return')
		
		return self.update_historical_txs(freshutxo)+total_change
	
	
	
	# run only once after startup to fill gaps if any
	# later base on list unspent ...
	
	#freshutxo [{"address","txid","amount"},..]
	def update_historical_txs(self,freshutxo): # max count: 80*tps * 60 =4800 < 5000
		idb=localdb.DB(self.db)	
		
		iterat_arr=freshutxo
		full_check=False
		
		
		if self.history_update_counter%60==0:
			iterat_arr=self.addr_list + self.external_addr # oncece a 60 times check full 
			full_check=True
			
		self.history_update_counter+=1
		
		
		table_history_notif={}
		
		for aa in iterat_arr:
			# print('aa',aa)
			# try:
			if True:
				tt=aa
				if full_check:
					
					tmp1=app_fun.run_process(self.cli_cmd,['z_listreceivedbyaddress',aa,str(self.min_conf) ])
					# print(186,tmp1)
					try:
						tt=json.loads(tmp1)
					except:
						print('Exception wal api 85 ',tmp1)
						break
				else:
					aa=tt['address']
					
					tt=[tt]
					
				# print('tt',tt)
				
				if aa not in self.historical_txs:
					self.historical_txs[aa]={}
			
				for tx in tt: 
						
					# print(211)
					if "txid" not in tx:
						continue
						
					# print(215)
					if tx["txid"] not in self.historical_txs[aa]:  # if this ever change - may be needed to update some records in case of reorg ?
						self.historical_txs[aa][tx["txid"]]={}
						
					# print(219)
					if 'change' in tx:
						if tx['change']:
							continue
						
					# print(223)
					outindex=0
					if 'outindex' in tx:
						outindex=tx['outindex']
					elif 'jsoutindex' in tx:
						outindex=tx['jsoutindex']
					
					if outindex not in self.historical_txs[aa][tx["txid"]]: # 'Category'= "'outindex_"+str(outindex)+"'"
					
					
						tmpmemo=tx["memo"]
						try:
							tmpmemo=bytes.fromhex(tmpmemo).decode('utf-8') #int(tx["memo"], 16)
						except:
							# print(226)
						
							pass
						tmpmemo=self.clear_memo(tmpmemo)
						
						self.historical_txs[aa][tx["txid"]][outindex]	= { "amount":tx["amount"]} #,"conf":tx["confirmations"],"memo":tmpmemo  }
						
						tmpwhere={'to_str':['=',"'"+aa+"'"],'Type':['=',"'in'"],'txid':['=',"'"+tx["txid"]+"'"],'Category':['=',"'outindex_"+str(outindex)+"'"] }
						
						
						
						checkexist=idb.select('tx_history', ["Type"],tmpwhere) #
						# print('checkexist',checkexist)
						if len(checkexist)==0:
							table={}
							
							y=self.getinfo()
							# print('getinfo',y)
															
							dt,ts=app_fun.now_to_str(False,ret_timestamp=True)
							# print('dt ts',dt,ts)
							
							# print('tx',tx)
							# insert incoming msgs:
							
							# estimate dt - why so big error?
							# print('blocks, conf',y["blocks"],tx["confirmations"])
							dt=localdb.blocks_to_datetime(y["blocks"]-tx["confirmations"]) # time it was sent 
							# print('dt?',dt)
							
							##### prepare for inserting msg
							if aa not in table_history_notif:
								# merged_msg[aa]={}
								table_history_notif[aa]={}
							
							if tx["txid"] not in table_history_notif[aa]:
								# merged_msg[aa][tx["txid"]]={}
								table_history_notif[aa][tx["txid"]]={}
							# print(268)
							if outindex not in table_history_notif[aa][tx["txid"]]:
								# merged_msg[aa][tx["txid"]][outindex]={'dt':dt, 'tmpmemo':tmpmemo } #table
								# print('times\ndt',dt,'timestamp',ts-60*tx["confirmations"]   ,'datetime',app_fun.date2str(datetime.datetime.now()-datetime.timedelta(seconds=60*tx["confirmations"]) ))
								q={'dt':dt
									, 'tmpmemo':tmpmemo
									,'block':y["blocks"]-tx["confirmations"]
									,'timestamp':ts-60*tx["confirmations"]   
									, 'date_time':app_fun.date2str(datetime.datetime.now()-datetime.timedelta(seconds=60*tx["confirmations"]) )
									, 'amount':tx["amount"]
									, 'outindex':'_'+str(outindex)
									}
								table_history_notif[aa][tx["txid"]][outindex]=q
							
			# except:
				# break
		# print('after for')	
		
		if self.first_block==None:
			idbinit=localdb.DB('init.db')
			first_block=idbinit.select_min_val('block_time_logs','block')
			self.first_block=first_block[0][0]
			
		for aa,txids in table_history_notif.items():
			# print('aa2',aa)
			for txid, iis in txids.items():
				
				kk_ordered=sorted(iis.keys())
				# print('320 wal api sorted ',kk_ordered)
				init_table=iis[kk_ordered[0]]
				
				# print('init_table',init_table)
				# init_table=txid[iis[0]]
				if len(kk_ordered)>1:
					for ii in kk_ordered[1:]:
						init_table['tmpmemo']+=iis[ii]['tmpmemo'] #merge memos if multiple outindex and multiple memos 
						init_table['outindex']+=iis[ii]['outindex']
						
				table_msg={} # insert only those after first block
				from_str=''
				
				
				# print('init_table["block"]>=self.first_block:',init_table["block"],self.first_block)
				
				if init_table["block"]>=self.first_block:
					
					table_msg=self.prep_msgs_inout(txid,[init_table['tmpmemo'],0,''],'in',init_table['dt'],tx_status='received', in_sign_uid=-2,addr_to=aa ) # -2 to be detected
					
					from_str=table_msg['msgs_inout'][0]['msg']
					# print(321,table_msg,from_str)
					tmpmsg=from_str
					# recognize if channel 
					
					is_channel=idb.select('channels',['channel_name'],{'address':['=',"'"+aa+"'"]} )	# aaaddr_to
					# print('is_channel',is_channel)
					if len(is_channel)>0:
						is_channel=True
					else:
						is_channel=False # try recognize incoming channel
						try:
							channel_json=json.loads(tmpmsg)
							# print(channel_json)
							
							for tt in ['channel_name' , 'channel_owner', 'channel_intro']:
								if tt in tmpmsg:
									is_channel=True # also below add to channels !
									break
							# print('is_channel2',is_channel)	
							if is_channel: #'channel_name' in tmpmsg and 'channel_owner' in tmpmsg and 'channel_intro' in tmpmsg:
								
								# get view key from table :
								vk_list=idb.select('view_keys', ["vk"],{'address':['=',"'"+aa+"'"]})
								vkey=''
								if len(vk_list)>0:
									vkey=vk_list[0][0]
								
								table={'channels':[{'address':aa, 'vk':vkey, 'creator':channel_json['channel_owner'], 'channel_name':channel_json['channel_name'], 'status':'active', 'own':'False'}]}	
			
								idb.insert(table,['address' , 'vk' , 'creator' , 'channel_name' , 'status' , 'own' ])
								
						except:
							# print("Not proper json",tmpmsg)
							pass
					
					table_msg['msgs_inout'][0]['is_channel']=str(is_channel)
					# print(table_msg)
					# if is channel - add sender to anon addr book to mark same name each time : self name + init hash 
						
					idb.insert(table_msg,['proc_json','type','addr_ext','txid','tx_status','date_time', 'msg','uid','in_sign_uid','addr_to','is_channel'])
				
				
				
				# print(362,from_str)
				# print(365,init_table) # dt vs datetime ??? 
				table={}
				table['tx_history']=[{'Category':"outindex"+init_table['outindex'] # "outindex" not to miss some amounts!
										, 'Type':'in'
										, 'status':'received'
										,'txid':txid
										,'block':init_table["block"] 
										, 'timestamp':init_table["timestamp"]
										, 'date_time':init_table["date_time"]
										,'from_str':from_str
										,'to_str':aa
										,'amount':init_table["amount"]
										, 'uid':'auto'
									}]
				idb.insert(table,['Category','Type','status','txid','block','timestamp','date_time','from_str','to_str','amount','uid'])
				
				if init_table["block"]>=self.first_block:
					table={}
					toalias=' to address '+aa
					if aa in self.alias_map:
						toalias=' to alias '+self.alias_map[aa]
						
					tmpjson='Amount: '+str(init_table["amount"])+toalias
					tmpopname='received'
					
					if len(from_str)>13 and from_str[:14] =='PaymentRequest':
					# if table_msg['msgs_inout'][0]['msg'][:14] =='PaymentRequest':
						# tmpjson+=';'+g['msgs_inout'][0]['msg']
						tmpjson+=';'+from_str
						tmpopname='payment request'
					
					table['notifications']=[{'opname':tmpopname,'datetime':init_table['dt'],'status':'Confirmed','details':txid,'closed':'False','orig_json':tmpjson
											,'uid':'auto'}]
					# print(398,table)	
					idb.insert(table,['opname','datetime','status','details', 'closed','orig_json' ,'uid'])
				
		return len(table_history_notif)		
				
				
	
	def str_wallet_summary(self):

		wl_str=[]
		wl_str.append("\nWallet Total {:.8f}".format(self.total_balance) )
		if self.total_unconf>0:
			wl_str.append(" - confirmed {:.8f}".format(self.total_conf) )
			wl_str.append(" - unconfirmed {:.8f}".format(self.total_unconf))
			
		wl_str.append("\n Alias | Amount | Full Address\n")
		for i in sorted(enumerate(self.amounts), key=lambda x:x[1], reverse=True):
			ii=i[0]
			
			tmp_total=self.wl[ii]['confirmed']+self.wl[ii]['unconfirmed']
			
			
			wl_str.append(" "+self.alias_map[self.wl[ii]['addr']]+" | {:.8f}".format(tmp_total)+" | "+self.wl[ii]['addr'] )
			if self.wl[ii]['unconfirmed']>0:
				wl_str.append("   - confirmed {:.8f}".format(self.wl[ii]['confirmed']) )
				wl_str.append("   - unconfirmed {:.8f}".format(self.wl[ii]['unconfirmed']) )
	
		return wl_str
		
		
	def display_wallet(self,sorting=None,rounding=1): 	
	
		sorting_lol=[]
		for ii,aa in enumerate(self.amounts):
			tmplen=0
			if self.wl[ii]['addr'] in self.historical_txs:
				tmplen=len(self.historical_txs[self.wl[ii]['addr']] )
			sorting_lol.append([ii, aa, int(self.wl[ii]['#conf']+self.wl[ii]['#unconf']), tmplen ])
			
		disp_dict={}
		disp_dict['top']={'Total': self.total_balance , 'Confirmed': self.total_conf , 'Pending': self.total_unconf }
		disp_dict['lol']=sorting_lol
		disp_dict['wl']=self.wl
		# disp_dict['historical']=self.historical_txs
		disp_dict['aliasmap']=self.alias_map
		disp_dict["blocks"]=self.last_block
		
		disp_dict['addr_amount_dict']=self.addr_amount_dict
		disp_dict['amounts']=self.amounts
		disp_dict['amounts_conf']=self.amounts_conf
		disp_dict['amounts_unc']=self.amounts_unc
		disp_dict['unconfirmed']=self.unconfirmed
		disp_dict['confirmed']=self.confirmed
		disp_dict['all_unspent']=self.all_unspent	
		disp_dict['addr_list']=self.addr_list
		disp_dict['external_addr']=self.external_addr
		
		
		return disp_dict
		
		
	
		
	def wallet_summary(self):
				
		self.addr_amount_dict={}
		self.total_balance=float(0)
		self.total_conf=float(0)
		self.total_unconf=float(0)
		self.wl=[]
		self.amounts=[]
		self.amounts_conf=[]
		self.amounts_unc=[]
		
		for aa in self.addr_list:
		
			amount_init=0 
			
			cc_conf=0
			if aa in self.confirmed:
				for vv in self.confirmed[aa]:
					amount_init+=self.confirmed[aa][vv]['amount'] 
					cc_conf+=1
					
			am_unc=0
			cc_unc=0
			if aa in self.unconfirmed:
				for vv in self.unconfirmed[aa]:
					am_unc+=self.unconfirmed[aa][vv]['amount'] 
					cc_unc+=1
			
			self.addr_amount_dict[aa]={'confirmed':amount_init,'unconfirmed':am_unc,'#conf':cc_conf,'#unconf':cc_unc}
			self.amounts_unc.append(am_unc)
					
			if amount_init>0:
				self.wl.append({'addr':aa,'confirmed': amount_init, 'unconfirmed': am_unc,'#conf':cc_conf,'#unconf':cc_unc })
				self.amounts.append(amount_init+am_unc)	
				self.amounts_conf.append(amount_init)	
				self.total_balance+=amount_init
				self.total_conf+=amount_init
			else:
				self.wl.append({'addr':aa,'confirmed':0, 'unconfirmed':am_unc,'#conf':cc_conf,'#unconf':cc_unc})
				self.amounts.append(0+am_unc)	
				self.amounts_conf.append(0)
				
			self.total_balance+=am_unc
			self.total_unconf+=am_unc
			
			
			
			
			
	def clear_memo(self,initmem):
		tmpmemo=initmem.replace('\\xf6','').replace('\\x00','').replace("b''",'') 
		
		ii=len(tmpmemo)-1
		lastii=ii+1
		while ii>-1:
		
			if tmpmemo[ii]==';':
				
				lastii=ii
				break
		
			elif ord(tmpmemo[ii])==0 or tmpmemo[ii]=='0':
				# print('lastii',ii)
				lastii=ii
				ii=ii-1
			else:
				break
		
		if lastii==0:
			return ''
			
		return tmpmemo[:lastii].strip()
		
		
		
		
		
	def update_unspent(self ): 
	
		cmdloc=['z_listunspent','0','999999999','true']
		
		tmp1=app_fun.run_process(self.cli_cmd,cmdloc)
		
		js1=json.loads(tmp1)
		
		self.unconfirmed={}
		self.confirmed={}
		self.all_unspent={}
		self.utxids={}
		
		fresh_tx=[]
		
		for jj in js1:
			# try:		
			if True:			
				tmpadr=jj["address"]
				tmptxid=jj["txid"]
				tmpam=jj["amount"]
				
				if tmptxid not in self.utxids: # add also in unspent
					self.utxids[tmptxid]=tmpam
				
				
				if 'outindex' in jj:
					tmptxid+=' outindex '+str(jj["outindex"])
				elif 'jsoutindex' in jj:
					tmptxid+=' outindex '+str(jj["jsoutindex"])
															
				tmpconf=jj["confirmations"]
				if tmpconf<30:
					fresh_tx.append(jj)
				
				tmpspendable=jj["spendable"] # false for watch only
				
				if tmpadr not in self.all_unspent:
					self.all_unspent[tmpadr]={}
					 
				if tmptxid not in self.all_unspent[tmpadr]:
					
					self.all_unspent[tmpadr][tmptxid]={'amount':tmpam,'conf':tmpconf,'own':tmpspendable} #,'memo':tmpmemo}
					
				if tmpconf==0:
					if tmpadr not in self.unconfirmed:
						self.unconfirmed[tmpadr]={}
					if tmptxid not in self.unconfirmed:
						self.unconfirmed[tmpadr][tmptxid]={'amount':tmpam,'conf':tmpconf,'own':tmpspendable}
				else:
					if tmpadr not in self.confirmed:
						self.confirmed[tmpadr]={}
					if tmptxid not in self.confirmed:
						self.confirmed[tmpadr][tmptxid]={'amount':tmpam,'conf':tmpconf,'own':tmpspendable}
			
		return fresh_tx #[{"address","txid","amount"},..]
	
	
	
	
	def alias_to_addr(self,alias):
			
		for oo in self.alias_map:
			if self.alias_map[oo]==alias:
				print('...alias['+alias+'] changed to addr ['+oo+']')
				return oo
					
		return alias
			
		

	
	def address_aliases(self ): # address_aliases(get_wallet(True))
		# self.alias_map={}
		sorted_addr=sorted(self.addr_list) #self.addr_list
		for aa in sorted_addr:
		
			if aa not in self.alias_map: # new addr:
			
				tmpa=aa[3:6].upper() #+aa[-3:].upper()
				
				iter=1
				while tmpa in self.alias_map.values():
					tmpa=aa[3:(6+iter)].upper()
					
					iter+=1
				
				self.alias_map[aa]=tmpa
			
		
	def z_viewtransaction(self,txid):
		try:
		# if True:
			tmp=app_fun.run_process(self.cli_cmd,'z_viewtransaction '+txid)
			if 'error' in tmp.lower():
				return 'not valid txid'
			# print(396,tmp)
			tmpj=json.loads(tmp)
			# print(397,tmpj)
					
			return tmp
		except:
			print('wallet api not valid txid')
			return 'not valid txid'
		
			

	def getinfo(self,toprint=False):
		try:
			gi=app_fun.run_process(self.cli_cmd,"getinfo")
			gi=json.loads(gi)
			if toprint:
				print(566,gi)
			
			
			kv_tmp=["name","errors","synced","notarized","blocks","longestchain","tiptime","connections"]
			gtmpstr={}
			for dd in kv_tmp:
				if dd in gi:
					gtmpstr[dd]=gi[dd]
			
			return gtmpstr
			# { "name":gi["name"],"errors":gi["errors"],"KMDversion":gi["KMDversion"],"synced":gi["synced"],"notarized":gi["notarized"],"blocks":gi["blocks"],"longestchain":gi["longestchain"],"tiptime":gi["tiptime"],"connections":gi["connections"]}
		except:
			print('wallet api getinfo')
			return { "name":'exception',"errors":'',"KMDversion":'',"synced":'',"notarized":'',"blocks":'',"longestchain":'',"tiptime":'',"connections":''}

		
		

	def update_all_addr(self):
	
		self.addr_list=[]
		self.external_addr=[]
					 
		try:
			r2=app_fun.run_process(self.cli_cmd,"z_listaddresses")
			
			with_external=app_fun.run_process(self.cli_cmd,"z_listaddresses true")
			
			a3=json.loads(with_external)
			
			a2=json.loads(r2)
			# print(403,r2,a2)

			for aa in a2:
				self.addr_list.append(aa)
			
			for ee in a3:
				if ee not in self.addr_list:
					self.external_addr.append(ee)
					
			# print('\n\n\nwith_external',self.external_addr)
				
		except:
			print('wallet api update_all_addr')
			return
		
		
		
	def new_zaddr(self):

		try:
			tmpnewaddr=app_fun.run_process(self.cli_cmd,"z_getnewaddress")
			self.refresh_wallet()
			return str(tmpnewaddr) 
		except:
			print('wallet api no addr exception')
			return 'no addr exception'
		
		
	def validate_zaddr(self,zaddr):
		try:
			tmp=app_fun.run_process(self.cli_cmd,'z_validateaddress '+zaddr)
			tmpj=json.loads(tmp)
					
			return tmpj['isvalid']
		except:
			print('wallet api not valid exception')
			return 'not valid exception'
		
		
	def exp_view_key(self,zaddr): # 'False' 'cannot export'
		try:
			# print('zaddr',zaddr)
			return str(app_fun.run_process(self.cli_cmd,"z_exportviewingkey "+zaddr)) 
		except:
			print('wallet api cannot export')
			return 'cannot export'
		
		
	def imp_view_key(self,zaddr,vkey,rescan="whenkeyisnew",startHeight=1375757 ): #996000

		# print('Importing viewing key may take a while (rescan) from height '+str(startHeight) ) 
		# print(zaddr,vkey)
		tmpnewaddr=''
		
		tmpnewaddr=app_fun.run_process(self.cli_cmd,["z_importviewingkey",vkey,rescan,str(startHeight),zaddr]) #,zaddr
		
		if 'error' in tmpnewaddr:
			return {'error':tmpnewaddr}
		
		# print(json.loads(tmpnewaddr))
		# deamon.run_subprocess(self.cli_cmd,["z_importviewingkey",vkey,rescan,str(startHeight),zaddr], 64 ) 
		self.refresh_wallet()
		# print('wallet refreshed')
		if tmpnewaddr.strip()=='': # current api vs future api	
			return {'address':zaddr, 'type':'sapling'} #'type' in tmpresult and tmpresult['type']=='sapling':
		
		return json.loads(tmpnewaddr) #future api	
		# print('Done')	
		
		
	def export_wallet(self):
		retv={}
		for aa in self.addr_list:
			# print('fetching priv key for',aa)
			retv[aa]=self.exp_prv_key(aa)
			# print('   ',retv[aa])
			
			
		return retv
			
	def merge(self,fr,tostr,limit):
		args=['z_mergetoaddress',fr,tostr ,'0.0001','1',str(limit)]
		# print(647,args,flush=True)
		return app_fun.run_process(self.cli_cmd,args)
	
	def send(self,fr,tostr):
		# print(tostr)
		args=['z_sendmany',fr,tostr]
		return app_fun.run_process(self.cli_cmd,args)

	def exp_prv_key(self,zaddr):
		try:
			return str(app_fun.run_process(self.cli_cmd,"z_exportkey "+zaddr)) 
		except:
			print('wallet api cannot export exp_prv_key')
			return 'cannot export'

		
	def imp_prv_key(self,zkey,rescan="whenkeyisnew",startHeight=996000):

		# print('Importing private key may take a while (rescan) from height '+str(startHeight) )
		
		tmpnewaddr=app_fun.run_process(self.cli_cmd,["z_importkey",zkey,rescan,str(startHeight) ])
		# deamon.run_subprocess(self.cli_cmd,"z_importkey "+zkey+rescan+str(startHeight), 64 ) 
		self.refresh_wallet()
		return json.loads(tmpnewaddr) 
		# print('Done')


