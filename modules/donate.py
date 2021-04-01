
import modules.gui as gui

def donate(parent_frame,wds,verus=False):
		
	addr='zs1nf7lsdgxpfj4m6tt7p0s4jfmnlhcdplnuu386xd5nfkm498w6nugvnaj20gfweeysg3zz6xutzm'
	llabel='Donate 1 Pirate'
	if verus:
		addr='zs1gezt5nne5lm94q3cvrrg7fxke668w7sjced0s90a5zetp0v5ndxa7sd4n8y7usqavl8mg898yhr'
		llabel='Donate 1 VRSC'
	
	dbutton=gui.Button(None,name=llabel,actionFun=wds.send_to_addr,args=(addr,1)) #

	return gui.ContainerWidget(parent_frame,layout=gui.QVBoxLayout(),widgets=[dbutton])
	
