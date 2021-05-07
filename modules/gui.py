# small widgets
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
		
		self.okbutton = Button( self,name='Enter',actionFun=self.enter_button, args=([cmdfun,self.optbox.currentText()],) )

		layout = QVBoxLayout()
		layout.addWidget(self.label )
		layout.addWidget(self.optbox )
		layout.addWidget(self.okbutton )
		self.setLayout(layout)	
		self.exec_()	
		
	def enter_button(self,btn,args ):
		# print(btn,args)
		args[0](args[1])
			
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
		
		if name!='':
			self.setText(name)
			
		if tooltip!='':
			self.setToolTip(tooltip)
			
		if actionFun!=None:
			self.clicked.disconnect()
			self.fun=actionFun
			self.args=args
			if args!=None:
				self.clicked.connect(lambda  : actionFun(self,*args))
			else:
				self.clicked.connect(lambda : actionFun(self ))
	
		# print(actionFun,args)

	def __init__(self,parent,name='',actionFun=None,args=None,tooltip=''): #item_list=[{'text'}]  OR item_list=[{'text','userdata'},{}]
		super(Button, self).__init__(name ,parent)
		
		
		self.args=args
		self.setFocusPolicy(Qt.ClickFocus)
		# self.setDefault(False)
		if actionFun!=None:
			# print(actionFun,args)
			self.fun=actionFun
			
			if args!=None:
				self.clicked.connect(lambda  : actionFun(self,*args))
			else:
				self.clicked.connect(lambda : actionFun(self ))
			
		if tooltip!='':
			self.setToolTip(tooltip)
			
		self.setStyleSheet('QPushButton {padding:3px;font-size:13px;}')
	
	def set_fun(self,no_self,actionFun,*args):
	
		if hasattr(self,'fun'):
			return
			
		self.fun=actionFun
	
		if no_self:
			self.clicked.connect(lambda:  actionFun(*args))
		else:
			self.clicked.connect(lambda:  actionFun(self,*args))
	# def keyPressEvent(self,event):
		# self.fun(self,args)
		


class TextEdit(QTextEdit):			
	def __init__(self,parent ,txt='' ):
		super(TextEdit, self).__init__(txt,parent)


	
class FramedWidgets(QGroupBox):
	def __init__(self,parent ,name=None,widgets=[],layout=None ):
		super(FramedWidgets, self).__init__(name,parent)
		if layout==None:
			layout=QHBoxLayout()
		
		self.setLayout(layout)
		self.widgets=[]
		# self.layout=layout
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
			
	
	def insertWidget(self, wdgt, row=-1, col=-1):
		
		if row>-1:
			self.widgets.append( self.layout().addWidget(wdgt, row, col) )
		else:
			self.widgets.append( self.layout().addWidget(wdgt) )
		
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
		
		self.orig_items_list=items_list.copy()
		self.every_click=every_click
		
		if 'text' not in items_list[0]: # assume convert:
			items_list=[{'text':il} for il in items_list]
			
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
					self.activated.connect(lambda  : actionFun(self,*args))
				else:
					self.activated.connect(lambda : actionFun(self ))
			else:
				if args!=None:
					# self.activated.connect(lambda  : actionFun(self,*args))
					self.currentTextChanged.connect(lambda: actionFun(self,*args))
				else:
					# self.activated.connect(lambda : actionFun(self ))
					self.currentTextChanged.connect(lambda: actionFun(self))	# self.currentText() self.currentData(Qt.UserRole) inside actionFun will get our values 
		
		self.setStyleSheet('QComboBox {padding:3px;font-size:13px;}')
		
	# currentIndex()	
	# currentText()
	def setIndexForText(self,txt):
		fid=self.findText(txt, Qt.MatchExactly)
		if fid==-1: fid=0
		
		self.setCurrentIndex( fid )
		
	
	def set_fun(self,actionFun,*args ):	
	
		if hasattr(self,'fun'):
			return
			
		self.fun=actionFun
	
		if self.every_click:
			self.activated.connect(lambda: actionFun(self,*args))
		else:
			self.currentIndexChanged.connect(lambda: actionFun(self,*args ))
		
	def replace(self,old_item_name,new_item={}): # new_item={'text'} or {'text','userdata'}
		idx=self.findText(old_item_name,Qt.MatchExactly)
		if 'userdata' not in new_item:
			new_item['userdata']=new_item['text']
		self.insertItem(idx,new_item['text'],new_item['userdata'])
		self.setItemData(idx, new_item['text'], Qt.ToolTipRole)

		
	# insert new, but do not delete old 
	def updateBox(self,new_items_list=[]):
		# self.orig_items_list=items_list
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

		
		
		
		
		
		
class LineEdit(QLineEdit):			
	def __init__(self,parent ,field_name='',placeholder_txt='',default_value='',tooltip=''):
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
		# self.setSizePolicy(QSizePolicy)
		if transparent:
			self.setAttribute(Qt.WA_TranslucentBackground)
		if tooltip!='':
			self.setToolTip(tooltip)
			
		# self.ltype=ltype
		

		
			
class TableCell(QTableWidgetItem):
	def __init__(self, value,ttype ): # ttype= float, int, str
		super(TableCell, self).__init__(value)
		self.ttype=ttype
		
		if ttype==QDateTime:
			tmsplit=value.strip().split()
			tmpdatetime=tmsplit[0]+'T'+tmsplit[-1]   #tm[2].replace(' ','T')
			self.typedvalue=QDateTime.fromString(tmpdatetime,Qt.ISODate)
		else:
			self.typedvalue=self.ttype(value)
		# if fsize>0:
			# self.setStyleSheet(" QTableWidgetItem {font-size:"+fsize+"px;}" )
		# self.setSizePolicy(QSizePolicy.Minimum,QSizePolicy.Minimum)
		
	def __lt__(self,other):
		if self.typedvalue <  other.typedvalue :
			return True
		return False
		


# importante: row indexes can be on or off if needed
# size options:
# setSectionResizeMode per vertical or horizonal section
# or setRowHeight and setRowHeight
class Table(QTableWidget):

	def __init__(self, parent=None, params={}):
	
		rows=params['dim'][0]
		cols=params['dim'][1]
		# print('rows,cols',rows,cols)
		super(Table, self).__init__(rows,cols,parent)
		
		# self.rowUIDs={} row names work as ids, and row data as checker if to update 
		self.row_key_svalue={}
		# self.col_names=[]
		self.updatable=False
		
		self.setCornerButtonEnabled(False)
		self.setFocusPolicy(Qt.NoFocus)
		self.setEditTriggers(QAbstractItemView.NoEditTriggers)
		self.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)

		
		self.verticalHeader().hide()
		self.horizontalHeader().sectionClicked.connect(self.clickDetected)
		
		self.horizontalHeader().setMinimumHeight(32)
		self.horizontalHeader().setDefaultAlignment(Qt.AlignLeft|Qt.AlignTop)
		
		if 'maxHeight' in params:
			self.setMaximumHeight(params['maxHeight'])
		
		if 'toContent' in params:
			self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
			self.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
		
		# optional params ON OFF	
		if 'updatable' in params:
			# if params['updatable']==True:
			self.updatable=True


		
		if 'colSizeMod' in params:
			for ii,mm in enumerate(params['colSizeMod']):
				if mm=='stretch':
					self.horizontalHeader().setSectionResizeMode(ii,QHeaderView.Stretch)
				elif mm=='toContent':
					self.horizontalHeader().setSectionResizeMode(ii,QHeaderView.ResizeToContents)
				else:
					self.setColumnWidth(ii,mm)
					
		
		if 'rowSizeMod' in params:
			for ii,mm in enumerate(params['rowSizeMod']):
				if mm=='stretch':
					self.verticalHeader().setSectionResizeMode(ii,QHeaderView.Stretch)
				elif mm=='toContent':
					self.verticalHeader().setSectionResizeMode(ii,QHeaderView.ResizeToContents)	
				else:
					self.setRowHeight(ii,mm)
		
		# sortable=[]
		if 'sortable' in params:
			self.setSortingEnabled(True)
			
		# if "show_grid" in params:
			# self.setShowGrid(params["show_grid"])
		self.setShowGrid(False)
		
		self.sort_col=''		
		if 'default_sort_col' in params:
			self.sort_col=params["default_sort_col"]
			# print('self.sort_col',self.sort_col)
		
		
		
		## STYLING CSS
		
		tmp_header_bg_color = "rgba(245, 245, 245, 1);"
		 # QTableWidget::item:edit-focus { background-color:%s; border:none; color:black;}
		 # QWidget  { background-color:%s; border:none; margin:5px; padding:5px;}
		tmp_style = """
					QTableWidget::item { background-color:%s; border-style:none;}
					QTableWidget::item:selected { background-color:%s; border-style:none; color:black }
					QHeaderView::section { background-color:%s; border-style:none; }
					QTableCornerButton::section { background-color:%s; border-style:none; }
					QTableWidget QPushButton {background-color:#ddd; border-style: solid;   border-width: 1px; border-color: #aaa; padding:3px; margin:3px;}
					QTableWidget QPushButton:hover {background-color:#eee;   border-width: 1px; border-color: green;}
					QTableWidget QPushButton:pressed {background-color:lightgreen;   border-width: 1px; border-color: green;}
					QTableWidget QComboBox {background-color:white; border-style: solid;  border-width: 1px; border-color: #aaa;}
					QTableWidget QComboBox QAbstractItemView {selection-background-color: lightgray;border-style: solid;  border-width: 1px; }
					QTableWidget QLineEdit {background-color:white; border-style: solid;  border-width: 1px; border-color: #aaa;}
					QTableWidget {margin:2px;padding:2px;font-size:13px; font-family:'DejaVu';border-style:none; }
					QHeaderView {font-size: 13px; padding:0px; margin:0px;font-family:'DejaVu';border-style:none;  }
					""" % (
			
			tmp_header_bg_color,
			tmp_header_bg_color,
			tmp_header_bg_color,
			tmp_header_bg_color
		)
# QTableWidget QLineEdit {background-color:white; border:inset;}
		self.setStyleSheet(tmp_style)
		# print(tmp_style)
		
		

	# colnames getting zeroed 
	# update which column currently  sorted in canse of insert to be in correct order 
	def clickDetected(self):
		if hasattr(self,'col_names') and self.sender().metaObject().className()==QHeaderView.staticMetaObject.className():
			tmpsender=self.sender()
			# print(self.col_names)
			# print(tmpsender)
			# print(tmpsender.sortIndicatorSection())
			self.sort_col=self.col_names[tmpsender.sortIndicatorSection()]
			# print(tmpsender.sortIndicatorOrder(),self.sort_col)
		
		
	# updateTable should mek this  
	def insert_at(self,widgets_line,at_line):
		wasSortingEnabled=self.isSortingEnabled()
		if wasSortingEnabled:
			self.setSortingEnabled(False)
		
		# ii=self.rowCount()
		# self.insertRow( ii)
		self.setWidgetRow(widgets_line,at_line)
		# for jj, w in enumerate(widgets_line):
			# self.setWidgetLine(w,ii,jj)
			# if 'span' in w:
				# self.setSpan(ii,jj,1,w['span'])
			
		if wasSortingEnabled:
			self.setSortingEnabled(True)
			tmpord=self.horizontalHeader().sortIndicatorOrder()
			tmpidx=self.horizontalHeader().sortIndicatorSection()
			self.sortByColumn(tmpidx, tmpord)

	# cellType= item or widget
	def filtering(self,cellType,colnum,fopt ):
		for ii in range(self.rowCount()):
			tmpcurcat='xxx'
			# print(ii,colnum,cellType,fopt)
			# print(self.cellWidget(ii,colnum).text())
			if cellType=='widget': tmpcurcat=self.cellWidget(ii,colnum).text()
			elif cellType=='item' : tmpcurcat=self.item(ii,colnum).text()
			# elif cellType=='item_date' : tmpcurcat=self.item(ii,colnum).text()
			else:
				print('Wrong filter value cellType')
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
			
		
		
		
	def updateTable(self,widgets_dict,col_names=[],insert_only=False):
	
		# print('\n\n',self,self.updatable,'\n\n')
		
		if hasattr(self,'widgets_dict'):
			if str(widgets_dict)==self.widgets_dict:
				return
			else:
				self.widgets_dict=str(widgets_dict)
	
		# print('update table col_names',col_names,self.col_names)
		if col_names==[]:
			if hasattr(self,'col_names')==False: # if first time 
				self.horizontalHeader().hide()
		else:
			self.col_names=col_names
			self.setHorizontalHeaderLabels(col_names)	
	
		# sorting off
		wasSortingEnabled=self.isSortingEnabled()
		if wasSortingEnabled:
			self.setSortingEnabled(False)
	
		# if init - connect ii,jj with row uids 
		tmpCurrentRowIDs=[]
		
		currentRowsIDs=[self.verticalHeaderItem(ll).text()  for ll in range(self.rowCount()) if self.verticalHeaderItem(ll)!=None]
		# print('currentRowsIDs',currentRowsIDs)
		# currentRowsData=[self.verticalHeaderItem(ll).data(Qt.EditRole) for ll in range(self.rowCount()) if self.verticalHeaderItem(ll)!=None ]
		tmpinit=len(currentRowsIDs)==0 and self.rowCount()>0
		
		new_rows=[]
		
		offset=0
		if insert_only:
			offset=self.rowCount()
			
		# print('\n\n\n self.col_names', col_names)
		
		for iii,rr in enumerate(widgets_dict):
		
			ii=iii+offset
			
			# print('\nupdating',ii,tmpinit,self.updatable,rr)
		
			if tmpinit and self.updatable:# initiate row ids 
				
				self.setVerticalHeaderItem(ii,TableCell(rr['rowk'],str))
				self.row_key_svalue[rr['rowk']]=str(rr['rowv'])
				
				self.setWidgetRow(rr['rowv'],ii)
				
				
				if 'rowSizeMod' in rr:
					if rr['rowSizeMod']=='stretch':
						self.verticalHeader().setSectionResizeMode(ii2,QHeaderView.Stretch)
					elif rr['rowSizeMod']=='toContent':
						self.verticalHeader().setSectionResizeMode(ii2,QHeaderView.ResizeToContents)	
					else:
						self.setRowHeight(ii2,rr['rowSizeMod'])
				
			elif self.updatable:
				tmpCurrentRowIDs.append(rr['rowk'])
				# print(772,rr['rowk'])
				
				if rr['rowk'] in currentRowsIDs:
					
					ii3=currentRowsIDs.index(rr['rowk'])
					
					if str(rr['rowv'])!=self.row_key_svalue[rr['rowk']]:
						# print('actual update',776,ii3,rr['rowv'])
						self.setWidgetRow(rr['rowv'],ii3)
						self.row_key_svalue[rr['rowk']]=str(rr['rowv'])
						
				else: #insert new row
					# print('new row?',currentRowsIDs)
					ii2=self.rowCount()
					# print('new row',ii2)
					self.insertRow( ii2)
					new_rows.append(ii2)
					self.setVerticalHeaderItem(ii2,TableCell(rr['rowk'],str))
					# print('\n\n\n\nheader set to',rr['rowk'])
					# print('check',self.verticalHeaderItem(ii2).text())
					
					self.row_key_svalue[rr['rowk']]=str(rr['rowv'])
					# print('set',rr['rowv'])
					self.setWidgetRow(rr['rowv'],ii2) 
					
					if 'rowSizeMod' in rr:
						if rr['rowSizeMod']=='stretch':
							self.verticalHeader().setSectionResizeMode(ii2,QHeaderView.Stretch)
						elif rr['rowSizeMod']=='toContent':
							self.verticalHeader().setSectionResizeMode(ii2,QHeaderView.ResizeToContents)	
						else:
							self.setRowHeight(ii2,rr['rowSizeMod'])
				
			else: #not updatable, just write cells
				# print(803,rr,ii)
				if 'rowk' in rr:
					# print(1032,rr)
					self.setWidgetRow(rr['rowv'],ii)
				else:
					# print('NO ROWK')
					self.setWidgetRow(rr,ii)
				
		if not insert_only:
			if len(tmpCurrentRowIDs)==0 and len(currentRowsIDs)>0: # remove all 
				# print('remove all')
				tmpl=self.rowCount()
				while self.rowCount()>0:
					self.removeRow(tmpl-1)
					tmpl=self.rowCount()
				
			else:	
				for nn,ccr in enumerate(currentRowsIDs) :
					# print(nn,ccr)
					if ccr not in tmpCurrentRowIDs:
						 
						for ll in range(self.rowCount()):						
							if self.verticalHeaderItem(ll).text()== ccr:
								# this is ll row to delete
								self.removeRow(ll)
								break
			
		self.adjustSize()
		
		
		# resort if on 
		if wasSortingEnabled:
			self.setSortingEnabled(True)
			if self.sort_col!='' and len(self.col_names)>0:
				try:
					# print(920,self.sort_col,self.col_names)
					sortidx=self.col_names.index(self.sort_col)
					# print(sortidx)
				except:
					sortidx=-1
				
				if sortidx==-1:
					print('WARNING - sort column name WRONG sortidx=',sortidx)
					sortidx=0
					# self.horizontalHeader().setSortIndicator(sortidx)
					tmpord=self.horizontalHeader().sortIndicatorOrder()
					self.sortByColumn(sortidx, tmpord)
				else:
					tmpord=self.horizontalHeader().sortIndicatorOrder()
					self.sortByColumn(sortidx, tmpord)
			else:
				tmpord=self.horizontalHeader().sortIndicatorOrder()
				self.sortByColumn(0, tmpord)
				
		return new_rows
		
		
		
	
	def setWidgetRow(self,r,ii):
		# print(r)
		for jj, w in enumerate(r):
			# print(w,ii,jj)
			self.setWidgetCell(w,ii,jj)
		
		
		
		
	def setWidgetCell(self,w,ii,jj):
	
		# print(841,w,ii,jj)
		if w=={}:
			# w={'T':'LabelE'}
			return
		# print(870,w,ii,jj)
		if w['T'] in ['LabelV','LabelC','LabelE']:
				
			tmptxt=''
			if 'L' in w:
				tmptxt=str(w['L'])
				
			cur_widget=self.item(ii,jj)
			if cur_widget!=None:
				if cur_widget.text()==tmptxt:
					return
									
			ttype=str
			if 'ttype' in w:
				ttype=w['ttype']
			
			# fsize=-1
			# if 'fontsize' in w:
				# fsize=w['fontsize']
				
			tmplbl=TableCell(tmptxt,ttype )
			tmptt=''
			if 'tooltip' in w:
				tmptt=w['tooltip']
				tmplbl.setToolTip(tmptt)
				
			self.setItem(ii,jj,tmplbl)
			# self.item(ii,jj).setProperty("rowii",ii)
			# self.item(ii,jj).setData(Qt.FontRole, QFont(self.item(ii,jj).data(Qt.FontRole).family(),weight=6));
			
			if 'span' in w:
				self.setSpan(ii,jj,1,w['span'])
			
		elif w['T'] in ['QLabel']:
		
			cur_widget=self.cellWidget(ii,jj) 
			if cur_widget!=None:
				if cur_widget.text()==str(w['L']):
					return
				
			tmptt=''
			if 'tooltip' in w:
				tmptt=w['tooltip'] 
							
			ttype=str
			if 'ttype' in w:
				ttype=w['ttype']
				self.setItem(ii,jj,TableCell(w['L'],ttype=QDateTime) )
				
				
			lll=Label( None,w['L'], str(tmptt),transparent=False )
			if 'style' in w:
				lll.setStyleSheet("QLabel {%s}" % w['style'])
				lll.setWordWrap(True)
				# print("QLabel {%s}" % w['style'])				
			
			self.setCellWidget( ii,jj, lll ) 
			self.cellWidget(ii,jj).setProperty("rowii",ii) 
			self.cellWidget(ii,jj).adjustSize()	
		
		elif w['T'] in ['Button']:
		
			cur_widget=self.cellWidget(ii,jj)
			# print('cur_widget',cur_widget)
			if cur_widget!=None:
				if cur_widget.text()==str(w['L']):
					return
				
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
			# print('ii,jj,rows',ii,jj,self.rowCount())
				
			bbb=Button( None,w['L'],tmpfun,tmpargs,str(tmptt) )
			if 'IS' in w:
				bbb.setEnabled(w['IS'])
			
			if 'style' in w:
				bbb.setStyleSheet("QPushButton {%s}" % w['style'])
			else:
				bbb.setStyleSheet("QPushButton {font-size:13px;padding:3px;}" )
				# print("QPushButton {%s}" % w['style'])
				# print(bbb.styleSheet() )
			
			# print(bbb,ii,jj,self.rowCount(),self.columnCount())
			self.setCellWidget( ii,jj, bbb )
			# print(self.cellWidget(ii,jj))
			self.cellWidget(ii,jj).setProperty("rowii",ii)
			# print(self.cellWidget(ii,jj))
			self.cellWidget(ii,jj).adjustSize()
			# print(bbb.styleSheet() )
						
		elif w['T'] in ['Combox']:
		
			cur_widget=self.cellWidget(ii,jj)
			# print(898,cur_widget)
			if cur_widget!=None:
			
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
				return
		
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
			self.cellWidget(ii,jj).setProperty("rowii",ii)
			self.cellWidget(ii,jj).adjustSize()
			
		elif w['T'] in ['TextEdit']:
		
			ttt=QTextEdit()
			if 'style' in w:
				ttt.setStyleSheet("QTextEdit {%s}" % w['style'])
			self.setCellWidget( ii,jj, ttt )
			self.cellWidget(ii,jj).setProperty("rowii",ii)
			self.cellWidget(ii,jj).adjustSize()
			
		if 'span' in w:
			self.setSpan(ii,jj,1,w['span'])
			
			
			

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
					 QComboBox QAbstractItemView {background-color:white;selection-background-color: lightgray;border-style: solid;  border-width: 1px; }
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
		# check blockchcian status works:
		if self.wrkr.block_closing:
			messagebox_showinfo('Cannot close before chain status is established - please wait','Please wait for connection to be able to close the application. Cannot close before chain status is established',self)
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
