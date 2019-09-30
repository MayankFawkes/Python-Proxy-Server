import os,sys,socket
import threading,ssl
import select
import json

BACKLOG = 50
BLOCKED = []

def main():
    port = 44444
    host = ''
    print("Proxy Server Running on ",host,":",port)
    try:
	    if sys.argv[1]:
	    	proxy=sys.argv[1]
    except:
    	proxy=False
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((host, port))
        s.listen(BACKLOG)
    except socket.error:
        if s:
            s.close()
        print("Could not open socket:", message)
        sys.exit(1)
    while 1:
        #print("Accept")
        conn, client_addr = s.accept()
        threading.Thread(target=proxy_thread,args=(conn, client_addr,proxy),).start()
    s.close()

def printout(type,request,address):
    print(address[0],"\t",type,"\t",request)

def proxy_thread(conn, client_addr,proxy):
    rawreq = conn.recv(2048)
    request = rawreq.decode()
    #print(len(rawreq))
    #print(len(request))
    first_line = request.split('\n')[0]
    url = first_line.split(' ')[1]
    for i in range(0,len(BLOCKED)):
        if BLOCKED[i] in url:
            printout("Blacklisted",first_line,client_addr)
            conn.close()
            sys.exit(1)
    printout("Request",first_line,client_addr)
    http_pos = url.find("://")
    if (http_pos==-1):
        temp = url
    else:
        temp = url[(http_pos+3):]
    port_pos = temp.find(":") 
    webserver_pos = temp.find("/")
    if webserver_pos == -1:
        webserver_pos = len(temp)
    webserver = ""
    port = -1
    if (port_pos==-1 or webserver_pos < port_pos):
        port = 80
        webserver = temp[:webserver_pos]
    else:
        port = int((temp[(port_pos+1):])[:webserver_pos-port_pos-1])
        webserver = temp[:port_pos]

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #s = ssl.wrap_socket(s,certfile="cert.pem",keyfile="cert.pem",ssl_version=ssl.PROTOCOL_TLSv1)   
        #print(port)
        #print(webserver)
        if proxy:
        	proxyip=proxy.split(":")[0]
        	proxyport=proxy.split(":")[1]
        	s.connect((proxyip, int(proxyport)))
        else:
            s.connect((webserver,port))
        if first_line.find('CONNECT ')!=-1:
            if proxy:
                s.send(request.encode())
            else:
                conn.send(b"HTTP/1.1 200 Connection Established\r\n\r\n")
            #print('More data')
            while True:
                triple = select.select([conn,s], [], [], 5)[0]
                if not len(triple): break
                if conn in triple:
                    data = conn.recv(2048)
                    #print('more data'+str(len(data)))
                    if not data: break
                    s.send(data)
                if s in triple:
                    data = s.recv(2048)
                    #print('remote data'+str(len(data)))
                    if not data: break
                    conn.send(data)
        else:
            #print(request.encode())
            s.send(request.encode())
            while True:
                data = s.recv(2048)
                if not data: break
                conn.send(data)
        #print('Recv finished')
        s.close()
        conn.close()
    except socket.error:
        if s:
            s.close()
        if conn:
            conn.close()
        printout("Peer Reset",first_line,client_addr)
        sys.exit(1)
    
if __name__ == '__main__':
    main()