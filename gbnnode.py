import socket
import argparse
import sys
import time, threading
import json
import random

BUFFER_SIZE = 2048
TIME_OUT = 0.5
DETERM_DROP = '-d'
PROBAB_DROP = '-p'

class GBN:
    def __init__(self, selfport, peerport, windowsize, way_to_drop, drop_param):
        # the opposite port
        self.peer_port = peerport

        # our listening port
        self.self_port = selfport
        self.window_size = int(windowsize)

        # create a socket
        self.socket = create_socket()
        bind_socket(self.socket, self.self_port)

        # a timer for resending window
        self.timer = time.time()

        # data structure for buffer and window
        self.buffer_string = []

        buffer_length = 0
        # a var used for the END hack
        self.window = []

        # a variable for the receiver side to track the farthest packet we've recevied
        self.receiver_latest_sequence = -1

        # a var for the sender side to track the farthest ack we've received 
        self.sender_latest_ack = -1

        # emulation purpose parameters
        self.way_to_drop = way_to_drop
        self.drop_param  = drop_param

    def deliver(self, packet):
        self.socket.sendto(packet[0], ("", int(self.peer_port)))
        seq = packet[0].split("|")[0]
        char = packet[0].split("|")[1]
        if int(seq) != self.buffer_length:
            print "[{}] packet{} {} sent".format(time.time(), seq, char)
        if packet[1] != 'ack':
            packet[1] = 'sent'

    def send_window(self):
        ACKED = False
        for i in range(len(self.window)):
            if self.window[i][1] == 'ack':
                # Kill all ACKed Previous
                self.window = self.window[i+1:]
                ACKED = True
                break
            elif self.window[i][1] == 'unsend':
                self.deliver(self.window[i])
                
        if ACKED:
            while len(self.window) < self.window_size and len(self.buffer_string) > 0:
                self.window.append(self.buffer_string.pop(0))
            self.timer = time.time() + 0.5

        # Handle Timeout
        if self.timer < time.time():
            # Print Timeout here
            print '[{}] packet{} timeout'.format(time.time(), self.window[0][0].split('|')[0])
            self.timer = time.time() + 0.5
            for i in range(len(self.window)):
                self.deliver(self.window[i])
        
    
    def send(self):
        '''Use this node as the client, sender'''
        try:
            while True:
                prompt()
                data = raw_input()
                if data == "":
                    continue
                action, message = message_split(data)
                # print "message: {}".format(message)
                if action == 'send':
                    # init the buffer, [[0a, unsend], [1b, unsend], [2c, unsend]...]
                    for i, c in enumerate(message):
                        # add "|" to prevent two-digits length of sequence
                        self.buffer_string.append([str(i) + '|' + c, 'unsend'])

                    self.buffer_length = len(self.buffer_string)
                    # self.buffer_string.append(["{}|END".format(len(message)), 'unsend'])
                    
                    # init the window
                    for i in range(self.window_size):
                        if len(self.buffer_string) != 0:
                            self.window.append(self.buffer_string.pop(0))
                    # Reset timer    
                    self.timer = time.time() + 0.5
                        
                    # start sending
                    while len(self.buffer_string) != 0 or len(self.window) > 0:
                        self.send_window()

                    self.socket.sendto("|END", ("", int(self.peer_port)))

                else:
                    print 'Please type in message starting with send'
        finally:
            print 'finally sending'
            self.socket.close()

    def dropper(self,determ_drop_count):
        if self.way_to_drop == DETERM_DROP:
            if determ_drop_count % self.drop_param:
                return True
            else:
                return False
        elif self.way_to_drop == PROBAB_DROP:
            rand = random.random()
            if rand < self.drop_param:
                return True
            else:
                return False
        else:
            print "Unknown Methods called"
            sys.exit()
            
    def listen(self):
        '''This function should be executed in a seperate thread for listening in coming message'''
        determ_drop_count = 0
        discarded_pkt = 0
        discarded_ack = 0
        total_pkt = 0
        total_ack = 0
        while True:
            # print 'start listening'
            # receive data from client (data, client address)
            try:
                # Refresh the recvfrom function every 0.01 second
                self.socket.settimeout(0.01)
                data, client_addr = self.socket.recvfrom(BUFFER_SIZE)
            except socket.timeout:
                data = None
            if not data:
                continue
            try:
                data = data.split('|')
                # receiver side
                if data[1] == 'END':
                    self.receiver_latest_sequence = -1
                    determ_drop_count = 0
                    ratio = float(discarded_pkt)/float(total_pkt)
                    print "[Summary] {}/{} packets discarded, loss rate = {}".format(discarded_pkt, total_pkt, ratio)
                    discarded_pkt = 0
                    total_pkt = 0
                    prompt()
                elif data[1] != '':
                    total_pkt += 1
                    # decide whether to drop or not
                    # drop deterministicly
                    determ_drop_count += 1
                    if self.dropper(determ_drop_count):
                        discarded_pkt += 1
                        print "[{}] packet{} {} discarded".format(time.time(), data[0], data[1])
                    else:
                        print "[{}] packet{} {} received".format(time.time(), data[0], data[1])
                    # print "receiver_latest: {}, received seq: {}".format(self.receiver_latest_sequence, data[0])
                    # if this is the right suquence that we're waiting for, we update our latest received sequence
                        if self.receiver_latest_sequence+1 == int(data[0]):
                            self.receiver_latest_sequence += 1
                        self.socket.sendto(str(self.receiver_latest_sequence)+'|', ("", int(self.peer_port)))
                    
                    # we don't print anything if we even lost the first packet, we also don't print END
                    if self.receiver_latest_sequence != -1 and data[1] != "END":
                        print "[{}] ACK{} sent, expecting packet {}".format(time.time(), self.receiver_latest_sequence, self.receiver_latest_sequence+1)
                    
                    # only reset the params when we're sure that we got all the packets
                    # if data[1] == "END" and self.receiver_latest_sequence == int(data[0]):
                        
                        # Print a summary
                # sender side
                else:
                    data[0] = int(data[0])
                    # update the packet status in the window
                    determ_drop_count += 1
                    total_ack += 1
                    if self.dropper(determ_drop_count):
                        discarded_ack += 1
                        print "[{}] ACK{} discarded".format(time.time(), data[0])
                    else:
                        # Print determine where we should move the window
                        num = int(self.window[0][0].split('|')[0])
                        if data[0] - num >= 0:
                            self.window[data[0] - num][1] = 'ack'
                            print "[{}] ACK{} received, window moves to {}".format(time.time(), data[0], data[0] + 1)
                            if data[0] == self.buffer_length - 1:
                                ack_lt_ratio = float(discarded_ack) / float(total_ack)
                                print "[Summary] {}/{} packets dropped, loss rate = {}".format(discarded_ack, total_ack, ack_lt_ratio)
                        # we break these two operations down to prevent sending packets multiple times since
                        # we resend packets right away after we move our window? (is this even right? LOL)s

            except ValueError as e:
                print "Value Error...{}".format(e)
                continue

def message_split(message):
    '''A function for parsing message'''
    message = message.split()
    action = message[0]
    string = ''.join(message[1:])
    return action, string

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

def prompt():
    '''A function that shows the correct cmd line interface'''
    sys.stdout.write('node> ')
    sys.stdout.flush()

def main():
    '''Main function executed by main'''
    parser = argparse.ArgumentParser(description='Go-Back-N Protocol')
    parser.add_argument('selfport', type=int)
    parser.add_argument('peerport', type=int)
    parser.add_argument('windowport', type=int)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-d', help='drop packets in a deterministic way(for every n packets)')
    group.add_argument('-p', help='drop packets with a probability of p', type=float)

    args = parser.parse_args()
    self_port = sys.argv[1]
    peer_port = sys.argv[2]
    window_size = sys.argv[3]
    way_to_drop = sys.argv[4]
    drop_param = float(sys.argv[5])

    # init node
    new_node = GBN(self_port, peer_port, window_size, way_to_drop, drop_param)

    try:
        t1 = threading.Thread(target=new_node.listen, name='listening mode')
        t2 = threading.Thread(target=new_node.send, name='sending mode')
        # daemon threads are killed automatically
        t1.daemon = True
        t2.daemon = True
        t1.start()
        t2.start()

        while t1.isAlive() and t2.isAlive():
            t1.join(1)
            t2.join(1)

    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
