# steps:
# -1. if existing wallet exist - ask to enter usb to backup otherwise quit

# 0 .before new addr creation - ask to insert usb for backup - if ok - progress with creating addr
# after new addr creation: 
# 1. select folder path on sub drive to backup wallet
# 2. check if selected path is removable usb drive if so - write backup and feedback if copy success
# 3. if not - ask to select another usb path 



# import re
import subprocess
from sys import platform

# returns list of detected removable drives
class USB:

	def __init__(self):
		self.os='unknown'
		self.located_usbs=[]
		if platform == "linux" or platform == "linux2":
			self.os='linux'
		elif platform == "darwin":
			self.os='osx'
		elif platform == "win32":
			self.os='windows'
			
			
		
	def locate_usb(self):
		if self.os in ['linux','osx'] :
			self.located_usbs=self.lin_locate_usb()
			
			#print('self.located_usbs',self.located_usbs)
			
		else:
			self.located_usbs=self.win10_locate_usb()
			
		if '' in self.located_usbs:
			self.located_usbs.remove('')
		
		return self.located_usbs.copy()
			
		
	def verify_path_is_usb(self,path):
	
		if self.os=='windows':
			ps=path.split(':')
			diskname=ps[0]
			dlen=len(diskname)
			
			for uu in self.located_usbs:
				if diskname==uu[:dlen]:
					return True
		else:
			for uu in self.located_usbs:
				lu=len(uu)
				if lu>0 and uu==path[:lu]: # path start ??
					return True
							
		return False
		
			
		
	def lin_locate_usb(self):
		usblist="""
				lsblk
				"""
		df = subprocess.run(["sh", "-c", usblist], capture_output=True)
		df=df.stdout.decode('utf8')#.replace('\n','')
		lines=df.split('\n')
		table=[]
		usbs=[]
		for ll in lines:
			col=ll.split()
			table.append([])
			for cc in col:
				table[-1].append(cc)
				if '/media/' in cc:
					usbs.append(cc)
		#print( usbs)
	
		#usblist="""
		#		REMOVABLE_DRIVES=""
		#		for _device in /sys/block/*/device; do
		#		
    	#			if echo $(readlink -f "$_device")|egrep -q "usb"; then
        #				_disk=$(echo "$_device" | cut -f4 -d/)
        #				REMOVABLE_DRIVES="$REMOVABLE_DRIVES;$_disk"
    	#			fi
		#		done
		#		echo "$REMOVABLE_DRIVES"
		#		"""
		#df = subprocess.run(["sh", "-c", usblist], capture_output=True)
		#df=df.stdout.decode('utf8').replace('\n','')
		#df=df[1:]
		
		#devices=df.split(';')
		
		return usbs

		
		
		
	def win10_locate_usb(self):
		import win32file
		drive_list = []
		drivebits = win32file.GetLogicalDrives()
		
		for d in range(1, 26):
			mask = 1 << d

			if drivebits & mask:
				# here if the drive is at least there
				drname = '%c:\\' % chr(ord('A') + d)

				t = win32file.GetDriveType(drname)
				if t == win32file.DRIVE_REMOVABLE:
					drive_list.append(drname)
		return drive_list
	
# tt=USB()	
# print(tt.locate_usb())
