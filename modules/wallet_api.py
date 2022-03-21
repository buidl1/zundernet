
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

	# in outgoing either addr to or addr ext should be own...
	# now 2 times the same is eddr to ...
	
	def prep_msgs_inout(self,txid_utf8,mm,ttype,dt,tx_status='sent' ,in_sign_uid=-1,addr_to='' ):
		# print('b4 split',mm[0])
		tmpmsg,sign1,sign1_n,sign2,sign2_n =app_fun.split_memo(mm[0],False)
			
		tmpaddr=mm[2] # for incoming save full sign info
		if tmpaddr=='':
			tmpdict={}
			if sign2!='none':
				tmpdict={'sign1':sign1,'sign1_n':sign1_n,'sign2':sign2,'sign2_n':sign2_n}
			elif sign1!='none':
				tmpdict={'sign1':sign1,'sign1_n':sign1_n}
				
			# print('tmpdict',tmpdict)
			tmpaddr=json.dumps(tmpdict) #.replace(',',';')
			# print('tmpaddr',tmpaddr)
			 
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
		self.last_load=last_load # prev session load 
		# self.first_block=None
		self.min_conf=1
		self.cli_cmd=CLI_STR
		self.addr_for_full_recalc=[]
		self.any_change=[] # to detect when addr added and so on 
		self.to_refresh=[]

		self.last_block=last_load # last load in session initialized with prev session 
		self.last_analized_block=0
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
		
		
		tx_in_sql=idb.select('tx_history',['Category','Type','status','txid','block','timestamp','date_time','from_str','to_str','amount','uid'],{'Type':[' like ',"'in%'"]})
		
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
				
		# print('init self.historical_txs',self.historical_txs)
				
		# depends on self.historical_txs 
		
		
	def refresh_wallet(self): # once a 1-2 minutes?
		
		if self.history_update_counter==0:
			self.update_all_addr() # disp_dict['addr_list']=self.addr_list # disp_dict['external_addr']=self.external_addr	
			self.address_aliases() # self.alias_map
			
			# updates:
		# disp_dict['unconfirmed']=self.unconfirmed
		# disp_dict['confirmed']=self.confirmed
		# disp_dict['all_unspent']=self.all_unspent	
		freshutxo=self.update_unspent() #init=False,maxconf=str(blocks_div) )
		
		
		
		# updates: self.wl  
		# disp_dict['amounts']=self.amounts
		# disp_dict['amounts_conf']=self.amounts_conf
		# disp_dict['amounts_unc']=self.amounts_unc
		# self.addr_amount_dict 
		# self.total_balance 
		# self.total_conf 
		# self.total_unconf 
		self.wallet_summary() # updating self.total_balance
		tmptotal_balance=self.total_balance
		
		total_change=round(self.total_balance-tmptotal_balance,8)
		
		other_chages=len(self.any_change)
		self.any_change=[]
		# print('wallet refresh almost done')
		
		return self.update_historical_txs( )+total_change+other_chages
		# return self.update_historical_txs(freshutxo)+total_change
	
	
	
	# TODO:
	# init run full run
	# later use zs_listreceivedbyaddress "addr"
	# z_listreceivedbyaddress “address” for addr view keys return all - only option ! 
	# Result:
# {
  # "txid": xxxxx,           (string) the transaction id
  # "amount": xxxxx,         (numeric) the amount of value in the note
  # "memo": xxxxx,           (string) hexadecimal string representation of memo field
  # "confirmations" : n,     (numeric) the number of confirmations
  # "jsindex" (sprout) : n,     (numeric) the joinsplit index
  # "jsoutindex" (sprout) : n,     (numeric) the output index of the joinsplit
  # "outindex" (sapling) : n,     (numeric) the output index
  # "change": true|false,    (boolean) true if the address that received the note is also one of the sending addresses
# }
	def get_all_txs(self,addr): # special case no other option for view key to get tx:
	# WARNING - ensure only viekey addr gets here!
		tt=[]
		try:
			# BUG in piraed? not returning change status for view keys ?
			tmp1=app_fun.run_process(self.cli_cmd,['z_listreceivedbyaddress',addr,'0' ])
			tt=json.loads(tmp1)
			# print('z_listreceivedbyaddress for '+addr+'\n',tt)
			
		except:
			print('Exception get_all_txs addr ',addr)
		
		return tt
	
	
# Result:
   # "txid":  "transactionid",           (string)  The transaction id.
   # "coinbase": "coinbase",             (string)  Coinbase transaction, true or false
   # "category": "category",             (string)  orphan (coinbase), immature (coinbase), generate (coinbase), regular
   # "blockhash": "hashvalue",           (string)  The block hash containing the transaction
   # "blockindex": n,                    (numeric) The block index containing the transaction
   # "blocktime": n,                     (numeric) The block time in seconds of the block containing the transaction, 0 for unconfirmed transactions
   # "rawconfirmations": n,              (numeric) The number of onchain confirmations for the transaction
   #>>>> "confirmations": n,                 (numeric) The number of dpow confirmations for the transaction
   # "time": xxx,                        (numeric) The transaction time in seconds of the transaction
   # "expiryHeight": n,                  (numeric) The expiry height of the transaction
   # "size": xxx,                        (numeric) The transaction size
   #>>>> "fee": n,                           (numeric) Transaction fee in arrrtoshis
   # "recieved": {                     A list of receives from the transaction
      # "type": "address type",          (string)  transparent, sprout, sapling
      #>>>> "output": n,                     (numeric) vout, shieledoutput or jsindex
      # "outIndex": n,                   (numeric) Joinsplit Output index (sprout address type only)
      # "outgoing": true or false,       (bool)    funds leaving the wallet
      # "address": "address",            (string)  Pirate address
      # "scriptPubKey": "script",        (string)  Script for the Pirate transparent address (transparent address type only)
      #>>> "value": x.xxxx,                 (numeric) Value of output being spent ARRR
      # "valueZat": xxxxx,               (numeric) Value of output being spent in arrrtoshis ARRR
      #>>>> "change": true/false             (bool)  The note is change. This can result from sending funds
      # "spendable": true/false          (bool)  Is this output spendable by this wallet
      #>>> "memo": "hex string",            (string)  Hex encoded memo (sprout and sapling address types only)
      # "memoStr": "memo",               (string)  UTF-8 encoded memo (sprout and sapling address types only)
   # },	
   
   # testing pirate-cli.exe -datadir=D:/zunqt/newPIRATE/PIRATE z_listreceivedbyaddress zs1...m
   # pirate-cli.exe -datadir=D:/zunqt/newPIRATE/PIRATE zs_listreceivedbyaddress myaddress
   # pirate-cli.exe -datadir=D:/zunqt/newPIRATE/PIRATE z_listreceivedbyaddress myaddress
   # [ok] notifications not showing update to notarized ??
   # todo: unify update_incoming_tx and line 121 deamon if len(toupdate)>0:
   # some buttons in msg not working ...
   
	def get_own_addr_txs(self,addr,min_block_height=-1):
	
		# temporary fix until zs_ fixed 
		return self.get_all_txs(addr)
		
		
		tt=[]
		try:
			tmp1=''
			if min_block_height==-1:	 # take all
				tmp1=app_fun.run_process(self.cli_cmd,['zs_listreceivedbyaddress',addr,'0' ])
			else:
				min_block_height=1720273-1000
				# print(['zs_listreceivedbyaddress',addr,'0','3',str(min_block_height) ]) 
				# tmp1=app_fun.run_process(self.cli_cmd,['zs_listreceivedbyaddress',addr,'0','3',str(min_block_height) ])
				tmp1=app_fun.run_process(self.cli_cmd,['zs_listreceivedbyaddress',addr,'0','2',str(120) ])
				# print(tmp1)
				
			t1=json.loads(tmp1) # FLATENNING RESULT TO COMMON FORMAT 
			# print(t1)
			for txid in t1:
				# tt.append({'txid':})
				for recieved in txid['received']:
					tmp={'txid':txid['txid'],
						'confirmations':txid['confirmations'],
						'fee':txid['fee'],
						"blockHeight":txid['blockHeight'],
						"change":recieved['change'],
						# "memo":recieved['memo'], # not needed when momoStr
						"memoStr": recieved['memoStr'], #.strip()
						"amount":recieved['value'],
						"jsindex":recieved['output'],
						}
					# print(tmp)
					if len(tmp["memoStr"])>0 and tmp["memoStr"][-1]==';':
						tmp["memoStr"]=tmp["memoStr"][:-1]
					tt.append(tmp)			
		except:
			print('Exception get_viewkey_txs addr ',addr)
		
		return tt
			
	# optimal for inner values: 
	# zs_listreceivedbyaddress "address" 0 2 _max_conf_
	# - return tx with confirmations between 0 and _max_conf_

	# zs_listreceivedbyaddress "address"
	# - returns all tx
	
	# NOW: test if new format ok, replace old functions ...
	
	def insert_history_tx(self,outindex,txid,block,timestamp,date_time,from_str,to_str,amount,ttype='in'):
		idb=localdb.DB(self.db)	
		table={}
		table['tx_history']=[{'Category':"outindex"+outindex
							, 'Type':ttype
							, 'status':'received'
							,'txid':txid
							,'block':block
							, 'timestamp':timestamp
							, 'date_time':date_time
							,'from_str':from_str
							,'to_str':to_str
							,'amount':amount
							, 'uid':'auto'
						}]
		idb.insert(table,['Category','Type','status','txid','block','timestamp','date_time','from_str','to_str','amount','uid'])
		# print('inserted tx history\n',table)
		if 'tx_history' not in self.to_refresh: self.to_refresh.append('tx_history') # channels,addr_book,tx_history
	
	#freshutxo [{"address","txid","amount"},..]
	def update_historical_txs(self): #,freshutxo): # max count: 80*tps * 60 =4800 < 5000
		idb=localdb.DB(self.db)	
		
		print_debug=False #True
		test_addr='zs1z0uw20wnatjvj3u9spfdhl4tkj3ljqjnzsqlx4qyrwqfsrv5pdv4k64wgxzklspsxcwd6shhx9y'
		
		# print('\n\ninit historical txs \n',self.historical_txs)
		# print(' self.last_load self.last_block', self.last_load,self.last_block)
		# iterat_arr=freshutxo # REPLACE????????????????
		full_check=False
		
		iterat_arr=self.addr_list + self.external_addr

		tmp_opti_block=self.last_block-120 #000
		
		if self.history_update_counter==0: # init run 
			if self.last_load==0: # first run ever:
				# print('# when run for the first time ever - full run')
				full_check=True
				tmp_opti_block=996000
			else: 
				# print('# when run first time in session: opti run from prev session max block')
				tmp_opti_block=self.last_load-120 # for safety minus 120 blocks 2h #prev_ses_block[0][0]
		# else:
			# print('next iter self.last_block',self.history_update_counter, self.last_block)
			
		tmp_opti_block=max(996000,tmp_opti_block)
		# print('tmp_opti_block self.last_load self.last_block',tmp_opti_block,self.last_load,self.last_block)
		
			
		self.history_update_counter+=1
		
		
		table_history_notif={}
		
		tmp_ord={}
		
		def get_outindex(tx): 
			if 'outindex' in tx: return tx['outindex']
			elif 'jsindex' in tx:return tx['jsindex']
			elif 'output' in tx: return tx['output']
			else: return 0
		
		for aa in iterat_arr:
		
			if aa!=test_addr and print_debug: continue # only pass the test addr 
		
			if print_debug: print('\n\nanalyzing aa',aa)
			tmpiter=0
			
			if True:
				tt=[] # tt=aa
				
				# here will be replaced by 
				# full run when first time
				# special full run per view key
				# partial run for own address when not init run 
				# when special rescan - full run 
				
				is_aa_external=aa in self.external_addr
				if full_check or is_aa_external or aa in self.addr_for_full_recalc:
					
					# tmp1=app_fun.run_process(self.cli_cmd,['z_listreceivedbyaddress',aa,str(self.min_conf) ])
					tt=self.get_all_txs(aa)
					# print('from view key',aa,tt) 
				else:
					# aa=tt['address'] freshutxo
					# tt=[tt] freshutxo
					# opti check inner addr:
					tt=self.get_own_addr_txs( aa,tmp_opti_block)
					# print('from opti',aa,tt)
					# print(tt)
				 	
				if len(tt)==0:
					continue
				
				# if aa not in tmp_ord: tmp_ord[aa]={}
				
				
				
				
				
				
				
				# if print_debug: 
					# print('\ntt before\n ',tt)
				
				#####################################################33
				# todo: test ordering is bad before and good after ... 
				# reordering tt
				# get confirmation 'confirmations'
				# ordering by conf number, grouped by txid, and order again by outindex
				conf_dict={}
				# ttiter=0
				for tx in tt: 
					if tx['confirmations'] not in conf_dict:
						conf_dict[tx['confirmations']]={}
					# print(ttiter,conf_dict[tx['confirmations']] )
					if tx['txid'] not in conf_dict[tx['confirmations']]:
						conf_dict[tx['confirmations']][tx['txid']]={}
					# print(ttiter,conf_dict[tx['confirmations']][tx['txid']] )
						
					outindex=get_outindex(tx)
					if outindex not in conf_dict[tx['confirmations']][tx['txid']]:
						conf_dict[tx['confirmations']][tx['txid']][outindex]=tx
						
					# print(ttiter,conf_dict[tx['confirmations']][tx['txid']][outindex])
					# ttiter+=1
					
					# if ttiter>10: break
				
				# print(conf_dict)
				# rebuild tt based on proper ordering:
				ord_conf=sorted(conf_dict.keys()) 
				# print('ord_conf',ord_conf)
				tt_rebuilt=[]
				for oc in ord_conf:
					txids=conf_dict[oc]
					# print('txids',txids)
					for ti in txids:
						tmp_tx=txids[ti]
						# print('tmp_tx',tmp_tx)
						# print('tmp_tx.keys()',tmp_tx.keys())
						ord_oi=sorted(tmp_tx.keys()) 
						# print('ord_oi',ord_oi)
						for oi in ord_oi:
							tt_rebuilt.append(tmp_tx[oi])
				
				tt=tt_rebuilt
				#####################################################33
				
				if print_debug: 
					print('\ntt after\n ',tt)
				
				# time.sleep(4)
				# return 0
				
				
				if aa not in self.historical_txs:
					self.historical_txs[aa]={}
					
				y=self.getinfo()
				
				for tx in tt: 
					
					# tmpiter+=1
					
					# if tmpiter>10: continue
					
					if print_debug  : print('analyzing tx\n',tx)
					if "txid" not in tx:
						continue
						
					# if "blockindex" in tx:
						# max_block_analized=max( tx["blockindex"], self.last_analized_block)
					# # if aa not in tmp_ord: tmp_ord[aa]={}	
					# if tx["txid"] not in tmp_ord[aa]: tmp_ord[aa][tx["txid"]]=tx["confirmations"]
					
					
					if tx["txid"] not in self.historical_txs[aa]:  # if this ever change - may be needed to update some records in case of reorg ?
						self.historical_txs[aa][tx["txid"]]={}
						
						
					outindex=get_outindex(tx)
					
					# if 'outindex' in tx:
						# outindex=tx['outindex']
					# elif 'jsindex' in tx:
						# outindex=tx['jsindex']
					# elif 'output' in tx:
						# outindex=tx['output']
						
					if outindex in self.historical_txs[aa][tx["txid"]]:
 
						if print_debug: print('outindex already in self.historical_txs[aa][tx["txid"]]',self.historical_txs[aa][tx["txid"]])
						continue
						
					if print_debug: print('before checking change')
					dt,ts=app_fun.now_to_str(False,ret_timestamp=True)
					tmp_timestamp=ts-60*tx["confirmations"]
					tmp_date_time=app_fun.date2str(datetime.datetime.now()-datetime.timedelta(seconds=60*tx["confirmations"]) )
					
					
					
					if 'change' in tx: # not interested in change tx ??
						if tx['change']:
							# print('\n\tchange found - pass by ;')
							
							# if outindex not in self.historical_txs[aa][tx["txid"]]:
							
							# table_msg=self.prep_msgs_inout(txid,[init_table['tmpmemo'],0,''],'in',init_table['dt'],tx_status='received', in_sign_uid=-2,addr_to=aa ) 
							from_str='self change from '+aa #'self' #table_msg['msgs_inout'][0]['msg']
							# print('inserting chnge tx ',from_str,tx["txid"])
							self.insert_history_tx('_'+str(outindex),tx["txid"],y["blocks"]-tx["confirmations"] , tmp_timestamp , tmp_date_time, from_str, aa, tx["amount"],ttype='in/change')
							
							self.historical_txs[aa][tx["txid"]][outindex] = { "amount":tx["amount"]}
							# is_aa_external
							
							continue
					# print('NOT CHANGE!',outindex not in self.historical_txs[aa][tx["txid"]])
					if print_debug: print('NOT CHANGE OK')
					
					if outindex not in self.historical_txs[aa][tx["txid"]]: # 'Category'= "'outindex_"+str(outindex)+"'"
					
						# if tx['txid']=='2a0a99f9644dc9e05e1417208d326abeff0710851b204235b80bdd013bc4698b': 
							# print('\nwallet api outindex not in tx=\n',tx)
						if print_debug: print('before memo decode')
					
						tmpmemo=''
						if "memoStr" in tx:
							tmpmemo=tx["memoStr"]
						else:
							tmpmemo=tx["memo"] # when no memostr needs decode 
							try:
								tmpmemo=bytes.fromhex(tmpmemo).decode('utf-8') #int(tx["memo"], 16)
							except:
								# print(226)
							
								pass
								
						# print('orig memmo',tmpmemo)
						tmpmemo=self.clear_memo(tmpmemo)
						if print_debug: print('clear memmo\n',tmpmemo) 
						
						if len(tmpmemo)<4: # in dev wallet change should fix this - taken by change:true
							from_str='too short memo imply error in msg format: ['+tmpmemo+']' 
							if print_debug: print(from_str) 
							self.insert_history_tx('_'+str(outindex),tx["txid"],y["blocks"]-tx["confirmations"] , tmp_timestamp , tmp_date_time, from_str, aa, tx["amount"],ttype='in/change?') 
							self.historical_txs[aa][tx["txid"]][outindex] = { "amount":tx["amount"]}
							continue
						
						tmpwhere={'to_str':['=',"'"+aa+"'"],'Type':[' like ',"'in%'"],'txid':['=',"'"+tx["txid"]+"'"],'Category':['=',"'outindex_"+str(outindex)+"'"] }
						
						# print('\ncheckexist where ',tmpwhere)
						checkexist=idb.select('tx_history', ["Type"],tmpwhere) # if not exist yet add for processing 
						# if tx['txid']=='2a0a99f9644dc9e05e1417208d326abeff0710851b204235b80bdd013bc4698b': 
						if print_debug: print('\ncheckexist\n',checkexist)
						
						# print(idb.select('tx_history', [ ],{'to_str':['=',"'"+aa+"'"],'Type':[' like ',"'in%'"],'txid':['=',"'"+tx["txid"]+"'"]  }))
						if len(checkexist)==0:
						
							table={}
							# updating tx history
							self.historical_txs[aa][tx["txid"]][outindex] = { "amount":tx["amount"]} #,"conf":tx["confirmations"],"memo":tmpmemo  }
							# print('updated tx history',self.historical_txs[aa][tx["txid"]][outindex])
							ttype='in'
							if aa in self.external_addr:
								ttype='in/external' 
								
							
							dt,ts=app_fun.now_to_str(False,ret_timestamp=True)
							tmp_timestamp=ts-60*tx["confirmations"]
							tmp_date_time=app_fun.date2str(datetime.datetime.now()-datetime.timedelta(seconds=60*tx["confirmations"]) )
							self.insert_history_tx( '_'+str(outindex),tx["txid"],y["blocks"]-tx["confirmations"] ,tmp_timestamp,tmp_date_time,tmpmemo,aa,tx["amount"],ttype)
						
							if print_debug: print('outindex inserted to history_tx ' )
															
							# dt,ts=app_fun.now_to_str(False,ret_timestamp=True)
							
							dt=localdb.blocks_to_datetime(y["blocks"]-tx["confirmations"]) # time it was sent 
							
							##### prepare for inserting msg
							if aa not in table_history_notif:
								# merged_msg[aa]={}
								table_history_notif[aa]={}
								# print('added aa to table_history_notif',aa)
							
							if tx["txid"] not in table_history_notif[aa]:
								# merged_msg[aa][tx["txid"]]={}
								table_history_notif[aa][tx["txid"]]={}
								# print('added txid  to table_history_notif',tx["txid"])
							if print_debug: print('before outindex in table_history_notif')
							if outindex not in table_history_notif[aa][tx["txid"]]:
								# merged_msg[aa][tx["txid"]][outindex]={'dt':dt, 'tmpmemo':tmpmemo } #table
								if print_debug: print(517)
								# print('times\n blocks_to_datetime dt',dt,'timestamp',ts-60*tx["confirmations"]   ,'date_time',app_fun.date2str(datetime.datetime.now()-datetime.timedelta(seconds=60*tx["confirmations"]) ))
								q={'dt':dt
									, 'tmpmemo':tmpmemo
									,'block':y["blocks"]-tx["confirmations"]
									,'timestamp':tmp_timestamp #ts-60*tx["confirmations"]   
									, 'date_time':tmp_date_time #app_fun.date2str(datetime.datetime.now()-datetime.timedelta(seconds=60*tx["confirmations"]) )
									, 'amount':tx["amount"]
									, 'outindex':'_'+str(outindex)
									}
								table_history_notif[aa][tx["txid"]][outindex]=q
								# print('\n\nadded outindex  to table_history_notif',aa,'\n',outindex,'\n',q)
							if aa not in tmp_ord: 
								tmp_ord[aa]={}	
								if print_debug: print('added aa to tmp_ord' )
								
							if tx["txid"] not in tmp_ord[aa]: 
								tmp_ord[aa][tx["txid"]]=tx["confirmations"]
								if print_debug: print('added txid to tmp_ord[aa]' )
								
								
		self.addr_for_full_recalc=[] # reset 
		
		tmpblocks=self.getinfo()["blocks"]
		# print('blocks getinfo',tmpblocks)
		self.last_block=tmpblocks
		
		
		
		
		
		
		def check_is_channel(tmpmsg,test_json=['channel_name' , 'channel_owner', 'channel_intro','channel_type']):
			channel_json=None
			try:
				channel_json=json.loads(tmpmsg)
				cc=0
				for tt in test_json:
					if tt in tmpmsg:
						cc=cc+1
						
				return cc==len(test_json),channel_json
				
			except:
				return False,channel_json
			
		if print_debug: print('tmp_ord',tmp_ord) # tmp org should only contain not empty msgs found in the loop ... 
		for_ord={}
		for aa,txids in tmp_ord.items():
			# print('aa,txids',aa,txids)
			for txid, confs in txids.items():
				# bug: for each conf there can be many entries
				if confs not in for_ord:
					for_ord[confs]=[[aa,txid]]
				else:
					for_ord[confs].append([aa,txid])
				# for_ord[confs]=[aa,txid]
				
		for_ord_keys=list( for_ord.keys())
		sorted_for_ord_keys=sorted(for_ord_keys, reverse=True) 
		
		if print_debug: print('for_ord',for_ord)
		if print_debug: print('sorted_for_ord_keys',sorted_for_ord_keys)
		
		for ss in sorted_for_ord_keys: 
			for conf_ar_txid in for_ord[ss]:
				aa=conf_ar_txid[0]
				txid=conf_ar_txid[1]
				if print_debug: print('aa txid',aa,txid) 
			
				is_aa_external=aa in self.external_addr
				if print_debug: print('is_aa_external', is_aa_external) # selected txid on aa 
				
				if aa not in table_history_notif:
					if print_debug: print(aa,'not in ',table_history_notif)
					continue
					
				if txid not in table_history_notif[aa]:
					if print_debug: print(txid,'not in ',table_history_notif[aa])
					continue
					
				iis=table_history_notif[aa][txid]
				if print_debug: print('iis',iis) 
				if True:
					
					kk_ordered=sorted(iis.keys()) 
					init_table=iis[kk_ordered[0]]
					
					if len(kk_ordered)>1:
						for ii in kk_ordered[1:]:
							init_table['tmpmemo']+=iis[ii]['tmpmemo'] #merge memos if multiple outindex and multiple memos 
							init_table['outindex']+=iis[ii]['outindex']
							
					if print_debug: print('init_table',init_table)		
							
					table_msg={} # insert only those after first block
					from_str=''
					
					if True: #init_table["block"]>=self.first_block:
						table_msg=self.prep_msgs_inout(txid,[init_table['tmpmemo'],0,''],'in',init_table['date_time'],tx_status='received', in_sign_uid=-2,addr_to=aa ) # -2 to be detected
						
						from_str=table_msg['msgs_inout'][0]['msg']
						if print_debug: print(606,table_msg,from_str)
						tmpmsg=from_str 
						
						
						
						
						# remove spoofing and add channe lupdate afte owner recognized in msg
						
						
						
						is_channel=idb.select('channels',['channel_name'],{'address':['=',"'"+aa+"'"]} ) # check if recognized channel
						# is_abuse=''
						channel_json={}
						if len(is_channel)>0: 
							is_channel=True
							
							# is_channel2 ,channel_json=check_is_channel(tmpmsg) # check if msg has channel definition 
							# if is_channel2  and aa not in self.addr_list:
								
								# is_abuse='\n'.join( ['\n\nCHANNEL ABUSE DETECTED SPOOFING CHANNEL INFO',aa,str(txid),'\n'] )
								# if print_debug: print('is_abuse,tmpmsg\n',is_abuse,tmpmsg)
								# tmpmsg= is_abuse+tmpmsg
							
						else: # if not recognized channel - check if needs registration?
							is_channel=False # try recognize incoming channel
							if print_debug: print('629 ') # if proper channel - register
							try: 
								is_channel,channel_json=check_is_channel(tmpmsg)
								if print_debug: print(635,channel_json)
								
								if is_channel:  # get view key from table :
									vk_list=idb.select('view_keys', ["vk"],{'address':['=',"'"+aa+"'"]})
									vkey=''
									if len(vk_list)>0:
										vkey=vk_list[0][0]
										
									is_chnl_own='False'
									chnl_owner=channel_json['channel_owner'] # own channel should be reigistered in creation 
									if aa in self.addr_list:
										is_chnl_own='True' 
									
									table={'channels':[{'address':aa, 'vk':vkey, 'creator':chnl_owner, 'channel_name':channel_json['channel_name'], 'channel_intro':channel_json['channel_intro'], 'status':'active', 'own':is_chnl_own , 'channel_type':channel_json['channel_type']  }]}	
									if print_debug: print('channel recog:',table)
									idb.insert(table,['address' , 'vk' , 'creator' , 'channel_name', 'channel_intro' , 'status' , 'own','channel_type' ])
									if 'channels' not in self.to_refresh: self.to_refresh.append('channels') # channels,
									
									if aa in self.external_addr: # change addr book viekey alias category 
								
										table={}
										table['addr_book']=[{'Category':'Channel: '+channel_json['channel_type'],'Alias': channel_json['channel_name'], 'Address':aa, 'ViewKey':vkey, 'viewkey_verif':1,'addr_verif':1 }]  
										idb.upsert(table,[ 'Category','Alias','Address' , 'ViewKey', 'viewkey_verif','addr_verif' ],{'Address':['=',"'"+aa+"'"]})
										if 'addr_book' not in self.to_refresh: self.to_refresh.append('addr_book') # channels,addr_book
								
							except:
								print("Not proper json channel / wallet api 662",tmpmsg)
								pass
						
						table_msg['msgs_inout'][0]['is_channel']=str(is_channel)
						# if is_abuse!='':
							# table_msg['msgs_inout'][0]['msg']=tmpmsg
							
							
							
							
							
							
						if print_debug: print('674 msg before insert',table_msg)
						# if is channel - add sender to anon addr book to mark same name each time : self name + init hash 
						# if is_channel: # is channel difinition  
						idb.insert(table_msg,['proc_json','type','addr_ext','txid','tx_status','date_time', 'msg','uid','in_sign_uid','addr_to','is_channel'])
					
					if not is_aa_external: #True: #init_table["block"]>=self.first_block:
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
						
						table['notifications']=[{'opname':tmpopname,'datetime':init_table['date_time'],'status':'Confirmed','details':txid,'closed':'False','orig_json':tmpjson ,'uid':'auto'}]
						
						idb.insert(table,['opname','datetime','status','details', 'closed','orig_json' ,'uid'])
						if 'notifications' not in self.to_refresh: self.to_refresh.append('notifications') #self.to_refresh=[] channels,addr_book,tx_history,notifications
				
		# print('return',table_history_notif)
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
		
		
	# depends on self.historical_txs self.wl self.total_balance self.total_conf self.total_unconf
	# self.alias_map self.last_block self.addr_amount_dict
	# disp_dict['amounts']=self.amounts
		# disp_dict['amounts_conf']=self.amounts_conf
		# disp_dict['amounts_unc']=self.amounts_unc
		# disp_dict['unconfirmed']=self.unconfirmed
		# disp_dict['confirmed']=self.confirmed
		# disp_dict['all_unspent']=self.all_unspent	
		# disp_dict['addr_list']=self.addr_list
		# disp_dict['external_addr']=self.external_addr
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
		disp_dict['wl']=self.wl #[] of {'addr':aa,'confirmed': amount_init, 'unconfirmed': am_unc,'#conf':cc_conf,'#unconf':cc_unc }
		# disp_dict['historical']=self.historical_txs
		disp_dict['aliasmap']=self.alias_map
		disp_dict["blocks"]=self.last_block
		
		disp_dict['addr_amount_dict']=self.addr_amount_dict #self.addr_amount_dict[aa]={'confirmed':amount_init,'unconfirmed':am_unc,'#conf':cc_conf,'#unconf':cc_unc}
		disp_dict['amounts']=self.amounts
		disp_dict['amounts_conf']=self.amounts_conf
		disp_dict['amounts_unc']=self.amounts_unc
		disp_dict['unconfirmed']=self.unconfirmed
		disp_dict['confirmed']=self.confirmed
		disp_dict['all_unspent']=self.all_unspent	
		disp_dict['addr_list']=self.addr_list
		disp_dict['external_addr']=self.external_addr
		
		
		return disp_dict
		
		
		#    
	#  self.last_block 
		 
	# updates:
	# disp_dict['amounts']=self.amounts
		# disp_dict['amounts_conf']=self.amounts_conf
		# disp_dict['amounts_unc']=self.amounts_unc
		# self.addr_amount_dict
	def wallet_summary(self):
				
		self.addr_amount_dict={}
		self.total_balance=float(0)
		self.total_conf=float(0)
		self.total_unconf=float(0)
		self.wl=[]
		self.amounts=[]
		self.amounts_conf=[]
		self.amounts_unc=[]
		
		# potential bug:
		# either self.confirmed or self.unconfirmed not having new aa or self.addr_list
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
		tmpmemo=initmem.replace('\\xf6','').replace('\\x00','') #.replace("\0",'') BUG \0
		
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
			
		return tmpmemo[:lastii] #.strip()
		
		
	# z_listreceivedbyaddress “address” need this for view key ?	
		
	# in new addr reciving tx not refreshig self.confirmed ??

	# updates:
	# disp_dict['unconfirmed']=self.unconfirmed
	# disp_dict['confirmed']=self.confirmed
	# disp_dict['all_unspent']=self.all_unspent	
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
				# print('...alias['+alias+'] changed to addr ['+oo+']')
				return oo
					
		return alias
			
		

	
	def address_aliases(self ): # address_aliases(get_wallet(True))
		# self.alias_map={} # to keep it consistent 
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
		
		# print('self.addr_list',self.addr_list)
		# print('self.external_addr',self.external_addr)
		
		
	def new_zaddr(self,new_seed=False):

		try:
			tmpnewaddr=''
			
			if new_seed: 
				print('creating address from new seed')
				tmpnewaddr=app_fun.run_process(self.cli_cmd,"z_getnewaddresskey ")	
			else: 
				print('creating diversified address')
				tmpnewaddr=app_fun.run_process(self.cli_cmd,"z_getnewaddress")		
			
			self.update_all_addr()
			self.address_aliases() # this takes only own addr 
			# self.update_unspent() # this important only for own addr 
			self.any_change.append('z_getnewaddress')
			# self.refresh_wallet()
			return str(tmpnewaddr).strip()
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
			print('exporting viewkey for zaddr',zaddr)
			return str(app_fun.run_process(self.cli_cmd,"z_exportviewingkey "+zaddr)) 
		except:
			print('wallet api cannot export')
			return 'cannot export'
		
	# "yes", "no" or "whenkeyisnew"
	def imp_view_key(self,zaddr,vkey,rescan="whenkeyisnew",startHeight=1790000 ): #996000 1575757 1780000

		if zaddr in self.addr_list: # self key quick return
			print('View key is owned by the wallet - not need to import')
			return {'address':zaddr, 'type':'sapling'}
	
		rescan="yes"
		tmpnewaddr=''
		print("started z_importviewingkey",vkey[:7]+'...','rescan',rescan,'start height',str(startHeight))
		tmpnewaddr=app_fun.run_process(self.cli_cmd,["z_importviewingkey",vkey,rescan,str(startHeight)]) #,zaddr
		print('finished z_importviewingkey')
		
		if 'error' in tmpnewaddr.lower():
			# if already in the wallet - test: 
			print('error',tmpnewaddr)
			print('additional check...')
			tmparr=self.get_all_txs( zaddr)
			if 'error' not in str(tmparr):
				print('... ok - valid - finishing update ... ')
				return {'address':zaddr, 'type':'sapling'}
		
			return {'error':tmpnewaddr}
		
		print('updating wallet addresses')
		self.update_all_addr()
		self.any_change.append('z_importviewingkey')
		
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
		# self.any_change.append('z_sendmany')
		# self.refresh_wallet()
		return app_fun.run_process(self.cli_cmd,args)

	def exp_prv_key(self,zaddr):
		try:
			return str(app_fun.run_process(self.cli_cmd,["z_exportkey",zaddr])) 
		except:
			print('wallet api cannot export exp_prv_key')
			return 'cannot export'

		
	def imp_prv_key(self,zkey,rescan="whenkeyisnew",startHeight=996000):

		# print('Importing private key may take a while (rescan) from height '+str(startHeight) )
		
		tmpnewaddr=app_fun.run_process(self.cli_cmd,["z_importkey",zkey,rescan,str(startHeight) ])
		tmpnewaddr_json=json.loads(tmpnewaddr) 
		# deamon.run_subprocess(self.cli_cmd,"z_importkey "+zkey+rescan+str(startHeight), 64 ) 
		self.update_all_addr()
		self.address_aliases()
		# self.update_unspent()
		
		self.addr_for_full_recalc.append(tmpnewaddr_json['address']) #tmpresult['address']
		self.any_change.append('z_importkey')
		# self.refresh_wallet()
		return tmpnewaddr_json
		# print('Done')


