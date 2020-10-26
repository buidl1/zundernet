# remove transparent - only pirate?
# remove staking
# remove logs ...

import os
import time
import datetime
from termcolor import colored
from pandas import DataFrame
import pandas
import subprocess
import json
import pytz

import re






	

def process_cmd(addr_book,FEE,DEAMON_DEFAULTS,CLI_STR,ucmd):

	currency_name=cur_name(DEAMON_DEFAULTS)

	# ucmd=iop.fix_equal(ucmd)
	
	cmdsplit=ucmd.lower().split()
	
	if "balance"==cmdsplit[0]:
			
		limav='\n\nApp current limit: '+str(get_available_limited_balance(DEAMON_DEFAULTS,currency_name))+'\n'
		
		return get_status(CLI_STR,FEE)+limav	

	elif "balance0"==cmdsplit[0]:
			
		limav='\n\nApp current limit: '+str(get_available_limited_balance(DEAMON_DEFAULTS,currency_name))+'\n'
		
		return get_status(CLI_STR)+limav
		
	elif "valaddr"==cmdsplit[0]: # in ucmd.lower():
		
		if len(cmdsplit)==1:
			return "Address missing"
			
		elif len(cmdsplit)==2:
		
			tmpaddr=cmdsplit[1]
			tmpb,isz=isaddrvalid(CLI_STR,tmpaddr)
			if tmpb:
				return '[VALID ADDR] '+tmpaddr
			else:
				return '[WRONG ADDR ! ! ! ] '+tmpaddr+' NOT VALID !'
			
			
	elif "unspent" ==cmdsplit[0]: # ucmd.lower():	
		
		
		return list_utxo(CLI_STR)
		
	elif "send"==cmdsplit[0]: #  in ucmd.lower():	
	
		amount=get_key_eq_value_x(ucmd,'amount')
		if "is missing in" in amount:
			return amount
		
		if amount.lower()!='all':
			amount=float(amount)
		else:
			amount='all'
			
			
		alias_map=address_aliases(get_wallet(CLI_STR,True))	# can be useful for verifying both addr
		

		addr_to=get_key_eq_value_x(ucmd,'to')
		
		if "is missing in" in addr_to:
			return addr_to
			
		if addr_to in alias_map.values(): # addr_to is alias!alias_map=address_aliases(get_wallet(True))
			print(' alias detected')
			addr_to=aliast_to_addr(alias_map,addr_to)
			
		if addr_to in addr_book.keys():
			addr_to=addr_book[addr_to]
			
		# addr validation
		v12,isz=isaddrvalid(CLI_STR,addr_to)
		
		if v12!=True: 
			return 'addr <to> not valid '+str(addr_to)
			
			
			
			
		addr_from=get_key_eq_value_x(ucmd,'from')
		if "is missing in" in addr_from:
			return addr_from
			
		
		if addr_from in alias_map.values():
			addr_from=aliast_to_addr(alias_map,addr_from)	
			
			
		# addr validation
		v12,isz=isaddrvalid(CLI_STR,addr_from)
		
		if v12!=True: 
			return 'addr <from> not valid '+str(addr_from)
			
		cur_balance=0
		if isz: #v1['isvalid']:
			cur_bal=subprocess.getoutput(CLI_STR+" "+'z_getbalance '+addr_from)
			cur_bal=round(float(cur_bal) ,8)
			if amount=='all':
				amount=round(cur_bal- FEE,8) #0.0001
			elif cur_bal<amount+FEE:
				return "\n TX CANCELLED. Current CONFIRMED balance requested addr is ["+str(cur_bal)+"] <= requested amount of ["+str(amount)+ "] + FEE exceeds the value!"
			
		
		amount=round(amount,8)
			
		if amount<=FEE:
			return 'Amount '+str(amount)+' lower then fee '+str(FEE)+' - wont process it.'
			
		left_balance=0
		
		if amount+FEE<cur_bal:
		
			left_balance=round(cur_bal-amount-FEE,8) # ENSURE LEFT BALANCE IS OK
			
			if left_balance+amount+FEE >cur_bal:
			
				btmp=(left_balance+amount-cur_bal+FEE)
				left_balance=round(left_balance - btmp,8) 
				if left_balance+amount+FEE>cur_bal: # just in case ...
					left_balance=round(left_balance - 0.00000001,8)
					
		memo=get_key_eq_value_x(ucmd,'memo')
		if "is missing in" in memo:
			memo="Sent via Wallet Navigator - github.com/passcombo"
		memo_hex=memo.encode('utf-8').hex()
			
		if isz: #v1['isvalid']:
			if addr_to[0]=='z':
				send_js_str='[{"address":"'+str(addr_to)+'","amount":'+str(amount)+',"memo":"'+str(memo_hex)+'"}]'  
			else:
				send_js_str='[{"address":"'+str(addr_to)+'","amount":'+str(amount)+'}]'
		else:			
			send_js_str='[{"address":"'+str(addr_to)+'","amount":'+str(amount)+'}]'
			
		send_js_str=send_js_str.replace('"','\\"')
		
		tmp_str=CLI_STR+" "+'z_sendmany "' + str(addr_from)+'" "'+send_js_str+'"'
		return 'CONFIRM OPERATION:: '+tmp_str
		
		
		
		
	elif cmdsplit[0]=='confirm':
	
		
	
		tmp_str=ucmd.replace('CONFIRM OPERATION:: '.lower(),'').replace('CONFIRM OPERATION:: ','')
		print('Confirmed command: '+tmp_str)
		tmp=subprocess.getoutput(tmp_str)
		# print(tmp)
		# if isz: #v1['isvalid']:
		time.sleep(7)
		# else:
			# 
			
		checkopstr="z_getoperationstatus "+'[\\"'+str(tmp)+'\\"]'
		opstat=subprocess.getoutput(CLI_STR+" "+checkopstr)
		
		opstat_orig=opstat
		opj=json.loads(opstat)[0]
		opstat=opj["status"]
		
		while "result" not in opj:
			opstat=subprocess.getoutput(CLI_STR+" "+checkopstr)
			print('...need more time ...')
			# print(opstat)
			opstat_orig=opstat
			opj=json.loads(opstat)[0]
			opstat=opj["status"]
			if opstat=="failed":
				
				return 'FAILED\n'+opstat_orig
				
			time.sleep(3)
		
		# print('opstat full\n\n',str(opstat))
		
		txid=''
		# print(opj)
		
		if "txid" in opj["result"]:
			txid=opj["result"]["txid"]
		
		while opstat=="executing":
			print('... processing . .. ... ')
			time.sleep(7)
			checkopstr="z_getoperationstatus "+'[\\"'+str(tmp)+'\\"]'
		
			opstat=subprocess.getoutput(CLI_STR+" "+checkopstr)
			opstat_orig=opstat
			# print(str(opstat))
			opj=json.loads(opstat)[0]
			opstat=opj["status"]
			if "txid" in opj["result"]:
				txid=opj["result"]["txid"]
			
		final_opstat=json.loads(opstat_orig)
		
		if opstat=="success":
			# print(txid)
			if txid!='':
				
				log_txid(txid,currency_name)
			
			limav='\n\nApp current limit: '+str(get_available_limited_balance(DEAMON_DEFAULTS,currency_name))+'\n'
			return 'SUCCESS \n ' +'\n\n'+ get_status(CLI_STR)+limav
		else:
		
			limav='\n\nApp current limit: '+str(get_available_limited_balance(DEAMON_DEFAULTS,currency_name))+'\n'
			return 'FAILED\n'+str(opstat_orig)+'\n\n'+ get_status(CLI_STR)+limav
		
		
		
	elif ucmd.lower()=="newzaddr":
		tmp=subprocess.getoutput(CLI_STR+" "+"z_getnewaddress" )
		return ucmd+" "+str(tmp)
		
	
		
	else:
		print("else")
		return subprocess.getoutput(CLI_STR+" "+ucmd)
	

