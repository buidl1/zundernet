## TODO 1h:
# [ok] add first usage block per key / addr to sync on import faster 
# [ok]  add exporting with info about first block - if none get latest saved block
# [ok] add importing with block nr
# [test: importing - pass the same ; importing to new wallet - scannig faster ... ]

# add channel creation init block 
# also add in import / export 
 
# [ok] new table with addr - key assignment
# [ok] on start after wallet synced - check if all addr got keys
# [ok] also after import priv keys - insert
# [ok] if no priv key - get and update
# >>>> refresh display to show priv key nr next to and addr in brackets (1)
# or better rename cagtegory to seed 1 if default category (Edit) or extende category _s1 if non default 
# >>>> allow priv key selection when doing new diversified addr 


# assign each addr to keys, assign ids to keys 1,2...
# display next to each addr? in brackets (1)
# when importing spending key ? also create one ?
# make sure if addr is there and i missing a spending key - extract one 

######### set primary key 
# z_setprimaryspendingkey
# D:\zunqt\newPIRATE\bin3>pirate-cli.exe -datadir=D:/zunqt/newPIRATE/PIRATE help z_setprimaryspendingkey
# z_setprimaryspendingkey

# Set the primary spending key used to create diversified payment addresses.

# Result: Returns True if the spending key was successfully set.



###### match keys with addresses:
# z_exportkey "zaddr"

# Reveals the zkey corresponding to 'zaddr'.
# Then the z_importkey can be used with this output

# Arguments:
# 1. "zaddr"   (string, required) The zaddr for the private key

# Result:
# "key"                  (string) The private key

# create new addr from new key
# z_getnewaddresskey ( type )
# This creates a new sapling extended spending key and
# returns a new shielded address for receiving payments.

# With no arguments, returns a Sapling address.

# Arguments:
# 1. "type"         (string, optional, default="sapling") The type of address. One of ["sprout", "sapling"].

# Result:
# "PIRATE_address"    (string) The new shielded address.

import os
import time
import sys
import datetime

# import subprocess
import json
# import modules.deamon as deamon
# import re
# import modules.localdb as localdb
import modules.app_fun as app_fun
import modules.gui as gui
global global_db, init_db
# import modules.aes as aes
# save in db last block nr, last time loaded, last loading time

class Wallet(gui.QObject): # should store last values in DB for faster preview - on preview wallt commands frozen/not active
	sending_signal = gui.Signal(list)
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
		super(Wallet, self).__init__()
		
		self.processing_update_historical_txs=False
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
		self.last_refresh_time=0
		
		# idb=localdb.DB(self.db)	
		 
		disp_dict=global_db.select('jsons',['json_content','last_update_date_time'],{'json_name':['=',"'display_wallet'"]})
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
		
		
		tx_in_sql=global_db.select('tx_history',['Category','Type','status','txid','block','timestamp','date_time','from_str','to_str','amount','uid'],{'Type':[' like ',"'in%'"]})
		
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
				
		# update priv keys to get start block
		tmp_addr_pk=global_db.select('priv_keys',['address','pk' ],{'usage_first_block':[' is '," null "]})
		# print(201,tmp_addr_pk)
		self.addr_privkey_start={}
		if len(tmp_addr_pk)>0:
			for rr in tmp_addr_pk:
				self.addr_privkey_start[rr[0]]=rr[1]
		
		# print('self.addr_privkey_start',self.addr_privkey_start)
		self.update_privkey_start()
		 
		# print('self.addr_privkey_start\n',self.addr_privkey_start)
		
		
		# table['view_keys']={'address':'text', 'vk':'text' }
		# tmp_addr_vk=global_db.select('view_keys',['address','vk', 'usage_first_block' ] )
		self.addr_viewkey_start={}
		# every addr to this vk shuold get start block 
		# not onnly on new tx insert (if first tx ever!
		# but also for historical - if key uploaded after first tx )
		
		# self.view_key_list=[]
		self.addr_view_key_dict={}
		self.view_key_addr_dict={} # vk->[a1,a2,...]
		
		self.update_vk_objects()
		
		# print('self.addr_viewkey_start\n',self.addr_viewkey_start)
		# print('self.addr_view_key_dict\n',self.addr_view_key_dict)
		# print('self.view_key_addr_dict\n',self.view_key_addr_dict)
		# for tt in tmp_addr_vk:
		
			# if tt[2]==None: #tmp_addr_vk=global_db.select('view_keys',['address','vk', 'usage_first_block' ] )
				# tt2=self.get_first_block( tt[0])
				# if tt2==None:
					# print('view key without start block',tt)
					# self.addr_viewkey_start[tt[0]]=tt[1] 
				# else: # update for all addr wih this vk 
					# table={'view_keys':[{'usage_first_block':tt2}]} 
					# global_db.upsert(table,['usage_first_block'],where={'vk':['=','"'+tt[1] +"'"]}) # separate viewkey table - was insert
			
			# if tt[1] not in self.view_key_addr_dict:
				# self.view_key_addr_dict[tt[1]]=[tt[0]]
			# elif tt[0] not in self.view_key_addr_dict[tt[1]]:
				# self.view_key_addr_dict[tt[1]].append(tt[0]])
		
			# if tt[1] not in self.view_key_list:
				# self.view_key_list.append(tt[1])
				
			# if tt[0] not in self.addr_view_key_dict:
				# self.addr_view_key_dict[tt[0]]=tt[1]
		# table['priv_keys']={'address':'text', 'pk':'text','id':'int', 'usage_first_block':'int'  } # firstblock init usage block
	
	def update_privkey_start(self): # from history , run on init and when added new 
		tmp_pk_aa={}
		for aa,pk in self.addr_privkey_start.items() : # reverse assignment
			if pk not in tmp_pk_aa: tmp_pk_aa[pk]=[aa]
			elif aa not in tmp_pk_aa[pk]: tmp_pk_aa[pk].append(aa)
		# print(252,tmp_pk_aa)
		pk_to_del=[]
		for pk in tmp_pk_aa :
			# print('pk',pk)
			fibl=self.get_first_block( tmp_pk_aa[pk] )
			# print('fibl',fibl)
			if fibl==None: continue # if still none - keep as is 
			# print('inserting',fibl)
			table={'priv_keys':[{'usage_first_block':fibl}]} 
			global_db.upsert(table,['usage_first_block'],where={'pk':['=',"'"+pk+"'"]}) # separate viewkey table - was insert
			
			pk_to_del.append(pk)
			
			# print('del',tmp_pk_aa[pk])
			for aa in tmp_pk_aa[pk]:
				# print('del aa',aa)
				del self.addr_privkey_start[aa]
			
	 
	
		
	# block to frequent run
	# if less then 15 seconds reject?
	def refresh_wallet(self): # once a 1-2 minutes?
	
		if time.time()-self.last_refresh_time<15: 
			# print('reject too freq refresh',time.time()-self.last_refresh_time)
			return 0
		self.last_refresh_time=time.time()
	
		
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
						'rawconfirmations':txid['confirmations'],
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
		# idb=localdb.DB(self.db)	
		table={}
		table['tx_history']=[{'Category':outindex # actually with prefix "outindex_"+
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
		global_db.insert(table,['Category','Type','status','txid','block','timestamp','date_time','from_str','to_str','amount','uid'])
		if 'tx_history' not in self.to_refresh: self.to_refresh.append('tx_history') # channels,addr_book,tx_history
		
		# update pk usage_first_block for all addr [per pk]
		if to_str in self.addr_privkey_start:
			pk_to_update=self.addr_privkey_start[to_str]
			table={'priv_keys':[{'usage_first_block':block}]}
			global_db.update(table,['usage_first_block'],{'pk':[' = ',"'"+pk_to_update+"'"]})
			
			# prep list to delete from future updates 
			tmp_list_to_del=[] 
			for aa,pk in self.addr_privkey_start.items():
				if pk==pk_to_update:
					tmp_list_to_del.append(aa)
			
			for dd in tmp_list_to_del:
				del self.addr_privkey_start[dd] # del from dict all adr conn to pk - already have start block 
				
		elif to_str in self.addr_viewkey_start: #[tt[0]]=tt[1]
			vk_to_update=self.addr_viewkey_start[to_str]
			table={'view_keys':[{'usage_first_block':block}]}
			global_db.update(table,['usage_first_block'],{'vk':[' = ',"'"+vk_to_update+"'"]})
			
			# prep list to delete from future updates 
			tmp_list_to_del=[] 
			for aa,vk in self.addr_viewkey_start.items(): # may be multiple adr fro vk 
				if vk==vk_to_update:
					tmp_list_to_del.append(aa)
			
			for dd in tmp_list_to_del:
				del self.addr_viewkey_start[dd] # del from dict all adr conn to pk - already have start block 
				
				
		
	def get_first_block(self,addr): # search for specific adddr or group of addr assoc with vk 
		# print('get_first_block',addr)
		if type(addr)==type('asdf'):
			retarr=global_db.select_min_val( 'tx_history','block',where={'to_str':['=',"'"+addr+"'"]} ) 
			# print(retarr)
			if len(retarr)>0:
				# print('return retarr[0][0]',retarr[0][0])
				return retarr[0][0]
		elif  type(addr)==type([]):  
			minv=None
			for aa in addr:
				retarr=global_db.select_min_val( 'tx_history','block',where={'to_str':['=',"'"+aa+"'"]} ) 
				# print(aa,retarr)
				if len(retarr)>0:
					if minv==None or retarr[0][0]<minv: minv=retarr[0][0]
			# print('return minv',minv)
			return minv
		
			
		return None
		
		
		
	# at start also read min block nr per addr/pk and fill in
	# same for missing vk start block	
		
	def add_pk_for_start_block(self,aa,pk): # used only in new addr gen 
		
		self.addr_privkey_start[aa]=pk
		
		self.update_privkey_start() # update from history 
		# if addr on new seed only
		# if old seed - als ocheck if proper start lbock exist
		
		
		
		
		# if aa in self.addr_privkey_start:
			# pk_to_update=self.addr_privkey_start[aa]
			# table={'priv_keys':[{'usage_first_block':block}]}
			# global_db.update(table,['usage_first_block'],{'pk':[' = ',"'"+pk_to_update+"'"]})
			 
			# tmp_list_to_del=[] 
			# for aa,pk in self.addr_privkey_start.items():
				# if pk==pk_to_update:
					# tmp_list_to_del.append(aa)
			
			# for dd in tmp_list_to_del:
				# del self.addr_privkey_start[dd]  
				
				
				
	


				
	# def add_vk_for_start_block(self,aa,vk):
		
		# self.addr_viewkey_start[aa]=vk
		
	
	#freshutxo [{"address","txid","amount"},..]
	def update_historical_txs(self): #,freshutxo): # max count: 80*tps * 60 =4800 < 5000
	
		
		if self.processing_update_historical_txs:
			print('update_historical_txs busy - return ')
			return 0
			
		self.processing_update_historical_txs=True
		
		# idb=localdb.DB(self.db)	
		
		print_debug=   False
		
		print_debug2= False
		test_addr='zs1z0uw20wnatjvj3u9spfdhl4tkj3ljqjnzsqlx4qyrwqfsrv5pdv4k64wgxzklspsxcwd6shhx9y'
		# test_addr='zs1qds8vy37aewz0ersgnxexj3w96gs642p0d0mh3vzlschgyn9ahfrvu7lq96wmff4l8lg7a8rpg6'
		 
		# if True:
		
		queue_table={}
		queue_table['queue_waiting']=[global_db.set_que_waiting(command='process tx' )] #,jsonstr=json.dumps({'left':'0 of N'})
		queue_table['queue_waiting'][0]['status']='processing' 
		queue_table['queue_waiting'][0]["type"]='auto'
		queue_id=queue_table['queue_waiting'][0]['id']
		global_db.insert(queue_table,['type','wait_seconds','created_time','command' ,'json','id','status' ])
		self.sending_signal.emit(['cmd_queue'])
		
		# print('update_historical_txs 2')
		
			
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
		
		#bug: first process 140 then once again 90 ... 
		
		for ind, aa in enumerate(iterat_arr):
		
			# print('update_historical_txs 4',ind,aa)
			working_on='Address '+str(ind+1)+' of '+str(len(iterat_arr))
			
			# print('update_historical_txs 5',working_on,queue_id) #queue_table['queue_waiting'][0]['status']='processing' 
			global_db.update( {'queue_waiting':[{'status':'processing\n'+working_on }]} ,['status'],{'id':[ '=',queue_id ]})
			self.sending_signal.emit(['cmd_queue'])
		 
			if aa!=test_addr and print_debug2: continue # only pass the test addr 
			
			# if aa!=test_addr: continue
		
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
				
				if aa not in self.historical_txs:
					self.historical_txs[aa]={}
				
				
				
				
				
				# if print_debug: 
					# print('\ntt before\n ',tt)
				
				#####################################################33
				# todo: test ordering is bad before and good after ... 
				# reordering tt
				# get confirmation 'confirmations'
				# ordering by conf number, grouped by txid, and order again by outindex
				
				global_db.update( {'queue_waiting':[{'status':'processing\n'+working_on+'\nanalyzing tx\'s '+str(len(tt)) }]} ,['status'],{'id':[ '=',queue_id ]})
				self.sending_signal.emit(['cmd_queue'])
			
				
				conf_dict={}
				tx_to_process=0
				# ttiter=0
				for tx in tt: 
				
					if 'txid' not in tx :
						print("ERR!!! BAD TX?? 'txid' not in tx",tx)
						continue
					elif 'rawconfirmations' not in tx:
						print("ERR!!! BAD TX?? 'rawconfirmations' not in tx",tx)
						continue
					
					# if print_debug and ttiter>3: break
					# if print_debug: print('\ntaking tx\n',tx)
					# ttiter+=1
					outindex=get_outindex(tx)
					
					# if aa in self.historical_txs :
					if tx['txid'] in self.historical_txs[aa]:
						if outindex in self.historical_txs[aa][tx['txid']]:
							# print('already in')
							continue
				
					if tx['rawconfirmations'] not in conf_dict:
						conf_dict[tx['rawconfirmations']]={}
						
						
					# if tx['rawconfirmations'] <39000 and print_debug2:
						# continue 
						
					# print(ttiter,conf_dict[tx['rawconfirmations']] )
					if tx['txid'] not in conf_dict[tx['rawconfirmations']]:
						conf_dict[tx['rawconfirmations']][tx['txid']]={}
					# print(ttiter,conf_dict[tx['confirmations']][tx['txid']] )
						
					if outindex not in conf_dict[tx['rawconfirmations']][tx['txid']]:
						conf_dict[tx['rawconfirmations']][tx['txid']][outindex]=tx
						tx_to_process+=1
						
					# print(ttiter,conf_dict[tx['confirmations']][tx['txid']][outindex])
					
				
				# if print_debug: print('conf_dict',conf_dict)
				# rebuild tt based on proper ordering:
				if tx_to_process<1:
					continue
				
				global_db.update( {'queue_waiting':[{'status':'processing\n'+working_on+'\nreordering tx\'s '+str(tx_to_process) }]} ,['status'],{'id':[ '=',queue_id ]})
				self.sending_signal.emit(['cmd_queue'])
				
				ord_conf=sorted(conf_dict.keys(),reverse=True) 
				# print('ord_conf',ord_conf)
				tt_rebuilt=[]
				for oc in ord_conf:
					txids=conf_dict[oc]
					# print('txids',txids)
					
					# if print_debug2: tmpiter+=1
					
					# if print_debug2 and tmpiter>3: continue # only take first 3 msgs ...
					
					for ti in txids:
						tmp_tx=txids[ti]
						# print('tmp_tx',tmp_tx)
						# print('tmp_tx.keys()',tmp_tx.keys())
						ord_oi=sorted(tmp_tx.keys()) #,reverse=True
						# print('ord_oi',ord_oi)
						for oi in ord_oi:
							# print(oi)
							# print(' self.historical_txs ', self.historical_txs  )
							# print( self.historical_txs[aa]  )
							# print( self.historical_txs[aa][tx["txid"]] )
							
							# tt_rebuilt.append(tmp_tx[oi]) # change 2022
							tt_rebuilt.append( [oi, tmp_tx[oi]] ) # added outindex not to cal again 
							# if ti not in self.historical_txs[aa]: 	
								# tt_rebuilt.append(tmp_tx[oi])
								
							# elif oi not in self.historical_txs[aa][ti]: 
								# tt_rebuilt.append(tmp_tx[oi])
				
				tt=tt_rebuilt
				
				# print('TX t oprocess for aa',aa,len(tt))
				if len(tt)>3:
					working_on_tx='TX\'s to process: '+ str(len(tt))
					# print(working_on_tx)
					global_db.update( {'queue_waiting':[{'status':'processing\n'+working_on+'\n'+working_on_tx }]} ,['status'],{'id':[ '=',queue_id ]})
					self.sending_signal.emit(['cmd_queue'])
					time.sleep(0.3)
				# else:
					# print('TX t oprocess for aa',aa,len(tt))
				#####################################################33
				
				
				
				
				
				# if print_debug: 
					# print('\ntt after\n ',tt)
					# change ???
					# txe dfe433d45bc39179d08377620970115a751d8b17b5e58b29e831d61ee058f12c
					# txe 1a0d30ead204f21eaf0cec641a8ab4048a962552a021b478eb9e3d6c06be85ae
					
				
				# time.sleep(4)
				# return 0
				
				
				# if aa not in self.historical_txs:
					# self.historical_txs[aa]={}
					
				y=self.getinfo()
				
				start_change=False
				
				for txind, tx2 in enumerate(tt): 
					
					tx=tx2[1] #[oi, tmp_tx[oi]]
					outindex=tx2[0]
					
					if (txind+1)%max([10,int(tx_to_process/100) ])==0:
						working_on_tx='TX\'s done: '+str((txind+1))+'/' +str(tx_to_process)
						# print('working_on_tx',working_on_tx)
						global_db.update( {'queue_waiting':[{'status':'processing\n'+working_on+'\n'+working_on_tx }]} ,['status'],{'id':[ '=',queue_id ]})
						self.sending_signal.emit(['cmd_queue'])
						# time.sleep(0.3)
					
					# tx_done+=1
					
					# if print_debug2: tmpiter+=1
					
					# if print_debug2 and tmpiter>3: continue # only take first 3 msgs ...
					
					if print_debug  : print('analyzing tx\n',tx["txid"],'outindex',outindex)
					# if "txid" not in tx:
						# continue
						
					# if "blockindex" in tx:
						# max_block_analized=max( tx["blockindex"], self.last_analized_block)
					# # if aa not in tmp_ord: tmp_ord[aa]={}	
					# if tx["txid"] not in tmp_ord[aa]: tmp_ord[aa][tx["txid"]]=tx["confirmations"]
					tx_confirmations = tx["rawconfirmations"]
					
					########### here updating starts!!
					if tx["txid"] not in self.historical_txs[aa]:  # if this ever change - may be needed to update some records in case of reorg ?
						self.historical_txs[aa][tx["txid"]]={}
						
						
					# outindex=get_outindex(tx)
						
					if outindex in self.historical_txs[aa][tx["txid"]]:
 
						if print_debug: print('outindex already in self.historical_txs[aa][tx["txid"]]' )
						continue
						
					# if print_debug: print('before checking change')
					dt,ts=app_fun.now_to_str(False,ret_timestamp=True)
					tmp_timestamp=ts-60*tx_confirmations
					tmp_date_time=app_fun.date2str(datetime.datetime.now()-datetime.timedelta(seconds=60*tx_confirmations) )
					
					def analyzeMemo(tx):
						a_tmpmemo=''
						if "memoStr" in tx:
							a_tmpmemo=tx["memoStr"]
						else:
							a_tmpmemo=tx["memo"] # when no memostr needs decode 
							try:
								a_tmpmemo=bytes.fromhex(a_tmpmemo).decode('utf-8') #int(tx["memo"], 16)
							except:
								print('Parsing memo bytes error[',a_tmpmemo,']')
								pass
								
						a_tmpmemo=self.clear_memo(a_tmpmemo)
						# if print_debug: 
						# print('clear memmo 64\n',a_tmpmemo[:64],len(a_tmpmemo) ) 
						if print_debug: print('len(a_tmpmemo)\n', len(a_tmpmemo) ) 
						return a_tmpmemo
					
					# change is unstable response from rpc so todo options:
					# 1. outindex 0 is never change
					# 2. outindex 1+ can be change only if 0 was not - process and find were real change startswith
					# 3. if no tx is change - detect when to stop
					# 4. detect change - EMPTY MEMO OR ALMOST EMPTY ANG GOT NO ';' ? - all next are change ?
					
					# 1. outindex 0 is never change
					tmpmemo=''
					# if 'change' in tx and outindex>0: # not interested in change tx ??
					# check for change for every tx >0
					# based on memo value no matter if change=True/False is in tx 
					if  outindex>0: # not interested in change tx ??
					
						# only exclude with additional conditions (sometimes change tru is misleading):
						# 1. memo is empty
						# 2. memo is almost empty ang got no ';'
						
						# detect change started ? actually should be last tx!
						if not start_change: # check additional conditions
							tmpmemo=analyzeMemo(tx)
							if len(tmpmemo)==0 or ( len(tmpmemo)<5 and tmpmemo[-1]!=';' ) :
								start_change=True
								# if len(tmpmemo)>1: tmpmemo=tmpmemo[:-1] # exclude ';'
								
						# if change already started - continue passing by 
						if start_change:  # if tx['change']: 
							# if print_debug:  								print('\n\tchange found - pass by ;') 
							from_str='self change from '+aa  
							self.insert_history_tx("outindex_"+str(outindex),tx["txid"],y["blocks"]-tx_confirmations , tmp_timestamp , tmp_date_time, from_str, aa, tx["amount"],ttype='in/change')
							
							self.historical_txs[aa][tx["txid"]][outindex] = { "amount":tx["amount"]}
							 
							continue
					
					# also need to check for change even when change condition not there ...
					
					# if outindex not in self.historical_txs[aa][tx["txid"]]: # 'Category'= "'outindex_"+str(outindex)+"'"
					if True: # above condition not needed already passed with continue 
					
						# if tx['txid']=='2a0a99f9644dc9e05e1417208d326abeff0710851b204235b80bdd013bc4698b': 
							# print('\nwallet api outindex not in tx=\n',tx)
						# if print_debug: print('before memo decode')
					
						if tmpmemo=='':  tmpmemo=analyzeMemo(tx) # could be prepared in change block above - then no need
							 
						if len(tmpmemo)==0:
							tmpmemo='[Empty memo] incoming amount '+str(tx['amount'])
						elif  tmpmemo[-1]==';': tmpmemo=tmpmemo[:-1]
						
						# if len(tmpmemo)<4: # in dev wallet change should fix this - taken by change:true
							# from_str='too short memo imply error in msg format: ['+tmpmemo+']' 
							# if print_debug: print(from_str) 
							# self.insert_history_tx("outindex_"+str(outindex),tx["txid"],y["blocks"]-tx_confirmations , tmp_timestamp , tmp_date_time, from_str, aa, tx["amount"],ttype='in/change?') 
							# self.historical_txs[aa][tx["txid"]][outindex] = { "amount":tx["amount"]}
							# continue
						
						
						
						# tmpwhere={'to_str':['=',"'"+aa+"'"],'Type':[' like ',"'in%'"],'txid':['=',"'"+tx["txid"]+"'"],'Category':['=',"'outindex_"+str(outindex)+"'"] }
						
						# print('\ncheckexist where ',tmpwhere)
						# this is double check not needed ??
						
						
						# checkexist=idb.select('tx_history', ["Type"],tmpwhere) # if not exist yet add for processing 
						# if tx['txid']=='2a0a99f9644dc9e05e1417208d326abeff0710851b204235b80bdd013bc4698b': 
						# if print_debug: print('\ncheckexist\n',checkexist)
						
						# print(idb.select('tx_history', [ ],{'to_str':['=',"'"+aa+"'"],'Type':[' like ',"'in%'"],'txid':['=',"'"+tx["txid"]+"'"]  }))
						if True: #len(checkexist)==0:
						
							table={}
							# updating tx history
							self.historical_txs[aa][tx["txid"]][outindex] = { "amount":tx["amount"]} #,"conf":tx["confirmations"],"memo":tmpmemo  }
							# print('updated tx history',self.historical_txs[aa][tx["txid"]][outindex])
							ttype='in'
							if aa in self.external_addr:
								ttype='in/external' 
								
							
							dt,ts=app_fun.now_to_str(False,ret_timestamp=True)
							tmp_timestamp=ts-60*tx_confirmations
							tmp_date_time=app_fun.date2str(datetime.datetime.now()-datetime.timedelta(seconds=60*tx_confirmations) )
							self.insert_history_tx( "outindex_"+str(outindex),tx["txid"],y["blocks"]-tx_confirmations ,tmp_timestamp,tmp_date_time,tmpmemo,aa,tx["amount"],ttype)
						
							if print_debug: print('outindex inserted to history_tx ' )
															
							# dt,ts=app_fun.now_to_str(False,ret_timestamp=True)
							
							dt=init_db.blocks_to_datetime(y["blocks"]-tx_confirmations) # time it was sent 
							
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
									,'block':y["blocks"]-tx_confirmations
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
								tmp_ord[aa][tx["txid"]]=tx_confirmations
								if print_debug: print('added txid to tmp_ord[aa]' )
								
		# idb.update( {'queue_waiting':[{'status':'processing tx\'s done'}]} ,['status'],{'id':[ '=',queue_id ]})
		# self.sending_signal.emit(['cmd_queue'])
		
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
			
		if print_debug2: print('tmp_ord',tmp_ord) # tmp org should only contain not empty msgs found in the loop ... 
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
		
		# if print_debug2: print('for_ord',for_ord)
		if print_debug2: print('sorted_for_ord_keys',sorted_for_ord_keys)
		
		global_db.update( {'queue_waiting':[{'status':'processing\n'+'merging messages'  }]} ,['status'],{'id':[ '=',queue_id ]})
		self.sending_signal.emit(['cmd_queue'])
				
		
		for ss in sorted_for_ord_keys: 
			for conf_ar_txid in for_ord[ss]:
				aa=conf_ar_txid[0]
				txid=conf_ar_txid[1]
				if print_debug2: print('aa txid',aa,txid) 
			
				is_aa_external=aa in self.external_addr
				if print_debug: print('is_aa_external', is_aa_external) # selected txid on aa 
				
				if aa not in table_history_notif:
					if print_debug: print(aa,'not in ',table_history_notif)
					continue
					
				if txid not in table_history_notif[aa]:
					if print_debug: print(txid,'not in ',table_history_notif[aa])
					continue
					
				iis=table_history_notif[aa][txid]
				if print_debug: print('iis',str(iis)[:64]) 
				if True:
					
					kk_ordered=sorted(iis.keys()) 
					init_table=iis[kk_ordered[0]]
					
					if len(kk_ordered)>1:
						for ii in kk_ordered[1:]:
							init_table['tmpmemo']+=iis[ii]['tmpmemo'] #merge memos if multiple outindex and multiple memos 
							init_table['outindex']+=iis[ii]['outindex']
							
					if print_debug: print('init_table',str(init_table)[:64]) 	
							
					table_msg={} # insert only those after first block
					from_str=''
					
					if True: #init_table["block"]>=self.first_block:
						table_msg=self.prep_msgs_inout(txid,[init_table['tmpmemo'],0,''],'in',init_table['date_time'],tx_status='received', in_sign_uid=-2,addr_to=aa ) # -2 to be detected
						
						from_str=table_msg['msgs_inout'][0]['msg']
						# if print_debug: print(606,table_msg,from_str)
						tmpmsg=from_str 
						
						
						
						
						# remove spoofing and add channe lupdate afte owner recognized in msg
						
						
						if print_debug2: print('recognizing channel wal api')
						is_channel=global_db.select('channels',['channel_name','vk'],{'address':['=',"'"+aa+"'"]} ) # check if recognized channel
						# is_abuse=''
						channel_json={}
						if len(is_channel)>0: 
							is_channel=True
							if print_debug2: print('recognizing channel wal api is_channel=True')
							# print(' CHANNEL DETECTED? OWN?',idb.select('channels',['channel_name','own',   'channel_intro'],{'address':['=',"'"+aa+"'"]} ))
							
							# is_channel2 ,channel_json=check_is_channel(tmpmsg) # check if msg has channel definition 
							# if is_channel2  and aa not in self.addr_list:
								
								# is_abuse='\n'.join( ['\n\nCHANNEL ABUSE DETECTED SPOOFING CHANNEL INFO',aa,str(txid),'\n'] )
								# if print_debug: print('is_abuse,tmpmsg\n',is_abuse,tmpmsg)
								# tmpmsg= is_abuse+tmpmsg
							
						else: # if not recognized channel - check if needs registration?
							# print('is_channel=',is_channel)
							is_channel=False # try recognize incoming channel
							if print_debug2: print('recognizing channel wal api is_channel=False',tmpmsg)
							try: 
								is_channel,channel_json=check_is_channel(tmpmsg)
								if print_debug2: print('is_channel,channel_json',is_channel,channel_json)
								
								if is_channel:  # get view key from table :
									vk_list=global_db.select('view_keys', ["vk"],{'address':['=',"'"+aa+"'"]}) # created when importing view keys ... 
									
									# here potential bug ?
									# is view key required?
									# why not here ?
									## this recognizes only imported channel, not own ?
									
									
									
									channel_json['channel_name']=channel_json['channel_name']+'-'+aa[3:6]
									
									
									vkey=''
									if len(vk_list)>0:
										vkey=vk_list[0][0]
									else:
										vk_list=global_db.select('channels', ["vk"],{'address':['=',"'"+aa+"'"]})
										if len(vk_list)>0:
											vkey=vk_list[0][0]
											table={'view_keys':[{'address':aa, 'vk':vkey }]}	
											global_db.upsert(table,[ 'address','vk' ],{'address':['=',"'"+aa+"'"]})
										# print('not recognized own channel vk? taking current',aa[:12],vkey[:55])
										
									is_chnl_own='False'
									chnl_owner=channel_json['channel_owner'] # own channel should be reigistered in creation 
									if aa in self.addr_list:
										is_chnl_own='True' 
									
									table={'channels':[{'address':aa, 'vk':vkey, 'creator':chnl_owner, 'channel_name':channel_json['channel_name'], 'channel_intro':channel_json['channel_intro'], 'status':'active', 'own':is_chnl_own , 'channel_type':channel_json['channel_type']  }]}	
									if print_debug2: print('channel recog:',table)
									global_db.insert(table,['address' , 'vk' , 'creator' , 'channel_name', 'channel_intro' , 'status' , 'own','channel_type' ])
									if 'channels' not in self.to_refresh: self.to_refresh.append('channels') # channels,
									
									if aa in self.external_addr: # change addr book viekey alias category 
								
										table={}
										table['addr_book']=[{'Category':'Channel: '+channel_json['channel_type'],'Alias': channel_json['channel_name'], 'Address':aa, 'ViewKey':vkey, 'viewkey_verif':1,'addr_verif':1 }]  
										global_db.upsert(table,[ 'Category','Alias','Address' , 'ViewKey', 'viewkey_verif','addr_verif' ],{'Address':['=',"'"+aa+"'"]})
										if 'addr_book' not in self.to_refresh: self.to_refresh.append('addr_book') # channels,addr_book
								
							except:
								print("Not proper json channel / wallet api 662",tmpmsg)
								pass
						
						table_msg['msgs_inout'][0]['is_channel']=str(is_channel)
						# if is_abuse!='':
							# table_msg['msgs_inout'][0]['msg']=tmpmsg
							
							
							
							
							
							
						# if print_debug2: 
						# print('wal api inserting msg\n', table_msg )
						# if is channel - add sender to anon addr book to mark same name each time : self name + init hash 
						# if is_channel: # is channel difinition  
						global_db.insert(table_msg,['proc_json','type','addr_ext','txid','tx_status','date_time', 'msg','uid','in_sign_uid','addr_to','is_channel'])
					
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
						
						global_db.insert(table,['opname','datetime','status','details', 'closed','orig_json' ,'uid'])
						if 'notifications' not in self.to_refresh: self.to_refresh.append('notifications') #self.to_refresh=[] channels,addr_book,tx_history,notifications
		
		
		
		# idb.update( {'queue_waiting':[{'status':'done','json':'TX and msgs processing completed'}]} ,['status','json'],{'id':[ '=',queue_id ]})
		# self.sending_signal.emit(['cmd_queue'])	
		 
		global_db.delete_where('queue_waiting',{'id':['=',queue_id ]})
		# print('processing tx done')
		# time.sleep(10)
		self.processing_update_historical_txs=False
		
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
			
			
			
			
	# change 2022  returning with ending ';'	
	def clear_memo(self,initmem):
		tmpmemo=initmem.replace('\\xf6','').replace('\\x00','') #.replace("\0",'') BUG \0
		
		ii=len(tmpmemo)-1
		lastii=ii+1
		while ii>-1:
		
			if tmpmemo[ii]==';':
				
				# lastii=ii
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
				if "rawconfirmations" in jj:
					tmpconf=jj["rawconfirmations"]
				
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
		
		self.update_vk_objects()
		
	def update_vk_objects(self):
	
		tmp_addr_vk=global_db.select('view_keys',['address','vk', 'usage_first_block' ] )
		# print(tmp_addr_vk)
		
		for tt in tmp_addr_vk:
		 
			if tt[1] not in self.view_key_addr_dict:
				self.view_key_addr_dict[tt[1]]=[tt[0]]
			elif tt[0] not in self.view_key_addr_dict[tt[1]]:
				self.view_key_addr_dict[tt[1]].append(tt[0])
					 
			
			# if tt[1] not in self.view_key_list:
				# self.view_key_list.append(tt[1])
				
			if tt[0] not in self.addr_view_key_dict:
				self.addr_view_key_dict[tt[0]]=tt[1]
				
		# try to update addr_viewkey_start:
		# del tt[0] if got block 
		self.addr_viewkey_start={} # delete all and only add none
		for tt in tmp_addr_vk:
			if tt[2]!=None: continue # if got value - pass 
			
			tt2=self.get_first_block(self.view_key_addr_dict[tt[1]] ) # extract from history using  array of addr per vk 
			if tt2==None :
				self.addr_viewkey_start[tt[0]]=tt[1] 
			else:
				table={'view_keys':[{'usage_first_block':tt2}]} 
				global_db.upsert(table,['usage_first_block'],where={'vk':['=',"'"+tt[1] +"'"]}) # separate viewkey table - was insert
				
			# if not in addr_viewkey_start - check if should be - noene start block
			# if on the lsit - check if to delete;/ 
			# tt2=tt[2]
			# if tt2==None:  # try to find in history for any addr associated with vk ; else: update and delete 
				# tt2=self.get_first_block(self.view_key_addr_dict[tt[1]] ) # array of addr per vk 
				# if tt2==None and tt[0] not in self.addr_viewkey_start:
					# self.addr_viewkey_start[tt[0]]=tt[1] 
			
			# if tt[0] in self.addr_viewkey_start and tt2!=None:
				# table={'view_keys':[{'usage_first_block':tt2}]} 
				# global_db.upsert(table,['usage_first_block'],where={'vk':['=','"'+tt[1] +"'"]}) # separate viewkey table - was insert
				# del self.addr_viewkey_start[tt[0]]
		
		
			# if tt[2]==None:  
				# tt2=self.get_first_block(self.view_key_addr_dict[tt[1]] ) # array of addr per vk 
				# if tt2==None: 
					# self.addr_viewkey_start[tt[0]]=tt[1] 
				# elif tt[0] in self.addr_viewkey_start: # update for all addr wih this vk 
					# table={'view_keys':[{'usage_first_block':tt2}]} 
					# global_db.upsert(table,['usage_first_block'],where={'vk':['=','"'+tt[1] +"'"]}) # separate viewkey table - was insert
					# del self.addr_viewkey_start[tt[0]]
			# elif tt[0] in self.addr_viewkey_start:
				# table={'view_keys':[{'usage_first_block':tt[2]}]} 
				# global_db.upsert(table,['usage_first_block'],where={'vk':['=','"'+tt[1] +"'"]}) # separate viewkey table - was insert
				# del self.addr_viewkey_start[tt[0]]
		
		# print('self.addr_list',self.addr_list)
		# print('self.external_addr',self.external_addr)
		
		
	def new_zaddr(self,new_seed='New'):

		try:
		# if True:
			tmpnewaddr=''
			
			if new_seed=='New': 
				# print('creating address from new seed')
				tmpnewaddr=app_fun.run_process(self.cli_cmd,"z_getnewaddresskey ")	
				return str(tmpnewaddr).strip() 
			else: 
				get_pk= global_db.select('priv_keys',['pk'],where={'id':['=',new_seed]},distinct=True)
				# print(get_pk)
				if len(get_pk)>0:
					set_pk_ok=app_fun.run_process(self.cli_cmd,"z_setprimaryspendingkey "+get_pk[0][0])	
					# print('try set primary key to',new_seed,'result',set_pk_ok)					
			
					# print('creating diversified address')
					tmpnewaddr=app_fun.run_process(self.cli_cmd,"z_getnewaddress")		
			
					self.update_all_addr()
					self.address_aliases() # this takes only own addr 
					# self.update_unspent() # this important only for own addr 
					self.any_change.append('z_getnewaddress')
					# self.refresh_wallet()
					return str(tmpnewaddr).strip()
				else:
					return 'no addr exception'
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
			# print('exporting viewkey for zaddr',zaddr)
			return str(app_fun.run_process(self.cli_cmd,"z_exportviewingkey "+zaddr)).strip().replace('\r','').replace('\\n','').replace('\\r','') 
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
		# print("started z_importviewingkey",vkey[:7]+'...','rescan',rescan,'start height',str(startHeight))
		tmpnewaddr=app_fun.run_process(self.cli_cmd,["z_importviewingkey",vkey,rescan,str(startHeight)]) #,zaddr
		# print('finished z_importviewingkey')
		
		if 'error' in tmpnewaddr.lower():
			# if already in the wallet - test: 
			print('error importing view key',tmpnewaddr)
			# print('additional check...')
			# tmparr=self.get_all_txs( zaddr)
			# if 'error' not in str(tmparr):
				# print('... ok - valid - finishing update ... ')
				# return {'address':zaddr, 'type':'sapling'}
		
			return {'error':tmpnewaddr}
		
		# print('updating wallet addresses')
		
		
		
		if tmpnewaddr.strip()=='': # current api vs future api	
			return {'address':zaddr, 'type':'sapling'} #'type' in tmpresult and tmpresult['type']=='sapling':
			
		
		
		tmpresult=json.loads(tmpnewaddr)
		
		table={}
		if 'type' in tmpresult :
			if tmpresult['type'].lower() in ['sapling','z-sapling','zsapling']:
				table['addr_book']=[{ 'viewkey_verif':1 }]
				# vkey update cancell - only update start block on usage 
				# table_vk={'view_keys':[{'address':zaddr, 'vk':vkey}]}
				# arrtmp=['address','vk']
				# if startHeight>1790000: # insert usage_first_block only if realistic value from init usage - not to propagate from import to import if was not yet used 
					# table_vk['view_keys'][0]['usage_first_block']= startHeight
					# arrtmp.append( 'usage_first_block')
					
				# global_db.upsert(table_vk,arrtmp,where={'vk':['=',"'"+vkey+"'"],'address':['=',"'"+zaddr+"'"]}) # separate viewkey table - was insert
		else:
			table['addr_book']=[{ 'viewkey_verif':-1 }]
			
		if table!={}:
			global_db.update(table,[  'viewkey_verif'],{'Address':['=',"'"+zaddr+"'"]}) 
			 
		self.update_all_addr()
		self.any_change.append('z_importviewingkey')
		
		
		
		return tmpresult #future api 
		
		
		 
		# tmpresult={}
		# for rr in aa_pk_blk: # res[addr]={pk:,usage_first_block:}
			# tmpresult[rr[0]]={'pk':rr[1]} #,'usage_first_block':min(rr[2],last_block ) }
			# if rr[2]!=None: tmpresult[rr[0]]['usage_first_block']=rr[2]
	def export_wallet(self):
		retv={}
		aa_pk_blk=global_db.select('priv_keys',['address', 'usage_first_block' ])
		aa_uu={}
		for rr in aa_pk_blk:
			aa_uu[rr[0]]=rr[1]
			
		# print(aa_uu)
		
		for aa in self.addr_list:
			# print('fetching priv key for',aa)
			retv[aa]={'pk':self.exp_prv_key(aa)}
			if aa in aa_uu: retv[aa]['usage_first_block']=aa_uu[aa]
			
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
			return str(app_fun.run_process(self.cli_cmd,["z_exportkey",zaddr])).strip().replace('\r','').replace('\\n','').replace('\\r','') # sometimes giving '\n' in the end 
		except:
			print('wallet api cannot export exp_prv_key')
			return 'cannot export'

		
	def imp_prv_key(self,zkey,rescan="whenkeyisnew",startHeight=996000):

		# print('Importing private key may take a while (rescan) from height '+str(startHeight) )
		
		tmpnewaddr=app_fun.run_process(self.cli_cmd,["z_importkey",zkey,rescan,str(startHeight) ])
		tmpnewaddr_json=json.loads(tmpnewaddr) 
		# print('\n\n\nz_importkey result\n',tmpnewaddr_json)
		# deamon.run_subprocess(self.cli_cmd,"z_importkey "+zkey+rescan+str(startHeight), 64 ) 
		self.update_all_addr()
		self.address_aliases()
		# self.update_unspent()
		
		self.addr_for_full_recalc.append(tmpnewaddr_json['address']) #tmpresult['address']
		self.any_change.append('z_importkey')
		# self.refresh_wallet()
		return tmpnewaddr_json
		# print('Done')


