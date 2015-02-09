'''
Created on 2013-1-15

@author: Administrator
'''

import sys
import socket
import Queue

class Webcrawler:
    # save the http header received from the server
    httpheader = ""
    # save the csrftoken received from the server
    csrftoken = ""
    # save the sessionid received from  the server
    sessionid = ""
    # save the http content received from the server
    buffer = ""
    # save the secret flag that we have found
    secret_flag = []
    # test use, test the error page
    error = []
    # it is a queue saving the pages that we need to crawl
    pages = Queue.Queue(0)
    # save the pages that we have crawled
    visited = {}
    # initialize the host, port and the username and password
    def __init__(self,host, port,username, pwd):
        self.host = host
        self.port = port
        self.username = username
        self.pwd = pwd
    # connect to the server
    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  
        self.sock.connect((self.host, self.port))
    # http get command
    def http_get(self,page):

        request = ''.join(("GET %s HTTP/1.1\r\n" % page) 
                          + ("Host: %s\r\n" % self.host) 
                          +"User-Agent:Mozilla/4.0\r\n"
                          +"Accept: */*\r\n"
                          +("Cookie: sessionid=%s\r\n" % self.sessionid)
                          +"Connection: keep-alive\r\n\r\n"
                          )
#        print request
        self.connect()
        self.sock.send(request)
    # http post command
    def http_post(self,page):

        request = ''.join(("POST %s HTTP/1.1\r\n" % page)
                          + ("Host: %s\r\n" % self.host) 
                          +"Content-Length: 109\r\n"
                          +"Content-Type: application/x-www-form-urlencoded\r\n"
                          +"User-Agent: Mozilla/4.0 (compatible; MSIE 6.0;Windows NT 5.1; SV1; .NET CLR 2.0.50727)\r\n"
                          +"Accept: */*\r\n"
                          +"Pragma: no-cache\r\n"
                          +"Cache-Control: no-cache\r\n"
                          +("Cookie: csrftoken=%s\r\n" % self.csrftoken)
                          +("Cookie: sessionid=%s\r\n" % self.sessionid)
                          +"Connection: keep-alive\r\n\r\n"
                          +("csrfmiddlewaretoken=%s&username=%s&password=%s&next=%%2Ffakebook%%2F" % (self.csrftoken,self.username,self.pwd)))
        #print request
        self.connect()
        self.sock.send(request)
    # get the response from the server and resolve it
    def get_response(self,page):
        # the total data received from the server
        total_data = []
        # the lenght that we want to receive
        recv_len = 4096
        # the status used to decide whether it is a correct page
        status = 0;
        
        tmp = self.sock.recv(recv_len)   
        total_data.append(tmp)
#        while len(tmp) > 0:
#            tmp = self.sock.recv(recv_len)
#            total_data.append(tmp)
  
        self.buffer = ''.join(total_data)
        #http header
        self.httpheader = self.buffer[:self.buffer.find('\r\n\r\n')+4]
        #http content
        self.buffer = self.buffer[self.buffer.find('\r\n\r\n')+4:]
        #set cookie
        self.set_cookie()
        
        # get the status, if it is not 0, it is a wrong page.
        status = self.http_status_codes_control(page)        
        #print self.httpheader
        self.close()
        return status
    # set the cookie that we received from the http header
    def set_cookie(self):
        #set cookie
        cookiesize = 32
        tmp = self.httpheader.find('csrftoken=')
        if  tmp > 0:
            self.csrftoken = self.httpheader[tmp+len('csrftoken='):tmp+len('csrftoken=')+cookiesize]
        tmp = self.httpheader.find('sessionid=')
        if tmp > 0:
            self.sessionid = self.httpheader[tmp+len('sessionid='):tmp+len('sessionid=')+cookiesize]
    # control the error page. we only control 404,403, 500 and 301 status code
    def http_status_codes_control(self,page):
        
        tmp = self.httpheader 
        # if it is 403 or 404,we just abandon it
        if tmp.find("HTTP/1.1 404")>=0 or tmp.find("HTTP/1.1 403")>=0:
            print page , "ERROR HTTP/1.1 404 NOT FOUND"
            self.visited.pop(page)
            self.error.append((page,"404 NOT FOUND"))
            return 4
        # if it is 500, we retry until it is correct
        elif tmp.find("HTTP/1.1 500")>=0:
            print page , "ERROR HTTP/1.1 500 Internal Server Error"
            
            while 1:
                print "retry"
                self.http_get(page)
                if self.get_response(page) == 0:
                    print "success\n", self.httpheader
                    break
            self.error.append((page,"500 Internal Server Error"))
            return 0
        # if it is 301, we retry the new page
        elif tmp.find("HTTP/1.1 301")>=0:
            print page, "ERROR HTTP/1.1 301"
            print "retry"
            t = tmp.find("Location: http://cs5700f12.ccs.neu.edu")
            
            page = tmp[t+len("Location: http://cs5700f12.ccs.neu.edu"):tmp.find("\r\n")]
            print page
            self.http_get(page)
            self.visited[page] = True
            self.get_response(page)
            self.error.append((page,"301 Moved Permanently"))
            return 2
        return 0 
    # obtain the href from the current page.       
    def get_pages(self,current_page):
        flagsize = 64
        tmp = self.buffer
        
        while tmp.find("href=\"/fakebook") > 0:
            tmp = tmp[tmp.find("href=\"")+len("href=\""):]
            page = tmp[:tmp.find("\"")]
            # if the href we have not visited, add it to the queue -- pages 
            if not self.visited.has_key(page):
                self.visited[page] = current_page
                self.pages.put(page)
            tmp = tmp[tmp.find("\""):] 
        #if find  the secret flag, we add it to the array
        tmp = self.buffer
        if tmp.find("FLAG:") > 0:
            flag = tmp[tmp.find("FLAG:")+len("FLAG:"):tmp.find("FLAG:")+len("FLAG:")+flagsize]
            self.secret_flag.append((current_page,flag))
    # used to login to the fakebook        
    def login(self):
        page = '/accounts/login/?next=/fakebook/'
        self.http_get(page)
        self.visited[page] = True
        self.get_response(page)
        page = '/accounts/login/'
        self.http_post(page)
        self.visited[page] = True
        self.get_response(page)
        page = '/fakebook/'
        self.http_get(page)
        self.visited[page] = True
        self.get_response(page)        
        self.get_pages(page)
    # main function, the main logic to crawl the website
    def crawl(self):

        i = 0
        while not self.pages.empty():
            page = self.pages.get()
            self.http_get(page)
            self.get_response(page)
            self.get_pages(page)
            i+=1
            print i, self.secret_flag,self.pages.qsize(),len(self.visited)
            if len(self.secret_flag) == 5:
                return 1
#        test use
        
#        print self.error 
    def close(self):
        self.sock.close()
        
def run():
    if len(sys.argv) < 4:
        print "use: %s <Address1> <username> <password>...\n" % (sys.argv[0])
        exit(1)
    else:
        host = sys.argv[1]
        username = sys.argv[2]
        password = sys.argv[3]
        
    print host
    
    crawler  = Webcrawler(host,80,username,password)

    crawler.login()
    crawler.crawl()
if __name__ == '__main__':

    run()
# Decode TCP header and store in a map
