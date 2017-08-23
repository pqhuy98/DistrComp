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

ms.close_connection()
