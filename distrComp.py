from __future__ import print_function
import socket
import threading
import os
import subprocess32 as subprocess
import traceback
import uuid
import cPickle as pickle

debug = False

lock = threading.Lock()
threads = []
master_ip = None
main_dir = os.getcwd()
PORT = 6969

common_port_file = ".6e0p4VsmBevqUKmCpvrrzKYXkl6KV5lI"
peers_file =       ".Xs9XoR1jPBWqptxPLJMJY5YuBZKADH32"

#================================C-O-M-M-O-N============================
def join() :
    global threads
    for x in threads :
        x.join()

# Search for an unused port.
def get_new_port() :
    sock = socket.socket()
    sock.bind(("",0))
    res = sock.getsockname()[1]
    sock.close()
    return str(res)

# Return my local IP in LAN.
def local_ip() :
    return [l for l in ([ip for ip in socket.gethostbyname_ex(socket.gethostname())[2]if not ip.startswith("127.")][: 1], [[(s.connect(('8.8.8.8', 53)), s.getsockname()[0], s.close())for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]]) if l][0][0]

# Read IP and discard wrong IPs.
def read_ip_from(file) :
    try :
        f = open(file,"r")
    except :
        raise "IP list \"%s\" is missing."%file
    res = []
    tmp = f.read().splitlines()
    for ip in tmp  :
        try:
            # raise exception if IP is in wrong format.
            socket.inet_aton(ip)
            res.append(ip)
        except socket.error:
            pass
    f.close()
    if (len(res) != len(set(res))) :
        print("FATAL : IP list must be unique !")
        quit()
    return res

# build a pickle string that stores files, commands to run and some setting.
def make_script_package(files, commands, IPs=None, directory = None, block = True, timelimit = 5) :
    data = dict()
    if not(directory is None) :
        data["dir"] = directory
    data["type"] = "run_script"
    if IPs is not None :
        data["IPs"] = IPs
        data["port"] = get_new_port()
        with open(peers_file,"w") as f :
            for x in data["IPs"] :
                f.write(x+"\n")
        with open(common_port_file,"w") as f :
            f.write(data["port"])

    data["block"] = block
    data["scripts"] = dict()
    data["scripts"]["name"]=list()
    data["scripts"]["data"]=list()
    data["commands"] = list()
    data["timelimit"] = timelimit
    for file in files :
        with open(file,"rb") as f :
            data["scripts"]["name"].append(file)
            data["scripts"]["data"].append(f.read())
    for cmd in commands :
        data["commands"].append(cmd)
    data = pickle.dumps(data)
    return data

# Send pickle string to worker and receive response.
def send_data(sock, address, data, timeout = 100) :
    try :
        sock.sendall(data)
        sock.settimeout(timeout+2);
        msg = sock.recv(999999)
        print("--------(Node %s returns)--------\n%s"%(address[0],str(msg)))
    except :
        print("--------(send_script result)--------\n"+traceback.format_exc())
    sock.close()

# Spawns subprocesses for each command sequentially.
# Returns stdout as string.
def run_command(commands,block=True,timelimit=100,shell=False) :
    if not(block) :
        return "Non-blocking mode hasn't been supported yet."
    global lock
    msg = ""
    try :
        for cmd in commands :
            if (debug) :
                print("$ %s"%cmd)
            if (timelimit==0) :
                timelimit = None
            try :
                msg+= subprocess.check_output(
                    cmd.split(),
                    stderr=subprocess.STDOUT,
                    timeout=timelimit,
                    shell=shell)
            except subprocess.TimeoutExpired as e:
                msg+= e.output
                msg+= traceback.format_exc()
            except subprocess.CalledProcessError as e:
                msg+= e.output
    except :
        msg+= traceback.format_exc()
    return msg

# receive all
def recv_all(sock) :
    data = []
    while True :
        try :
            data.append(sock.recv(4096))
        except :
            break
        if (len(data[-1])==0) :
            break
    return "".join(data)

#============================M-A-S-T-E-R============================
def connect_to(address,port) :
    while True :
        try :
            local_sock = socket.socket()
            local_sock.settimeout(0.1)
            local_sock.connect((address,port))
            break
        except :
            local_sock.close()
            local_sock = None
    return local_sock


def send_command_to(ip, port, handler, handler_args=()) :
    sock = socket.socket()
    sock.settimeout(3)
    try :
        sock.connect((ip,port))
        if debug :
            print("Connected to %s"%str((ip,port)))
            print("Accepted.")
        with lock :
            threads.append(threading.Thread(target=handler,args=(sock,(ip,port))+handler_args))
            threads[-1].start()
    except :
        print("Cannot connect to %s."%str((ip,port)))
        sock.close()
        print(traceback.format_exc())

def distribute_script(data,slaves_ip) :
    global PORT
    for ip in slaves_ip :
        if (ip==local_ip()) :
            continue
        with lock :
            threads.append(threading.Thread(
                    target=send_command_to,
                    args=(ip,PORT,send_data,(data,))
            ))
            threads[-1].start()
#============================S-L-A-V-E-S============================
#Receives and executes command from master by socket.
def receive_command_from(sock) :
    global lock
    with lock :
        try :
            data = pickle.loads(recv_all(sock))
            if (data["type"]=="run_script") :
                if ("dir" in data) :
                    directory = data["dir"]
                else :
                    directory = "tmp/z"+str(uuid.uuid4())+"/"
                os.chdir(main_dir)
                try :
                    os.makedirs(directory)
                except :
                    pass
                os.chmod(directory,0777)
                os.chdir(directory)
                if ("port" in data) :
                    with open(common_port_file,"w") as f :
                        f.write(data["port"])
                if ("IPs" in data) :
                    with open(peers_file,"w") as f :
                        for x in data["IPs"] :
                            f.write(x+"\n")
                block = data["block"]
                print(data["scripts"]["name"])
                print(data["commands"])
                for i in range(len(data["scripts"]["name"])) :
                    with open(data["scripts"]["name"][i],"wb") as f :
                        f.write(data["scripts"]["data"][i])                
                result = run_command(data["commands"],block,data["timelimit"],False)
                sock.send(result)
                print(result)
                return True
            else :
                pass
        except :
            print("Command corrupted.")
            print(traceback.format_exc())
        os.chdir(main_dir)

def listen_to_master(port) :
    #Listen to master forever.
    if (master_ip is None) :
        print("Master is not set. Listen to everyone.")
    else :
        print("Master is set. Listen to %s."%master_ip)
    sock = socket.socket()
    sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
    sock.bind(("",port))
    sock.listen(1000)
    try :
        while True :
            print("Listen to master...")
            sk,address = sock.accept()
            if not(master_ip is None) and (address[0]!=master_ip) :
                sk.close()
                continue
            print("Got connection from master.")
            sk.settimeout(1)
            receive_command_from(sk)
            sk.close()
    except KeyboardInterrupt :
        sock.close()
        print("Socket closed.")
