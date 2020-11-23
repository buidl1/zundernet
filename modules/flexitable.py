
import tkinter as tk
from tkinter import filedialog, StringVar, ttk, messagebox, Toplevel,Scrollbar
import os,sys
from functools import partial
import datetime
import json
import time
import threading
import  modules.localdb as localdb
import  modules.app_fun as app_fun
# import operator


def messagebox_showinfo(fr_title,fr_content,before_root=True):
	tmproot=None
	if before_root:
		tmproot=tk.Tk()
		tmproot.overrideredirect(1)
		tmproot.withdraw()
		
	messagebox.showinfo(fr_title,fr_content)
	
	if before_root:
		tmproot.destroy()
	




def msg_yes_no(a,b):
	return messagebox.askyesno(a, b)
	

def get_file_dialog(strtitle="Select relevant file"):
	return filedialog.askopenfilename(initialdir=os.getcwd(), title=strtitle)
		
def setfile(elem=None,validation_fun=None ):
	if elem==None:
		return
	else:	
		
		while True:
		
			path=filedialog.askopenfilename(initialdir=os.getcwd(), title="Select relevant file")
			if path==None:
				return 
				
			elif validation_fun==None:
				elem.set(str(path))
				break
				
			elif validation_fun(path):
				elem.set(str(path))
				break
			else:
				messagebox.showinfo("Path is not correct!", "Select relevant path!" )		
		
		
		
		
def setdir(elem=None,validation_fun=None ):
	if elem==None:
		return
	else:	
		
		while True:
		
			path=filedialog.askdirectory(initialdir=os.getcwd(), title="Select directory")
			# print(path)
			if path==None or path=='':
				return 
				
			elif validation_fun==None:
				elem.set(str(path))
				break
				
			elif validation_fun(path):
				elem.set(str(path))
				break
			else:
				messagebox.showinfo("Path is not correct!", "Select apropriate path!" )
				
						
						
						
						

def copy(elem,vv):
	elem.clipboard_clear() 
	elem.clipboard_append(vv)
	elem.update()
	messagebox.showinfo("Value copied to clipboard", "Value [ "+vv+" ] copied to clipboard." )
	

	
	
	



class FlexiTable(ttk.Frame): # process buttons last!

	# scrollable canvas events
	def _on_mousewheel(self, event):
		# if hasattr(self,'canvas1'):
		try:
			self.canvas1.yview_scroll(int(-1*(event.delta/120)), "units")
		except:
			pass # some error ...
		
	def _bound_to_mousewheel(self, event):
		self.canvas1.bind_all("<MouseWheel>", self._on_mousewheel)  
		

	def _unbound_to_mousewheel(self, event):
		self.canvas1.unbind_all("<MouseWheel>")
		
		
		
	def getstyle(self,uid=None,elemtype='TButton',bgc= 'red',fgc= 'white',wid= None,fontsize=None ):
		style = ttk.Style()
		if uid==None:
			return elemtype
			
		elemuid=str(uid)+'.'+elemtype
		
		if wid!=None:
			style.configure(elemuid, background = bgc, foreground = fgc, width = wid, borderwidth=1, focusthickness=3, focuscolor='none')
		else:
			style.configure(elemuid, background = bgc, foreground = fgc,borderwidth=1, focusthickness=3, focuscolor='none')
			
		if fontsize!=None:
			style.configure(elemuid,font=("TkDefaultFont",fontsize))
			
		style.map(str(uid)+'.'+elemtype, background=[('active',bgc)])
		return str(uid)+'.'+elemtype
		
		
		
		
		
		
	def resize_canvas(self,scalex,scaley=1):
	
		if hasattr(self,'canvas1') and self.is_fully_loaded: # and scalex>0.1:
			if time.time()-self.loaded_time>0.2:
				
				if scalex<=1: #self.min_canvas_width 
					self.canvas1.config(width=self.min_canvas_width  )
					
				elif scalex>1.2: 
					self.canvas1.config(width=int(self.canvas1.winfo_width()*scalex) ) # *1.2
					
				if scaley<=1: #self.min_canvas_width
					self.canvas1.config( height=self.min_canvas_height  )
					
				elif scaley>1.2:
					self.canvas1.config( height=int(self.canvas1.winfo_height()*scaley)   ) # *1.2
					
				self.loaded_time=time.time()	
				
				
		

	def add_scrollable_canvas(self):

		self.canvas1=tk.Canvas(self)
		self.canvas1.columnconfigure(0, weight=1)
		self.canvas1.rowconfigure(0, weight=1)
		self.canvas1.config(width=self.min_canvas_width,height=self.min_canvas_height)
		
		scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas1.yview)
		x_scrollbar = ttk.Scrollbar(self, orient="horizontal", command=self.canvas1.xview)
		
		scrollable_frame = ttk.Frame(self.canvas1)	
		
		scrollable_frame.columnconfigure(0, weight=1)
		scrollable_frame.rowconfigure(0, weight=1)
		
		scrollable_frame.bind("<Configure>",lambda e: self.canvas1.configure(scrollregion=self.canvas1.bbox("all") ) ) 
		
		scrollable_frame.bind('<Enter>', self._bound_to_mousewheel)
		scrollable_frame.bind('<Leave>', self._unbound_to_mousewheel)
		
		
		self.canvas1.create_window((0, 0), window=scrollable_frame, anchor="nw") #
		self.canvas1.configure(yscrollcommand=scrollbar.set, xscrollcommand=x_scrollbar.set )
		
		# self.canvas1.pack(side="top", fill="both", expand=True) #, expand=True
		# scrollbar.pack(side="right", fill="y")	
		# x_scrollbar.pack(side="bottom", fill="x")	
				
		self.canvas1.grid(row=0, column=0, sticky="nsew")
		scrollbar.grid(row=0, column=1, sticky="ns")
		x_scrollbar.grid(row=1, column=0, sticky="ew")
			
		return scrollable_frame
		
		

	def __init__(self, master=None, grid_lol=None, min_canvas_width=400,force_scroll=False, scale_width=True ):
	
		super().__init__(master)
		self.master = master
		self.min_canvas_width=min_canvas_width
		self.min_canvas_height=400
		self.is_fully_loaded=False
		self.force_scroll=force_scroll
		self.scale_width=scale_width
		
		self.pack(padx=5, pady=5,side='left',fill='both', expand=True) 
		self.columnconfigure(0, weight=1)
		self.rowconfigure(0, weight=1)
		
		self.int_validation_fun = (self.register(self.validate_int),'%P')
		self.float_validation_fun = (self.register(self.validate_float),'%P')
		
		self.main_frame=ttk.Frame(self)		
		
		self.elements=[]
		self.elements_grid_opt={}
		
		self.elements_uid={}
		self.row_ids={}
		self.variables={}
		self.button_args={}
		self.max_col_width={}
		self.tooltip_arr={}
		self.current_grid_lol=json.dumps(grid_lol.copy())
		
		rowcounttmp=len(grid_lol)
		
		
		if rowcounttmp>15 or force_scroll:
			self.main_frame=self.add_scrollable_canvas()
		else:
			self.main_frame.grid(row=0,column=0,sticky='nw') 
		
		self.calc_max_col_width(grid_lol)
		
		
		for ii,rr2 in enumerate(grid_lol): # prepare grid and variables
			
			row_id=list(rr2.keys())[0]
			rr=rr2[row_id]
			
			self.row_ids[row_id]={}
			for jj,vv in enumerate(rr):
				if len(vv)==0:
					continue
				
				self.add_new_element(vv,ii,jj,row_id)
				
		self.is_fully_loaded=True
		self.loaded_time=time.time()
	
	
	
	def get_width(self,vv,jj):
		sspan=1
		if 'span' in vv:
			sspan=vv['span']
		
		tmpwidth=sspan*self.max_col_width[jj]
		if 'width' in vv:
			if vv['width']<tmpwidth:
				tmpwidth=vv['width']
		
		return tmpwidth
			
	
	def add_new_element(self,vv,ii,jj,row_id ):
	
		# print('new elem',ii,jj,vv,row_id)
	
		if 'T' not in vv:
			return
			
		if str(row_id)=='999':
			ii=999
			
		mywraplength=2048
		if 'wraplength' in vv:
			mywraplength=vv['wraplength']
		
		elemtype='TButton'
		
		if 'Label' in vv['T']:
			elemtype='TLabel'	
		sstyle=self.getstyle(None,elemtype)
		
		if 'style' in vv and 'uid' in vv: # style={bgc:,fgc:,wid:}
			
			wid=None
			if 'wid' in vv['style']:
				wid=vv['style']['wid']
				
			fontsize=None
			if 'fontsize' in vv['style']:
				fontsize=vv['style']['fontsize']
			
			sstyle=self.getstyle(vv['uid'],elemtype,vv['style']['bgc'] , vv['style']['fgc']  ,wid,fontsize  )
			
		tmpiter=0
		if len(self.variables)>0:
			tmpiter=max(self.variables.keys())+1
		
		
		if vv['T']=='LabelC': # constant
			
			self.elements.append(ttk.Label(self.main_frame,text=vv['L'], wraplength=mywraplength, style=sstyle) )
			
		elif vv['T']=='LabelE': # empty
			self.elements.append(ttk.Label(self.main_frame,text='')  )
			
		elif vv['T']=='LabelV': # variable
			
			self.variables[tmpiter]=StringVar()
			self.variables[tmpiter].set(vv['L'])
			
			self.elements.append(ttk.Label(self.main_frame,textvariable=self.variables[tmpiter], wraplength=mywraplength , style=sstyle)  ) #, style=sstyle
			
		elif vv['T']=='Button': 
			tmp_state='normal'
			if 'IS' in vv:
				tmp_state=vv['IS']
			self.variables[tmpiter]=StringVar()
			if 'L' in vv:
				self.variables[tmpiter].set(vv['L'])
				
			self.elements.append( ttk.Button(self.main_frame,textvariable=self.variables[tmpiter],state=tmp_state , style=sstyle)  ) 
			
		elif vv['T']=='Combox': 
		
			self.variables[tmpiter]=StringVar()
			
			self.elements.append( ttk.Combobox(self.main_frame,textvariable=self.variables[tmpiter],values=vv['V'], state="readonly") ) #
			self.elements[-1].current(0)
		
		elif vv['T']=='InputL':
		
			self.variables[tmpiter]=StringVar()
			if 'L' in vv: self.variables[tmpiter].set(vv['L'])
			
			self.elements.append( ttk.Entry(self.main_frame,textvariable=self.variables[tmpiter]))
		elif vv['T']=='InputINT':
			
			self.variables[tmpiter]=StringVar()
			self.elements.append( ttk.Entry(self.main_frame,textvariable=self.variables[tmpiter], validate='focusout', validatecommand=self.int_validation_fun)) 
		
		elif vv['T']=='InputFloat':
		
			sspan=1
			if 'span' in vv:
				sspan=vv['span']
			
			self.variables[tmpiter]=StringVar()
			
			self.elements.append( ttk.Entry(self.main_frame,textvariable=self.variables[tmpiter], validate='focusout', validatecommand=self.float_validation_fun  )) 
		
		elif vv['T']=='Text':
			
			tmpheight=2
			if 'height' in vv:
				tmpheight=vv['height']
							
			self.variables[tmpiter]=StringVar() 
			self.variables[tmpiter].set('__TEXT__')
			
			self.elements.append( tk.Text(self.main_frame,height=tmpheight, xscrollcommand=None, yscrollcommand=None  )) 
			
		else:
			print('return - diff type')
			return
		
		# print(373,'ok')
		
		if 'tooltip' in vv:
			tmptt=CreateToolTip(self.elements[-1],vv['tooltip'])
			if 'uid' in vv.keys():
				self.tooltip_arr[vv['uid']]=tmptt
				
		tmp_columnspan=1
		if 'span' in vv:
			tmp_columnspan=vv['span']
		
		tmp_pads=[5,2]
		if 'pads' in vv:
			tmp_pads=vv['pads']
		
		if tmpiter in self.variables and type(self.variables[tmpiter])==type([]) and type(self.variables[tmpiter][0])==type(int(0)):
			
			self.elements[-1].grid(row=ii,column=jj,padx=tmp_pads[0],pady=tmp_pads[1],sticky='E',columnspan=tmp_columnspan)
			self.elements_grid_opt[self.elements[-1]]={'padx':tmp_pads[0],'pady':tmp_pads[1],'sticky':'E','columnspan':tmp_columnspan}
			
			if 'visible' in vv:
				if not vv['visible']:
					self.elements[-1].grid_forget()
		# except:
		else:
			self.elements[-1].grid(row=ii,column=jj,padx=tmp_pads[0],pady=tmp_pads[1],sticky='W',columnspan=tmp_columnspan ) #, ipady=1, ipadx=1
			self.elements_grid_opt[self.elements[-1]]={'padx':tmp_pads[0],'pady':tmp_pads[1],'sticky':'W','columnspan':tmp_columnspan}
			
			if 'visible' in vv:
				if not vv['visible']:
					self.elements[-1].grid_forget()

		if self.scale_width and jj in self.max_col_width:
			if vv['T']=='Combox': 
				self.elements[-1].configure(width=self.get_width(vv,jj)-2 )			
			else:
				self.elements[-1].configure(width=self.get_width(vv,jj) )	
		# print('before ading element ui 408')
		if 'uid' in vv.keys():
			# print(vv['uid'])
			if vv['T'] in ['LabelV','InputL','InputINT','InputFloat' ]: 
				self.elements_uid[vv['uid']]= self.variables[tmpiter]
				
			else:
				
				self.elements_uid[vv['uid']]= [self.variables[tmpiter],self.elements[-1]]
				
			if row_id not in self.row_ids: self.row_ids[row_id]={}
			
			self.row_ids[row_id][vv['uid']]=[self.variables[tmpiter],self.elements[-1]]
				
			
	def calc_max_col_width(self,grid_lol ):
		
		for ii,rr2 in enumerate(grid_lol) : # calculate width
		
			row_id=list(rr2.keys())[0]
			rr=rr2[row_id]
			
			for jj,vv in enumerate(rr):
			
				if len(vv)==0:
					continue
					
				if 'L' not in vv and 'width' not in vv and vv['T']!='InputD'  and vv['T']!='Combox':
					continue
					
				tmpval=0
				
				if 'width' in vv:
					tmpval=vv['width']
					
				else:
					if vv['T']=='InputD':
						tmpval=12
					elif vv['T']=='Combox':
						for zz in vv['V']:
							if len(zz)+3>tmpval:
								tmpval=len(zz)+3
					
					else:
						
						tmpval=int(len(vv['L'])*1.1)+1
						
				if 'span' in vv:
					tmpval=int(tmpval/vv['span'])+1
								
				if jj not in self.max_col_width or tmpval>self.max_col_width[jj]:
					
					self.max_col_width[jj ]=tmpval
					
				# print(ii,jj,tmpval)
				
		mmaxtmp=max(self.max_col_width)
		for jj in range(len(grid_lol[0])):
			if jj not in self.max_col_width:
				self.max_col_width[jj ]=int(mmaxtmp/2)+1
		# print(self.max_col_width)
		
		
		
		
		
		
				
		
	def update_frame(self,grid_lol,head_offset=0):
		# print('flexi 469')
		tmpj=json.dumps(grid_lol)
		if self.current_grid_lol == tmpj :
			# print('same same')
			return
			
		self.current_grid_lol=tmpj #grid_lol.copy()
		# print('freshhhh')
		# print('flexi 476')
		def del_elems(k):
			
			for vvuid,vv in self.row_ids[k].items():
				vv[1].grid_forget()
				
				for kkk,vvv in self.variables.items():
					if vvv==vv[0]:
						del self.variables[kkk]				
						break
				
				if vv[1] in self.elements:
					self.elements.remove(vv[1]) #self.elements
					
				if vvuid in self.tooltip_arr:
					del self.tooltip_arr[vvuid]
				
				if vvuid in self.elements_uid:
					del self.elements_uid[vvuid] 
				
			self.row_ids[k]={}
			
		
		if len(grid_lol)==0:
			# clear grid for eac helement - drop 
			for k,v in self.row_ids.items():
				if k=='head':
					continue
				del_elems(k)	
			return
		else: 
			for k,v in self.row_ids.items():
				if k=='head':
					continue
				matched=False
				for ii,rr2 in enumerate(grid_lol):
					row_id=list(rr2.keys())[0]
					if row_id==k:
						matched=True
						break
				if not matched:
					
					del_elems(k)
				
		row_id=list(grid_lol[0].keys())[0]
		
		for ii in range(len(grid_lol[0][row_id])):
			
			self.main_frame.columnconfigure(ii, weight=1)
		
		self.calc_max_col_width(grid_lol ) #max_col_width=
		
		tmp_pads=[5,2]
		# print('flexi 528')
		for iii,rr2 in enumerate(grid_lol): # prepare grid and variables
			
			ii=iii+head_offset
			row_id=list(rr2.keys())[0]
			rr=rr2[row_id]
			# print('flexi 534',iii)
			
			if row_id in self.row_ids.keys(): # update
			
				for jj,vv in enumerate(rr):
					# print('flexi 539',jj)
					
					if len(vv)==0:
						continue
						
					if 'uid' not in vv:
						continue
						
					# if 'Address' in vv['uid']:
						# print(' flexi 546 ', vv['uid'])
						
					sspan=1
					if 'span' in vv:
						sspan=vv['span']
						
					if vv['uid'] not in self.row_ids[row_id]:
						
						self.add_new_element(vv,ii+1,jj,row_id )
						
					if 'tooltip' in vv:
						tmptt=CreateToolTip(self.row_ids[row_id][vv['uid']][1],vv['tooltip'])	
						if 'uid' in vv.keys():
							self.tooltip_arr[vv['uid']]=tmptt
					
					elemtype='TButton'
					if 'Label' in vv['T']:
						elemtype='TLabel'	
					
					if 'style' in vv and 'uid' in vv: 
						
						wid=None
						if 'wid' in vv['style']:
							wid=vv['style']['wid']
							
						fontsize=None
						if 'fontsize' in vv['style']:
							fontsize=vv['style']['fontsize']
				
						
						sstyle=self.getstyle(vv['uid'],elemtype,vv['style']['bgc'] , vv['style']['fgc']  ,wid,fontsize  )
						# try:
						self.row_ids[row_id][vv['uid']][1].configure(style=sstyle)
						# except:
							# pass
						
					if row_id in self.row_ids:
						if vv['uid'] in self.row_ids[row_id]:
							# try:
							
							if 'L' in vv and self.row_ids[row_id][vv['uid']][0]!=None:
								self.row_ids[row_id][vv['uid']][0].set(vv['L'])
				
				
				# if 'L' in vv and self.row_ids[row_id][vv['uid']][0]!=None:
					
					# try:
						# self.row_ids[row_id][vv['uid']][0].set(vv['L'])
					# except:
						# print(row_id,vv['uid'],vv['L'])
						# print(self.row_ids)
					
							if 'V' in vv and self.row_ids[row_id][vv['uid']][1]!=None:
								self.row_ids[row_id][vv['uid']][1].configure(values=vv['V'])
							# except:
								# pass
						
					if 'pads' in vv:
						self.elements_grid_opt[self.row_ids[row_id][vv['uid']][1]]['padx']=vv['pads'][0]
						self.elements_grid_opt[self.row_ids[row_id][vv['uid']][1]]['pady']=vv['pads'][1]
						
					grid_opt=self.elements_grid_opt[self.row_ids[row_id][vv['uid']][1]]
					if 'visible' in vv:
						if vv['visible']:
							
							self.row_ids[row_id][vv['uid']][1].grid(row=ii+1,column=jj,padx=grid_opt['padx'],pady=grid_opt['pady'],sticky=grid_opt['sticky'],columnspan=grid_opt['columnspan'] )
							
							if head_offset==0 or ii+1>0 : 
								
								if self.scale_width and jj in self.max_col_width:
									if vv['T']=='Combox': 
										self.row_ids[row_id][vv['uid']][1].configure(width=self.get_width(vv,jj)-2 )			
									else:
										self.row_ids[row_id][vv['uid']][1].configure(width=self.get_width(vv,jj) )	
					
						else:
							
							self.row_ids[row_id][vv['uid']][1].grid_forget()
							
					else:
						
						self.row_ids[row_id][vv['uid']][1].grid(row=ii+1,column=jj,padx=grid_opt['padx'],pady=grid_opt['pady'],sticky=grid_opt['sticky'],columnspan=grid_opt['columnspan'] )
						if head_offset==0 or ii+1>0 :
							
							if self.scale_width and jj in self.max_col_width:
								if vv['T']=='Combox': 
									self.row_ids[row_id][vv['uid']][1].configure(width=self.get_width(vv,jj)-2 )			
								else:
									self.row_ids[row_id][vv['uid']][1].configure(width=self.get_width(vv,jj) )	
					
			else:
				# print('new elem?')
				self.row_ids[row_id]={}
				for jj,vv in enumerate(rr):
					
					self.add_new_element(vv,ii+1,jj,row_id ) # ?? ii+1
		
				
				
	def validate_float(self,P):
		
		if len(P)==0:
			return True
		
		try:
			f=float(P)
			if len(str(f-round(f,0)))>10:
				messagebox.showinfo("Wrong value",'['+P+"] has to many digits after dot. Maximum 8 allowed.")
				self.master.lift()
				return False
				
			return True
		except:
			messagebox.showinfo("Wrong value",'['+P+"] is not correct number. Only numbers are allowed in this entry! ")
			self.master.lift()
			
		return False
				
				
				
		
	def validate_int(self,P):
		
		if len(P)==0:
			return True
			
		try:
			# print(P)
			if int(P)==float(P):
				return True
			else:
				messagebox.showinfo("Wrong value",'['+P+"] is not correct integer number. Only integers are allowed in this entry! ")
				self.master.lift()
		except:
			messagebox.showinfo("Wrong value",'['+P+"] is not correct integer number. Only numbers are allowed in this entry! ")
			self.master.lift()
			
		return False
	
	
	
	
	
	def has_uid(self,uid):
		if uid in self.elements_uid:
			return True
			
		return False
	
	
	
	def set_button_status(uid,mystatus): 
		self.elements_uid[ uid][1].config(status=mystatus)
	
	
	
	def set_valid_input_fun(self,input_uid,args_uids,cmd_function):
	
		arg_tupl=self.args_to_tupl(args_uids)
		
		if arg_tupl==():
		
			self.row_ids[args_uids[0]][input_uid][1].bind("<KeyRelease>", partial(cmd_function))
			return
			
		self.row_ids[args_uids[0]][input_uid][1].bind("<KeyRelease>", partial(cmd_function,*arg_tupl[1:]))
			
	
	
	def args_to_tupl(self,args_uids):
		arg_tupl=()
		# toprint=True
		# print(args_uids)
		for aa in args_uids:
			# if aa=='Rejected':
				# toprint=True
			# print(aa)
				
			if type(aa)==type('a') and aa in self.elements_uid: 
				# if toprint: print(699,self.elements_uid)
				if type([])==type(self.elements_uid[aa]): # button and combox
					# if toprint: print('# button and combox')
					arg_tupl+=(self.elements_uid[aa][1],)
				else:
					arg_tupl+=(self.elements_uid[aa],) #inputs 
					# if toprint: print('#inputs ')
			else:
				arg_tupl+=(aa,) # or other args
				# if toprint: print('# or other args')
				
		# print(arg_tupl)
		return arg_tupl
	
	
	def set_cmd(self,button_uid,args_uids,cmd_function):
			
		if 	button_uid not in self.elements_uid:
			return
				
		arg_tupl=self.args_to_tupl(args_uids)
		
		if arg_tupl==():
		
			self.elements_uid[button_uid][1].configure( command=partial(cmd_function) )
			return
				
		self.button_args[button_uid]=arg_tupl
				
		self.elements_uid[button_uid][1].configure( command=partial(cmd_function, *self.button_args[button_uid]) )
		
	
	
	
	def bind_combox_cmd(self,cbox_uid,args_uids,cmd_function):
		
		arg_tupl=self.args_to_tupl(args_uids)
		
		if arg_tupl==():
			self.elements_uid[cbox_uid][1].bind("<<ComboboxSelected>>", partial(cmd_function))
			return
			
		
		self.elements_uid[cbox_uid][1].bind("<<ComboboxSelected>>", partial(cmd_function, *arg_tupl))
		
		
	def set_textvariable(self,uid,x_val): 
	
		if uid==None: # if not specified assume there is only one and drop there
			alluids=list(self.elements_uid.keys())
			uid=alluids[0]
			
		tmpo=self.elements_uid[uid]
		if type(self.elements_uid[uid])==type([]): # combox
			if type(self.elements_uid[uid][0])==type( StringVar() ) :
				# print()
				self.elements_uid[uid][0].set(x_val) 
		else:	
			if type(self.elements_uid[uid])==type( StringVar() ) :
				self.elements_uid[uid].set(x_val) 
		
	 
	def get_value(self,uid):
		
		
		if uid in self.elements_uid:
			if type(self.elements_uid[uid])==type([]):
				try :
					if self.elements_uid[uid][0].get()=='__TEXT__':
						return self.elements_uid[uid][1].get("1.0",tk.END)
					
					return self.elements_uid[uid][1].get() # combox
				except:
					return self.elements_uid[uid][0].get() # button
			
		return self.elements_uid[uid].get()


def showinfo(tit,lbl):
	messagebox.showinfo(tit, lbl)

def ask_password(tmpval,title='Enter password',lbl='Enter password to decrypt file',fun_run_after=None):
	
	rootframe = Toplevel() #tk.Tk()
	rootframe.title(title)
	ttk.Label(rootframe,text=lbl).pack(fill='x')
	tmpvar=StringVar()
	
	entr=ttk.Entry(rootframe,textvariable=tmpvar, show='*')
	entr.pack(fill='x')
	
	def get_pass(*args):
		
		if len(tmpvar.get().strip())>0:
			tmpval.append(tmpvar.get().strip())
			fun_run_after(tmpval)
			
			rootframe.destroy()
	
	ttk.Button(rootframe,text='Enter',command= get_pass  ).pack(fill='x')
	entr.bind('<Return>',  get_pass )
	entr.focus()
			
	def on_closing():
		if len(tmpval)==0:
			tmpval.append(' ')
	
	rootframe.protocol("WM_DELETE_WINDOW", on_closing)			
	


def output_copy_input(strtitle,stroutput):
	
	newwin=Toplevel()
	newwin.title(strtitle)
	entr=ttk.Label( newwin,text=strtitle+'\n\n'+stroutput) #
	entr.pack()

	okb=ttk.Button( newwin,text='Copy',command=partial(copy, entr,stroutput))
	okb.pack()
	
	
	
	
	
def simple_opt_box( strtitle,opt,cmdfun):
	
	
	newwin=Toplevel()
	newwin.title(strtitle)
		
	cmboxv=StringVar()
	
	cmbox=ttk.Combobox( newwin,textvariable=cmboxv,values=opt, state="readonly")
	cmbox.pack(side = 'left')
	cmboxv.set(opt[0])
	
	def okcmd():
		
		cmdfun(cmboxv.get())
		newwin.destroy()
		
	okb=ttk.Button( newwin,text='OK',command=okcmd)
	okb.pack(side = 'right')
	
	






class ResultOptions:

	def __init__(self,strtitle,result_str_arr=[],cmd_names=[],cmd_fun=[], args=[]):
		
		self.newwin=Toplevel()
		self.newwin.title(strtitle)

		scrollbar = Scrollbar(self.newwin)
		scrollbar.pack(side = 'right', fill = 'y') 
		
		ylist = tk.Listbox(self.newwin,yscrollcommand = scrollbar.set , width=100 , height=30) # 
		
		try:
		
			for tt in result_str_arr:
				if type(tt)==type([]):
					ylist.insert('end', str(tt[0] ) )   
				else:
					ylist.insert('end', str(tt) )   #.decode("utf-8")
		
		except:
			ylist.insert('end', str('Binary format to avoid system exception') )
			for tt in result_str_arr:
				if type(tt)==type([]):
					ylist.insert('end', str(tt[0].encode("utf-8")) )   
				else:
					ylist.insert('end', str(tt.encode("utf-8")) )   
		
		ylist.pack(side = 'top', fill = 'x') 
  
		scrollbar.config( command = ylist.yview )
		
		btns=[]
		
		for ii,btn in enumerate(cmd_names):
		
			tmpargs=()
			if args[ii][0]!=None:
				tmpargs=(result_str_arr,) + args[ii] 
			else:
				tmpargs=(result_str_arr,)
				
				
			btns.append(ttk.Button(self.newwin,text=btn,command=partial(self.run_opt,cmd_fun[ii],tmpargs) ) )
			btns[-1].pack(side='top', fill = 'x')
			
	def run_opt(self,opt_fun,args):
	
		opt_fun(*args)
	
		self.newwin.destroy()
	
	
	
	
	
	
	
	
class Confirm:

	def __init__(self,strlabel,cmd, args):
		self.delete=False
		self.txt=strlabel
		self.newwin=Toplevel()
		self.newwin.title('Are you sure?')

		lbl=ttk.Label(self.newwin, text=strlabel)
		lbl.pack(side="top")
		delete=ttk.Button(self.newwin,text='YES, DELETE',command=lambda:self.set_confirm(cmd, args) )
		cancell=ttk.Button(self.newwin,text='NO! CANCELL!',command=lambda:self.newwin.destroy())
		
		delete.pack(side='left' )
		cancell.pack(side='right' )
		
	def set_confirm(self,cmd, args):
	
		cmd(*args)
	
		self.newwin.destroy()
	








class CreateToolTip(object):
	"""
	create a tooltip for a given widget
	https://stackoverflow.com/questions/3221956/how-do-i-display-tooltips-in-tkinter
	"""
	def __init__(self, widget, text='widget info'):
		self.waittime = 300	 #miliseconds
		self.wraplength = 250   #pixels
		self.widget = widget
		self.text = text
		self.widget.bind("<Enter>", self.enter)
		self.widget.bind("<Leave>", self.leave)
		self.widget.bind("<ButtonPress>", self.leave)
		self.id = None
		self.tw = None
		

	def enter(self, event=None):
		self.schedule()
		self.widget.after(15000,self.hidetip)
		

	def leave(self, event=None):
		self.unschedule()
		self.hidetip()

	def schedule(self):
		self.unschedule()
		self.id = self.widget.after(self.waittime, self.showtip)

	def unschedule(self):
		id = self.id
		self.id = None
		if id:
			self.widget.after_cancel(id)

	def showtip(self, event=None):
		x = y = 0
		x, y, cx, cy = self.widget.bbox("insert")
		# x += self.widget.winfo_rootx() + 25
		x += self.widget.winfo_rootx() + self.widget.winfo_width() - 5
		# y += self.widget.winfo_rooty() + 20
		y += self.widget.winfo_rooty() + self.widget.winfo_height() - 5
		# creates a toplevel window
		# self.hidetip() # prevent hangup
		self.tw = tk.Toplevel(self.widget)
		# Leaves only the label and removes the app window
		self.tw.wm_overrideredirect(True)
		self.tw.wm_geometry("+%d+%d" % (x, y))
		label = tk.Label(self.tw, text=self.text, justify='left',
					   background="#ffffff", relief='solid', borderwidth=1,
					   wraplength = self.wraplength)
		label.pack(ipadx=1)

	def hidetip(self):
		tw = self.tw
		self.tw= None
		if tw:
			tw.destroy()
