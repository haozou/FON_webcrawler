from socket import *
import sys
import select
host = "www.ccs.neu.edu"
sock = socket(AF_INET, SOCK_STREAM)  
sock.connect((host, 80))
page = "/home/cbw/4700/project4.html"
request = ''.join(("GET %s HTTP/1.1\r\n" % page) 
                          + ("Host: %s\r\n" % host) 
                          +"User-Agent:Mozilla/4.0\r\n"
                          +"Accept: */*\r\n"
                          +"Connection: keep-alive\r\n\r\n"
                          )

sock.send(request)

tmp = sock.recv(2048)
data = ''.join(tmp)
tmp = tmp[tmp.find('Content-Length:') + len('Content-Length:'):]
tmp = tmp[:tmp.find('\n')]
print tmp
while len(tmp) > 0:
    tmp = sock.recv(2048)
    data += tmp
    print len(tmp)

print len(data) - len(data[:data.find('\r\n\r\n')+4])    

sock.close()