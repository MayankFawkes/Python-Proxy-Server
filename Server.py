import os,sys,socket
import threading,ssl
import select, json
from datetime import datetime
import argparse

class ProxyServer:
	BACKLOG = 50
	BLOCKED = [""]
	auth=b"HTTP/1.1 200 Connection Established\r\n\r\n"
	block_response = b'HTTP/1.1 200 OK\r\nPragma: no-cache\r\nCache-Control: no-cache\r\nContent-Type: text/html\r\nDate: Sat, 15 Feb 2020 07:04:42 GMT\r\nConnection: close\r\n\r\n<html><head><title>ISP ERROR</title></head><body><p style="text-align: center;">&nbsp;</p><p style="text-align: center;">&nbsp;</p><p style="text-align: center;">&nbsp;</p><p style="text-align: center;">&nbsp;</p><p style="text-align: center;">&nbsp;</p><p style="text-align: center;">&nbsp;</p><p style="text-align: center;"><span><strong>**YOU ARE NOT AUTHORIZED TO ACCESS THIS WEB PAGE | YOUR PROXY SERVER HAS BLOCKED THIS DOMAIN**</strong></span></p><p style="text-align: center;"><span><strong>**CONTACT YOUR PROXY ADMINISTRATOR**</strong></span></p></body></html>'
	http_requests=["get","head","post","put","delete","connect","options","trace","patch"]
	def __init__(self,addr:dict,proxy:dict=None,debug=False):
		self.host=addr["host"]
		self.port=addr["port"]
		self.proxy=proxy
		self.debug=debug
		if self.debug:self.log(f"[{self._get_time()}] Proxy Server Running on {self.host}:{self.port}")
		print(f"[{self._get_time()}] Proxy Server Running on {self.host}:{self.port}")
		try:
			self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			self.sock.bind((self.host, self.port))
			self.sock.listen(self.BACKLOG)
		except socket.error as message:
			if self.debug:self.log(f"Could not open socket: {message}")
			print(f"Could not open socket: {message}")
			sys.exit(1)
	@staticmethod
	def printout(type,request,address):
		print(address[0],"\t",type,"\t",b" ".join(request))
	@staticmethod
	def _get_time():
		dt = datetime.now().strftime("%I:%M:%S %p")
		return dt
	def process(self,conn, client_addr):
		rawreq = conn.recv(2048)
		print(client_addr)
		print(rawreq)
		if rawreq:
			header=self._requests_header(head=rawreq,client_addr=client_addr)
			if header["DOMAIN"] not in self.BLOCKED:
				if header["REQUESTS_TYPE"].lower() in ["connect"]:
					print(header)
					self._action(conn=conn,host=header["DOMAIN"],port=header["PORT"],data=rawreq,type="connect")
				else:
					self._action(conn=conn,host=header["DOMAIN"],data=rawreq)
			else:
				conn.send(self.block_response)
				conn.close()
				if self.debug:self.log(f'[{self._get_time()}] Domain is blocked By ProxyServer')
	def _action(self,conn:object,host:str,port:int=80,data:bytes=b"",type:str=None,timeout=3):
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		try:
			if self.proxy:
				s.connect((self.proxy["host"],self.proxy["port"]))
				s.send(data)
			else:
				print(host,port)
				s.connect((host,port))
				if not type:
					s.send(data)
				else:
					conn.send(self.auth)
		except:
			if self.debug:self.log(f'[{self._get_time()}] Internet is not connected or domain is invalid')
			print(f'[{self._get_time()}] Internet is not connected or domain is invalid')
		while True:
			try:
				triple = select.select([conn,s], [], [])[0]
				if not len(triple): break
				if conn in triple:
					data = conn.recv(8192)
					print('Client data '+str((data)))
					if not data: break
					s.send(data)
				if s in triple:
					data = s.recv(8192)
					print('Remote data '+str((data)))
					if not data: break
					conn.send(data)
			except:
				conn.close()
				s.close()
	def _requests_header(self,head:bytes,client_addr:tuple,data:dict={}):
		try:
			d=head
			first = d.split(b'\r\n')[0].split(b' ')
			schemes=False
			if first[1].find(b"http://") != -1 or first[1].find(b"http://") != -1:
				schemes=True
			if schemes:
				self.printout("Request",first,client_addr)
				data["REQUESTS_TYPE"] = first[0].decode()
				data["PROTO"], other= first[1].split(b"://")
				DOMAIN_PROTO = other.split(b"/")[0]
				data["LOC_PARAMS"] = "/"+b"/".join(other.split(b"/")[1:]).decode()
				if DOMAIN_PROTO.find(b":") is not -1:
					DOMAIN = DOMAIN_PROTO.split(b":")[0].decode()
					PORT = DOMAIN_PROTO.split(b":")[1].decode()
				else:
					DOMAIN = DOMAIN_PROTO.decode()
					PORT = 80
				data["DOMAIN"] = DOMAIN
				data["PORT"] = PORT
				return data
			else:
				self.printout("Request",first,client_addr)
				data["PORT"] = 443
				data["REQUESTS_TYPE"] = first[0].decode()
				DOMAIN_PROTO = first[1].split(b"/")[0]
				data["DOMAIN"] = DOMAIN_PROTO.decode()
				data["LOC_PARAMS"] = "/"+b"/".join(first[1].split(b"/")[1:]).decode()
				if DOMAIN_PROTO.find(b":") is not -1:
					DOMAIN = DOMAIN_PROTO.split(b":")[0]
					PORT = DOMAIN_PROTO.split(b":")[1]
				else:
					DOMAIN = DOMAIN_PROTO
					PORT = 80
				data["DOMAIN"] = DOMAIN.decode()
				if PORT:data["PORT"] = int(PORT.decode())
				return data
		except:
			self.printout("Error",first,client_addr)
			print(head)

	def start(self):
		while True:
			conn, client_addr = self.sock.accept()
			s=threading.Thread(target=self.process,args=(conn, client_addr),)
			s.start()
			# s.join()
		self.sock.close()
	def __repr__(self):
		return f'<{self.__class__.__name__}.{self.__class__.__module__} host={self.host}, port={self.port} at {hex(id(self))}>'
	def __str__(self):
		return f'<{self.__class__.__name__}.{self.__class__.__module__} host={self.host}, port={self.port} at {hex(id(self))}>'
	@staticmethod
	def log(msg):
		with open("ProxyServer.logs","a") as file:
			file.write(f'{msg}\n')
			file.close()


if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument("--lhost","-LH",help="IP of local server",type=str)
	parser.add_argument("--lport","-LP",help="IP of local server",type=int)
	parser.add_argument("--rhost","-RH",help="IP of remote server",type=str)
	parser.add_argument("--rport","-RP",help="PORT of remote server",type=int)
	args = parser.parse_args()
	kwargs={"addr":{"host":"0.0.0.0","port":44444},"proxy":{}}
	if args.lhost:kwargs["addr"]["host"]=args.lhost
	if args.lport:kwargs["addr"]["port"]=args.lport
	if args.rhost and args.rport:
		kwargs["proxy"]["port"]=args.rport
		kwargs["proxy"]["host"]=args.rhost
	ProxyServer(**kwargs,debug=False).start()
