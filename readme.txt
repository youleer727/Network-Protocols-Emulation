#CSEE4119 Network Protocols Emulation
Name: Xiyan Liu UNI: xl2672

## Go-Back-N Protocol(GBN)
 
### Description:
GBN protocol can guarantee that all packets can be delivered in the correct order. 
To emulate an unreliable channel, the receiver or the sender will drop the incoming packets 
and acks with a specific probability. 


### Command Line Instructions:

#### Initiate a gbnnode as a listener
```bash
$ python gbnnode.py <self-port> <peer-port> <window-size> [-d <value-of-n> | -p <value-of-p>]
```

#### Initiate a gbnnode as a sender
```bash
$ python gbnnode.py <self-port> <peer-port> <window-size> [-d <value-of-n> | -p <value-of-p>]
```

#### Send messages
```bash
$ node> send <message>
```

### Program Feature
GBN protocol is bulit on top of UDP. Several cases are considered in this implementation.
Normal packet sending: window moves and ACK replied. 
An ACK is lost: Following ACK could also move the window.
A packet is dropped: Timer timout and packets resent.
Duplicate packets: the packet is not delivered and teh correct ACK is replied.
Duplicate ACKs: the window will not move.

### Data Structure and Internal Logic
A GBN class is created which including a buffer_string list and a window list. 
buffer_string is the whole message, while window list is the list of characters which are available to operate. 

Two Theads
- main 
- sending 
- listening 

## Distance Vector Routing Algorithm(DVN)
 
### Description:
DVN algorithm is to implemente a routing protocol in a static network. Route table is based on the distaces to other nodes
in the network. The Bellman-Ford algorithm is used build and update the rounting tables. UDP protocol is used to exchage 
the routing tables.


### Command Line Instructions:

#### Initiate a GVNode
```bash
$ python gbnnode.py <local-port> <neighbor1-port> <loss-rate-1> <neighbor2-port> <loss-rate-2> ...[last]
```

### Program Feature
Distance Vector: Routing tables and their updates should follow DV algorithms.
DV Updates: DV updates should be sent out to all neighbors once the routing table is changed. 

### Data Structure and Internal Logic
Routing table is a dictionary of other nodes and distances.
Next_hop is a dictionary to store other nodes and the mapped detour node. 
Broadcast is a set of neighbours. 

Listen():
We implement Bellmanford Algotithm here, update distance according to the formula
d(A, B) = min( d(A,B), d(A,C) + d(C,B) )

Broadcast():
this function is triggered when the node haven't send it's routing table at once or when there is a update 
change in the routing table. 







