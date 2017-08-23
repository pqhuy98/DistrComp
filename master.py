import distrComp as dc
from timeit import default_timer as clock

# Files to send to all workers
files = ["test.py","message.py","peers.txt"]

# Command to run on all workers
commands = ["python -B test.py"]

# IP of everyone who does the job.
IPs = dc.read_ip_from("peers.txt")

# Port which workers listen to
comm_port = 6969

# Time to live in seconds.
timelimit = 3

s = clock()
data = dc.make_script_package(
    files,
    commands,
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