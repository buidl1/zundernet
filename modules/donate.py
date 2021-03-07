
import modules.gui as gui

def donate(parent_frame,wds):
		
	addr='zs1nf7lsdgxpfj4m6tt7p0s4jfmnlhcdplnuu386xd5nfkm498w6nugvnaj20gfweeysg3zz6xutzm'
	dbutton=gui.Button(None,name='Donate 1 Pirate',actionFun=wds.send_to_addr,args=(addr,1)) #

	return gui.ContainerWidget(parent_frame,layout=gui.QVBoxLayout(),widgets=[dbutton])
	
