# lambda bugs
# lambda:  actionFun(*args)
# sgould be# lambda *args:  actionFun(*args)
import os,time

from PySide2.QtCore import (
	QAbstractTableModel,
	QModelIndex,
	QPersistentModelIndex,
	QSortFilterProxyModel,
	Qt,
	Slot,
	QLocale,
	QThread,
	QObject,
	Signal,
	QTimer,
	QDateTime,
	QEvent
	
)
from PySide2.QtGui import (
	QColor,
	QValidator,
	QDoubleValidator,
	QIntValidator,
	QFont,
	QKeySequence,
	QIcon
	# QClipboard 
)
from PySide2.QtWidgets import (
	QApplication,
	QGridLayout,
	QLayout,
	QHBoxLayout,
	QItemDelegate,
	QLabel,
	QMainWindow,
	QPushButton,
	QStackedLayout,
	QTableView,
	QWidget,
	QVBoxLayout,
	QTabWidget,
	QTextEdit,
	QLineEdit,
	QGroupBox,
	QMessageBox,
	QComboBox,
	QFileDialog,
	QDialog,
	QProgressDialog,
	QTableWidget,
	QTableWidgetItem,
	QHeaderView,
	QAbstractScrollArea,
	QSizePolicy,
	QAbstractItemView,
	QShortcut
)

import traceback

def copy_progress(path,deftxt,src,dest,fromfile=True):

	src_size=0
	if fromfile:
		src_size=os.path.getsize(src)
	else:
		src_size=len(src )
	
	qpd= QProgressDialog(deftxt,'Cancel',0,src_size) # parent none
	qpd.setAutoClose(True)
	qpd.setMinimumDuration(1000)
	qpd.setWindowModality(Qt.WindowModal)
	qpd.setValue(0)
	
	progress=0
	readmode='rb'
	writemode='wb'
	if fromfile==False:
		# readmode='r'
		if type(src)!=type(b''):
			writemode='w'
	# if True:
	try:
		bb1=b''
		if fromfile:
			with open(src, "rb") as fin:
				bb1=fin.read() # read all 
		else:
			bb1=src
		
		chunks=max(1,int(src_size/50))
		
		fo=open(dest, writemode)
		
		bts=bb1[0:chunks]
		# time.sleep(1)
		# print('before while')
		while progress<src_size:
			# print('fo.write(bts)')
			fo.write(bts)
			progress+=chunks
			
			if qpd.wasCanceled():
				break
			# print('qpd.setValue(progress)')
			qpd.setValue(progress)
			
			if progress+chunks>src_size:
				chunks=src_size-progress
				
			# print('bts')
			bts=bb1[progress:progress+chunks]
			# print(progress,src_size)
			
			# if progress+chunks>=src_size*0.5 and progress<src_size*0.5:
				# time.sleep(0.5)
			
		# print('fo.close()')
		fo.close()
			
		if qpd.wasCanceled():
			
			showinfo('Backup CANCELED','Please try again!\n'  )
			qpd.close()
			if os.path.exists(dest):
				os.remove(dest)		
				
			return ''
		else:
			return dest
	# else:
	except:
		traceback.print_exc()
	
		if progress>0:
			showinfo('Backup FAILED ','Please check if there is enough space on your drive and try again!\nFailed at byte '+str(progress)+' out of '+str(src_size)  )
		else:
			showinfo('Backup FAILED','Please check if your drive is not locked!\n'  )
		
		fo.close()
		if os.path.exists(dest):
			print('Exception - remove dest?',dest,os.path.exists(dest))
			os.remove(dest)
			
		return ''



def askokcancel(title, question,parent=None):
	
	if QMessageBox.question(parent, title, question, QMessageBox.Yes|QMessageBox.No|QMessageBox.Cancel ) == QMessageBox.Yes:
		return True
	return False

def messagebox_showinfo(fr_title,fr_content,parent=None):
	
	msgBox=QMessageBox()
	if parent !=None:
		msgBox=QMessageBox(parent)
		
	msgBox.setSizePolicy(  QSizePolicy.Expanding,QSizePolicy.Expanding )
	msgBox.setStyleSheet('QPushButton {padding:3px;font-size:13px;}')
	msgBox.setWindowTitle(fr_title)
	msgBox.setText(fr_content)
	msgBox.layout().setSizeConstraint(QLayout.SetNoConstraint)
	
	msgBox.exec_()
	
def showinfo(tit,lbl,parent=None):
	messagebox_showinfo(tit, lbl,parent)

def msg_yes_no(a,b,parent=None):
	
	msgBox=QMessageBox(parent)
	msgBox.setStyleSheet('QPushButton {padding:3px;font-size:13px;}')
	# reply=msgBox.question(parent,a, b,QMessageBox.Yes|QMessageBox.No)
	reply = QMessageBox.question(msgBox,a, b,QMessageBox.Yes|QMessageBox.No)
	if reply==QMessageBox.Yes:
		return True
	else:
		return False
	# return reply #messagebox.askyesno(a, b)
	
	
# setdir
# askdirectory
def get_file_dialog(strtitle ,init_path=os.getcwd(),parent=None,name_filter=''): #init_path=os.getcwd()

	if name_filter=='dir':
		return QFileDialog.getExistingDirectory(parent,strtitle,init_path )
		
	else: #if name_filter!='':
		return QFileDialog.getOpenFileName(parent,strtitle,init_path,name_filter,name_filter) #parent,strtitle,init_path,'','',options=QFileDialog.ExistingFile )
		
	
# setdir
def set_file( widget,validation_fun=None,dir=False,parent=None,init_path=os.getcwd(),title="Select relevant file",on_change_fun=None):

	# print('dir')
	
	name_filter=''
	if dir:
		title="Select directory"
		name_filter='dir'
		
	while True:
	
		path=get_file_dialog(title,init_path,parent,name_filter) 
		if path=='':
			return 
			
		elif validation_fun==None or validation_fun(path):
		
			if widget==None:
				return path
		
			change=False
			
			if type(path)==type('asdf'):
				if path!=widget.text():
					change=True
			
				widget.setText(path )
				widget.setToolTip(path )
			
			else:
				if path[0]!=widget.text():
					change=True
				widget.setText(path[0])
				widget.setToolTip(path[0])
			
			if on_change_fun!=None and change:
				on_change_fun()
				
			if parent!=None:
				parent.parent().adjustSize()
			break
			
		else:
			messagebox_showinfo("Path is not correct!", "Select apropriate path!",parent )
	
	
# copy from clipboard clipboardclipboard
def copy(btn,txt):
	cli=QApplication.clipboard()
	cli.setText(txt)
	messagebox_showinfo('Value ready in clipboard','Value ready in clipboard:\n'+txt,btn)
	# print(btn)
	if btn!=None:
		xtmp=btn
		for ii in range(5):
			if hasattr(xtmp,'parent'):
				if xtmp.parent()!=None:
					xtmp=xtmp.parent()
			else:
				break
		# print('close?')
		xtmp.close()	
	
	# if hasattr(btn,'parent'):
		# btn.parent().close()		
	# if hasattr(btn,'parent'):
		# btn.parent().close()
		
		# btn.parent().parent().parent().parent().parent().close()
	
	
class CopyDialog(QDialog):
	def __init__(self, parent = QWidget(),strtitle='',stroutput=('',) ):
	
		super(CopyDialog,self).__init__(parent)
		
		self.setMinimumWidth(256)
		self.setMaximumWidth(512)
		strtitle_split=strtitle.split('.')
		tmptitle=strtitle  
		tmpcont=strtitle
		
		if len(strtitle_split)>1:
			tmptitle= strtitle_split[0]
			tmpcont='.'.join(strtitle_split[1:])
		
		self.setWindowTitle(tmptitle)
		self.label = QLabel(strtitle+'\n\n'+stroutput[0])
		self.label.setWordWrap(True)
		
		self.cpbutton = Button( self,name='Copy',actionFun=copy,args=stroutput)

		layout = QVBoxLayout()
		layout.addWidget(self.label )
		layout.addWidget(self.cpbutton )
		self.setLayout(layout)	
		self.exec_()

def output_copy_input(parent = QWidget(),strtitle='',stroutput=('',)):	
	
	cd=CopyDialog(parent ,strtitle ,stroutput )
		
	
class CmdYesNoDialog(QDialog):
	def __init__(self, parent = None,strtitle='',opt=[],cmdfun=None):
	
		super(CmdYesNoDialog,self).__init__(parent)
		
		self.setMinimumWidth(256)
		self.setMaximumWidth(512)
		self.setWindowTitle(strtitle)
		self.label = QLabel(strtitle )
		self.label.setWordWrap(True)
		
		self.optbox=Combox(parent ,items_list=opt)
		
		self.okbutton = Button( self,name='Enter',actionFun=self.enter_button, args=([cmdfun, ],) ) # [cmdfun,self.optbox.currentText()]

		layout = QVBoxLayout()
		layout.addWidget(self.label )
		layout.addWidget(self.optbox )
		layout.addWidget(self.okbutton )
		self.setLayout(layout)	
		self.exec_()	
		
	def enter_button(self,btn,args ):
		# print(btn,args)
		# print(self.optbox.currentText())
		# args[0](args[1])
		args[0](self.optbox.currentText())
			
		self.close()
	
def simple_opt_box(parent = QWidget(), strtitle='',opt=[],cmdfun=None):
	CmdYesNoDialog(parent,strtitle,opt,cmdfun)
	
	
	
# def ask_password(tmpval,title='Enter password',lbl='Enter password to decrypt file',fun_run_after=None):
class PassForm(QDialog):
	def __init__(self, tmpval, first_time, parent = None,fun_run_after=None,title="Enter password to decrypt wallet and database"):
	
		super(PassForm,self).__init__(parent)
		self.setGeometry(128, 128, 512, 128)
		
		self.tmpval=tmpval
		self.fun_run_after=fun_run_after
		
		if first_time:
			title="Set up a password for wallet and database encryption"
		
		self.setWindowTitle(title)
		self.password = QLineEdit(self)
		self.password.setEchoMode(QLineEdit.Password)
		
		self.showbutton = Button( self,name='Show',actionFun=self.show_button)
		self.okbutton = Button( self,name='Enter',actionFun=self.quit_button)
		self.okbutton.setDefault(True)
		
		layout = QGridLayout()
		layout.addWidget(self.password,0,0)
		layout.addWidget(self.showbutton,0,1)
		layout.addWidget(self.okbutton,1,0,1,2)
		self.setLayout(layout)	
		self.setAttribute(Qt.WA_QuitOnClose,False)
		self.exec_()
		
	def quit_button(self,btn ):#,args
		# print(self,args,misc)
		tmppas=self.password.text().strip()
		if tmppas!='':
			self.tmpval.append(tmppas)
			if self.fun_run_after!=None:
				self.fun_run_after(self.tmpval)
			
			self.close()
		
		
	def show_button(self,btn ):#,args
		
		if btn.text()=='Show':
			btn.setText('Hide')
			self.password.setEchoMode(QLineEdit.Normal)
		else:
			btn.setText('Show')
			self.password.setEchoMode(QLineEdit.Password)
	
	
	
	
# accept table widget inside
# and "go button" closes it !	
class CustomDialog(QDialog):

	# table_widget must have function to quit this dialog 
	def __init__(self, parent = None , table_widget=None, title='',wihi=None, defaultij=[]):
	
		super(CustomDialog,self).__init__(parent)
		# self.tmpval=tmpval
		if wihi!=None:
			self.setGeometry(128, 128, wihi[0], wihi[1])
		
		self.setWindowTitle(title)
		# self.setAttribute(Qt.WA_QuitOnClose,True)
		# self.setAttribute(Qt.WA_DeleteOnClose,True)
		self.setSizeGripEnabled(True)
		# self.widgets=[]
		# self.setSizeAdjustPolicy(QComboBox.AdjustToContents)
		
		# QWidget {font-family:'Open Sans','Helvetica Neue',Helvetica,Arial,DejaVu }	
				# QFrame { border:none;}
				# QTabBar {background-color:rgba(255, 255, 255, 1);}
				 # QPushButton {background-color:#ddd; border-style: solid;   border-width: 1px; border-color: #aaa; padding:3px; margin:3px;min-width:32px;}
				 # QPushButton:hover {background-color:#eee;   border-width: 1px; border-color: green;}
				 # QPushButton:pressed {background-color:lightgreen;   border-width: 1px; border-color: green;}
				 # QComboBox {background-color:white; border-style: solid;  border-width: 1px; border-color: #aaa; padding:3px; margin:3px;}
				 # QComboBox QAbstractItemView {background-color:white;selection-background-color: lightgray;border-style: solid;  border-width: 1px; }
				 # QLineEdit {background-color:white; border-style: solid;  border-width: 1px; border-color: #aaa; padding:3px; margin:3px;}
				 # QAbsractScrollArea {border-style:none}
		tmp_style = """ 
		
				 QTableWidget  {border-color:rgba(255, 255, 255, 1);}
				 QHeaderView  { border-color:rgba(255, 255, 255, 1); }
				""" 
		self.setStyleSheet(tmp_style)	
			
		if table_widget!=None:
			layout = QVBoxLayout() #
			
			if type(table_widget)==type([]):
				for ww in table_widget:
					layout.addWidget(ww)
			else:
				layout.addWidget(table_widget)
				
			
			self.setLayout(layout)	
			QApplication.processEvents()
			
			if len(defaultij)==2 and type(table_widget)!=type([]): #default button, only if table widget is single widget 
				table_widget.cellWidget(defaultij[0],defaultij[1]).setDefault(True)
			
			# print(table_widget.parent())
			self.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
			# self.adjustSize()
			
			
			self.exec_()
			
		
	def widgetAt(self,idx):
		return self.layout().itemAt(idx).widget()
		
		
	def keyPressEvent(self,event):
		if event.key()==Qt.Key_Enter or event.key()==Qt.Key_Return:
			return
		# QDialog.keyPressEvent(event)
	
	
	
	
	
	
	
	
	
	
	
	
	
	



class Button(QPushButton):	

	def updateButton(self,name='',actionFun=None,args=None,tooltip=''):
		# print(args)
		if name!='':
			self.setText(name)
			
		if tooltip!='':
			self.setToolTip(tooltip)
			
		if actionFun!=None:
			self.clicked.disconnect()
			self.fun=actionFun
			self.args=args
			
			def fun_on_off():
				self.setEnabled(False)
				if args!=None: actionFun(self,*args) 
				else: actionFun(self ) 
				self.setEnabled(True)
				
			self.clicked.connect(lambda  : fun_on_off() )
			# if args!=None:
				# self.clicked.connect(lambda   : actionFun(self,*args))
			# else:
				# self.clicked.connect(lambda  : actionFun(self ))
	
		# print(actionFun,args)

	def __init__(self,parent,name='',actionFun=None,args=None,tooltip=''): #item_list=[{'text'}]  OR item_list=[{'text','userdata'},{}]
		super(Button, self).__init__(name ,parent)
		
		
		self.args=args
		self.setFocusPolicy(Qt.ClickFocus)
		# self.setDefault(False)
		if actionFun!=None:
			# print(actionFun,args)
			self.fun=actionFun
			
			def fun_on_off():
				self.setEnabled(False)
				if args!=None: actionFun(self,*args) 
				else: actionFun(self ) 
				self.setEnabled(True)
				
			self.clicked.connect(lambda  : fun_on_off() )
			
			# if args!=None:
				# self.clicked.connect(lambda   : actionFun(self,*args))
			# else:
				# self.clicked.connect(lambda  : actionFun(self ))
			
		if tooltip!='':
			self.setToolTip(tooltip)
			
		self.setStyleSheet('QPushButton {padding:2px;font-size:13px;}')
		
		
	
	def set_fun(self,no_self,actionFun,*args):
	
		if hasattr(self,'fun'):
			return
			
		self.fun=actionFun
		
		def fun_on_off():
			self.setEnabled(False)
			if no_self: actionFun( *args) 
			else: actionFun(self,*args ) 
			self.setEnabled(True)
				
		self.clicked.connect(lambda  : fun_on_off() )
	
		# if no_self:
			# self.clicked.connect(lambda  :  actionFun(*args))
		# else:
			# self.clicked.connect(lambda  :  actionFun(self,*args))
			
			
	# def keyPressEvent(self,event):
		# self.fun(self,args)
	
	# def __lt__(self,other): 
		# if str(self.text()) <  str(other.text()) :
			# return True
		# return False




	
class FramedWidgets(QGroupBox):
	def __init__(self,parent ,name=None,widgets=[],layout=None ):
		super(FramedWidgets, self).__init__(name,parent)
		if layout==None:
			layout=QHBoxLayout()
		
		self.setLayout(layout)
		self.widgets=[]
		# self.layout=layout
		# print('frame widget init size',self.width(),self.height())
		for ww in widgets:
			self.widgets.append( self.layout().addWidget(ww) )
			# ww.setParent(self)
			
			
		tmpcss="""
					QGroupBox {background-color:rgba(245,245,245,1)}
					QGroupBox QPushButton {background-color:#ddd; border-style: solid;   border-width: 1px; border-color: #aaa;}
					QGroupBox QPushButton:hover {background-color:#eee;   border-width: 1px; border-color: green;}
					QGroupBox QPushButton:pressed {background-color:lightgreen;   border-width: 1px; border-color: green;}
				"""
		self.setStyleSheet(tmpcss)
		# self.setSizePolicy(QSizePolicy.Preferred,QSizePolicy.Preferred)
	
	def insertWidget(self, wdgt, row=-1, col=-1):
		
		if row>-1:
			self.widgets.append( self.layout().addWidget(wdgt, row, col) )
		else:
			self.widgets.append( self.layout().addWidget(wdgt) )
			
		# self.adjustSize()
		# print('frame widget after size',self.width(),self.height())
		
	def widgetAt(self,idx):
		return self.layout().itemAt(idx).widget()
	
	
class Tabs(QTabWidget):
	def __init__(self,parent ):
		super(Tabs, self).__init__(parent)
		self.index=[]
		# QTabBar::tab  {background-color:rgba(245, 245, 245, 1);}
		# css="""
				# QTabWidget::pane {background-color:rgba(245, 245, 245, 1);}
				
			# """		
			# https://www.qt.io/blog/2007/06/22/styling-the-tab-widget
		# self.setStyleSheet(css)
		
	def insertTab(self,tab_dict={'name':QWidget()}):
		for k,v in tab_dict.items():
			self.index.append( self.addTab(v,k) )	
			# v.setParent(self)
		

		
		
class Combox(QComboBox):		

	def __init__(self,parent ,items_list=[],actionFun=None,every_click=False,args=None): #item_list=[{'text'}]  OR item_list=[{'text','userdata'},{}]
		super(Combox, self).__init__(parent)
		# sorted(threads_aa.keys(),reverse=True)
		self.orig_items_list= items_list.copy()
		self.orig_items_values=[] #sorted(items_list) #.copy()
		self.every_click=every_click
		
		if 'text' not in items_list[0]: # assume convert:
			self.orig_items_values=sorted(items_list)
			items_list=[{'text':il} for il in items_list]
		else:
			self.orig_items_values=sorted([ii['text'] for ii in items_list])
		# print(items_list)
		
		for jj,ii in enumerate(items_list):
			if 'userdata' not in ii:
				ii['userdata']=ii['text']
			self.addItem(ii['text'],ii['userdata'])
			self.setItemData(jj, ii['text'], Qt.ToolTipRole)
			
		self.setCurrentIndex(0)
		# self.setSizeAdjustPolicy(QComboBox.AdjustToContents)
		
		if actionFun!=None:
		
			self.fun=actionFun
			# self.currentIndexChanged.connect(lambda: actionFun(self))	# self.currentText() self.currentData(Qt.UserRole) inside actionFun will get our values 
			if self.every_click:
				# self.activated.connect(lambda: actionFun(self))
				
				if args!=None:
					self.activated.connect(lambda   : actionFun(self,*args))
				else:
					self.activated.connect(lambda  : actionFun(self ))
			else:
				if args!=None:
					# self.activated.connect(lambda  : actionFun(self,*args))
					self.currentTextChanged.connect(lambda  : actionFun(self,*args))
				else:
					# self.activated.connect(lambda : actionFun(self ))
					self.currentTextChanged.connect(lambda  : actionFun(self))	# self.currentText() self.currentData(Qt.UserRole) inside actionFun will get our values 
		
		self.setStyleSheet('QComboBox {padding:3px;font-size:13px;}')
		
	def text(self):
		return self.currentText()
		
	# currentIndex()	
	# currentText()
	def setIndexForText(self,txt):
		fid=self.findText(txt, Qt.MatchExactly)
		if fid==-1: fid=0
		
		self.setCurrentIndex( fid )
		
	
	def set_fun(self,actionFun,*args ):	
		# print('combox setfin',actionFun,*args)
		if hasattr(self,'fun'):
			return 
			
		self.fun=actionFun
	
		if self.every_click:
			self.activated.connect(lambda  : actionFun(self,*args))
		else:
			# print('setting function',args)
			self.currentIndexChanged.connect(lambda  : actionFun(self,*args ))
		
	def replace(self,old_item_name,new_item={}): # new_item={'text'} or {'text','userdata'}
		idx=self.findText(old_item_name,Qt.MatchExactly)
		if 'userdata' not in new_item:
			new_item['userdata']=new_item['text']
		self.insertItem(idx,new_item['text'],new_item['userdata'])
		self.setItemData(idx, new_item['text'], Qt.ToolTipRole)

		
	# insert new, but do not delete old 
	def updateBox(self,new_items_list=[]):
		# self.orig_items_list=items_list
		tmp_new_items_arr=[]
		
		if 'text' not in new_items_list[0]: # assume convert:
			tmp_new_items_arr=sorted(new_items_list) 
		else:
			tmp_new_items_arr=sorted([ii['text'] for ii in new_items_list])
		
		if str( tmp_new_items_arr )==str(self.orig_items_values):
			# print('\nsame box values')
			return
		
		
		
		# self.orig_items_list=sorted(new_items_list)
		
		# self.orig_items_list=new_items_list.copy()
		# delete if old item not in new items
		# insert if new item list contains sth additional
		tmp=self.currentText()
		new_box_items=[]
		for ni in new_items_list:
			
			# self.orig_items_list.remove(ni)
			if type(ni)!=type({}):
				ni={'text':ni,'userdata':ni}
				
			new_box_items.append(ni['text'])
			
			if ni['text'] not in self.orig_items_list:
			
				# new_box_items.append(ni['text'])
			
				# if 'userdata' not in ni:
					# ni['userdata']=ni['text']
				
				self.addItem(ni['text'],ni['userdata'])
				self.setItemData(self.count()-1, ni['text'], Qt.ToolTipRole)
			# else:
				
		# for oi in self.orig_items_list:
			# self.orig_items_list.remove(ni)
		
		self.orig_items_list=new_box_items.copy()
		for ii in range(self.count()-1,-1,-1):
			# tt=
			if self.itemText(ii) not in self.orig_items_list:
				self.removeItem(ii)
			
		self.setIndexForText( tmp)

		
		
		
		
		
		# LineEdit(None, tmpname,'',tmpdef,tmptt )	
class LineEdit(QLineEdit):			
	def __init__(self,parent ,field_name='',placeholder_txt='',default_value='',tooltip=''):
		# try:
		super(LineEdit, self).__init__(default_value,parent)
		self.setPlaceholderText(placeholder_txt)
		self.field_name=field_name
		if tooltip!='':
			self.setToolTip(tooltip)
			
		self.setStyleSheet(" QLineEdit {background-color:white; border-style: solid;  border-width: 1px; border-color: #aaa;}" )
		
		
	def eventFilter(self, source, event):
		# print('EVENT',source)
		if (event.type() == QEvent.KeyPress and source is self):
			if event.key() in [int(Qt.Key_Enter),int(Qt.Key_Return) ]:
				# print('key press:', (event.key(), event.text()),int(Qt.Key_Enter),int(Qt.Key_Return))
				self.label_to_set_on_enter.setText(self.text().strip())

		return super(LineEdit, self).eventFilter(source, event)		
		
		
		
	def setEventFilter(self,lbl2set):
		self.installEventFilter(self ) #.parent().parent().parent()
		self.label_to_set_on_enter=lbl2set
		
		
		
	def addValidator(self,vtype,rrange=[]): #vtype=int,float
		qv=None 
		self.rrange=rrange
		x1,x2=0,0
		if len(rrange)==2:
			x1,x2=rrange[0],rrange[1]
		# print(x1,x2)
		self.textChanged.connect(self.test_validation)
		
		if vtype==float:
			if len(rrange)==2:
				qv=QDoubleValidator(float(x1),float(x2),8,self)
			else:
				
				qv=QDoubleValidator( self)
		elif vtype==int:
			if len(rrange)==2:
				qv=QIntValidator(int(x1),int(x2),self)
			else:
				qv=QIntValidator( self)
		elif vtype=='custom':
		
			return # range[0]=custom function, int ii1, int ii2
			
		# print(qv)
		qv.setLocale(QLocale(QLocale.English)) #,QLocale.Germany
		# print(qv.bottom(),qv.top(),qv.decimals(),qv.locale())
		self.setValidator(qv)
		
		
		
	def test_validation(self):
		# print('validator')
		if self.text().strip()=='':
			return
		
		try:
			
			if type(self.validator()) ==   QDoubleValidator : #.decimals()==8: # check float
				x=float(self.text().strip())
				
				if x<self.validator().bottom() or x>self.validator().top():
					messagebox_showinfo('Wrong value in '+self.field_name, 'Value out of range! Please correct value '+self.text()+' in '+self.field_name+'.\n'+self.toolTip(),self)
			elif type(self.validator()) ==  QIntValidator :
				ii=int(self.text().strip())
				if ii<self.validator().bottom() or ii>self.validator().top():
					messagebox_showinfo('Wrong value in '+self.field_name, 'Value out of range! Please correct value '+self.text()+' in '+self.field_name+'.\n'+self.toolTip(),self)
			else:
		# if True:
			# if True:
				if hasattr(self,'property'):
					rowii=self.property('rowii')
					parwidget=self.parent().parent()
					# print(parwidget,rowii)
					tmpaddrelem=parwidget.cellWidget(rowii,self.rrange[2]) 
					tmpoutelem=parwidget.item(rowii,self.rrange[1]) 
					# print(tmpaddrelem ,tmpoutelem )
					self.rrange[0](self,tmpoutelem,tmpaddrelem)
		
		except:
			messagebox_showinfo('Wrong value in '+self.field_name, 'Please correct value '+self.text()+' in '+self.field_name+'.\n'+self.toolTip(),self)	
	
		

class Label(QLabel):			
	def __init__(self,parent,txt,tooltip='',transparent=True ):
		super(Label, self).__init__(txt ,parent)
		self.maxWidth=None
		# self.setSizePolicy(QSizePolicy)
		if transparent:
			self.setAttribute(Qt.WA_TranslucentBackground)
		if tooltip!='':
			self.setToolTip(tooltip)
			
		# self.ltype=ltype
		

		
			
class TableCell(QTableWidgetItem):
	def __init__(self, value,ttype,aalign=None, rowii=None ): # ttype= float, int, str
		super(TableCell, self).__init__(value)
		self.ttype=ttype
		self.rowii=rowii
		
		if ttype==QDateTime:
			tmsplit=value.strip().split()
			tmpdatetime=tmsplit[0]+'T'+tmsplit[-1]   #tm[2].replace(' ','T')
			self.typedvalue=QDateTime.fromString(tmpdatetime,Qt.ISODate)
		else:
			self.typedvalue=self.ttype(value)
			
		if aalign!=None:
			if 'center':
				self.setTextAlignment(Qt.AlignCenter)
			elif 'right':
				self.setTextAlignment(Qt.AlignRight)
			elif 'left':
				self.setTextAlignment(Qt.AlignLeft)
				
		# if fsize>0:
			# self.setStyleSheet(" QTableWidgetItem {font-size:"+fsize+"px;}" )
		# self.setSizePolicy(QSizePolicy.Minimum,QSizePolicy.Minimum)
		
	def __lt__(self,other):
	
		if self.ttype==str:
			# print('comparing',self.typedvalue.lower(),'<',other.typedvalue.lower(),self.typedvalue.lower() < other.typedvalue.lower())
			if self.typedvalue.lower() < other.typedvalue.lower() :
				# if self.typedvalue <  other.typedvalue :
				return True
	
		elif self.typedvalue <  other.typedvalue :
			return True
			
		return False
		

class TextEdit(QTextEdit):			
	def __init__(self,parent ,txt='' , maxWidth=None):
		super(TextEdit, self).__init__(txt,parent)
		self.textChanged.connect(self.updateGeometry)
		self.maxWidth=maxWidth
		
	def sizeHint(self):
		# print(' TEXTEDIT size hint')
		hint =super().sizeHint()
		if self.maxWidth!=None:
			width =self.maxWidth
			doc = self.document().clone()
			doc.setTextWidth(width)
			# print('orig height',round(doc.size().height()))
			# nlines=doc.lineCount() #doc.blockCount()
			# print(self.toPlainText() ,'nlines',nlines,'width',width)
			# print('doc.characterCount()',doc.characterCount())
			# print(doc.size().height(),self.frameWidth())
			
			height = round(doc.size().height()+self.frameWidth() * 2)
			
			# wrongl shows nlines always 1 need t ofix it :
			if doc.characterCount()<104: #nlines==1:
				height = round(doc.size().height()*2+self.frameWidth() * 2)
				
			# print('orig height plust frame',height)
			if self.horizontalScrollBar().isVisible():
				height += self.horizontalScrollBar().height()
				# print('addbar',self.horizontalScrollBar().height())
			# print(' plust scrollbar',height)
			hint.setHeight(height)
			hint.setWidth(width)
			# print('calc hint',hint)
			return hint
		else:
			return super().sizeHint()
		

# importante: row indexes can be on or off if needed
# size options:
# setSectionResizeMode per vertical or horizonal section
# or setRowHeight and setRowHeight
class Table(QTableWidget):

	def __init__(self, parent=None, params={}):
		# print('params',params)
		self.params=params
		self.updatable=False
		self.tableUpdating=False
		if 'updatable' in params:
			self.updatable=True 
			params['dim'][1]+=1 # more columns 
			
		rows=params['dim'][0]
		cols=params['dim'][1]
		self.last_col_ii=cols-1
		
		super(Table, self).__init__(rows,cols,parent)
		
		if  self.updatable:
			self.hideColumn(self.last_col_ii) 
		
		# self.rowUIDs={} row names work as ids, and row data as checker if to update 
		self.row_key_svalue={}
		# self.col_names=[]
		
		self.setCornerButtonEnabled(False)
		self.setFocusPolicy(Qt.NoFocus)
		self.setEditTriggers(QAbstractItemView.NoEditTriggers)
		# self.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
		self.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding) #Maximum
		
		# print('table hint',self.sizeHint())
		self.indexedRowNames={} # rowk:ii # vertical heaer item is mixing order 
		
		if 'maxHeight' in params:
			self.setMaximumHeight(params['maxHeight'])
			
		## SECTIONS:
		self.hideColumns=[]
		if 'hideColumns' in params:
			if type(params['hideColumns'])==type([]):
				self.hideColumns=params['hideColumns']
				
		# print('self.hideColumns',self.hideColumns )
		
		self.hideColNames=False
		if  'hideColNames' in params:
			self.hideColNames=True
		# if 'hideColumns' in params: # if all hide here, otherwise hide in update table loop by selected name !
			'all'
			# if params['hideColumns']=='all':
				# for cc in range(self.columnCount()):
					# self.hideColumn(cc)
			# elif type(params['hideColumns'])==type([]):
				# self.hideColumns=params['hideColumns'] #self.hideColumn(cc)
		
		self.verticalHeader().hide()
		# self.verticalHeader().setMinimumSectionSize(258)
		if 'maxColSize' in params:
			self.verticalHeader().setMaximumSectionSize(params['maxColSize'])
			self.verticalHeader().setMaximumWidth(params['maxColSize'])
			self.verticalHeader().setStretchLastSection(True)
		else:
			self.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
			
		# print('\n\nTABLE ADJ POLICY',self.sizeAdjustPolicy(),self.sizePolicy() )
		
		self.horizontalHeader().sectionClicked.connect(self.clickDetected)
		
		self.horizontalHeader().setMinimumHeight(32)
		self.horizontalHeader().setDefaultAlignment(Qt.AlignLeft|Qt.AlignTop)
		
		if 'toContent' in params:
			self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
			self.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
		
		# optional params ON OFF	
		


		# default is interactive
		# self.constWidthColumns=False
		if 'colSizeMod' in params:
			# print('colSizeMod',params['colSizeMod'])
			for ii,mm in enumerate(params['colSizeMod']):
				if mm=='stretch':
					self.horizontalHeader().setSectionResizeMode(ii,QHeaderView.Stretch)
				elif mm=='toContent':
					self.horizontalHeader().setSectionResizeMode(ii,QHeaderView.ResizeToContents)
					
				else:
					# self.setMinimumColumnWidth(ii,mm)
					self.setColumnWidth(ii,mm)
					# self.constWidthColumns=True
					# print('col wid',ii,mm)
					
		# default is interactive
		if 'rowSizeMod' in params:
			self.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
			
		self.sortable=False
		self.lockSorting=False
		if 'sortable' in params:
			self.setSortingEnabled(True)
			self.sortable=True
			
		# if "show_grid" in params:
			# self.setShowGrid(params["show_grid"])
		self.setShowGrid(False)
		
		self.sort_col=''		
		if 'default_sort_col' in params:
			self.sort_col=params["default_sort_col"]
			# self.sortable=True
			# self.setSortingEnabled(True)
			# print('self.sort_col',self.sort_col)
		
		
		
		## STYLING CSS
		# QHeaderView::section:horizontal {margin-right: 2; border: 1px solid}"
		
		tmp_header_bg_color = "rgba(245, 245, 245, 1);"
		 # QTableWidget::item:edit-focus { background-color:%s; border:none; color:black;}
		 # QWidget  { background-color:%s; border:none; margin:5px; padding:5px;}
		tmp_style = """
					QTableWidget::item { background-color:%s; border-style:none;}
					QTableWidget::item:selected { background-color:%s; border-style:none; color:black }
					QHeaderView::section { background-color:%s; border-style:none; padding:0px; margin:0px;line-height:normal;}
					QTableCornerButton::section { background-color:%s; border-style:none; }
					QTableWidget QPushButton {background-color:#ddd; border-style: solid;   border-width: 1px; border-color: #aaa; padding:3px; margin:3px;}
					QTableWidget QPushButton:hover {background-color:#eee;   border-width: 1px; border-color: green;}
					QTableWidget QPushButton:pressed {background-color:lightgreen;   border-width: 1px; border-color: green;}
					QTableWidget QComboBox {background-color:white; border-style: solid;  border-width: 1px; border-color: #aaa;}
					QTableWidget QComboBox:item { selection-background-color: lightgreen; } 
					QTableWidget QComboBox QAbstractItemView {selection-background-color: lightgreen;border-style: solid;  border-width: 1px; }
					QTableWidget QLineEdit {background-color:white; border-style: solid;  border-width: 1px; border-color: #aaa;}
					QTableWidget {margin:2px;padding:2px;font-size:13px; font-family:'DejaVu';border-style:none; }
					QHeaderView {font-size: 13px; padding:0px; margin:0px;font-family:'DejaVu';border-style:none;  }
					QHeaderView::section:horizontal {font-size: 13px; padding:0px; margin:0px;font-family:'DejaVu';border-style:none;  }
					""" % (
			
			tmp_header_bg_color,
			tmp_header_bg_color,
			tmp_header_bg_color, #"rgba(45, 245, 245, 1);", #tmp_header_bg_color,
			tmp_header_bg_color
		)
# QTableWidget QLineEdit {background-color:white; border:inset;}
		self.setStyleSheet(tmp_style)
		# print(tmp_style)
		
		

	# colnames getting zeroed 
	# update which column currently  sorted in canse of insert to be in correct order 
	def clickDetected(self):
		# print('click',self.sender().metaObject().className())
		if self.blockUpdate('sorting'):
			return
		# maxwait=3
		# while self.tableUpdating: #self.lockSorting or 
			# print('self.lockSorting', maxwait,self.tableUpdating)
			# time.sleep(0.2)
			# maxwait=maxwait-1
			# if maxwait<0:
				# print('return give up sorting ' )
				# return
				
		self.tableUpdating=True
		
		if hasattr(self,'col_names') and self.sender().metaObject().className()==QHeaderView.staticMetaObject.className():
			if len(self.col_names)>0:
				tmpsender=self.sender()
				self.sort_col=self.col_names[tmpsender.sortIndicatorSection()]
			# print(self.sort_col)
		self.tableUpdating=False	
			# sortidx=self.col_names.index(self.sort_col)
			# tmpord=self.horizontalHeader().sortIndicatorOrder()
			# self.sortByColumn(sortidx, tmpord)
			# print(tmpsender.sortIndicatorOrder(),self.sort_col)
		
		
	# updateTable should mek this  
	# of for reason of updatable table : row ids resort 
	# def insert_at(self,widgets_line,at_line):
		# wasSortingEnabled=self.isSortingEnabled()
		# if wasSortingEnabled:
			# self.setSortingEnabled(False) 
		# self.setWidgetRow(widgets_line,at_line) 
			
		# if wasSortingEnabled:
			# self.setSortingEnabled(True)
			# tmpord=self.horizontalHeader().sortIndicatorOrder()
			# tmpidx=self.horizontalHeader().sortIndicatorSection()
			# self.sortByColumn(tmpidx, tmpord)

	# cellType= item or widget
	def blockUpdate(self,tt=''):
		maxwait=3
		while self.tableUpdating: #self.lockSorting or 
			# print('self.tableUpdating', maxwait,self.tableUpdating)
			time.sleep(0.3)
			maxwait=maxwait-1
			if maxwait<0:
				# print(' give up ', tt)
				return True
				
		return False
	
	def filtering(self,cellType,colnum,fopt ):
		if self.blockUpdate('filtering'):
			return
			
		self.tableUpdating=True	
		for ii in range(self.rowCount()):
			tmpcurcat='xxx'
			# print(ii,colnum,cellType,fopt)
			# print(self.cellWidget(ii,colnum).text())
			if cellType=='widget': tmpcurcat=self.cellWidget(ii,colnum).text()
			elif cellType=='item' : tmpcurcat=self.item(ii,colnum).text()
			# elif cellType=='item_date' : tmpcurcat=self.item(ii,colnum).text()
			else:
				print('Wrong filter value cellType')
				self.tableUpdating=False	
				return
			
			t1= fopt in ['All',tmpcurcat]
			t2= fopt=='Not hidden' and  tmpcurcat!='Hidden'
			# print(t1,t2,tmpcurcat)
			if t1 or t2:
				# print('show')
				self.showRow(ii)
			else:
				# print('hide')
				self.hideRow(ii)
				
		self.tableUpdating=False		
		
	# MORE OPTIMAL pass styling and withd separately no to separate in loop just apply separately 
	# currently backword compatible but less optimal 
	# updatable separates styling and withds
	# not updatable take as is 
	# if updatable - additional hidden column created if self.updatable:				rr['rowv']=rr['rowv'] + [{'T':'LabelV', 'L':rr['rowk'] }]
	# for sorting reason by default it takes row names
	# add sorting columns allowed ? also default sorting column ? 
	# also hidden columns ? in that case create column external! no need to do rr['rowv']=rr['rowv'] + [{'T':'LabelV', 'L':rr['rowk'] }] and add artificial column ...
	# steps:
	# [ok] add hidden column and use it as default sorting column 
	# [off prev solution]
	def updateTable(self,widgets_dict,col_names=[],insert_only=False,reset_values=False,doprint=False):
	 
		if self.blockUpdate('tableUpdating'):
			return [] 
		 
		self.tableUpdating=True
		
		if hasattr(self,'widgets_dict'):
			if str(widgets_dict)==self.widgets_dict: # no change return
				if doprint: print('updateTable # no change return')
				
				# self.lockSorting=False
				self.tableUpdating=False
				return []
				
			# print('self.widgets_dict\n',self.widgets_dict)
			# print('str(widgets_dict)\n',str(widgets_dict))
			# else:
				# self.widgets_dict=str(widgets_dict)
		self.widgets_dict=str(widgets_dict)
	
		# print('update table col_names',col_names,self.col_names)
		if col_names==[]:
			if hasattr(self,'col_names')==False: # if first time 
				self.horizontalHeader().hide()
		else:
			
			self.col_names=col_names 
			self.setHorizontalHeaderLabels(col_names) 
			if self.hideColNames :
				self.horizontalHeader().hide()
				
			# print(col_names,self.hideColumns)
			for ii,cc in enumerate(col_names):
				# print(ii,cc)
				if cc in self.hideColumns:
					self.hideColumn(ii) 
					# print('hiding column',ii,cc)
			
		# is this still needed ?
		# if self.updatable:
			# self.last_col_ii=self.columnCount()-1
			# if self.last_col_ii>-1: self.hideColumn(self.last_col_ii)
			# if this works the rowid can be taken from self.item(rr,0).text() like previously from vertical header jsut sorted!
					
			
		# sorting off
		wasSortingEnabled=self.isSortingEnabled()
		if wasSortingEnabled:
			self.setSortingEnabled(False)
			
		if reset_values: # if new values less then old - only remove exceeding rows 
			# if len(tmpCurrentRowIDs)==0 and len(currentRowsIDs)>0: # remove all 
			tmpl=self.rowCount()
			newmaxrowcount=len(widgets_dict)
			# print('remove rows start,',tmpl,newmaxrowcount)
			while tmpl>newmaxrowcount:
				self.removeRow(tmpl-1)
				tmpl-=1 #self.rowCount()
			# print('remove rows end,',tmpl)
			 
		# if init - connect ii,jj with row uids 
		tmpCurrentRowIDs=[]
						
		# def update_rowids(alsoItem=False): # on init may be different when sorting clicked
			
			# tmp_indexedRowNames=self.indexedRowNames.copy() # UPDATE CURRENT INDEXES FROM ORIG SOURCE 
			# if len(tmp_indexedRowNames)>0:
				# indexedRowNames_values=list(tmp_indexedRowNames.values())
				# indexedRowNames_keys=list(tmp_indexedRowNames.keys())
				 
				# for newii in range(self.rowCount()	):
					# tmpi=self.item(newii,0)
					# oldii=tmpi.rowii  
					# kkeyii=indexedRowNames_values.index(oldii)
					# kkey=indexedRowNames_keys[kkeyii]					 
					# tmp_indexedRowNames[kkey]=newii
					# if alsoItem:
						# self.item(newii,0).rowii=newii
						# self.indexedRowNames[kkey]=newii
					
			# return tmp_indexedRowNames
			
		# tmp_indexedRowNames=update_rowids()
		# currentRowsIDs= [ll  for ll in tmp_indexedRowNames]
		__currentRowsIDs=[]
		if self.rowCount()>0 and not reset_values: 
			__currentRowsIDs=[self.item(ll,self.last_col_ii).text()  for ll in range(self.rowCount()	) if self.item(ll,self.last_col_ii) !=None  ] #self.verticalHeaderItem(ii2).text()
		# if self.rowCount()>0 and not reset_values:  
			# for ll in range(self.rowCount()	): # only find ids for non empty widgets:
				# for cc in range(self.columnCount()	):
					# if self.item(ll,cc) !=None and self.cellWidget(ll,cc) !=None:
						# print("ll,cc,",ll,cc,)
						# __currentRowsIDs.append(self.item(ll,cc).text())
						# break # just need first nonempty widget column per row ... 
			
			# __currentRowsIDs=[self.item(ll,0).text()  for ll in range(self.rowCount()	) if self.item(ll,0) !=None  ] #self.verticalHeaderItem(ii2).text()
		
		
		currentRowsIDs=__currentRowsIDs
		# print('comapre currentRowsIDs __currentRowsIDs')
		# print(currentRowsIDs)
		# print(__currentRowsIDs) # use in finding id to update and later to remove / after update ??
		 
		tmpinit=len(currentRowsIDs)==0 and self.rowCount()>0
		
		new_rows=[]
		
		offset=0
		if insert_only:
			offset=self.rowCount()
			
		def applyRowSizeMode(rrrs,iindx): #rr['rowSizeMod']
			if rrrs=='stretch':
				self.verticalHeader().setSectionResizeMode(iindx,QHeaderView.Stretch)
			elif rrrs=='toContent':
				self.verticalHeader().setSectionResizeMode(iindx,QHeaderView.ResizeToContents)	
			else:
				self.setRowHeight(iindx,rrrs)
				
				
		tmp_row_styling={}
		tmp_row_widths={}
		tmp_styling_elements={}
		
		def getElemType(r):
			elem_types=[]
			for jj, w in enumerate(r): 
				
				et=''
				# for jj, w in enumerate(r):
				if w=={}: et=''
					
				elif w['T'] in ['LabelV','LabelC','LabelE','Combox','LineEdit']: et=''
				elif w['T'] in ['QLabel']: et= 'QLabel'	 
				elif w['T'] in ['Button']: et= 'QPushButton'					 
				# elif w['T'] in ['Combox']: return '' 				
				# elif w['T'] in ['LineEdit']: return ''  				
				elif w['T'] in ['TextEdit']: et= 'QTextEdit' # "QTextEdit {%s}" % w['style']
			  	
				elem_types.append(et)
				 
			return elem_types 
		
		
		
		
		tmp_cur_row_ii={}
		
		for iii,rr in enumerate(widgets_dict):
		
			ii=iii+offset
			
			if self.updatable:
				rr['rowv']=rr['rowv'] + [{'T':'LabelV', 'L':rr['rowk'] }] # additional ending column for row names 
				
				tmpCurrentRowIDs.append(rr['rowk'])
				
				# if updatable and style in elements of rr['rowv'] - remove style and save without style in row_key_svalue
				# save style separately and use at the end!
				tmp_row_styling[rr['rowk']]=[]
				tmp_row_widths[rr['rowk']]=[]
				tmp_cur_row_ii[rr['rowk']]=ii
				for ei, ee in enumerate(rr['rowv']):
					if 'style' in ee:
						tmp_row_styling[rr['rowk']].append(ee['style'])
						# print('set styling',rr['rowk'],ee['style'])
						del rr['rowv'][ei]['style']
					else:
						tmp_row_styling[rr['rowk']].append('')
						
					if 'width' in ee:
						tmp_row_widths[rr['rowk']].append(ee['width'])
						del rr['rowv'][ei]['width']
					else:
						tmp_row_widths[rr['rowk']].append(0)
							
				if doprint: print(rr['rowk']," rr['rowv']",rr['rowv'])
				if rr['rowk'] not in currentRowsIDs:
					if doprint: print("rr['rowk'] not in currentRowsIDs")
				
					if not tmpinit or ii>=self.rowCount(): #if new row or more rows then table row count (by mistake)
						if doprint:  print('# case 2 new row',tmpinit,ii,self.rowCount())
						ii=self.rowCount() # case 2 new row
						self.insertRow( ii)
						new_rows.append(ii)
						tmp_cur_row_ii[rr['rowk']]=ii
					else:
						if doprint: print('# case 1 init or mistake',tmpinit,ii>=self.rowCount())
					
					
					
					self.row_key_svalue[rr['rowk']]=str(rr['rowv'])
					tmp_styling_elements[rr['rowk']]=self.setWidgetRow(rr['rowv'],ii)
				 
					if 'rowSizeMod' in rr:
						applyRowSizeMode(rr['rowSizeMod'],ii)
						
				elif str(rr['rowv'])!=self.row_key_svalue[rr['rowk']]:	
					if doprint:  
						print('# case 3 update	')
						print('\t',str(rr['rowv']))
						print('\t',self.row_key_svalue[rr['rowk']])
						
					ii=currentRowsIDs.index(rr['rowk']) 
					tmp_cur_row_ii[rr['rowk']]=ii
										
					self.row_key_svalue[rr['rowk']]=str(rr['rowv'])				
					tmp_styling_elements[rr['rowk']]=self.setWidgetRow(rr['rowv'],ii) #, doprint)
				else:
					if doprint: print('# case 4 same row no update needed')
					# only update styling:
					tmp_styling_elements[rr['rowk']]=getElemType(rr['rowv'])
					tmp_cur_row_ii[rr['rowk']]=currentRowsIDs.index(rr['rowk']) 
			
				
			else: #not updatable, just write cells
				if doprint: print('# case 5 not updatable, just write cells')
				if 'rowk' in rr:
					# print(1032,rr)
					self.setWidgetRow(rr['rowv'],ii)
				else:
					# print('NO ROWK')
					self.setWidgetRow(rr,ii)
		
		# ii jj missing: 
		if doprint: print('\n\n styling:')
		for kk,vv in tmp_styling_elements.items():
			tmpstyles=tmp_row_styling[kk]
			tmpwidths=tmp_row_widths[kk]
			ii=tmp_cur_row_ii[kk]
			if doprint: print('styling kk',kk)
			for jj,el in enumerate(vv):
				if doprint: print('styling jj, el',jj,el,tmpstyles[jj])
				if el!='':
				
					if tmpwidths[jj]>0 and hasattr(self.cellWidget(ii,jj),'maxWidth') :
						if self.cellWidget(ii,jj).maxWidth==None or self.cellWidget(ii,jj).maxWidth!=tmpwidths[jj] : # print('width ',el,tmpwidths[jj])
							self.setWidgetWidth( self.cellWidget(ii,jj),el,tmpwidths[jj])
						
					if tmpstyles[jj]!='':
						if doprint: print('styling?',jj,el)
						tmpstr=el+(" {%s}" % tmpstyles[jj])
						if doprint: print('styling 2 ?',tmpstr)
						if self.cellWidget(ii,jj).styleSheet()==tmpstr:
							if doprint:  print('same stylesheet',tmpstr,self.cellWidget(ii,jj).styleSheet())
							continue # print('final style',ii,jj,tmpstr)
						else:
							if doprint: print('styling 3 yes  ',ii,jj)
							self.cellWidget(ii,jj).setStyleSheet(tmpstr)
			
		
		# print('updated or inserted rows',len(tmpCurrentRowIDs),'all prev rows',len(currentRowsIDs))
		if not insert_only:
			if len(tmpCurrentRowIDs)==0 and len(currentRowsIDs)>0: # remove all 
				# print('remove all')
				tmpl=self.rowCount()
				while self.rowCount()>0:
					self.removeRow(tmpl-1)
					tmpl=self.rowCount()
				
			else:	
				# first find all currentRowsIDs not in tmpCurrentRowIDs
				# find there index
				# reverse order of index 
				# remove 
				# to_remove=[]
				# for ccr in  currentRowsIDs:
					# if ccr not in tmpCurrentRowIDs:
						# to_remove.append(ccr)
						
				__to_remove=[]
				for ccr in __currentRowsIDs:
					if ccr not in tmpCurrentRowIDs:
						__to_remove.append(ccr)
				
				# idx_to_remove=[]
				# for tr in to_remove:
					# tmpi=self.indexedRowNames[tr ]
					# idx_to_remove.append(tmpi)
					# del self.indexedRowNames[tr ]
					
				__idx_to_remove=[]
				for tr in __to_remove: 
					tmpi=__currentRowsIDs.index(tr)
					__idx_to_remove.append(tmpi) 
					
				idx_to_remove=__idx_to_remove
				if len(idx_to_remove)>0:
					idx_to_remove.sort(reverse=True)
					for tmpi in idx_to_remove:
						
						self.removeRow(tmpi )
						
					# update_rowids(alsoItem=True) # reindex item rowii and indexrownames:
					
								
		if not 'maxColSize' in self.params: # impacts channels up row which is not table!?
			self.adjustSize()
		
		# resort if on 
		if wasSortingEnabled:
			self.setSortingEnabled(True)
			# print('SORTINF ON')
			
		# print('SORTINF ?',self.sort_col,self.last_col_ii)
		if self.sort_col!='':
			sortidx=-1
			if hasattr(self,'col_names') and len(self.col_names)>0:
				# print("hasattr(self,'col_names')",self.col_names)
				try:
					# print('sorting',self.sort_col,self.col_names)
					sortidx=self.col_names.index(self.sort_col)
					# print(sortidx)
				except:
					print('WARNING - sort column name WRONG sortidx=',sortidx)
					sortidx=-1
			 
				if sortidx<0: sortidx=0 
				
				tmpord=self.horizontalHeader().sortIndicatorOrder()
				# print('SORTING',sortidx, tmpord)
				self.sortByColumn(sortidx, tmpord)
			# elif self.sort_col=='__rowii': # sorting by rownames e.g. dates 
				# sortidx=self.last_col_ii
				# tmpord=self.horizontalHeader().sortIndicatorOrder()	# print('sorting __rowii',sortidx)
				# self.sortByColumn(sortidx, tmpord)
		
		# self.lockSorting=False
		self.tableUpdating=False
				
		return new_rows
		
		# rpt iunder znu orig rpt cant send ...
		
	
	def setWidgetRow(self,r,ii,doprint=False):
		# print('\n\nnew row',r)
		elem_types=[]
		for jj, w in enumerate(r):
			# print(w,ii,jj)
			et=self.setWidgetCell(w,ii,jj,doprint )
			elem_types.append(et)
			
			
		if 'rowSizeMod' in self.params:
			self.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
		
		return elem_types
		
		
	def setWidgetWidth(self,wwi,wwi_type,wwidth): #w['width'] 
		# if wwi_type=='QLabel':
			# wwi.setMaximumWidth(wwidth)
		# el
		wwi.setMaximumWidth(wwidth )	# shared for qlabel and qtextedit
		wwi.maxWidth=wwidth # shared for qlabel and qtextedit
		if wwi_type=='QTextEdit':
			wwi.setMinimumWidth(0)
			wwi.setLineWrapColumnOrWidth( int(0.98*wwidth) )
			wwi.setLineWrapMode(QTextEdit.FixedPixelWidth)
			# print('sizehint',wwi.sizeHint())
		# wwi.adjustSize() #.updateGeometry()
		# self.cellWidget(ii,jj).adjustSize()
				
				
				
				
	# goal:
	# if table updatable remove 'style' from both remembering and styling and pply separately ...
	# 'style' in w:
	def setWidgetCell(self,w,ii,jj,doprint=False):
	
		# bug when updating summary with ombobox - updating the function ... 
		# should only update the current row /col widget if content is different 
		# or block refresh when special keyword is there ?
		# 
	
	
		elem_type=''
		# print(841,w,ii,jj)
		if w=={}:
			w={'T':'LabelE'} # to overwrite 
			# return
			
		# if w['T'] in ['LabelV','LabelC','LabelE']: w['T']='QLabel'
		
			
		# if doprint: print('\n\n\nUPDATING CELL 1348',w,ii,jj)
		if w['T'] in ['LabelV','LabelC','LabelE']:
				
			tmptxt=''
			if 'L' in w:
				tmptxt=str(w['L'])
				
			cur_widget=self.item(ii,jj)
			if cur_widget!=None:
				# if doprint: print('item before  ii jj',ii,jj,cur_widget.text())
				if cur_widget.text()==tmptxt:
					return elem_type
									
			ttype=str
			if 'ttype' in w:
				ttype=w['ttype']
			
			aalign=None
			if 'align' in w:
				aalign=w['align']
			# fsize=-1
			# if 'fontsize' in w:
				# fsize=w['fontsize']
				
			tmplbl=TableCell(tmptxt,ttype,aalign,rowii=ii )
			tmptt=''
			if 'tooltip' in w:
				tmptt=w['tooltip']
				tmplbl.setToolTip(tmptt)
				
			# setCellWidget( ii,jj, None ) 
			self.removeCellWidget(ii,jj)
			self.setItem(ii,jj,tmplbl)		
			elem_type=''			
			
			if 'span' in w:
				self.setSpan(ii,jj,1,w['span'])
			
		elif w['T'] in ['QLabel']:
			# print('QLABEL',w)
			elem_type='QLabel'	
			cur_widget=self.cellWidget(ii,jj) 
			if cur_widget!=None:
				if cur_widget.text()==str(w['L']):
					return elem_type
				
			tmptt=''
			if 'tooltip' in w:
				tmptt=w['tooltip'] 
							
			ttype=str
			if 'ttype' in w:
				ttype=w['ttype']
				self.setItem(ii,jj,TableCell(w['L'],ttype,rowii=ii) ) #=QDateTime
				
				
			# print(str(tmptt))
			lll=Label( None,w['L'], str(tmptt),transparent=False )
			lll.setTextFormat(Qt.RichText)
			
			if 'width' in w:
				# print('setMaximumWidth to',w['width'] )
				# lll.resize(w['width'],lll.height())
				# lll.setMaximumWidth(w['width'] )
				self.setWidgetWidth(lll,'QLabel',w['width'])
			
			# print('new style?')
			if 'style' in w:
				# print('\t',w['style'])
				lll.setStyleSheet("QLabel {%s}" % w['style'])
			
			lll.setWordWrap(True)
				# print("QLabel {%s}" % w['style'])			
			# print(lll.sizeHint(),lll.width(),lll.height())
			self.setCellWidget( ii,jj, lll ) 
			self.cellWidget(ii,jj).setProperty("rowii",ii) #self.cellWidget(ii,jj).setStyleSheet("QLabel {%s}" % w['style'])
			self.cellWidget(ii,jj).adjustSize()	
			# self.cellWidget(ii,jj).repaint() # does not help 
			# print(lll.sizeHint(),lll.width(),lll.height())
		
		elif w['T'] in ['Button']:
			
			elem_type='QPushButton'		
			cur_widget=self.cellWidget(ii,jj)
			if cur_widget!=None:
				# print('cellwidget size',cur_widget.width(),cur_widget.height())
				if cur_widget.text()==str(w['L']):
					return elem_type
				
			tmpargs=None
			if 'args'  in w:
				tmpargs=w['args']
			tmptt=''
			if 'tooltip' in w:
				tmptt=w['tooltip']
			tmpfun=None
			if 'fun' in w:
				tmpfun=w['fun']
				
			# print('button',w['L'],tmpfun,tmpargs)
			# print('TableCell size ',TableCell(str(w['L']),ttype=str).sizeHint() )
			self.setItem(ii,jj,TableCell(str(w['L']),ttype=str,rowii=ii) )
				
			bbb=Button( None,w['L'],tmpfun,tmpargs,str(tmptt) )
			if 'IS' in w:
				bbb.setEnabled(w['IS'])
			
			if 'style' in w:
				bbb.setStyleSheet("QPushButton {%s}" % w['style'])
			else:
				bbb.setStyleSheet("QPushButton {font-size:13px;padding:2px;}" )
				# print("QPushButton {%s}" % w['style'])
				# print(bbb.styleSheet() )
			
			# print('bbb style',bbb.styleSheet() )
			bbb.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
			bbb.adjustSize()
			# print('size hint',bbb.sizeHint())
			# print(bbb.sizePolicy())
			self.setCellWidget( ii,jj, bbb )
			# print('Button width height vs cell ',bbb.width(),bbb.height(),self.cellWidget(ii,jj).width(),self.cellWidget(ii,jj).height())
			# print(self.cellWidget(ii,jj))
			self.cellWidget(ii,jj).setProperty("rowii",ii)
			# print(self.cellWidget(ii,jj))
			self.cellWidget(ii,jj).adjustSize()
			# print(bbb.styleSheet() )
						
		elif w['T'] in ['Combox']:
			elem_type=''
			cur_widget=self.cellWidget(ii,jj)
			# print('\n\nUpdating combox')
			if cur_widget!=None:
				# print('Updating combox - already exists')
			
				for jj,ci in enumerate(cur_widget.orig_items_list):
					if ci not in w['V']:
						cur_widget.removeItem(jj)
						# print('remove',ci,'not in ',w['V'])
						
				for ci in w['V']:
					if ci not in cur_widget.orig_items_list:
						cur_widget.addItem(ci,ci)
						# print('add',[ci],'not in ',cur_widget.orig_items_list)
			
				# cur_widget.updateCombox(w['V'])
				# print('UPDATED COMBOBOX')
				return elem_type
		
			tmpargs=None
			if 'args'  in w:
				tmpargs=w['args']
		
			tmpfun=None
			if 'fun' in w:
				tmpfun=w['fun']
				
			if 'every_click' in w:
				self.setCellWidget( ii,jj, Combox( None,w['V'],tmpfun,every_click=True,args=tmpargs ) )
			else:
				self.setCellWidget( ii,jj, Combox( None,w['V'],tmpfun,args=tmpargs ) )
				
			self.setItem(ii,jj,TableCell('',ttype=str,rowii=ii) )
			self.cellWidget(ii,jj).setProperty("rowii",ii)
			self.cellWidget(ii,jj).adjustSize()
					
			
		elif w['T'] in ['LineEdit']:
		
		
			tmptt=''
			if 'tooltip' in w:
				tmptt=w['tooltip']
			tmpdef=''
			if 'V' in w:
				tmpdef=w['V']
			tmpname=''
			if 'L'	in w:
				tmpname=w['L']
			
			le=LineEdit(None, tmpname,'',tmpdef,tmptt )	
			
			if 'mode' in w:
				if w['mode']=='pass':
					le.setEchoMode( QLineEdit.Password) 
			
			if 'valid' in w: # {ttype:,rrange:[]}
				le.addValidator( w['valid']['ttype'],w['valid']['rrange'] ) #vtype=int,float
				
			self.setCellWidget( ii,jj, le )
			self.setItem(ii,jj,TableCell(tmpname,ttype=str,rowii=ii) )
			self.cellWidget(ii,jj).setProperty("rowii",ii)
			self.cellWidget(ii,jj).adjustSize()
			elem_type=''
			
		elif w['T'] in ['TextEdit']:
		 
			tmptxt=w['L'] if 'L' in w else ''
			# print('creating text edit')
			ttt=TextEdit(None, tmptxt , w['width'] if 'width' in w else None ) #QTextEdit()
			
			ttt.setSizePolicy(QSizePolicy.Fixed ,QSizePolicy.Expanding)
			if 'style' in w:
				ttt.setStyleSheet("QTextEdit {%s}" % w['style'])
			
			# if 'L' in w:
				# ttt.setText(w['L'])
				
			if 'readonly' in w:
				ttt.setReadOnly(True)
				
			self.setCellWidget( ii,jj, ttt )
			self.cellWidget(ii,jj).setProperty("rowii",ii)
			self.setItem(ii,jj,TableCell('',ttype=str,rowii=ii) )
			
			
			# print('updating width  text edit')
			if 'width' in w:
				# self.cellWidget(ii,jj).setMaximumWidth(w['width'] )	
				
				# self.cellWidget(ii,jj).setMinimumWidth(0)
				# self.cellWidget(ii,jj).setLineWrapColumnOrWidth( int(0.98*w['width']) )
				# self.cellWidget(ii,jj).setLineWrapMode(QTextEdit.FixedPixelWidth)
				self.setWidgetWidth(ttt,'TextEdit',w['width'])
				
			# self.cellWidget(ii,jj).updateGeometry()
			# self.cellWidget(ii,jj).adjustSize()
			elem_type='QTextEdit'		
			
		if 'span' in w:
			self.setSpan(ii,jj,1,w['span'])
			
		return  elem_type
			

class ContainerWidget(QWidget):

	# QStackedLayout() QVBoxLayout() QHBoxLayout() 
	def __init__(self, parent , layout=None, widgets=[] ): # ContainerWidget(None,gui.QVBoxLayout(),widgets=[])

		super(ContainerWidget, self).__init__(parent)
		if layout==None:
			layout=QGridLayout()
			
		self.setLayout(layout)
		self.widgets=[]
		
		if widgets!=[]:
			for w in widgets:
				self.insertWidget(w)
				# w.setParent(self)
				
		
		self.setStyleSheet("QWidget {background-color:rgba(245,245,245,1);}")
		
		
		
		

	def insertWidget(self, wdgt, row=-1, col=-1):

		if row>-1:
			self.widgets.append( self.layout().addWidget(wdgt, row, col) )
		else:
			self.widgets.append( self.layout().addWidget(wdgt) )
		
	def widgetAt(self,idx):
		return self.layout().itemAt(idx).widget()
		
	# def insertWidgetAt(self,idx,new_wdgt): for some reason not working correct 
		# tmp=self.layout().replaceWidget( self.layout().itemAt(idx).widget(), new_wdgt, Qt.FindDirectChildrenOnly )
		# print('delete',tmp.widget())
		# tmp.widget().deleteLater()
		
	
	

class MainWindow(QMainWindow):

	# QStackedLayout() QVBoxLayout() QHBoxLayout() 
	def __init__(self, title="Default title",  geo=(128, 128, 1024, 768), central_widget=None):

		super(MainWindow, self).__init__()
		# if layout==None:
			# layout=QGridLayout()
		self.setWindowTitle(title)
		
		# self.layout = layout
		self.setGeometry(*geo)

		if central_widget == None:
			central_widget = QWidget()

		# central_widget.setLayout(layout)

		self.setCentralWidget(central_widget)
		self.widgets=[]
		 
		# tmp_header_bg_color = "rgba(255, 255, 255, 1);"
		# QWidget  { background-color:%s; border:none; margin:5px; padding:5px;}	
		#
		tmp_style = """ QWidget {font-family:'Open Sans','Helvetica Neue',Helvetica,Arial,DejaVu }	
					QFrame {border:none;}
					QTabBar {background-color:rgba(255, 255, 255, 1);}
					 QPushButton {background-color:#ddd; border-style: solid;   border-width: 1px; border-color: #aaa; padding:3px; margin:3px;min-width:32px;}
					 QPushButton:hover {background-color:#eee;   border-width: 1px; border-color: green;}
					 QPushButton:pressed {background-color:lightgreen;   border-width: 1px; border-color: green;}
					 QComboBox {background-color:white; border-style: solid;  border-width: 1px; border-color: #aaa; padding:3px; margin:3px;}
					 QComboBox:item { selection-background-color: lightgreen; } 
					 QComboBox QAbstractItemView {background-color:yellow;selection-background-color: lightgreen;border-style: solid;  border-width: 1px; }
					 QLineEdit {background-color:white; border-style: solid;  border-width: 1px; border-color: #aaa; padding:3px; margin:3px;}
					 QAbsractScrollArea {border-style:none}
					 QTableView  {border-style:none}
					 QAbstractItemView {border-style:none}
					 QHeaderView {border-style:none}
					""" 
					# % (
			# tmp_header_bg_color
		# )
# QTableWidget QLineEdit {background-color:white; border:inset;}
		self.setStyleSheet(tmp_style)
		
		self.setWindowIcon( QIcon('icon.png'))
		
	def setWorker(self,wrkr,thrd):
		self.wrkr=wrkr
		self.thrd=thrd

	# def insertWidget(self, wdgt, row=-1, col=-1):

		# if row>-1:
			# self.widgets.append( self.layout().addWidget(wdgt, row, col) )
		# else:
			# self.widgets.append( self.layout().addWidget(wdgt) )
	
	def setOnClose(self,closeFun):
		self.on_close=closeFun 
	
	def closeEvent(self,event):
		 
		if not hasattr(self,'wrkr') or not  hasattr(self,'thrd') :
			if not hasattr(self,'wrkr') and not  hasattr(self,'thrd') :
				self.close()
				return
			
			# if either worker or thread is on:
			print('awaiting worker or thread - try later')
			event.ignore()
			return
		
		if self.wrkr.block_closing:
			messagebox_showinfo('Cannot close at this moment','Application is doing some background job (e.g. encryption)',self)
			event.ignore()
			return
			
		if not self.on_close(self):
			event.ignore()
			return
		
		self.wrkr.init_app.close_thread=True
		# print('1106 self.wrkr.init_app.close_thread',self.wrkr.init_app.close_thread)
		self.thrd.terminate()
		self.thrd.wait()
		
	
		
		self.close()
