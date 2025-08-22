#!/usr/bin/env python3

import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import time
import threading
import argparse
import socket

from packet import Packet

class Sender:
    def __init__(self, ne_host, ne_port, port, timeout, send_file, seqnum_file, ack_file, n_file, send_sock, recv_sock):

        self.ne_host = ne_host
        self.ne_port = ne_port
        self.port = port
        self.timeout = timeout / 1000 # needs to be in seconds

        self.send_file = send_file # file object holding the file to be sent
        self.seqnum_file = seqnum_file # seqnum.log
        self.ack_file = ack_file # ack.log
        self.n_file = n_file # N.log

        self.send_sock = send_sock
        self.recv_sock = recv_sock

        # internal state
        self.lock = threading.RLock() # prevent multiple threads from accessing the data simultaneously
        self.window = [] # To keep track of the packets in the window
        self.window_size = 1 # Current window size 
        self.timer = None # Threading.Timer object that calls the on_timeout function
        self.timer_packet = None # The packet that is currently being timed
        self.current_time = 0 # Current 'timestamp' for logging purposes
        self.EOT = 0

    def run(self):
        self.recv_sock.bind(('', self.port))
        self.perform_handshake()

        # write initial N to log
        self.n_file.write('t={} {}\n'.format(self.current_time, self.window_size))
        self.current_time += 1

        recv_ack_thread = threading.Thread(target=sender.recv_ack)
        send_data_thread = threading.Thread(target=sender.send_data)
        recv_ack_thread.start()
        send_data_thread.start()
        
        recv_ack_thread.join()
        send_data_thread.join()
        exit()

    def perform_handshake(self):
        "Performs the connection establishment (stage 1) with the receiver"
        syn_pac = Packet(3, 0, 0, "")
        while (1):
            self.send_sock.sendto(syn_pac.encode(), (self.ne_host, self.ne_port))
            self.seqnum_file.write("t=-1 SYN\n")
            self.recv_sock.settimeout(3)
            try: 
                ack_raw, _ = self.recv_sock.recvfrom(1024)
                ack = Packet(ack_raw).decode()
                if (ack[0] == 3 and ack[1] == 0):
                    print("received SYN ack, start transmission")
                    self.ack_file.write('t={} {}\n'.format("-1", "SYN"))
                    break
            except socket.timeout:
                continue   
        # set the timeout value to none
        self.recv_sock.settimeout(None) 

    def transmit_and_log(self, packet):
        """
        Logs the seqnum and transmits the packet through send_sock.
        """
        pac_deco = packet.decode()
        self.send_sock.sendto(packet.encode(), (self.ne_host, self.ne_port))
        if (pac_deco[0] == 1):
            #print(f"t={self.current_time} {pac_deco[1]}\n")
            self.seqnum_file.write('t={} {}\n'.format(self.current_time, pac_deco[1]))
        if (pac_deco[0] == 2):
            #print(f"t={self.current_time} EOT\n")
            self.seqnum_file.write('t={} {}\n'.format(self.current_time, "EOT"))
        self.current_time+=1


    def recv_ack(self):
        """
        Thread responsible for accepting acknowledgements and EOT sent from the network emulator.
        """
        while (1):
            ack_pac = Packet(self.recv_sock.recvfrom(1024)[0]).decode()
            self.lock.acquire()
            # if receiver ack he received our EOT packet
            if (ack_pac[0] == 2):
                print("received EOT ack, terminating")
                self.ack_file.write('t={} {}\n'.format(self.current_time, "EOT"))
                self.EOT = 1
                break
            else:
                print(f"received ack packet {ack_pac[1]}")
                self.ack_file.write('t={} {}\n'.format(self.current_time, ack_pac[1]))
                # check if this is a new ack
                new = False
                index = 0
                print(self.window)
                for pac in self.window:
                    # remove all the packet before the newly acked from the window
                    index+=1
                    if (pac.decode()[1] == ack_pac[1]):
                        self.window = self.window[index:]
                        new = True
                        print(f"remove packets before {pac.decode()[1]} from window")
                        # increase the N if possible
                        if (self.window_size < 10):
                            self.window_size+=1
                            self.n_file.write('t={} {}\n'.format(self.current_time, self.window_size))
                        # stop the timer if all the packets in window are resolved
                        if (len(self.window) == 0):
                            print(f"remove timer on packet {pac.decode()[1]}")
                            self.timer.cancel()
                            self.timer = None
                        # restart a new timer for the oldest packet in window otherwise
                        elif (len(self.window) != 0):
                            self.timer.cancel()
                            print(f"restart timer on packet {self.window[0].decode()[1]}")
                            self.timer = threading.Timer(self.timeout, self.on_timeout)
                            self.timer.start()
                            self.timer_packet = self.window[0]
                        break
                    
            self.current_time+=1
            self.lock.release()

    def send_data(self):
        """ 
        Thread responsible for sending data and EOT to the network emulator.
        """
        seq_num = 0
        # make this block into a packet
        length_for_test = 500 
        block = self.send_file.read(length_for_test)
        while block:
            # if window is not full
            if (len(self.window) < self.window_size):
                self.lock.acquire()
                cur_pac = Packet(1, seq_num, len(block), block)
                self.transmit_and_log(cur_pac)
                # add the transmitted packet into the window
                print(f"add {seq_num} packet into window")
                self.window.append(cur_pac)
                # restart timer if there is no running timer
                if (self.timer == None):
                    print(f"new timer start for packet {seq_num}")
                    self.timer = threading.Timer(self.timeout, self.on_timeout)
                    self.timer.start()
                    self.timer_packet = cur_pac
                seq_num += 1
                seq_num = seq_num % 32
                block = self.send_file.read(length_for_test)
            # if window is full, wait 3 seconds and try again later   
                self.lock.release()
            else:
                time.sleep(0.03)

        # Wait for all data to be ack
        while (len(self.window) != 0):
            time.sleep(1)

        # finish all data, send EOT until we receive EOT ack
        while (self.EOT == 0):
            eot_pac = Packet(2, seq_num, 0, "")
            self.transmit_and_log(eot_pac)
            time.sleep(1)

    def on_timeout(self):
        """
        Deals with the timeout condition
        """
        self.lock.acquire()
        print("Timeout happened!!!")
        self.window_size = 1
        self.n_file.write('t={} {}\n'.format(self.current_time, self.window_size))
        print(f"retransmit packet {self.timer_packet.decode()[1]}")

        self.transmit_and_log(self.timer_packet)

        self.timer.cancel()
        print(f"reset timer on packet {self.window[0].decode()[1]} for retransmition")
        self.timer = threading.Timer(self.timeout, self.on_timeout)
        self.timer.start()
        self.current_time += 1
        self.lock.release()

if __name__ == '__main__':
    # Parse args
    parser = argparse.ArgumentParser()
    parser.add_argument("ne_host", type=str, help="Host address of the network emulator")
    parser.add_argument("ne_port", type=int, help="UDP port number for the network emulator to receive data")
    parser.add_argument("port", type=int, help="UDP port for receiving ACKs from the network emulator")
    parser.add_argument("timeout", type=float, help="Sender timeout in milliseconds")
    parser.add_argument("filename", type=str, help="Name of file to transfer")
    args = parser.parse_args()
   
    with open(args.filename, 'r') as send_file, open('seqnum.log', 'w') as seqnum_file, \
            open('ack.log', 'w') as ack_file, open('N.log', 'w') as n_file, \
            socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as send_sock, \
            socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as recv_sock:
        sender = Sender(args.ne_host, args.ne_port, args.port, args.timeout, 
            send_file, seqnum_file, ack_file, n_file, send_sock, recv_sock)
        sender.run()
