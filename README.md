# DistrComp
A distributed computing library.

This library contains 4 main function : `node_id`, `n_node`, `send`, `recv`.

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
2) Place `peers.txt`, `distrComp.py` and `master.py` into folder which contains `myprogram.py`.
3) Tweak `master.py` to fit your purpose. Don't be afraid to read the code.
4) If you don't understand, then...

<h2>How it works</h2>
When you run `worker.py`, the machine will listen to a determined port (default : 6969). When you run `master.py`, the master will connect to all workers specified in `peers.txt`, or more precisely, in variable `IPs`. In `master.py`, you specify which files you want send to workers and which terminal commands you want to execute simultaneously. The master will send those files and commands (encoded to a binary string) to workers. Workers receive the package, decode it, save the files into a temporary folder, set it as current working directory, then execute the commands.