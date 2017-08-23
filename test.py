import message as ms

ms.setup_connection()

rank = ms.node_id
nodes = ms.n_node
nxt = (rank+1)%nodes
pre = (rank-1+nodes)%nodes

x = 69

if rank == 0 :
    print "master"
    print x
    ms.send(nxt, x+1)
else :
    x = ms.recv(pre)
    print x
    ms.send(nxt, x+1)

ms.close_connection()