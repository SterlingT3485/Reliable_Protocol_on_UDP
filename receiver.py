import os
import sys
import argparse
import socket
import math

from packet import Packet

# Writes the received content to file
def append_to_file(filename, data):
    file = open(filename, 'a')
    file.write(data)
    file.close()

def append_to_log(type, seq_num):
    """
    Appends the packet information to the log file
    """
    if (type == 2):
        append_to_file('arrival.log', "EOT\n")
    elif (type == 3):
        append_to_file('arrival.log', "SYN\n")
    else:
        append_to_file('arrival.log', str(seq_num) + "\n")
    
    

def send_ack(type, seq_num): #Args to be added
    """
    Sends ACKs, EOTs, and SYN to the network emulator. and logs the seqnum.
    """
    ack_pac = Packet(type, seq_num, 0, "")
    socket.socket(socket.AF_INET, socket.SOCK_DGRAM).sendto(ack_pac.encode(), (args.ne_addr, int(args.ne_port)))
    
if __name__ == '__main__':
    # Parse args
    parser = argparse.ArgumentParser(description="Congestion Controlled GBN Receiver")
    parser.add_argument("ne_addr", metavar="<NE hostname>", help="network emulator's network address")
    parser.add_argument("ne_port", metavar="<NE port number>", help="network emulator's UDP port number")
    parser.add_argument("recv_port", metavar="<Receiver port number>", help="network emulator's network address")
    parser.add_argument("dest_filename", metavar="<Destination Filename>", help="Filename to store received data")
    args = parser.parse_args()

    # Clear the output and log files
    open(args.dest_filename, 'w').close()
    open('arrival.log', 'w').close()

    expected_seq_num = 0 # Current Expected sequence number
    seq_size = 32 # Max sequence number
    max_window_size = 10 # Max number of packets to buffer
    recv_buffer = {}  # Buffer to store the received data

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind(('', int(args.recv_port)))  # Socket to receive data

        while True:
            # Receive packets, log the seqnum, and send response
            cur_data = Packet(s.recvfrom(1024)[0]).decode()
            print(f"received {cur_data[0]} packet with seq number {cur_data[1]} when expecting {expected_seq_num}")
            append_to_log(cur_data[0], cur_data[1])
            # if it is SYN
            if (cur_data[0] == 3):
                # send SYN back to sender
                print("send SYN ack to sender")
                send_ack(3, 0)
            # if not a SYN
            else:
                # if seq time is expected
                if (cur_data[1] == expected_seq_num):
                    # if it is an EOT
                    if (cur_data[0] == 2):
                        # send an EOT back
                        print(f"send EOT ack to sender")
                        send_ack(2,0)
                        break
                    # if it is data
                    if (cur_data[0] == 1):
                        append_to_file(args.dest_filename, cur_data[3])
                        print(f"put seq number {cur_data[1]} to output")

                        # keep checking if the packet with next sequence number is in the recv buffer and keep removing 
                        while (expected_seq_num + 1) % 32 in recv_buffer:
                            pac = recv_buffer.pop((expected_seq_num + 1) % 32)  # Remove and get the packet
                            append_to_file(args.dest_filename, pac[3])
                            print(f"drop seq number {pac[1]} to output")
                            expected_seq_num = (expected_seq_num + 1) % 32

                        # there are no more continuous packet in the recv_buffer
                        # send ack with seq number as the last written to disk packet
                        print(f"send ack packet {expected_seq_num}")
                        send_ack(0, expected_seq_num)
                        # update the expected seq number to be the next one looking forward
                        expected_seq_num = (expected_seq_num + 1) % 32
                
                # if seq time is not expected
                else:
                    # if seq number is within next 10 seq number
                    if ((cur_data[1] - expected_seq_num) % 32 <= 10):
                        # store it in buffer if it is not already in
                        if cur_data not in recv_buffer:
                            recv_buffer[cur_data[1]] = cur_data
                    # send ack with seq number as the requested
                    print(f"(unexpected) send ack packet {(expected_seq_num-1)%32}")
                    send_ack(0, (expected_seq_num-1)%32)
                    

                        


            
