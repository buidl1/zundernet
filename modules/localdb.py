# create new .encr storage only when blockchain run was done (wallet file created too)
# otherwise do not save
# and do not write to init - set default create new option / delete last file value 


# Traceback (most recent call last):
  # File "D:\zunqt\zundernet.py", line 279, in upload_settings
    # wata_settings=Settings( wds, init_app )
  # File "D:\zunqt\modules\frame_settings.py", line 147, in __init__
    # grid_db, colnames=update_db_info()
  # File "D:\zunqt\modules\frame_settings.py", line 102, in update_db_info
    # tmpsize_multi=self.db_main.table_size(['jsons','tx_history','notifications','queue_done'])
  # File "D:\zunqt\modules\localdb.py", line 293, in table_size
    # curs=self.connection.cursor()
# sqlite3.ProgrammingError: Cannot operate on a closed database.

# import sqlite3 as sql
import modules.app_fun as app_fun
import modules.aes as aes
import json
import datetime
import time
import queue

	
	
	
class DB:

	
	def init_init(self):
		# idb=DB('init.db')	
		
		table={}
		table['init_settings']={"komodo":'text', "datadir":'text',  "start_chain":'text', "data_files":'text'}
		# table['lock_db_threads']={"lock":'text' }
		# table['busy']={"fun_name":'text','ts':'real' }
		table['block_time_logs']={'uid':'int', 'ttime':'real','block':'int' }
		table['current_session']={'uid':'int', 'datetime':'txt' } # inserted before db decrypt
		
		# self.drop_table('lock_db_threads')
		# nearest_time=self.select_min_val('block_time_logs','ttime',where={'block':['>=', 1377250]} )
		# print('nearest_time',nearest_time)
		
		# zxc=self.select('block_time_logs',['uid' , 'ttime' ,'block' ])
		# for zz in zxc:
			# print('zz',zz)
		# tt=zxc[-1][1]
		# tt2=app_fun.timestamp_to_datetime(tt)
		# bb=zxc[-1][2]
		# print('\n\nblock_time_logs\n\n',tt,tt2,bb,time.time()-tt )
		
		
		self.create_table(table) # creates if not exist 
		
		indexes={}
		# indexes['busy']=[{'idx_name':'busy_idx','cname':['ts','fun_name']}]
		indexes['block_time_logs']=[{'idx_name':'time_logs_idx','cname':['block','ttime']}]
		indexes['block_time_logs'].append({'idx_name':'time_logs_idx2','cname':['ttime']})
		
		self.create_indexes(indexes)
	
	
	
	def init_tables(self, app_db_version): #to update tables and indexes iterate app version db +1
		
		# idb=DB(dbfname)
		
		existing_tables=self.all_tables()
		create_tables=False
		# print('check app version',app_db_version)
		# to=time.time()
		for et in existing_tables:
			# print(et )
			if 'jsons' ==et[1]:
				# print('jsons exist!')
				tmptmp=self.select('jsons',['json_content'],{'json_name':['=',"'app_db_version'"]})
				# print('tmptmp',tmptmp)
				if len(tmptmp)==0:
					# print('init entry app_db_version')
					table={}
					table['jsons']=[{'json_name':'app_db_version', 'json_content':str(app_db_version) }]
					self.insert(table,['json_name','json_content' ]) #,"password_on"
					create_tables=True
				elif tmptmp[0][0]==str(app_db_version):
					# print('do not create tables and indexes')
					create_tables=False
				else:
					# print(' create tables and indexes and update app version ')
					table={}
					table['jsons']=[{'json_content':str(app_db_version) }]
					self.update(table,[ 'json_content' ],{'json_name':['=',"'app_db_version'"]}) #,"password_on"
					create_tables=True
					
				break
		
		# print('all\n',self.select('msgs_inout',[ ],where={'is_channel':['=',"'True'"] , 'addr_to': ['=',"'"+'zs1avkprmlsaumw9kymq2fjhshv0umpqmhx6va4qrx6jz4vylje3fekhn9dcd5pghzdtdg3w60h2lx'+"'"]  } ))
		
		if len(existing_tables)==0: 	create_tables=True	
		# self.drop_table('msgs_inout')
		# self.drop_table('channels')
		# self.drop_table('tx_history')
		# self.drop_table('in_signatures')
		# self.drop_table('notifications')
		# create_tables=True # REMOVE after testing !!!!!!!!!!!!!!!!!!!!!!!
		if not create_tables: return
		# print('hash seeds',self.select( 'out_signatures' ) )
		
		
		
		
		
		table={}
		table['view_keys']={'address':'text', 'vk':'text' }
		table['channels']={'address':'text', 'vk':'text', 'creator':'text', 'channel_name':'text', 'channel_intro':'text', 'status':'text', 'own':'text', 'channel_type':'text' }
		# 2 indexes:
		# indexes['channels']=[{'idx_name':'chnl_idx1','cname':['address' ]}]  
		# indexes['channels'].append({'idx_name':'chnl_idx2','cname':['creator' ]})  
		
		table['address_category']={'address':'text', 'category':'text', 'last_update_date_time':'text' }
		table['deamon_start_logs']={'uid':'int', 'time_sec':'int', 'ttime':'real','loaded_block':'int' }
		table['jsons']={'json_name':'text', 'json_content':'text', 'last_update_date_time':'text' }
		table['wallet_display']={'option':'text', 'value':'text'}
		table['addr_book']={'Category':'text', 'Alias':'text', 'Address':'text','ViewKey':'text','usage':'int','addr_verif':'int','viewkey_verif':'int' }
		table['tx_history']={'uid':'auto','Category':'text', 'Type':'text', 'status':'text','txid':'text','block':'int','timestamp':'real','date_time':'text','from_str':'text','to_str':'text','amount':'real'}
		
		table['notifications']={'datetime':'text','opname':'text','details':'text','status':'text','closed':'text','uid':'auto','orig_json':'text'}
		
		table['out_signatures']={'addr':'text','seed':'text','n':'int'}
		
		table['in_signatures']={'hex_sign':'text','n':'int','addr_from_book':'text','uid':'auto'}
		
		table['channel_signatures']={'addr':'text','signature':'text','uid':'auto'}
		
		table['msgs_inout']={'proc_json':'text','type':'text','addr_ext':'text','txid':'text','tx_status':'text','date_time':'text', 'msg':'text','uid':'auto','in_sign_uid':'int','addr_to':'text','is_channel':'text'}
		
		
		# tmptmp=self.select('tx_history',{'Category':['=',"'send'"]})
		# for ttt in tmptmp:
			# print(ttt)
		# self.drop_table('msgs_inout')
		# self.drop_table('channels')
		# self.drop_table('tx_history')
		# self.drop_table('in_signatures')
		# self.drop_table('addr_book')
		
		table['queue_waiting']={"type":'text' # auto/manual
								
								, "wait_seconds":'int' # max time to wait
								, "created_time":'text' #datetime of creation
								, "command":'text' # send, new wallet, ... 
								, "json":'text' # if needed
								, "id":'int' # uniwue id
								, "status":'text' # waiting/processing/done
								} 
							
		table['queue_done']={"type":'text' # auto/manual
								, "wait_seconds":'int' # max time to wait
								, "created_time":'text' #datetime of creation
								, "command":'text' # send, new wallet, ... 
								, "json":'text' # if needed
								, "id":'int' # unique id
								, "result":'text' # success or failed + reason
								, 'end_time':'text'
								} 
				
		self.create_table(table)

		# else: self.delete_where('queue_done',{'command':[' in ',"('show_bills','new_addr','export_viewkey')"]})
		
		
		# table={'msgs_inout':[{'txid':''}]}
		# self.update( table,['txid'  ], {'date_time':['<', app_fun.today_add_days(-7)], 'proc_json':['=',"'True'"] })
		
		# table={'notifications':[{'details':''}]}
		# self.update( table,['details'  ], {'datetime':['<', app_fun.today_add_days(-7)], 'opname':['=',"'received'"], 'closed':['=',"'True'"]	})
		
		indexes={}
		
		indexes['queue_done']=[{'idx_name':'queue_done_id','cname':['id']}]
		indexes['queue_waiting']=[{'idx_name':'queue_waiting_id','cname':['id','status']}]
		indexes['queue_waiting'].append({'idx_name':'queue_waiting_id','cname':['status','command']})
		
		indexes['addr_book']=[{'idx_name':'addr_book_id','cname':['Address']}]
		
		indexes['deamon_start_logs']=[{'idx_name':'deamon_start_logs_id','cname':['uid']}]
		
		indexes['tx_history']=[{'idx_name':'tx_history_idx_type','cname':['Type','Category']}]
		indexes['tx_history'].append({'idx_name':'tx_history_idx_block','cname':['block']})
		indexes['tx_history'].append({'idx_name':'tx_history_idx_from','cname':['from_str','txid'],'where':{'Category':['=',"'send'"], 'Type':['=',"'out'"]} })
		indexes['tx_history'].append({'idx_name':'tx_history_idx_to','cname':['to_str','txid'],'where':{'Category':['=',"'incoming'"], 'Type':['=',"'in'"]} })
		indexes['tx_history'].append({'idx_name':'tx_history_idx_timestamp','cname':['timestamp']})
		indexes['tx_history'].append({'idx_name':'tx_history_idx_txid','cname':['txid']})
		indexes['tx_history'].append({'idx_name':'tx_history_idx_status','cname':['status']})
		
		
		indexes['out_signatures']=[{'idx_name':'tx_signatures_idx','cname':['addr']}]
		
		indexes['in_signatures']=[{'idx_name':'tx_insignatures_idx','cname':[ 'hex_sign']}]
		
		indexes['msgs_inout']=[{'idx_name':'msg_idx1','cname':['proc_json' ]}]
		indexes['msgs_inout'].append({'idx_name':'msg_idx2','cname':['addr_ext']})
		indexes['msgs_inout'].append({'idx_name':'msg_idx3','cname':['txid' ]})
		indexes['msgs_inout'].append({'idx_name':'msg_idx4','cname':['in_sign_uid']})
		indexes['msgs_inout'].append({'idx_name':'msg_idx5','cname':['addr_to']})
		
		indexes['view_keys']=[{'idx_name':'vk_idx1','cname':['address' ]} ] 
		indexes['channels']=[{'idx_name':'chnl_idx1','cname':['address' ]}]  
		indexes['channels'].append({'idx_name':'chnl_idx2','cname':['creator' ]})  
		
		self.create_indexes(indexes)
		
	
	 
		
		
		
	
	
	

	def get_table_columns(self,tname,add_quotes=True): 
		# print('get_table_columns',self.connected)
		if not self.connected: return []
		
		# fname='get_table_columns'
		# print('fname',fname)
		# this_time=self.add_processing("PRAGMA table_info(__replace__)".replace('__replace__',tname), fname) # sql, fname 
		# print('this_time',this_time,self.processing_queue)
		retv=[]
		
		
		# if self.waitifbusy(this_time) : 
			# self.processing=self.processing_queue[this_time] 
			# print('self.processing',self.processing)
			# curs,conn,ts=self.getcursor( )
			# cc=curs.execute(self.processing['sql'])
			# cc=cc.fetchall()
			# print('cc 239',cc)
			# for c in cc:
				# if add_quotes:
					# retv.append('"'+c[1]+'"')
				# else:
					# retv.append( c[1] )
			
			# del self.processing_queue[this_time] # clear object sql 
			# self.processing_list.remove(this_time) # clear list order 
			# self.processing={'sql':'','fname': '' } # clear processing 
			
		# else:
			# print('Failed waiting ',self.processing_queue[this_time] )
			# print('Failed waitifbusy max iter 100, waiting for ',self.processing)
		
		# curs,conn,ts=self.getcursor( )
		curs=self.connection.cursor()
		curs.execute("PRAGMA table_info(__replace__)".replace('__replace__',tname) )
		cc=curs.fetchall()
		retv=[]
		for c in cc:
			if add_quotes:
				retv.append('"'+c[1]+'"')
			else:
				retv.append( c[1] )
				
		curs.close()
		# self.close_connection(curs,conn,fname,ts)
		
		return retv

		
	def delete_old(self,tname,datetime_colname='created_time',ddays=31):
		if not self.connected: return
		got_date=datetime.datetime.now()- datetime.timedelta(days=ddays)
		
		wwhere={}
		wwhere['datetime('+datetime_colname+')']=['<',"datetime('"+app_fun.date2str(got_date)+"')"]
		self.delete_where( tname,wwhere)
		

	def table_size(self,tname,datetime_colname='created_time'):
	
		# print('\n\ntable_size')
		
		onlyone=False
		if type(tname)==type('str'):
			tname=[tname]
			datetime_colname=[datetime_colname]
			onlyone=True
			
		ret_dict={}
		fname='table_size'
	
		# curs,conn,ts=self.getcursor( )
		curs=self.connection.cursor()
	
		# may jam with other process comming in between column names get and actual query ? 
		#
		#
		# 
		this_time=self.add_processing(fname, fname) # sql, fname 
		if self.waitifbusy(this_time) : 
			for tii,tn in enumerate(tname):
				colnames=self.get_table_columns(tn)
				# print('colnames',colnames)
				
				# if not self.connected: return {}
				
				
				tmpsql='SELECT '+','.join(colnames)+' FROM __replace__'.replace('__replace__',tn)
				
				if not self.sql_init_check( tmpsql,tn): #self.connected:	 
					return {}
			
				# if self.waitifbusy(this_time) : 
				self.processing={'sql':tmpsql,'fname': fname } #self.processing_queue[this_time] 
				
				
				curs.execute(tmpsql)
				cc=curs.fetchall()
				
				
				total_chars=0
				rowsii=0
				old_rows=0
				older_chars=0 # older then 1 month
				ret_dict[tn]={'total_chars':total_chars, 'total_rows':rowsii, 'older_chars':older_chars, 'old_rows':old_rows}
				
				got_date='"'+datetime_colname[tii]+'"' in colnames
				date_index=None
				if got_date:
					got_date=datetime.datetime.now()- datetime.timedelta(days=30)
					date_index=colnames.index('"'+datetime_colname[tii]+'"')
					
					
					
				if len(cc)==0:
					# self.clear_queue( this_time,without_current=True)
					continue
					# return {'total_chars':total_chars, 'total_rows':rowsii, 'older_chars':older_chars, 'old_rows':old_rows}
				# print('cc',cc)
				col_size=[0 for ii in range(len(cc[0])) ]
				for c in cc:
					rowsii+=1
					cur_row_size=0
					mark_row=False
					for jj,ii in enumerate(c):
						tmpsize=len(str(ii))
						col_size[jj]+=tmpsize
						total_chars+=tmpsize
						cur_row_size+=tmpsize
						
						if jj==date_index:
							if got_date!=False:
								if app_fun.datetime_from_str(ii)<got_date:
									mark_row=True
									
					if mark_row:
						old_rows+=1
						older_chars+=cur_row_size
						
				ret_dict[tn]={'total_chars':total_chars, 'total_rows':rowsii, 'older_chars':older_chars, 'old_rows':old_rows}
				# tmp_clear()
				# self.clear_queue( this_time,without_current=True)
				# del self.processing_queue[this_time] # clear object sql 
				# self.processing_list.remove(this_time) # clear list order 
				# self.processing={'sql':'','fname': '' } # clear processing  self.clear_queue( this_time,without_current=True)
				# curs.close()
		else:
			for tii,tn in enumerate(tname):
				ret_dict[tn]={'total_chars':0, 'total_rows':0, 'older_chars':0, 'old_rows':0}
			return ret_dict  #[tn]={'total_chars':-1, 'total_rows':-1, 'older_chars':-1, 'old_rows':-1}
			# print('Failed waiting ',self.processing_queue[this_time] )
			# print('Failed waitifbusy max iter 100, waiting for ',self.processing)	
			# break
		# self.close_connection(curs,conn,fname,ts)
		self.clear_queue( this_time )
		# self.processing={'sql':'','fname': '' } # clear processing 
		curs.close()
		if onlyone: return ret_dict[tname[0]]
		
		return ret_dict # {'total_chars':total_chars, 'total_rows':rowsii, 'older_chars':older_chars, 'old_rows':old_rows}

		
		
	# def db_stats(self):
		# fname='db_stats'
		# curs,conn,ts=self.getcursor(fname)
		
		# curs.execute("SELECT * FROM sqlite_master WHERE type='table'")
		# retv=curs.fetchall()
		
		# for rr in retv:
			
			# print(rr[1])
			# curs.execute("PRAGMA table_info(__replace__)".replace('__replace__',rr[1]) )
			# print(curs.fetchall())
		
			# cc=curs.execute('SELECT * FROM __replace__'.replace('__replace__',rr[1]))
			# cc=cc.fetchall()
			# if len(cc)==0:
				# continue
			
			# total_chars=0
			# rowsii=0
			
			# col_size=[0 for ii in range(len(cc[0])) ]
			# for c in cc:
				# rowsii+=1
				# for jj,ii in enumerate(c):
					# col_size[jj]+=len(str(ii))
					# total_chars+=len(str(ii))
					
			# print('chars of ',rr[1],total_chars,rowsii)
			# print(' ',col_size)

		# self.close_connection(curs,conn,fname,ts)
		


	def __init__(self,dbname, app_db_version, _connection=None ): #='local_storage.db'
	
		self.waiting_request_iterator=0
		self.dbname=dbname # source- either mem or disk - new version memory 
		
		# self.busy=False
		if _connection !=None:
			self.connection=_connection
		else:
			self.connection=sql.connect(self.dbname)
			
		# self.cursor=self.connection.cursor()
		self.connected=True
		self.processing={'sql':'','fname':''} #,'busy':False}
		
		self.processing_queue  = {} # queue.Queue()	#queue_start_stop.put({'cmd':'start_deamon','addrescan':addrescan})
		self.processing_list=[]
		
		self.db_table_columns={}
		if 'init' in dbname : self.init_init() # check anyway and not self.check_table_exist( 'init_settings')
		elif 'local' in dbname  : self.init_tables(app_db_version)
		
		self.db_table_columns=self.all_tables( with_columns=True)
		# print('self.db_table_columns\n',self.db_table_columns)
	
			
		
		
	def commit(self):
		if self.connected:	
			self.connection.commit()	
		
	# maybe not needed ? only close cursor cause conn closed externally 
	# def close_connection(self,curs,conn,fname='',ts=0): # self.close_connection(curs)

		# if self.connected:	
			# self.connection.commit()	
			# self.cursor.close() # self.connection.close()
			# self.connected=False

			
	# def getcursor(self ): #ts=set_busy(fname), del_busy(fname,ts)
	 
		# return self.cursor, self.connection	, 0	 
		
	def clear_queue(self,this_time ): # trick for blocking in iterations / when closing 
		# print('\ndone, clearing',self.processing_queue[this_time])
		del self.processing_queue[this_time] # clear object sql 
		self.processing_list.remove(this_time) # clear list order 
		self.processing={'sql':'','fname': '' } # clear processing if not without_current: 
		
		
		
	def waitifbusy(self, this_time):
		# if not first to process - wait  
		# if self.processing_list[0]!=this_time : # if current is not this one - wait 
		# print('waiting with',self.processing_queue[this_time],'for',self.processing)
		maxiter=100
		while self.processing_list[0]!=this_time: # or self.processing['busy']: # if still busy - wait 
			time.sleep(0.3)
			maxiter-=1
			# print('currently processing',self.processing_list,this_time)
			# print('self.processing_queue',self.processing_queue)
			if maxiter<0: 
				print('Failed waiting ',self.processing_queue[this_time] )
				print('Failed waitifbusy max iter 100, waiting for ',self.processing)	
				self.clear_queue( this_time) # unblock and delete by default on exit for all entries:
				return False
			
		return True
		
		
		
	def add_processing(self, sql, fname):
		if not self.connected:	return
		
		self.waiting_request_iterator+=1
		this_time=self.waiting_request_iterator #time.time_ns() # identity of the process
		# print('self.waiting_request_iterator',self.waiting_request_iterator)
		# print('adding ',this_time,sql,fname, 'to',self.processing_queue)
		self.processing_queue[this_time]={'sql':sql, 'fname': fname}
		self.processing_list.append(this_time)
		# print('after',self.processing_queue,'\n',self.processing_list)
		return this_time 
		
		
		
	def vacuum(self): # tiem should addd uniqueness in other case do rand signature rand_password(self,llen)
		if not self.connected:	
			print('disconnected, rejecting sql', 'vacuum')
			return
		
		this_time=self.add_processing('vacuum', 'vacuum') # sql, fname 
		
		# if this is the first job - process  
		if self.waitifbusy(this_time) : 
		
			self.processing=self.processing_queue[this_time] 
			
			curs=self.connection.cursor() #curs,conn,ts=self.getcursor( )
			curs.execute('vacuum') #self.processing['sql'])
			self.commit()
			
			# del self.processing_queue[this_time] # clear object sql 
			# self.processing_list.remove(this_time) # clear list order 
			# self.processing={'sql':'','fname': '' } # clear processing 
			self.clear_queue( this_time)
			curs.close()
		# else:
			# print('Failed waiting ',self.processing_queue[this_time] )
			# print('Failed waitifbusy max iter 100, waiting for ',self.processing)
			
		
		
	def check_table_exist(self,table): 
	
		if self.db_table_columns=={}: # exception on init app version check 
			# alternative to move check condition to init db from main db 
			# print('check_table_exist init exception')
			return True
	
		if table in self.db_table_columns:
			return True
			
		return False
		
		# fname='check_table_exist'
		# tmpsql="SELECT count(*) FROM sqlite_master WHERE name='"+table+"' AND type='table'"
		
		# if not self.connected:	
			# print('disconnected, rejecting sql', tmpsql)
			# return False
			
		# this_time=self.add_processing(tmpsql, fname)   # print('this_time',this_time)
		# if self.waitifbusy(this_time) : 
		
			# self.processing=self.processing_queue[this_time]  
			
			# curs=self.connection.cursor()  
			# curs.execute(tmpsql)
			# tmpf=curs.fetchone()  
			
			# self.clear_queue( this_time)
			# curs.close()
			
			# if len(tmpf)>0 and tmpf[0]==1:  
				# return True 
			# return False 
		
		# return False
			
			
	# for easy debug purpsoe		
	def sql_init_check(self,tmpsql,tname):
	
		if not self.connected:	
			# print('disconnected, rejecting sql', tmpsql)
			return False
			
		if not self.check_table_exist(tname):#tname not in self.db_table_columns:
			print('wrong db? table not exists', tname, tmpsql)
			print('self.dbname',self.dbname)
			return False
			
		return True
		
		
		
	def drop_table(self,tname):  
		fname='drop_table'
		tmpsql="drop table if exists "+tname
		
		if not self.sql_init_check( tmpsql,tname): #self.connected:	 
			return
			
		this_time=self.add_processing(tmpsql, fname)  
		 
		if self.waitifbusy(this_time) : 
		
			self.processing=self.processing_queue[this_time] 
			
			curs=self.connection.cursor() #curs,conn,ts=self.getcursor( )
			curs.execute(tmpsql)
			self.commit()
			
			# del self.processing_queue[this_time] # clear object sql 
			# self.processing_list.remove(this_time) # clear list order 
			# self.processing={'sql':'','fname': '' } # clear processing 
			self.clear_queue( this_time)
			curs.close()
		# else:
			# print('Failed waiting ',self.processing_queue[this_time] )
			# print('Failed waitifbusy max iter 100, waiting for ',self.processing)	
			
	
	
	def create_indexes(self,indexes): 
		fname='create_index_s'
		tmpsql='create indexes'
		
		
		if not self.connected:	
			print('disconnected, rejecting sql', tmpsql)
			return
			
		this_time=self.add_processing(tmpsql, fname)  
		 
		if self.waitifbusy(this_time) : 
		
			self.processing=self.processing_queue[this_time] 
			
			curs=self.connection.cursor() #curs,conn,ts=self.getcursor( )
			for kk,vva in indexes.items():
				# print(kk,vva)
				for vv in vva:
					# print(kk)
					str_tmpl="CREATE INDEX IF NOT EXISTS _index_name_ ON _table_name_ (_columns_)".replace('_index_name_',vv['idx_name']).replace('_table_name_',kk)
					str_tmpl=str_tmpl.replace('_columns_', ','.join(vv['cname'])) 
					if 'where' in vv:
						str_tmpl+=self.add_where(vv['where'])
						
					# check before each exec 
					if not self.connected:	
						print('disconnected, rejecting sql', tmpsql) 
						self.commit()
						self.clear_queue( this_time)
						curs.close()
						return 
						
					curs.execute(str_tmpl)
			
			self.commit()
			
			self.clear_queue( this_time)
			curs.close()
			
		
	
	def create_index(self,tname,idx_name='',cname=[],where={}):	
		str_tmpl="CREATE INDEX IF NOT EXISTS _index_name_ ON _table_name_ (_columns_)".replace('_index_name_',idx_name).replace('_table_name_',tname)
		str_tmpl=str_tmpl.replace('_columns_', ','.join(cname))+self.add_where(where)
		fname='create_index'
		tmpsql=str_tmpl
		
		
		if not self.sql_init_check( str_tmpl,tname):
			return 
						
		# if not self.connected:	
			# print('disconnected, rejecting sql', tmpsql)
			# return
			
		this_time=self.add_processing(tmpsql, fname)  
		
		if self.waitifbusy(this_time) : 
		
			self.processing=self.processing_queue[this_time] 
			
			curs=self.connection.cursor() #curs,conn,ts=self.getcursor( )
			curs.execute(tmpsql)
			self.commit() 
			
			self.clear_queue( this_time)
			curs.close()
			
		
		
	def create_table(self,table): 
		
		fname='create_table'
		tmpsql=str(table.items())
		
		if not self.connected:	
			print('disconnected, rejecting sql', tmpsql)
			return
			
		this_time=self.add_processing(tmpsql, fname)  	
		
		if self.waitifbusy(this_time) : 
		
			self.processing=self.processing_queue[this_time] 
			
			curs=self.connection.cursor() #curs,conn,ts=self.getcursor( )
			# print("CREATE TABLE IF NOT EXISTS ",self.processing_queue[this_time] )
			
			for k,v in table.items():
			
				tmparr=['"'+k2+'" "'+v2+'"' for k2,v2 in v.items()]
				
				sql_str="CREATE TABLE IF NOT EXISTS "+k+' ('+','.join(tmparr)+')'

				curs.execute(sql_str)
					
				colnames=self.get_table_columns( k,False)
				
				for vi,vii in v.items():
					if vi not in colnames:
						sql_str="ALTER TABLE "+k+' ADD COLUMN '+vi+' '+vii
						curs.execute(sql_str)
					
					
			self.commit() 
			self.clear_queue( this_time)
			curs.close()	
		
		
	
	def all_tables(self, with_columns=False):

		fname='all_tables'
		tmpsql="SELECT * FROM sqlite_master WHERE type='table'"
		
		if not self.connected:	
			print('disconnected, rejecting sql', tmpsql)
			return []

		this_time=self.add_processing(tmpsql, fname)  	
		
		retv=[]
		if self.waitifbusy(this_time) : 
		
			self.processing=self.processing_queue[this_time] 
			
			curs=self.connection.cursor() #curs,conn,ts=self.getcursor( )
			curs.execute(tmpsql)
			self.clear_queue( this_time)
			retv=curs.fetchall()
			curs.close()
			
		if with_columns:
			ret_dict={}
			for tt in retv:
				tname=tt[1]
				cc=self.get_table_columns(tname, add_quotes=False)
				ret_dict[tname]=[c  for c in cc]
				
			return ret_dict
		
		return retv
		
		
	def delete_where(self,table_name,where={}):

		fname='delete_where'
		tmpsql="delete from "+table_name+self.add_where(where)
		
		if not self.sql_init_check( tmpsql,table_name): #self.connected:	 
			return
		# if not self.connected:	
			# print('disconnected, rejecting sql', tmpsql)
			# return
		

		this_time=self.add_processing(tmpsql, fname)  	
		
		
		if self.waitifbusy(this_time) : 
		
			self.processing=self.processing_queue[this_time] 
			
			curs=self.connection.cursor() #curs,conn,ts=self.getcursor( )
			curs.execute(tmpsql)
			self.commit()  
			self.clear_queue( this_time)
			curs.close() 
			 

	# messages are the same, datetime is different
	# orig msg from creator missing
	# some process doing badly update ? with where missing ???
	
	
	def upsert(self,table,items_order,where={}): #={'json_name':['=',tmp_max_val]}
		if table=={}:
			print('\n\n! ! ! EMPTY UPSERT TABLE!!!!!\n\n')
			return
	
		tname=list(table.keys())
		tname=tname[0] 
		cc=self.count(tname,where) 
		if cc[0][0]==0: #len(cc)>0 and 
			# print('inserting ...')
			self.insert(table,items_order)
		elif cc[0][0]==1:
			self.update(table,items_order,where)
		else:
			print(cc[0][0],' upsert more then 1 - exception!?',tname,where)
			# self.update(table,items_order,where)
		
		
		
	def adj_old_edge(self,tt):
		if tt[0]=="'" or tt[0]=='"':
			tt=tt[1:]
		if tt[-1]=="'" or tt[-1]=='"':
			tt=tt[:-1]
		return tt
		
		
	
	def add_where_new(self,where_dict):
	
		sqlstr=''
		vtuple=[]
		vwhere=[]
		if len(where_dict)>0:
			for k2,v2 in where_dict.items():
				
				
				tmpw=k2 +str(v2[0])+'?'
				if 'in' in v2[0].lower():
					tmpsplit=v2[1].replace('(','').replace(')','').split(',')
					
					tmpw=k2 +str(v2[0])+'('+ ', '.join(['?' for ii in range(len(tmpsplit))]) +')'
					
					for tt in tmpsplit: 
						if type(tt)==type('asdf'):
							tt=self.adj_old_edge(tt)
							
						try:
							int(tt)
							vtuple.append( int(tt))
						except:
							
							vtuple.append( tt )
					
				else:
					tt=v2[1]
					if type(tt)==type('asdf'):
						tt=self.adj_old_edge( tt )
					vtuple.append(tt)
				
				vwhere.append(tmpw)
		
			sqlstr=' where '+ ' and '.join(vwhere)
			
		return sqlstr,vtuple
		
		
	def update(self,table,items_order,where):
		if table=={}:
			print('\n\n! ! ! EMPTY UPSERT TABLE!!!!!\n\n')
			return

		tname=list(table.keys())
		tname=tname[0]
		fname='update'
		tmpsql=tname
		
		if not self.sql_init_check( tmpsql,tname): #self.connected:	 
			return
		# if not self.connected:	
			# print('disconnected, rejecting sql', tmpsql)
			# return
		

		this_time=self.add_processing(tmpsql, fname)  	
		
		
		if self.waitifbusy(this_time) : 
		
			self.processing=self.processing_queue[this_time] 
			
			curs=self.connection.cursor() #curs,conn,ts=self.getcursor( )
			
			if 'uid' in items_order:
				items_order.remove('uid')
			
			for rr in table[tname]:
			
				update_str='update '+tname+' set '+', '.join([ io+'=?' for io in items_order]) 
				vtuple=[rr[io] for io in items_order]
				
				strwhere,vtup=self.add_where_new(where)
				
				update_str+=strwhere
				vtuple=tuple(vtuple+vtup) 
				# print('updating',update_str, vtuple)
				curs.execute(update_str, vtuple)
			
			self.commit() 
			
			# del self.processing_queue[this_time] # clear object sql 
			# self.processing_list.remove(this_time) # clear list order 
			# self.processing={'sql':'','fname': '' } # clear processing 
			self.clear_queue( this_time)
			curs.close()
		# else:
			# print('Failed waiting ',self.processing_queue[this_time] )
			# print('Failed waitifbusy max iter 100, waiting for ',self.processing)	
			
		
		
		
	
	def insert(self,table,items_order): 
		if table=={}:
			print('\n\n! ! ! EMPTY UPSERT TABLE!!!!!\n\n')
			return []
			
		fname='insert'
		tname=list(table.keys())
		tname=tname[0]
		
		sqlstr="insert into "+tname+"("+','.join(items_order)+") values ("+','.join(['?' for ii in items_order])+")"
		tmpsql=sqlstr
			
		
		if not self.sql_init_check( tmpsql,tname): #self.connected:	 
			return []
		# if not self.connected:	
			# print('disconnected, rejecting sql', tmpsql)
			# return []
			
		max_val=0
		if 'uid' in items_order:
			
			tmp_max_val=self.select_max_val(tname,'uid' )
			# print('before inserting',items_order,tname,'tmp_max_val',tmp_max_val)
			
			if len(tmp_max_val)>0 and tmp_max_val[0][0]!=None:
				max_val=tmp_max_val[0][0]+1
		
		# print('max_val',max_val)
		this_time=self.add_processing(tmpsql, fname)  	
		
		
		ret_uids=[]
		if self.waitifbusy(this_time) : 
		
			self.processing=self.processing_queue[this_time] 
			
			curs=self.connection.cursor() #curs,conn,ts=self.getcursor( ) 
			# print('inserting',sqlstr )
			
			# max_val=0
			if 'uid' in items_order:
				# tmp_max_val=self.select_max_val(tname,'uid' )
				
				# if tmp_max_val[0][0]!=None:
					# max_val=tmp_max_val[0][0]+1
				
				iter=0
				for rr in table[tname]:
					
					ret_uids.append(max_val+iter)
					tmpval=tuple( max_val+iter if io=='uid' else rr[io] for io in items_order)
					# print('     ins ',sqlstr,tmpval)
					curs.execute(sqlstr,tmpval)
					iter+=1
					
			else:
				
				for rr in table[tname]:
				
					tmpval=tuple(rr[io] for io in items_order)
					# print('     ins ',sqlstr,tmpval)
					curs.execute(sqlstr,tmpval)
					
			self.commit() 
			
			# del self.processing_queue[this_time] # clear object sql 
			# self.processing_list.remove(this_time) # clear list order 
			# self.processing={'sql':'','fname': '' } # clear processing 
			self.clear_queue( this_time)
			curs.close()
			
		# else:
			# print('Failed waiting ',self.processing_queue[this_time] )
			# print('Failed waitifbusy max iter 100, waiting for ',self.processing)		
			
			
		return ret_uids
		
	
	
	
	
	def select_min_val(self,table_name,column,where={},groupby=[]):
		fname='select_min_val'
		
		sqlstr='select min("'+column+'") as mmin from '+table_name
		if len(groupby)>0:
			tmpcol=','.join([gg if gg[0]=='"' else '"'+gg+'"' for gg in groupby])
			sqlstr=sqlstr.replace('min("',tmpcol+', min("') + ' group by '+tmpcol
			sqlstr='select * from ('+sqlstr+') as xx order by mmin desc'
			
		sqlstr+=self.add_where(where)
		
		tmpsql=sqlstr
			
		# if not self.connected:	
			# print('disconnected, rejecting sql', tmpsql)
			# return []
		
		if not self.sql_init_check( tmpsql,table_name): #self.connected:	 
			return	[]
		
		this_time=self.add_processing(tmpsql, fname)  	
		
		# testing
		
		
		
		retv=[]
		if self.waitifbusy(this_time) : 
		
			self.processing=self.processing_queue[this_time] 
			
			curs=self.connection.cursor() #curs,conn,ts=self.getcursor( ) 
			
			curs.execute(sqlstr)
			retv=curs.fetchall()
			# del self.processing_queue[this_time] # clear object sql 
			# self.processing_list.remove(this_time) # clear list order 
			# self.processing={'sql':'','fname': '' } # clear processing 
			self.clear_queue( this_time)
			curs.close()
		# else:
			# print('Failed waiting ',self.processing_queue[this_time] )
			# print('Failed waitifbusy max iter 100, waiting for ',self.processing)		
			
		return retv
		
		
		
	def select_max_val(self,table_name,column,where={},groupby=[],_limit=0, _ord_by=[]): # _ord_by - ii of col from max val 
		fname='select_max_val'
				
		sqlstr=''
		
		if type(column)==type('asdf'):
			sqlstr='select max("'+column+'") as mmax from '+table_name+' '
		else:
			sqlstr='select ' + ','.join([' max("'+cc+'") as mmax'+str(jj) for jj,cc in enumerate(column)] )+' from ' + table_name+' '
			
		if len(where)>0:
			sqlstr+=self.add_where(where)
		
		if len(groupby)>0:
			tmpcol=','.join([gg if gg[0]=='"' else '"'+gg+'"' for gg in groupby])
			sqlstr=sqlstr.replace('select ','select '+tmpcol+', ') + ' group by '+tmpcol
			
			if type(column)==type([]):
				ord_arr=[' mmax'+str(jj)+' desc' for jj,cc in enumerate(column)]
				
				if len(_ord_by)>0:
					
					try:
						ord_arr=[]
						for jj in _ord_by:
							if jj<len(column):
								ord_arr.append(' mmax'+str(jj)+' desc')
						# ord_arr=[' mmax'+str(jj)+' desc' for jj in _ord_by )]
						# ord_arr=[' mmax'+str(jj)+' desc' for jj,cc in enumerate([column[_ord_by])]
					except:
						print('error order by ',_ord_by,column)
						return []
						
				
				sqlstr='select * from ('+sqlstr+') as xx order by '+','.join(ord_arr ) #[' mmax'+str(jj)+' desc' for jj,cc in enumerate(column)] 
			else:
				sqlstr='select * from ('+sqlstr+') as xx order by mmax desc' # case when str passed not aray - single value 
				
		if _limit>0:
			sqlstr+=' limit '+str(_limit)
				
				
		tmpsql=sqlstr
		# print(tmpsql)
		
		if not self.sql_init_check( tmpsql,table_name): #self.connected:	 
			return	[]
		# if not self.connected:	
			# print('disconnected, rejecting sql', tmpsql)
			# return []
			
		this_time=self.add_processing(tmpsql, fname)  
		
		retv=[]
		if self.waitifbusy(this_time) : 
		
			self.processing=self.processing_queue[this_time] 
			
			curs=self.connection.cursor() #curs,conn,ts=self.getcursor( ) 
			curs.execute(sqlstr)
			retv=curs.fetchall()
			# del self.processing_queue[this_time] # clear object sql 
			# self.processing_list.remove(this_time) # clear list order 
			# self.processing={'sql':'','fname': '' } # clear processing 
			self.clear_queue( this_time)
			curs.close()
		# else:
			# print('Failed waiting ',self.processing_queue[this_time] )
			# print('Failed waitifbusy max iter 100, waiting for ',self.processing)		
			
		return retv
		
		
	# combined sql may be problematic?
	# another sql may come in the middle ?
	
	def select_last_val(self,tname,column): # by default max uid value
		
		if not self.sql_init_check( 'select_max_val',tname ): #self.connected:	 
			return None
			
		# if not self.connected:	
			# print('disconnected, rejecting sql', tmpsql)
			# return None
			
		tmp_max_val=self.select_max_val(tname,'uid' )
		if len(tmp_max_val)==0:
			return None
			
		tmp_max_val=tmp_max_val[0][0]
		
		if tmp_max_val==None:
			return None
		
		retv=self.select(tname,[column],where={'uid':['=',tmp_max_val]})
		
		return retv[0][0]
		
		
	def add_where(self,where_dict): # either 'is_channel':['=',"'False'"] or OR  'is_channel':[ ['=',"'False'"], [' is ','null']]
	
		sqlstr=''
		if len(where_dict)>0:
			# whrstr=[ k2 +str(v2[0])+str(v2[1]) for k2,v2 in where_dict.items()]
			whrstr=[]
			for k2,v2 in where_dict.items():
				tmpw=''
				if type(v2[0])==type([]): # join in () example 'is_channel':[ ['=',"'False'"], [' is ','null']]
					tmpwa=[ k2 +str(v[0])+str(v[1]) for v in v2]
					tmpw=' ( '+' or '.join(tmpwa)+' ) '
				else:
					tmpw=k2 +str(v2[0])+str(v2[1])
				
				whrstr.append(tmpw)
				
			sqlstr+=' where '+' and '.join(whrstr)
			
			
		return sqlstr
	
	
	def count(self,table_name,where={}):
	
		fname='count'
		sqlstr='select count(*) from '+table_name
		
		sqlstr+=self.add_where(where)
		tmpsql=sqlstr
		
		if not self.sql_init_check( tmpsql,table_name): #self.connected:	 
			return [0]
			
		# if not self.connected:	
			# print('disconnected, rejecting sql', tmpsql)
			# return [0]
			
		retv=[0]
		this_time=self.add_processing(tmpsql, fname)  
		
		# retv=[]
		if self.waitifbusy(this_time) : 
		
			self.processing=self.processing_queue[this_time] 
			
			curs=self.connection.cursor() #curs,conn,ts=self.getcursor( ) 
			curs.execute(sqlstr)
			retv=curs.fetchall()
			# print('count result',retv)
			# del self.processing_queue[this_time] # clear object sql 
			# self.processing_list.remove(this_time) # clear list order 
			# self.processing={'sql':'','fname': '' } # clear processing 
			self.clear_queue( this_time)
			curs.close()
		# else:
			# print('Failed waiting ',self.processing_queue[this_time] )
			# print('Failed waitifbusy max iter 100, waiting for ',self.processing)		
			
		return retv
	
	
	# Failed waitifbusy max iter 100, waiting for  {'sql': 'select  "komodo","datadir","data_files" from init_settings', 'fname': 'select'}	
	
	def select(self,table_name,columns=[],where={},orderby=[],distinct=False, limit=''): 
		
		fname='select'
		
		dist=''
		if distinct: dist='distinct'
		
		sqlstr='select '+dist+' * from '+table_name
		if len(columns)>0:
			columns=['"'+cc+'"' for cc in columns]
			sqlstr=sqlstr.replace('*', ','.join(columns))
			
		sqlstr+=self.add_where(where)
		
		if len(orderby)>0:
			sqlstr+='\n order by '
			
			sqlstr+=','.join([ k+' '+v for dd in orderby for k,v in dd.items()])
			
		if limit!='':
			sqlstr+=' limit '+str(limit)
			
		tmpsql=sqlstr
		
		
		if not self.sql_init_check( tmpsql,table_name): #self.connected:	 
			return [ ]
			
		# if not self.connected:	
			# print('disconnected, rejecting sql', tmpsql)
			# return []
		
		retv=[]
		this_time=self.add_processing(tmpsql, fname)  
		
		retv=[] 
		if self.waitifbusy(this_time) : 
			# print('in ')
			self.processing=self.processing_queue[this_time] 
			
			# curs,conn,ts=self.getcursor( ) 
			curs=self.connection.cursor() #
			curs.execute(sqlstr)
			retv=curs.fetchall()
			# del self.processing_queue[this_time] # clear object sql 
			# self.processing_list.remove(this_time) # clear list order 
			# self.processing={'sql':'','fname': '' } # clear processing 
			self.clear_queue( this_time)
			curs.close()
		# else:
			# print('Failed waiting ',self.processing_queue[this_time] )
			# print('Failed waitifbusy max iter 100, waiting for ',self.processing)		
			
		return retv
		
	

# now local connections left - replace with global connections objects !	
	
	
	
	
	# idb= DB('init.db')
	def blocks_to_datetime(self, blknr):
		
		if 'init' not in self.dbname:
			print('wrong DB! blocks_to_datetime')
			return app_fun.now_to_str(False)
			
			
		nearest_time=self.select_min_val('block_time_logs','ttime',where={'block':['>=',blknr]} )
		if len(nearest_time)>0:
			if nearest_time[0][0]!=None:
		
				nearest_block=self.select_min_val('block_time_logs','block',where={'block':['>=',blknr]} )
				
				dt=app_fun.timestamp_to_datetime(nearest_time[0][0]) + datetime.timedelta( minutes=blknr-nearest_block[0][0] )
				
				return app_fun.date2str(dt)
				
		return app_fun.now_to_str(False)


	
	
	
	# for  not init 
	def set_que_waiting( self, command,jsonstr='', wait_seconds=0):
		# initdb= DB('init.db')
		# tt= initdb.select('init_settings',columns=["data_files"]) 
		
		# dbname=json.loads(tt[0][0])
		# dbname=dbname['db']+'.db'
		
		# idb=DB(dbname)
		# if 'init' not in self.dbname:
			# print('wrong DB! set_que_waiting')
			
			
		tmparr=[0]
		latestid1=self.select_max_val( 'queue_done','id' )
		if len(latestid1)>0: 
			
			if latestid1[0][0]!=None:
				tmparr.append(latestid1[0][0])
			
		latestid2=self.select_max_val( 'queue_waiting','id')
		if len(latestid2)>0: 

			if latestid2[0][0]!=None:
				tmparr.append(latestid2[0][0])
		
		nextid=max(tmparr)+1
		
		return {"type":'manual'
				, "wait_seconds":wait_seconds # max time to wait
				, "created_time":app_fun.now_to_str(False) #datetime of creation
				, "command":command # send, new wallet, ... 
				, "json":jsonstr # if needed
				, "id":nextid # uniwue id
				, "status":'waiting' 
				}	


				
				
	def get_addr_to_hash(self, addrto,onlylentest=False):
		# addrto='ANY' #overwrite to have a common one !
		# not good sinceending will replace only for a single one not all addr that can recognize it ... 
		# would require to publish to a special channel public signatures that it was changed ... then sync in a proper order ... 

		# initdb= DB('init.db')
		# tt= initdb.select('init_settings',columns=["data_files"]) 
		# dbname=json.loads(tt[0][0])
		# dbname=dbname['db']+'.db'

		# idb= DB(dbname)
		tmpsign=self.select( 'out_signatures',['seed','n'], {'addr':['=',"'"+addrto+"'"], 'n':['>',0]}, orderby=[{'n':'asc'}] )
		# tmpsign=idb.select( 'out_signatures',['seed','n'], { 'n':['>',0]}, orderby=[{'n':'asc'}] )
		# db_sign=idb.select_last_val('channel_signatures','signature')
		
		if onlylentest:
			if len(tmpsign)==0:
				return 1+33+1+2+1
			else:
				if tmpsign[0][1]==1:
					return 1+33+1+2+1+33+1+2+1
				else:
					return 1+33+1+2+1
		
		cc=aes.Crypto(hashalgo=224)
		
		def create_new_seed():
			nmax=126*126-1
			init_seed=cc.init_hash_seed()
			first_hash=cc.hash2utf8_1b(init_seed,nmax)
			table={}
			table['out_signatures']=[{'addr':addrto,'seed':init_seed,'n':nmax-1}]
			self.insert(table,['addr' ,'seed' ,'n' ])
			
			return first_hash,nmax
			
			
		if len(tmpsign)==1:
		
			next_hash=cc.hash2utf8_1b(tmpsign[0][0],tmpsign[0][1])
			table={}
			table['out_signatures']=[{ 'n':tmpsign[0][1]-1}]
			self.update(table,[ 'n' ],{'addr':['=',"'"+addrto+"'"]})
			
			if tmpsign[0][1]==1:
				first_hash,nmax=create_new_seed()
				return '\n'+next_hash+';'+cc.int_to_utf8_1b(tmpsign[0][1])+';'+first_hash+';'+nmax+';'
			else:
				return '\n'+next_hash+';'+cc.int_to_utf8_1b(tmpsign[0][1])+';'
		
		else: 
			first_hash,nmax=create_new_seed()

			return '\n'+first_hash+';'+cc.int_to_utf8_1b(nmax)+';'
			
		

# if only 1 addr >0 disp_dict['wl'] {'addr':aa,'confirmed': amount_init, 'unconfirmed': am_unc,'#conf':cc_conf,'#unconf':cc_unc }

	def get_default_addr(self):	
		# initdb= DB('init.db')
		# tt= initdb.select('init_settings',columns=["data_files"]) 
		# dbname=json.loads(tt[0][0])
		# dbname=dbname['db']+'.db'
		
		# idb= DB(dbname)
		disp_dict=self.select('jsons',['json_content','last_update_date_time'],{'json_name':['=',"'display_wallet'"]})
		if len(disp_dict)>0:
			disp_dict=json.loads(disp_dict[0][0])
			ready_addr=''
			for rr in disp_dict['wl']:
				if rr['confirmed']+rr['unconfirmed']>=0.0001:
					if ready_addr=='':
						ready_addr=rr['addr']
					else:
						return '...' # if more then 1
						
			return ready_addr
				
		return '...'		

	
	



	def get_last_addr_from(self,ttype):  # ttype "'last_book_from_addr'", "'last_msg_from_addr'"
		# initdb= DB('init.db')
		# tt= initdb.select('init_settings',columns=["data_files"]) 
		# dbname=json.loads(tt[0][0])
		# dbname=dbname['db']+'.db'
		
		# idb= DB(dbname)
		rr=self.select('jsons',['json_content' ],{'json_name':['=',ttype]} )
		
		if len(rr)>0:
			disp_dict=json.loads(rr[0][0])
			return disp_dict['addr']
		else:
			return get_default_addr()
		

	def set_last_addr_from(self, addr, ttype):  # ttype "'last_book_from_addr'", "'last_msg_from_addr'"
		if addr=='':
			return
			
		# initdb= DB('init.db')
		# tt= initdb.select('init_settings',columns=["data_files"]) 
		# dbname=json.loads(tt[0][0])
		# dbname=dbname['db']+'.db'
			
		# idb= DB(dbname)
		table={'jsons':[{'json_content':json.dumps({'addr':addr}), 'json_name':ttype.replace("'","")}]}
		self.upsert(table,['json_content','json_name' ],{'json_name':['=',ttype]} )


	#####################
	### needed for 	wallet_display_set.py got_bad_char, msg_arr=global_db.prep_msg(msg,addr)
		

	def get_msg_parts(self, mm):	

		def splitutf8_512bytes(mm):

			if len(mm.encode('utf-8') )<513:
				return [mm ,len(mm.encode('utf-8') )], ''
				
			cur_ii=len(mm)//2
			cur_vv=len(mm[:cur_ii].encode('utf-8') )
			cur_step=cur_ii
			cur_diff=512-cur_vv
			tmpabs=abs(cur_diff)
			
			while cur_vv>511 or tmpabs>4:
			
				if tmpabs>cur_step:
					new_step=max(min(cur_step//2+1,tmpabs),1)
				else:
					new_step=max(min(cur_step//2,tmpabs),1)
					
				if new_step<cur_step:
					cur_step=new_step
					
				if cur_diff==0:
					break
				
				elif cur_diff<0:
					cur_ii=cur_ii-cur_step
				else:
					cur_ii=cur_ii+cur_step
					
				cur_vv=len(mm[:cur_ii].encode('utf-8') )
				new_diff=512-cur_vv
				
				cur_diff=new_diff
				tmpabs=abs(cur_diff)

			return [mm[:cur_ii],cur_vv], mm[cur_ii:]

			
		ar=[]

		while len(mm)>0:
			m1,mm=splitutf8_512bytes(mm)
			ar.append(m1)
			
		return ar





	def prep_msg(self, mm,addr):
			
		got_bad_char=False
		total_bytes=0
		
		try:
			total_bytes=len(mm.encode('utf-8')) #sys.getsizeof(mm.encode('utf-8'))
		
		except:
			badc=''
			bad_ii=-1
			for ii,cc in enumerate(mm):
				try:
					cc.encode('utf-8')
				except:
					badc=cc
					bad_ii=ii
					got_bad_char=True
					break
			
			# gui.showinfo('Bad character in memo input', 'This input contains bad character ['+badc+']:\n'+mm+'\n position: '+str(bad_ii))
			return got_bad_char, ['Bad character in memo input', 'This input contains bad character ['+badc+']:\n'+mm+'\n position: '+str(bad_ii)]
			
		msg_parts= get_msg_parts(mm)
		tmpsignature= get_addr_to_hash(addr)
		
		if msg_parts[-1][1]+len(tmpsignature)<513:
			msg_parts[-1]=[msg_parts[-1][0]+tmpsignature , msg_parts[-1][1]+len(tmpsignature) ]
		else:
			msg_parts.append([tmpsignature,len(tmpsignature)])
			
		msg_parts=[mm[0] for mm in msg_parts]
		
		return got_bad_char, msg_parts
