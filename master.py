import distrComp as dc
from timeit import default_timer as clock

# Files to send to all workers
files = ["test.py","message.py","peers.txt"]
# Command to run on all workers
commands = ["python -B test.py"]


s = clock()
slaves_ip = dc.read_ip_from("peers.txt")
comm_port = 6969
timelimit = 3

data = dc.make_script_package(
    files,
    commands,
    # directory = "cache/",
    block=True,
    timelimit=timelimit)

def foo() :
    global data
    dc.distribute_script(data, slaves_ip)
    if (dc.local_ip() in slaves_ip) :
        msg = dc.run_command(commands,timelimit=timelimit+1.1,shell=False)
        dc.safe_print("--------(Node localhost     return)--------\n%s"%msg)

try :
    for i in range(1) :
        foo()
        dc.join()
except KeyboardInterrupt:
    dc.join()

dc.safe_print("Total time : %s."%"{0:.3f}".format(clock()-s))