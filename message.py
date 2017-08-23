

import socket
import traceback
import threading
import cPickle
import struct
import time
import select
import os
from timeit import default_timer as clock

#debug = True
debug = False

common_port_file = ".6e0p4VsmBevqUKmCpvrrzKYXkl6KV5lI"
peers_file = "peers.txt"
#------
# Utils
#------
def safe_print(content) :
    print "Time : %i -- {0}\n".format(content,int(round(time.time()*1000))%100000),
def get_port() :
    with open(common_port_file,"r") as f :
        res = int(f.read())
    os.remove(common_port_file)
    return res
def local_ip() :
    return [l
        for l in ([ip
            for ip in socket.gethostbyname_ex(socket.gethostname())[2]
            if not ip.startswith("127.")
        ][: 1], [
            [(s.connect(('8.8.8.8', 53)), s.getsockname()[0], s.close())
                for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]
        ]) if l
    ][0][0]
def read_ip_from(file) :
    try :
        f = open(file,"r")
    except :
        raise "IP list \"%s\" is missing."%file
    res = []
    tmp = f.read().splitlines()
    for ip in tmp  :
        try:
            socket.inet_aton(ip)
            res.append(ip)
        except socket.error:
            pass
    f.close()
    return res


# IP list ("index to IP")
i2ip = read_ip_from(peers_file)
# IP to index eg. ip2i['192.168.0.123'] = 2
ip2i = dict()
for i in range(len(i2ip)) :
    ip2i[i2ip[i]] = i

#----------------
# Cluster details
#----------------

# My node ID
node_id = ip2i[local_ip()]

# Every node listen/connect to other nodes by this port.
port = get_port()

# Number of nodes.
n_node = len(i2ip)

# Sockets used to send/recv data. Locks for multithreading.
sock = [socket.socket() for i in range(n_node)]
lock = [threading.Lock() for i in range(n_node)]

# Used to recv from anyone (recv(-1)).
cached_sock = None
sock_avail = []

threads = []
threads_lock = threading.Lock()

"""
Node i will connect to every node j<i, ie their ID lesser than i.
Node i will listen to every node k>i, ie their ID greater than i.
"""
listen_to = set(i2ip[node_id+1:]) #Set of IP that this node will listen to
listen_to.discard("")
connect_to = list(i2ip[:node_id]) #List of IP that this node will connect to
nodes = len(listen_to)

if (debug) :
    safe_print("ID : %i, port : %i."%(node_id,port))


"==================================C-O-N-N-E-C-T=================================="
def listen_to_others() :
    global port,sock,listen_to
    #-----------------------------------
    if (debug) :
        safe_print("Listen to %s at port %i."%(str(listen_to),port))
    #-----------------------------------
    tmp_sock = socket.socket()
    tmp_sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
    tmp_sock.settimeout(None)
    tmp_sock.bind(("",port))
    tmp_sock.listen(1000)
    try :
        while len(listen_to)>0 :
            sk,address = tmp_sock.accept()
            #-----------------------------------
            if (debug) :
                safe_print("Get connection from %s."%str(address))
            #-----------------------------------
            if (address[0] in listen_to) :
                listen_to.remove(address[0])
                sock[ip2i[address[0]]] = sk
                sock_avail.append(sk)
            else :
                #-----------------------------------
                sk.close()
                if (debug) :
                    safe_print("Rejected : %s."%str(address))
                #-----------------------------------
                pass
    except :
        safe_print(traceback.format_exc())
    tmp_sock.close()

def _connect(ip,port) :
    idx = ip2i[ip]
    #-----------------------------------
    if (debug) :
        safe_print("Try to connect to %s by socket %i"%(str((ip,port)),idx))
    #-----------------------------------
    global sock, sock_avail
    cnt = 0
    succ = False
    while True :
        try :
            sk = socket.socket()
            sk.settimeout(0.1)
            sk.connect((ip,port))
            sock[idx] = sk
            sock_avail.append(sk)
            succ = True
            break
        except :
            cnt+=1
            sk.close()
    #-----------------------------------
    if (debug) :
        if (succ) :
            safe_print("Succeed after %i attempts."%cnt)
        else :
            safe_print("Failed after %i attempts."%cnt)
    #-----------------------------------
    
def connect_to_others() :
    global port,sock,connect_to
    #-----------------------------------
    if (debug) :
        safe_print("Connect to %s at port %i."%(str(connect_to),port))
    #-----------------------------------
    thr = []
    for ip in connect_to :
        if ip=="" :
            continue
        thr.append(threading.Thread(target=_connect,args=(ip,port)))
        thr[-1].start()
    for x in thr :
        x.join()

def setup_connection() :
    start = clock()
    #-----------------------------------
    if (debug) :
        safe_print("Setup connection.")
    #-----------------------------------
    global sock
    try :
        thr_listen = threading.Thread(target=listen_to_others)
        thr_listen.start()
        thr_connect = threading.Thread(target=connect_to_others)
        thr_connect.start()
        thr_listen.join()
        thr_connect.join()
        stop = clock()
        print "Setup connection :","{0:.3f}".format(stop-start)
        for x in sock :
            x.settimeout(None)
        for i in range(n_node) :
            if (i!=node_id) :
                try :
                    sock[i].send("OK")
                except :
                    raise Exception("Connection error. Cannot send validate message to %s."%i2ip[i])
        for i in range(n_node) :
            if (i!=node_id) :
                try :
                    msg = sock[i].recv(2)
                except :
                    safe_print(traceback.format_exc())
                    raise Exception("Validate recv: socket[%i] with %s."%(i,i2ip[i]))
                if (msg!="OK") :
                    raise Exception("Connection error. Message is not \"OK\".")
#        for x in sock :
#            x.settimeout(None)
        sock[node_id].close()
        sock[node_id] = None
        #-----------------------------------
        if (debug) :
            safe_print("Setup succeed.")
        #-----------------------------------
    except :
        #-----------------------------------
        if (debug) :
            safe_print("Setup failed.")
        #-----------------------------------
        safe_print(traceback.format_exc())

def close_connection() :
    #-----------------------------------
    if (debug) :
        safe_print("Close connection.")
    #-----------------------------------
    global sock, threads
    for x in threads :
        x.join()
    for x in sock :
        try :
            x.close()
        except :
            pass

#==================================S-E-N-D--&--R-E-C-E-I-V-E==================================#
def _send(idx,data) :
    global sock
    try :
        x = cPickle.dumps(data)
        y = struct.pack("i",len(x))
        with lock[idx] :
            sock[idx].sendall("x"+y+x)
    except :
        safe_print(traceback.format_exc())
        raise Exception("Send : socket[%i] with %s is dead."%(idx,i2ip[idx]))

def send(idx,data) :
    # safe_print("DB <<" + str(idx))
    if (idx==node_id) :
        raise "Cannot send message to myself."
    else :
        with threads_lock :
            threads.append(threading.Thread(target=_send,args=(idx,data)))
            threads[-1].start()

def recv(idx) :
    if (idx==node_id) :
        raise Exception("Cannot receive message from myself.")
    global sock, sock_avail, cached_sock
    if (idx<0) :
        if not(cached_sock is None) :
            return cached_sock
        while (True) :
            s,tmp1,tmp2 = select.select(sock_avail, [], [])
            sk = None
            for i in range(len(s)) :
                x = s[i].recv(1)
                if (len(x)==0) :
                    sock_avail.remove(s[i])
                else :
                    sk = s[i]
                    break
            if not(sk is None) :
                break
        for i in range(len(sock)) :
            if (sock[i]==sk) :
                cached_sock = i
                return i
    try :
        if (idx!=cached_sock) :
            sock[idx].recv(1)
        else :
            cached_sock = None
        s = sock[idx].recv(4)
        while len(s)==0 :
            s = sock[idx].recv(4)
        y = struct.unpack("i",s)[0]
        s = sock[idx].recv(y)
        while (len(s)<y) :
            s+=sock[idx].recv(y-len(s))
        x = cPickle.loads(s)
        return x
    except :
        safe_print(traceback.format_exc())
        raise Exception("Recv : socket[%i] with %s is dead."%(idx,i2ip[idx]))
    return False