# encryption aes

import json, sys, os
from base64 import b64encode, b64decode,a85decode,a85encode
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad,unpad
from Crypto.Random import get_random_bytes, random
from Crypto.Hash import SHA256, SHA224
import modules.gui as gui




class Crypto:

	# max nn=126*126-1
	
	# sha224 59 chars -> 33 chars of 1 byte utf-8
	def int_to_utf8_1b(self,intstr): # ensure int is hex int 16 
	
		if type(intstr)!=type(int(1)):
			intstr=int(intstr,16)
	
		base=len(self.utf8_127)
		ustr=''
		while intstr>0:
			tmp=intstr % base
			ustr+=self.utf8_127[tmp]
			intstr=intstr//base
			
		return ustr

		
	def utf8_1b_to_int(self,ustr):
		base=len(self.utf8_127)
		n=0
		for jj in range((len(ustr)-1),-1,-1):
			try:
				ii=self.utf8_127.index(ustr[jj])
				n=n*base+ii
			except:
				return -1
		
		return n


	def __init__(self,hashalgo=256):
		self.principal4="Individuals security and privacy on the internet are fundamental and must not be treated as optional."
		self.hashalgo=SHA256
		if hashalgo==224:
			self.hashalgo=SHA224
		# 126
		self.utf8_127= ["\u0000", "\u0001", "\u0002", "\u0003", "\u0004", "\u0005", "\u0006", "\u0007", "\b", "\t", "\u000b", "\f", "\r", "\u000e", "\u000f", "\u0010", "\u0011", "\u0012", "\u0013", "\u0014", "\u0015", "\u0016", "\u0017", "\u0018", "\u0019", "\u001a", "\u001b", "\u001c", "\u001d", "\u001e", "\u001f", " ", "!", "\"", "#", "$", "%", "&", "'", "(", ")", "*", "+", ",", "-", ".", "/", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", ":", "<", "=", ">", "?", "@", "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z", "[", "\\", "]", "^", "_", "`", "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z", "{", "|", "}", "~", "\u007f"]
		
		
	def hash(self,ddata,times=1):
		
		if type(ddata)!=type(b'asdf'):
			ddata = ddata.encode('utf-8')
		
		def rem_leading_zeros(strtmp):
			while strtmp[0]=='0':
				strtmp=strtmp[1:]
				
			return strtmp
			
		hash_object = rem_leading_zeros( self.hashalgo.new(ddata).hexdigest() )
		
		while times>1:
			times=times-1
			hash_object=hash_object.encode('utf-8')
			hash_object = rem_leading_zeros( self.hashalgo.new(hash_object).hexdigest() )
			
		return hash_object
		
		
	
	def rand_slbls(self,slbls_count):
		c1=[ "B", "C", "D",  "F", "G", "H",  "J", "K", "L", "M", "N",  "P",  "R", "S", "T",  "V",  "Z"] #17
		c2=["a",   "e",  "i",   "o",  "u",  "y" ] # 6
		
		retv=''
		for ii in range(slbls_count):
			ri=random.randint(0,len(c1)-1)
			retv+=c1[ri]
			ri=random.randint(0,len(c2)-1)
			retv+=c2[ri]
			
		return retv
		
		
	
	def rand_abc(self,llen):
		
		ascii_chain="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
		ascii_arr=list(ascii_chain) 
		
		arr_len=len(ascii_arr)
		retpass=''
		for ii in range(llen):
			ri=random.randint(0,arr_len-1)
			retpass+=ascii_arr[ri]
		
		return retpass
		
	
	def rand_password(self,llen):
		
		# ascii_chain="!#$%&'()*+,-./0123456789:<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[]^_abcdefghijklmnopqrstuvwxyz{}~"
		ascii_chain="ABCDEFGHIJKLMN*PQRSTUVWXYZabcdefghijklmnopqrstuvwxyz23456789@#$+=?"
		ascii_arr=list(ascii_chain) 
		
		arr_len=len(ascii_arr)
		retpass=''
		for ii in range(llen):
			ri=random.randint(0,arr_len-1)
			retpass+=ascii_arr[ri]
		
		return retpass
	
		
	def rand_utf8(self,llen):
	
		initlen=llen*2
		
		while True: # to ensure length
			
			tmp=get_random_bytes(initlen).decode('utf-8','ignore')
			if len(tmp)>=llen:
				return tmp[:llen]
			else:
				initlen=initlen*2 #in case of too many escaped chars
	

	def aes_encrypt_file(self,path1,path2,password):
		
		if os.path.exists(path1):
			try:
				ddata=self.read_bin_file( path1)
				encr_dd=self.aes_encrypt( ddata ,password,False)
				self.write_file(path2,encr_dd)
				return True
			except:
				pass
		else: # path1 = data
			try: 
				encr_dd=self.aes_encrypt( path1 ,password,True)
				self.write_file(path2,encr_dd)
				return True
			except:
				pass
				
		return False
		
	
	def aes_decrypt_file(self,path1,path2,password):
		
		if os.path.exists(path1):
			try:
			# if True:
				ddata=self.read_file( path1)
				decr_dd=self.aes_decrypt( ddata ,password,False)
				if path2==None:
					return decr_dd.decode('utf-8').replace(self.principal4,'')
				else:
					self.write_bin_file(path2,decr_dd)
				return True
			except:
				pass
				
		return False
		
		
		
		
	def aes_encrypt(self,ddata,kkey='',encode=True): # key must be 16, 24 or 32 bytes long

		if kkey=='':
			kkey = get_random_bytes(32)
		else:
			while len(kkey)<16:
				kkey=kkey+kkey
	
			kklen=len(kkey)
				
			if type(kkey)!=type(b'asdf'):
				kkey = kkey.encode('utf-8')
				
			if kklen>32:
				kkey=kkey[:32]
			elif kklen>24:
				kkey=kkey[:24]
			elif kklen>16:
				kkey=kkey[:16]
			
		if type(ddata)!=type(b'asdf') and encode:
			ddata = ddata.encode('utf-8')
		
		if encode:		
			ddata=self.principal4.encode('utf-8')+ddata+self.principal4.encode('utf-8')
				
		cphr = AES.new(kkey, AES.MODE_CBC)
		ct_bytes = cphr.encrypt(pad(ddata, AES.block_size))
		
		iv = b64encode(cphr.iv).decode('utf-8')
		ct = b64encode(ct_bytes).decode('utf-8')
		
		return json.dumps({'iv':iv, 'ct':ct})


		
		
		

	def aes_decrypt(self,json_input,kkey,decode=True):

		while len(kkey)<16:
			kkey=kkey+kkey

		kklen=len(kkey)
			
		if type(kkey)!=type(b'asdf'):
			kkey = kkey.encode('utf-8')
			
		if kklen>32:
			kkey=kkey[:32]
		elif kklen>24:
			kkey=kkey[:24]
		elif kklen>16:
			kkey=kkey[:16]
			
		try:
		
			b64 = json.loads(json_input)
			iv = b64decode(b64['iv'])
			ct = b64decode(b64['ct'])
			
			cipher = AES.new(kkey, AES.MODE_CBC, iv)
			
			pt = unpad(cipher.decrypt(ct), AES.block_size)
			
			if decode:
				pt=pt.decode('utf-8').replace(self.principal4,'')
			
			return pt
			
		except:
		
			return 'Could not decrypt message'
			
		# return retv
		

	def read_file(self,path):
		rstr=""
		with open(path, "r") as f:
			rstr = f.read()
	
		return rstr
	
	def read_bin_file(self,path):
		bytes=b""
		with open(path, "rb") as f:
			bytes = f.read()
	
		return bytes
		
	def write_file(self,path,wstr):
		gui.copy_progress(path,'Encrypting to '+path,wstr,path, False)
		# with open(path, "w") as f:
			# f.write(wstr)
			
			
	def write_bin_file(self,path,bstr):
		# with open(path, "wb") as f:
			# f.write(bstr)
		gui.copy_progress(path,'Decrypting to '+path,bstr,path, False)
			
			
	def init_hash_seed(self):
		return self.hash(self.rand_num_N_bit(1024),1)
	
	
	def rand_num_N_bit(self,N):
		return str(random.getrandbits(N))
			
	# when sending message:
	def hash2utf8_1b(self,datastr,N):
		return self.int_to_utf8_1b(self.hash(datastr, N))
		
	# when reading - utf8 to hash
	def verify_hash(self,datastr,N):
		return self.hash(self.utf8_1b2hash(datastr),N)
	
	def utf8_1b2hash(self,datastr):
		
		return hex(self.utf8_1b_to_int(datastr)).replace('0x','')
 
