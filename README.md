# DistrComp
A distributed computing library.

This library contains 4 main function : `node_id`, `n_node`, `send`, `recv`.  
You can send / receive many types of data (list, dict, set, numpy array,...), as long as they are pickle-able.

```python
import message as ms

ms.setup_connection()

rank = ms.node_id
nodes = ms.n_node
nxt = (rank+1)%nodes
pre = (rank-1+nodes)%nodes

print "My ID is", rank
ms.send(nxt, "Next to %i is %i" % (rank, nxt))
msg = ms.recv(pre)

print msg
```
Output on my cluster :
```
--------(Node 192.168.0.179 return)--------
My ID is 1
Next to 0 is 1

--------(Node 192.168.0.113 return)--------
My ID is 3
Next to 2 is 3

--------(Node 192.168.0.169 return)--------
My ID is 0
Next to 3 is 0

--------(Node localhost     return)--------
My ID is 2
Next to 1 is 2

Total time : 1.455.
```

<h2>How to use</h2>  

Suppose you have `N` machine, then `1` of them would be master and `N-1` of them would be workers. You want to run `myprogram.py` on those machines.  

On <b>each</b> worker machine :  

1) Put `distrComp.py` and `worker.py` into a folder.
2) Run command line `python -B worker.py`.

On master machine :  

1) Create file `peers.txt` contains IPs of all machines.
2) Place `peers.txt`, `distrComp.py`, `message.py` and `master.py` into folder which contains `myprogram.py`.
3) Tweak `master.py` constants to fit your purpose. Don't be afraid of reading the code.
4) When you're ready to go, run `python -B master.py`. Your `myprogram.py` would be automatically distributed to all workers.
4) If you're still confused, then read...

<h2>How it works</h2>

When you run `worker.py`, the machine will listen to a determined port (default : 6969). When you run `master.py`, the master will connect to all workers whose IPs are specified in `peers.txt`, or more precisely, the variable `IPs` inside `master.py`. 
  
By tweaking `master.py`, you specify which files (eg. source code, header files,...) you want send to workers and which terminal commands (eg. `python XXX.py`, `g++ main.cpp ; ./a.out`,...) you want to execute simultaneously. The master will send those files and commands (encoded as a binary string) to workers.  

Workers will receive the string, decode it, save the files into a temporary folder, set the folder as current working directory and spawn subprocesses to execute the commands.  

Output from STDOUT of those subprocesses are sent back to master to be printed out. 

<h2>What these files do</h2>

`distrComp.py` : required by `master.py` and `worker.py`  
`master.py` and `worker.py` : scripts to run on master and workers.  
`message.py` : handle connection between machines, implementation of `message.send`, `message.recv`.  

<b>(WARNING)<b> This library was implemented when I started learning about socket programming (January 2017). Its functionality is pretty good. However, the implementation is naive and contains a very serious security hole. Also it's better to use MPI. This project is now an antique that reminds me what I've struggled with during my education.
