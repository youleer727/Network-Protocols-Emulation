import socket
import sys
import time, threading
import json

BUFFER_SIZE = 2048

class DVNode(object):
    '''This is a class that implements the distant vector'''
    def __init__(self, selfport):

        # the routing table column 1
        self.routing_table = {}
        # the routing table column 2, that stores next_hop value
        self.next_hop = {}

        # neighbor set, we don't modify it, used for broadcast
        self.neighbors = set()

        # our listening port
        self.self_port = selfport
        # set the distance to ourself as zero
        self.routing_table[selfport] = 0

        # create a server socket
        self.server_socket = create_socket()
        bind_socket(self.server_socket, self.self_port)

        # create a client socket
        self.client_socket = create_socket()

        # at least sent once
        self.first_broadcast = False

    def add_neighbor(self, port, drop_rate):
        '''A function to help initialize the routing table'''
        self.routing_table[port] = drop_rate

        # add hop to None, since they are direct neighbors at first
        self.next_hop[port] = None
        self.neighbors.add(port)


    def broadcast(self):
        '''Send current routing table to all the neighbors'''
        for port in self.neighbors:
            self.send_table(port)


    def send_table(self, target_port):
        '''Send routing table in this dvnode instance to the target port'''

        # pack our routing table and our port into a packet
        # our package has three keys
        packet = {}
        packet['sending_port'] = self.self_port
        packet['routing_table'] = self.routing_table
        packet['timestamp'] = time.time()

        # send it as json format
        self.client_socket.sendto(json.dumps(packet), ("", int(target_port)))

        # print "routing table sent to {}".format(target_port)
        print "[{}] Message sent from Node {} to Node {}".format(time.time(), self.self_port, target_port)


    def listen(self):
        '''Executed in a seperate thread listening in coming message'''

        try:
            while True:

                data, client_addr = self.server_socket.recvfrom(BUFFER_SIZE)
                if not data:
                    continue
                try:

                    data = json.loads(data)
                    # print data

                    sending_port = data['sending_port']
                    received_table = data['routing_table']
                    timestamp = data['timestamp']

                    print "[{}] Message received at Node {} from Node {}".format(time.time(), self.self_port, sending_port)

                    # update our routing table accordingly
                    # nn mean's neighbor's neighbor

                    # define a variable to check if we updated our routing table
                    table_updated = False

                    # update routing table based on the received routing table
                    for nn in received_table:

                        # if this routing table has a router that we don't know, we add it to our routing table
                        if not nn in self.routing_table:

                            # add it to our routing table
                            self.routing_table[nn] = self.routing_table[sending_port] + received_table[nn]

                            # since this router was not a neighbor, there must be a hop in between, add it into 
                            # the next_hop dictionary
                            self.next_hop[nn] = sending_port
                            
                            # set the variable to True, so we can broadcast the current routing table
                            table_updated = True

                        # if we have this router in our routing table as well
                        else:
                            # we implement Bellmanford Algo here, update distance according to the formula
                            # d(A, B) = min( d(A,B), d(A,C) + d(C,B) )
                            original_distance = self.routing_table[nn]
                            detour_distance = self.routing_table[sending_port] + received_table[nn]

                            # if the new route is shorter, we update it
                            if detour_distance < original_distance:
                                # print "[update with Bellmanford algorithm]"
                                # print "detour: {}, original_distance: {}".format(detour_distance, original_distance)
                                
                                # update the routing table
                                self.routing_table[nn] = detour_distance

                                # update the next_hop dictionary
                                self.next_hop[nn] = sending_port

                                # set the variable to True
                                table_updated = True

                    # broadcast current table to all neighbors if routing table update
                    # or if haven't sent its routing table to anyone yet
                    if (not self.first_broadcast) or (table_updated):

                        # print the routing table after updating
                        self.print_routing_table()

                        # remove the first broadcast flag
                        self.first_broadcast = True

                        # broadcast 
                        self.broadcast()



                except ValueError as e:
                    print "Value Error...{}".format(e)
                    continue


        finally:
            self.server_socket.close()


    def print_routing_table(self):
        # first line of the print message
        print "[{}] Node {} Routing Table".format(time.time(), self.self_port)

        # print each router's information
        for router in self.routing_table:

            # continue to next router if it is itself
            if router == self.self_port:
                continue

            # start setting the string to print
            router_str = "- ({}) -> Node {}".format(self.routing_table[router], router)

            # append the string if it has a next_hop value
            if router in self.next_hop and self.next_hop[router] != None:
                router_str = "{}; Next hop -> Node {}".format(router_str, self.next_hop[router])

            # print it finally
            print router_str


def create_socket():
    '''A function that creates a socket and return the instance'''
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    except socket.error as e:
        # print FAIL_TO_CREATE_SOCKET.format(str(e))
        print e
        sys.exit()
    return s


def bind_socket(s, port):
    '''A function that binds the socket to the designated port'''
    try:
        s.bind(('', int(port)))
    except socket.error as e:
        s.close()
        # print FAIL_TO_BIND_SOCKET.format(str(e))
        sys.exit()


def main():
    '''Main function executed by main'''

    # here we kinda assume that all the inputs are correct
    # get self port
    self_port = sys.argv[1]

    # extract the remaining neighbor ports and drop_rate
    neighbor_ports = sys.argv[2:]
    last = False

    # check if last exists
    if len(neighbor_ports)%2 != 0:
        neighbor_ports.pop()
        last = True

    # initialize the dvnode
    dvnode = DVNode(self_port)
    
    # parse and add its neighbors into the dvnode
    for i in range(len(neighbor_ports)/2):
        neighbor_port = neighbor_ports[i*2]
        neighbor_drop_rate = float(neighbor_ports[i*2+1])
        dvnode.add_neighbor(neighbor_port, neighbor_drop_rate)

    try:
        t1 = threading.Thread(target=dvnode.listen, name='listening mode')
        # daemon threads are killed automatically
        t1.daemon = True
        t1.start()


        # print the routing table on start 
        dvnode.print_routing_table()

        # if this is the last router to be included, we broadcast its routing table
        if last:
            dvnode.broadcast()

        while t1.isAlive():
            t1.join(1)

    except KeyboardInterrupt:
        pass



if __name__ == "__main__":
    main()


