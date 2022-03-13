
# TODO: 
# chanel types - blog, set min fee  ... 
# public signatures?
# ann channels/categories ?
# warning fo local backup folders
# tail -f ~/.komodo/PIRATE/debug.log for rescan progress 
# reordering msg when sent in the ame block: sort queue ? if first msg in a queue does not send but another sends (wallet status change) then return to main loop and first go with e first one 
# DB err 397 - no db name
# QThread: Destroyed while thread is still running
# small bug merging regular tx got signature in between 

# seems send wrongly? didnt merge properly ?
 
# add sync start at 179... and per  key pair
#call setprimarykey to set main key 
# block quit when wallet being encrypted after blockchain stop!
# use db in memoery
# load backup to memory on start
# shared db object between classes

# bad foramt channel message show only in notifications and history but not in channels if possible ?
 

# todo: refresh interface only when change in window tab etc 
# ?? store keys encrypted in local db to recover in case it is needed
 

# NEXT:
 
# verus exception not enough fee
  
# pycryptodome
# python -m pip install pywin32

# compile: pyinstaller zundernet.py --onefile #--windowed


import os
import sys
import queue
import time
import signal

def ctrlc():	print('got ctrl-c')
def ctrlbreak():	print('got ctrl-break')

signal.signal(signal.SIGINT, ctrlc) #signal.SIG_DFL) signal.SIGBREAK
if os.name == 'nt':
	signal.signal(signal.SIGBREAK, ctrlbreak)
	
from PySide2.QtWidgets import QApplication
# t0=time.time()
app = QApplication( )
# print(' QApplication dt',time.time()-t0)
# t0=time.time()
import modules.gui as gui


import modules.wallet_tab as wallet_tab
import modules.wallet_api as wallet_api
import modules.msg as msg
import modules.chnls as chnls
import modules.donate as donate
import modules.addr_book as addr_book
from modules.wallet_display_set import WalDispSet 
from modules.init_checks import InitApp
from modules.frame_settings import Settings

init_app=InitApp() 


tabs0=gui.Tabs(None)

# print(' tabs0 dt',time.time()-t0)
# t0=time.time()
new_root=gui.MainWindow(title="zUndernet | Wallet file: "+init_app.data_files['wallet'],central_widget=tabs0)
new_root.setOnClose(init_app.on_closing)
new_root.show()
# print(' new_root dt',time.time()-t0)
# t0=time.time()


queue_start_stop = queue.Queue()	

wds=WalDispSet([init_app.app_password],init_app.data_files )

init_app.wds_addr_cat_map=wds.addr_cat_map # pointer to object for next init ? 
init_app.wds_addr_book=wds.grid_lol_select # pointer to object for next init ? grid_lol_select
init_app.wds_addr_book_category_alias=wds.addr_book_category_alias # pointer to object for next init ? grid_lol_select
init_app.wds_disp_dict=wds.disp_dict # pointer to object for next init ? grid_lol_select

# print(' WalDispSet dt',time.time()-t0) #0.16
# t0=time.time()
  
wata=wallet_tab.WalletTab(init_app.is_started,queue_start_stop, wds)
init_app.wallet_tab_byaddr_frame =wata.byaddr_frame  # pointer to object for next init ?
init_app.wallet_tab_summary_frame =wata.summary_frame  # pointer to object for next init ?
init_app.wallet_tab_summary_options =wata.summary_options  # pointer to object for next init ?
init_app.wallet_tab_queue_frame =wata.queue_frame  # pointer to object for next init ?

dmn=init_app.dmn
def upload_0():
	# print('upload_0')
	dmn.start_stop_enable.connect(wata.enableStartStop)
	dmn.sending_signal.connect(wata.updateWalletDisplay) 
	dmn.msg_signal.connect(wata.display_message)
	dmn.msg_signal_list.connect(wata.display_list)
	dmn.wallet_status_update.connect(wata.updateStatus) #self.start_stop_enable.emit(True)
	dmn.wallet_synced_signal.connect(init_app.check_if_new_wallet_backup_needed)
	dmn.wallet_synced_signal.connect(wds.setSynced)
 
	
gui.QTimer.singleShot(500,upload_0)

 


tabs0.insertTab( tab_dict={'Wallet':wata.tabs1})

# is this correct ? ok
wds.sending_signal.connect(wata.updateWalletDisplay)

addrb=addr_book.AddressBook( wds)
init_app.addr_book_view_grid=addrb.addr_book_view_grid # pointer to object for next init ?
def upload_1():
	# t0=time.time()
	tabs0.insertTab( tab_dict={'Address Book':addrb.setaddrbook()})
	# print(' AddressBook dt',time.time()-t0) # 0.4s
	# t0=time.time()
	wata.init_additional_tabs(addrb,init_app) # 0.5s
	# print(' init_additional_tabs dt',time.time()-t0)


gui.QTimer.singleShot(1000,upload_1)
	
	
def uploadTabs():
	 
	# t0=time.time()
	mmm=msg.Msg( addrb )

	init_app.msg_grid_main=mmm.grid_threads_msg # pointer to object for next init ?
	init_app.msg_grid_threads=mmm.grid_threads # pointer to object for next init ?
	init_app.msg_grid_order=mmm.thr_ord # pointer to object for next init ?
	tabs0.insertTab( tab_dict={'Messages':mmm.parent_frame})
	# print(' Msg dt',time.time()-t0) #  2
	gui.QTimer.singleShot(500,mmm.update_msgs)
	# print('uploadTabs 1 ')
	 
	ccc=chnls.Chnls(mmm, addrb )
	ccc.refreshAddrBook.connect(addrb.refresh_addr_book)
	dmn.wallet_synced_signal.connect(ccc.updateFilter)
	
	init_app.msg_grid_main=ccc.grid_threads_msg # pointer to object for next init ?
	init_app.msg_grid_threads=ccc.grid_threads # pointer to object for next init ?
	init_app.msg_grid_order=ccc.thr_ord # pointer to object for next init ?
	tabs0.insertTab( tab_dict={'Channels':ccc.parent_frame})
	gui.QTimer.singleShot(1000,ccc.update_channels)
	# print('uploadTabs 2 ')
	# print(' Chnls dt',time.time()-t0) #0.14
	# t0=time.time()
	###################################################  donate
	tabs0.insertTab( tab_dict={'Donate':donate.donate(None,wds,init_app.chain=='verus')})
	# print(' Donate dt',time.time()-t0)
	# t0=time.time()
	 
	
	dmn.set_wallet_widgets(wds) #,wata,task_history=None,txhi=None,notif=None,messages=None)
	# print('uploadTabs 3 ')
	dmn.update_addr_book.connect(wds.addr_book_data_refresh)
	dmn.refresh_msgs_signal.connect(mmm.update_msgs)

	mmm.refreshChannels.connect(ccc.update_channels)
	mmm.refreshChannels.connect(ccc.updateFilter)
	mmm.refreshTxHistory.connect(wata.txhi.update_history_frame)
	mmm.refreshNotifications.connect(wata.notif.update_notif_frame)
	mmm.refreshAddrBook.connect(addrb.refresh_addr_book)
	 
	dmn.update_addr_book.connect(addrb.refresh_addr_book)
	dmn.send_viewkey.connect(wds.set_channel)
	
	# print('uploadTabs 4 ')
	# when wallet synced emit signal to backup fresh wallet init check self.creating_new_wallet

	wrk=wallet_tab.Worker(init_app, queue_start_stop, dmn)

	wrk_thread=gui.QThread(parent=new_root)
	wrk.moveToThread(wrk_thread)
	wrk_thread.finished.connect(wrk_thread.deleteLater)
	wrk.finished.connect(wrk_thread.quit)
	wrk.finished.connect(wrk.deleteLater)
	wrk.refreshed.connect(wata.updateWalletDisplay)
	
	wrk_thread.started.connect(wrk.run)
	wrk_thread.start()
	new_root.setWorker(wrk,wrk_thread)
	# print('uploadTabs done ')
	



gui.QTimer.singleShot(2000,uploadTabs)


def upload_settings():
	# t0=time.time()
	wata_settings=Settings( wds, init_app)
	init_app.tab_settings_grid=wata_settings.grid_settings # pointer to object for next init ?
	wata.tabs1.insertTab(tab_dict={'Settings': wata_settings.parent_frame}  )
	dmn.start_stop_enable.connect(wata_settings.updatePassChangeState )
	# print(' Settings dt',time.time()-t0) #0.74
	# t0=time.time()
gui.QTimer.singleShot(5000,upload_settings)


app.exec_()
