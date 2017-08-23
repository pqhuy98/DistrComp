import distrComp as dc
from timeit import default_timer as clock

# ---------Change these constants to fit your use.
my_source_code = "myprogram.py"

# Files to send to all workers
# If you want to `import message`, then you have to send `message.py`.
files = [my_source_code,"message.py"]

# Command to run on all workers
commands = ["python -B myprogram.py"]

# List of unique IP from all machines.
IPs = dc.read_ip_from("peers.txt")
# Or just :
# IPs = ["192.168.0.169","192.168.0.179","192.168.0.103","192.168.0.113"]

# Port which workers listen to. See worker.py for details.
comm_port = 6969

# Time to live in seconds.
# Programs which run longer than 'timelimit' seconds would be terminated.
timelimit = 3


# ----------------------------------------------
s = clock()
data = dc.make_script_package(
    files,
    commands,
    IPs = IPs,
    directory = None,
    block=True,
    timelimit=timelimit)

def foo() :
    global data
    dc.distribute_script(data, IPs)
    if (dc.local_ip() in IPs) :
        msg = dc.run_command(commands,timelimit=timelimit+1.1,shell=False)
        print("--------(Node localhost     return)--------\n%s"%msg)

try :
    for i in range(1) :
        foo()
        dc.join()
except KeyboardInterrupt:
    dc.join()

print("Total time : %s."%"{0:.3f}".format(clock()-s))