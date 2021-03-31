
# add solution to easy update columns in db 
# check if table exist
# check if columns exist 

import sqlite3 as sql
import modules.app_fun as app_fun
import modules.aes as aes
import json
import datetime
import time

def init_init():
	idb=DB('init.db')	
	
	table={}
	table['init_settings']={"komodo":'text', "datadir":'text',  "start_chain":'text', "data_files":'text'}
	table['lock_db_threads']={"lock":'text' }
	table['busy']={"fun_name":'text','ts':'real' }
	table['block_time_logs']={'uid':'int', 'ttime':'real','block':'int' }
	
	idb.create_table(table) # creates if not exist 
	
	indexes={}
	indexes['busy']={'idx_name':'busy_idx','cname':['ts','fun_name']}
	indexes['block_time_logs']={'idx_name':'time_logs_idx','cname':['block','ttime']}
	indexes['block_time_logs']={'idx_name':'time_logs_idx2','cname':['ttime']}
	
	idb.create_indexes(indexes)
	
	

def check_local_storage_not_encrypted():
	
	idb=DB('init.db')	
	
	tmp=idb.select('lock_db_threads',['lock'])
	
	if tmp[0][0]=='yes':
		return False # exit query 
		
	return True # proceed
	
	
def set_busy(fname): # ts=set_busy(fname), del_busy(fname,ts)
	idb=DB('init.db')
	ts=time.time()
	curs,conn,ts2=idb.getcursor()
	
	sqlstr="insert into busy (fun_name,ts) values (?,?)"
	curs.execute(sqlstr,(fname,ts))
	idb.close_connection(curs,conn)
	return ts

def del_busy(fname,ts):
	idb=DB('init.db')
	curs,conn,ts2=idb.getcursor()
	
	sqlstr="delete from busy where fun_name=? and ts=?"
	curs.execute(sqlstr,(fname,ts))
	idb.close_connection(curs,conn)
	
def del_busy_too_long(): # before encryption ...
	too_long=5 # seconds
	tsto=time.time()-too_long
	idb=DB('init.db')
	curs,conn,ts2=idb.getcursor()
	sqlstr="delete from busy where ts<?"
	curs.execute(sqlstr,(tsto,))
	idb.close_connection(curs,conn)
	
def is_busy():
	idb=DB('init.db')
	curs,conn,ts2=idb.getcursor()
	sqlstr="select count(*) as cc, max(ts) as mmax from busy"
	curs.execute(sqlstr)
	tt=curs.fetchall()
	idb.close_connection(curs,conn)
	if len(tt)==0:
		return False
	elif tt[0][0]==0:
		return False
	
	ts=time.time()-tt[0][1]
	# print('still busy ',tt[0][0],'last task sec ago: ',ts)
	# print(idb.select('busy'))
	# print('cur time ',time.time())
	
	return True
	
	
	
	
	
def init_tables(dbfname): #localdb.init_tables()
	
	idb=DB(dbfname)
	
	table={}
	table['address_category']={'address':'text', 'category':'text', 'last_update_date_time':'text' }
	table['deamon_start_logs']={'uid':'int', 'time_sec':'int', 'ttime':'real','loaded_block':'int' }
	table['jsons']={'json_name':'text', 'json_content':'text', 'last_update_date_time':'text' }
	table['wallet_display']={'option':'text', 'value':'text'}
	table['addr_book']={'Category':'text', 'Alias':'text', 'Address':'text','ViewKey':'text','usage':'int','addr_verif':'int','viewkey_verif':'int' }
	table['tx_history']={'uid':'auto','Category':'text', 'Type':'text', 'status':'text','txid':'text','block':'int','timestamp':'real','date_time':'text','from_str':'text','to_str':'text','amount':'real'}
	
	table['notifications']={'datetime':'text','opname':'text','details':'text','status':'text','closed':'text','uid':'auto','orig_json':'text'}
	
	table['out_signatures']={'addr':'text','seed':'text','n':'int'}
	
	table['in_signatures']={'hex_sign':'text','n':'int','addr_from_book':'text','uid':'auto'}
	
	table['msgs_inout']={'proc_json':'text','type':'text','addr_ext':'text','txid':'text','tx_status':'text','date_time':'text', 'msg':'text','uid':'auto','in_sign_uid':'int'}
	
	
	# tmptmp=idb.select('tx_history',{'Category':['=',"'send'"]})
	# for ttt in tmptmp:
		# print(ttt)
	# idb.drop_table('tx_history')
	
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
							
	idb.create_table(table)
	
	idb.delete_where('queue_done',{'command':[' in ',"('show_bills','new_addr','export_viewkey')"]})
	
	table={'msgs_inout':[{'txid':''}]}
	idb.update( table,['txid'  ], {'date_time':['<', app_fun.today_add_days(-7)], 'proc_json':['=',"'True'"] })
	
	table={'notifications':[{'details':''}]}
	idb.update( table,['details'  ], {'datetime':['<', app_fun.today_add_days(-7)], 'opname':['=',"'received'"], 'closed':['=',"'True'"]	})
	
	indexes={}
	
	indexes['queue_done']={'idx_name':'queue_done_id','cname':['id']}
	indexes['queue_waiting']={'idx_name':'queue_waiting_id','cname':['id','status']}
	indexes['queue_waiting']={'idx_name':'queue_waiting_id','cname':['status','command']}
	
	indexes['addr_book']={'idx_name':'addr_book_id','cname':['Address']}
	
	indexes['deamon_start_logs']={'idx_name':'deamon_start_logs_id','cname':['uid']}
	
	indexes['tx_history']={'idx_name':'tx_history_idx_type','cname':['Type','Category']}
	indexes['tx_history']={'idx_name':'tx_history_idx_block','cname':['block']}
	indexes['tx_history']={'idx_name':'tx_history_idx_from','cname':['from_str','txid'],'where':{'Category':['=',"'send'"], 'Type':['=',"'out'"]} }
	indexes['tx_history']={'idx_name':'tx_history_idx_to','cname':['to_str','txid'],'where':{'Category':['=',"'incoming'"], 'Type':['=',"'in'"]} }
	indexes['tx_history']={'idx_name':'tx_history_idx_timestamp','cname':['timestamp']}
	indexes['tx_history']={'idx_name':'tx_history_idx_txid','cname':['txid']}
	indexes['tx_history']={'idx_name':'tx_history_idx_status','cname':['status']}
	
	
	indexes['out_signatures']={'idx_name':'tx_signatures_idx','cname':['addr']}
	
	indexes['in_signatures']={'idx_name':'tx_insignatures_idx','cname':[ 'hex_sign']}
	
	indexes['msgs_inout']={'idx_name':'msg_idx1','cname':['proc_json' ]}
	indexes['msgs_inout']={'idx_name':'msg_idx2','cname':['addr_ext']}
	indexes['msgs_inout']={'idx_name':'msg_idx3','cname':['txid' ]}
	indexes['msgs_inout']={'idx_name':'msg_idx4','cname':['in_sign_uid']}
	
	
	idb.create_indexes(indexes)
	

class DB:

	def get_table_columns(self,tname,add_quotes=True): 
		fname='get_table_columns'
		curs,conn,ts=self.getcursor(fname)
		cc=curs.execute("PRAGMA table_info(__replace__)".replace('__replace__',tname) )
		cc=cc.fetchall()
		retv=[]
		for c in cc:
			if add_quotes:
				retv.append('"'+c[1]+'"')
			else:
				retv.append( c[1] )
				
		
		self.close_connection(curs,conn,fname,ts)
		
		return retv

		
	def delete_old(self,tname,datetime_colname='created_time',ddays=31):
		
		got_date=datetime.datetime.now()- datetime.timedelta(days=ddays)
		
		wwhere={}
		wwhere['datetime('+datetime_colname+')']=['<',"datetime('"+app_fun.date2str(got_date)+"')"]
		self.delete_where( tname,wwhere)
		

	def table_size(self,tname,datetime_colname='created_time'):
	
		colnames=self.get_table_columns(tname)
		fname='table_size'
	
		curs,conn,ts=self.getcursor(fname)
		
		cc=curs.execute('SELECT '+','.join(colnames)+' FROM __replace__'.replace('__replace__',tname))
		cc=cc.fetchall()
		total_chars=0
		rowsii=0
		old_rows=0
		older_chars=0 # older then 1 month
		got_date='"'+datetime_colname+'"' in colnames
		date_index=None
		if got_date:
			got_date=datetime.datetime.now()- datetime.timedelta(days=30)
			date_index=colnames.index('"'+datetime_colname+'"')
			
		if len(cc)==0:
			return {'total_chars':total_chars, 'total_rows':rowsii, 'older_chars':older_chars, 'old_rows':old_rows}
		
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
				
		self.close_connection(curs,conn,fname,ts)
		
		return {'total_chars':total_chars, 'total_rows':rowsii, 'older_chars':older_chars, 'old_rows':old_rows}

		
		
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
		

	def check_encrypted(self,dbname=''):
		
		if dbname=='':
			if hasattr(self,'dbname'):
				dbname=self.dbname
			else:
				self.db_encrypted=True
			
		if dbname[:13]=='local_storage' and dbname[-3:]=='.db':
			if not check_local_storage_not_encrypted():
				self.db_encrypted=True

	def __init__(self,dbname): #='local_storage.db'
		
		self.db_encrypted=False
		self.check_encrypted(dbname)
		if self.db_encrypted==False:
			self.dbname=dbname
		
			

		
	def vacuum(self):
		fname='vacuum'
		curs,conn,ts=self.getcursor(fname)
		curs.execute("vacuum")
		self.close_connection(curs,conn,fname,ts)
		
		
	def getcursor(self,fname=''): #ts=set_busy(fname), del_busy(fname,ts)
	
		if not hasattr(self,'dbname'):
			print('DB err 397 - no db name')
			exit()
	
		conn=sql.connect(self.dbname)
		ts=0
		# if self.dbname=='local_storage.db':
		# print(self.dbname,self.dbname[:13],self.dbname[-3:])
		if self.dbname[:13]=='local_storage' and self.dbname[-3:]=='.db':
			ts=set_busy(fname)
			return conn.cursor(), conn, ts
		# else:
		return conn.cursor(), conn, ts # init.db 
		
		
		
	def close_connection(self,curs,conn,fname='',ts=0): # self.close_connection(curs)
		if self.dbname[:13]=='local_storage' and self.dbname[-3:]=='.db':
		# if self.dbname=='local_storage.db':
			del_busy(fname,ts)
			
		conn.commit()	
		curs.close()
		conn.close()
		
		
	def check_table_exist(self,table):
		fname='check_table_exist'
		self.check_encrypted()
		if self.db_encrypted:
			return False
	
		curs,conn,ts=self.getcursor(fname)
		curs.execute("SELECT count(*) FROM sqlite_master WHERE name='"+table+"' AND type='table'")
		tmpf=curs.fetchone()
		self.close_connection(curs,conn,fname,ts)
		if tmpf[0]==1:
			# curs.close()
			return True
		
		# self.close_connection(curs,conn)
			
		return False
			
		
	def drop_table(self,tname):
		self.check_encrypted()
		if self.db_encrypted:
			return False
			
		fname='drop_table'
		curs,conn,ts=self.getcursor(fname)
		curs.execute("drop table if exists "+tname)
		self.close_connection(curs,conn,fname,ts)
	
	
	def create_indexes(self,indexes): 
		self.check_encrypted()
		if self.db_encrypted:
			return False
			
		fname='create_index_s'
		curs,conn,ts=self.getcursor(fname)
		for kk,vv in indexes.items():
			str_tmpl="CREATE INDEX IF NOT EXISTS _index_name_ ON _table_name_ (_columns_)".replace('_index_name_',vv['idx_name']).replace('_table_name_',kk)
			str_tmpl=str_tmpl.replace('_columns_', ','.join(vv['cname'])) 
			if 'where' in vv:
				str_tmpl+=self.add_where(vv['where'])
			curs.execute(str_tmpl)
	
		self.close_connection(curs,conn,fname,ts)
		
	
	def create_index(self,tname,idx_name='',cname=[],where={}):	
		self.check_encrypted()
		if self.db_encrypted:
			return False
			
		fname='create_index'
		curs,conn,ts=self.getcursor(fname)
		
		str_tmpl="CREATE INDEX IF NOT EXISTS _index_name_ ON _table_name_ (_columns_)".replace('_index_name_',idx_name).replace('_table_name_',tname)
		str_tmpl=str_tmpl.replace('_columns_', ','.join(cname))+self.add_where(where)

		curs.execute(str_tmpl)
		
		self.close_connection(curs,conn,fname,ts)
		
		
		
	def create_table(self,table): 
		self.check_encrypted()
		if self.db_encrypted:
			return False
			
		fname='create_table'

		curs,conn,ts=self.getcursor(fname)
		
		for k,v in table.items():
			
			tmparr=['"'+k2+'" "'+v2+'"' for k2,v2 in v.items()]
			
			sql_str="CREATE TABLE IF NOT EXISTS "+k+' ('+','.join(tmparr)+')'

			curs.execute(sql_str)
				
			# verify all columns 
			colnames=self.get_table_columns( k,False)
			
			for vi,vii in v.items():
				if vi not in colnames:
					sql_str="ALTER TABLE "+k+' ADD COLUMN '+vi+' '+vii
					# print('adding',sql_str)
					curs.execute(sql_str)
		
			
		self.close_connection(curs,conn,fname,ts)
		
	
	def all_tables(self):	
		self.check_encrypted()
		if self.db_encrypted:
			return []
			
		fname='all_tables'
		curs,conn,ts=self.getcursor(fname)
		curs.execute("SELECT * FROM sqlite_master WHERE type='table'")
		retv=curs.fetchall()
		self.close_connection(curs,conn,fname,ts)
		return retv
		
		
	def delete_where(self,table_name,where={}):
		self.check_encrypted()
		if self.db_encrypted:
			return 
			
		fname='delete_where'
		curs,conn,ts=self.getcursor(fname)
		sql_init="delete from "+table_name+self.add_where(where)
		curs.execute(sql_init)
		self.close_connection(curs,conn,fname,ts)
		
	def upsert(self,table,items_order,where): #={'json_name':['=',tmp_max_val]}
		self.check_encrypted()
		if self.db_encrypted:
			return 
	
		tname=list(table.keys())
		tname=tname[0]
		
		cc=self.count(tname,where)
		
		if cc[0][0]==0:
			self.insert(table,items_order)
		elif cc[0][0]==1:
			self.update(table,items_order,where)
		else:
			print(cc[0][0],' upsert more then 1 - exception!?',tname,where)
		
		
		
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
		self.check_encrypted()
		if self.db_encrypted:
			return 
			
		fname='update'
		curs,conn,ts=self.getcursor(fname)
		
		tname=list(table.keys())
		tname=tname[0]
		
		# print('tname',tname)
		
		if 'uid' in items_order:
			items_order.remove('uid')
		
		# print('items_order',items_order)
		
		for rr in table[tname]:
			
			update_str='update '+tname+' set '+', '.join([ io+'=?' for io in items_order])
			vtuple=[rr[io] for io in items_order]
			
			strwhere,vtup=self.add_where_new(where)
			
			update_str+=strwhere
			vtuple=tuple(vtuple+vtup)
			# print('update_str',update_str,vtuple)
			
			curs.execute(update_str, vtuple)
 
		self.close_connection(curs,conn,fname,ts)
		
		
		
	
	def insert(self,table,items_order): 
		self.check_encrypted()
		if self.db_encrypted:
			return []
			
		fname='insert'
		curs,conn,ts=self.getcursor(fname)
		
		tname=list(table.keys())
		tname=tname[0]
		
		sqlstr="insert into "+tname+"("+','.join(items_order)+") values ("+','.join(['?' for ii in items_order])+")"
		
		max_val=0
		ret_uids=[]
		if 'uid' in items_order:
			tmp_max_val=self.select_max_val(tname,'uid' )
			
			if tmp_max_val[0][0]!=None:
				max_val=tmp_max_val[0][0]+1
			
			iter=0
			for rr in table[tname]:
				
				ret_uids.append(max_val+iter)
				tmpval=tuple( max_val+iter if io=='uid' else rr[io] for io in items_order)
				
				curs.execute(sqlstr,tmpval)
				iter+=1
				
		else:
			
			for rr in table[tname]:
			
				tmpval=tuple(rr[io] for io in items_order)
				
				curs.execute(sqlstr,tmpval)
				
				
		self.close_connection(curs,conn,fname,ts)
		return ret_uids
		
	
	
	def select_min_val(self,table_name,column,where={},groupby=[]):
		self.check_encrypted()
		if self.db_encrypted:
			return []
		fname='select_min_val'
		curs,conn,ts=self.getcursor(fname)
		sqlstr='select min("'+column+'") as mmin from '+table_name
		if len(groupby)>0:
			tmpcol=','.join([gg if gg[0]=='"' else '"'+gg+'"' for gg in groupby])
			sqlstr=sqlstr.replace('min("',tmpcol+', min("') + ' group by '+tmpcol
			sqlstr='select * from ('+sqlstr+') as xx order by mmin desc'
			
		sqlstr+=self.add_where(where)
			
		curs.execute(sqlstr)
		retv=curs.fetchall()
		self.close_connection(curs,conn,fname,ts)
		return retv
		
	def select_max_val(self,table_name,column,where={},groupby=[]):
		# print('select_max_val',self.dbname)
		# print(self.all_tables())
	
		self.check_encrypted()
		if self.db_encrypted:
			return []
		fname='select_max_val'
		curs,conn,ts=self.getcursor(fname)
		
		
		
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
				sqlstr='select * from ('+sqlstr+') as xx order by '+','.join([' mmax'+str(jj)+' desc' for jj,cc in enumerate(column)] )
			else:
				sqlstr='select * from ('+sqlstr+') as xx order by mmax desc'
				
		curs.execute(sqlstr)
		retv=curs.fetchall()
		self.close_connection(curs,conn,fname,ts)
		
		return retv
		
		
		
	def select_last_val(self,tname,column): # by default max uid value
		self.check_encrypted()
		if self.db_encrypted:
			return ''
			
		tmp_max_val=self.select_max_val(tname,'uid' )
		tmp_max_val=tmp_max_val[0][0]
		
		if tmp_max_val==None:
			return None
		
		retv=self.select(tname,[column],where={'uid':['=',tmp_max_val]})
		
		return retv[0][0]
		
		
	def add_where(self,where_dict): 
	
		sqlstr=''
		if len(where_dict)>0:
			whrstr=[ k2 +str(v2[0])+str(v2[1]) for k2,v2 in where_dict.items()]
			
			sqlstr+=' where '+' and '.join(whrstr)
			
		return sqlstr
	
	
	def count(self,table_name,where={}):
		self.check_encrypted()
		if self.db_encrypted:
			return []
			
		fname='count'
		curs,conn,ts=self.getcursor(fname)
		sqlstr='select count(*) from '+table_name
		
		sqlstr+=self.add_where(where)
		
		curs.execute(sqlstr)
		retv=curs.fetchall()
		self.close_connection(curs,conn,fname,ts)
		
		return retv
	
	
	
	def select(self,table_name,columns=[],where={},orderby=[],distinct=False, limit=''): 
	
		self.check_encrypted()
		if self.db_encrypted: 
			return [ ]
		
			
		fname='select'
		curs,conn,ts=self.getcursor(fname)
		
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
		
		curs.execute(sqlstr)
		
		retv=curs.fetchall()
		
		self.close_connection(curs,conn,fname,ts)
		
		return retv
		
	

	
	
	
	
	
	
	
	
	

def blocks_to_datetime(blknr):
	idb= DB('init.db')
	
	nearest_time=idb.select_min_val('block_time_logs','ttime',where={'block':['>=',blknr]} )
	if len(nearest_time)>0:
		if nearest_time[0][0]!=None:
	
			nearest_block=idb.select_min_val('block_time_logs','block',where={'block':['>=',blknr]} )
			
			dt=app_fun.timestamp_to_datetime(nearest_time[0][0]) + datetime.timedelta( minutes=blknr-nearest_block[0][0] )
			return app_fun.date2str(dt)
			
	return app_fun.now_to_str(False)



def set_que_waiting( command,jsonstr='', wait_seconds=0):
	initdb= DB('init.db')
	tt= initdb.select('init_settings',columns=["data_files"]) 
	# print(tt)
	# print(tt[0])
	dbname=json.loads(tt[0][0])
	dbname=dbname['db']+'.db'
	# print(dbname)
 
	idb=DB(dbname)
	tmparr=[0]
	latestid1=idb.select_max_val( 'queue_done','id' )
	if len(latestid1)>0: 
		
		if latestid1[0][0]!=None:
			tmparr.append(latestid1[0][0])
		
	latestid2=idb.select_max_val( 'queue_waiting','id')
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


def get_addr_to_hash(addrto,onlylentest=False):
	initdb= DB('init.db')
	tt= initdb.select('init_settings',columns=["data_files"]) 
	dbname=json.loads(tt[0][0])
	dbname=dbname['db']+'.db'

	idb= DB(dbname)
	tmpsign=idb.select( 'out_signatures',['seed','n'], {'addr':['=',"'"+addrto+"'"], 'n':['>',0]}, orderby=[{'n':'asc'}] )
	
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
		idb.insert(table,['addr' ,'seed' ,'n' ])
		
		return first_hash,nmax
		
		
	if len(tmpsign)==1:
	
		next_hash=cc.hash2utf8_1b(tmpsign[0][0],tmpsign[0][1])
		table={}
		table['out_signatures']=[{ 'n':tmpsign[0][1]-1}]
		idb.update(table,[ 'n' ],{'addr':['=',"'"+addrto+"'"]})
		
		if tmpsign[0][1]==1:
			first_hash,nmax=create_new_seed()
			return '\n'+next_hash+';'+cc.int_to_utf8_1b(tmpsign[0][1])+';'+first_hash+';'+nmax+';'
		else:
			return '\n'+next_hash+';'+cc.int_to_utf8_1b(tmpsign[0][1])+';'
	
	else: 
		first_hash,nmax=create_new_seed()

		return '\n'+first_hash+';'+cc.int_to_utf8_1b(nmax)+';'
		
		

# if only 1 addr >0 disp_dict['wl'] {'addr':aa,'confirmed': amount_init, 'unconfirmed': am_unc,'#conf':cc_conf,'#unconf':cc_unc }

def get_default_addr():	
	initdb= DB('init.db')
	tt= initdb.select('init_settings',columns=["data_files"]) 
	dbname=json.loads(tt[0][0])
	dbname=dbname['db']+'.db'
	
	idb= DB(dbname)
	disp_dict=idb.select('jsons',['json_content','last_update_date_time'],{'json_name':['=',"'display_wallet'"]})
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

	
	



def get_last_addr_from(ttype):  # ttype "'last_book_from_addr'", "'last_msg_from_addr'"
	initdb= DB('init.db')
	tt= initdb.select('init_settings',columns=["data_files"]) 
	dbname=json.loads(tt[0][0])
	dbname=dbname['db']+'.db'
	
	idb= DB(dbname)
	rr=idb.select('jsons',['json_content' ],{'json_name':['=',ttype]} )
	
	if len(rr)>0:
		disp_dict=json.loads(rr[0][0])
		return disp_dict['addr']
	else:
		return get_default_addr()
		

def set_last_addr_from( addr, ttype):  # ttype "'last_book_from_addr'", "'last_msg_from_addr'"
	if addr=='':
		return
		
	initdb= DB('init.db')
	tt= initdb.select('init_settings',columns=["data_files"]) 
	dbname=json.loads(tt[0][0])
	dbname=dbname['db']+'.db'
		
	idb= DB(dbname)
	table={'jsons':[{'json_content':json.dumps({'addr':addr}), 'json_name':ttype.replace("'","")}]}
	idb.upsert(table,['json_content','json_name' ],{'json_name':['=',ttype]} )

