CSEE4119 Network Protocols Emulation
Name: Xiyan Liu UNI: xl2672

Go-Back-N Protocol(GBN)
 
- Description:
GBN protocol can guarantee that all packets can be delivered in the correct order. 
To emulate an unreliable channel, the receiver or the sender will drop the incoming packets 
and acks with a specific probability. 


- Command Line Instructions:

-- Initiate a gbnnode as a listener
$ python gbnnode.py <self-port> <peer-port> <window-size> [-d <value-of-n> | -p <value-of-p>]

-- Initiate a gbnnode as a sender
$ python gbnnode.py <self-port> <peer-port> <window-size> [-d <value-of-n> | -p <value-of-p>]

-- Send messages
$ node> send <message>

- Program Feature
GBN protocol is bulit on top of UDP. Several cases are considered in this implementation.
Normal packet sending: window moves and 



