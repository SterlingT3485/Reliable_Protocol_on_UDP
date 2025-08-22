# Sender & Receiver (Python 3.10.12)

This project provides a **sender** and **receiver** implementation for reliable file transfer, with optional support for a **network emulator** that simulates delay and packet loss.  

---

## Usage

### With `network_emulator`

1. **Start the network emulator** (on `host1`):

   ```bash
   python network_emulator.py <port1> <host2> <port4> <port3> <host3> <port2> <delay_value> <packet_discard_probability> <verbose_mode>
   ```

   - `<port1>`: Emulator's receiving UDP port (forward direction, from sender)  
   - `<host2>`: Receiver's network address  
   - `<port4>`: Receiver's receiving UDP port  
   - `<port3>`: Emulator's receiving UDP port (backward direction, from receiver)  
   - `<host3>`: Sender's network address  
   - `<port2>`: Sender's receiving UDP port  
   - `<delay_value>`: Maximum delay of the link (milliseconds)  
   - `<packet_discard_probability>`: Probability of packet loss (0–1)  
   - `<verbose_mode>`: `1` for verbose logging, `0` otherwise  

   ⚠️ Make sure that all ports are available.

---

2. **Start the receiver** (on `host2`):

   ```bash
   python receiver.py <host1> <port3> <port4> <output_file>
   ```

   - `<host1>`: Hostname of the network emulator  
   - `<port3>`: UDP port (ACKs from receiver to emulator)  
   - `<port4>`: UDP port (data from emulator to receiver)  
   - `<output_file>`: File to write the received data  

---

3. **Start the sender** (on `host3`):

   ```bash
   python sender.py <host1> <port1> <port2> <timeout_value> <input_file>
   ```

   - `<host1>`: Hostname of the network emulator  
   - `<port1>`: UDP port (emulator receives data from sender)  
   - `<port2>`: UDP port (sender receives ACKs from emulator)  
   - `<timeout_value>`: Timeout interval (milliseconds)  
   - `<input_file>`: File to be transferred  

---

### Without `network_emulator`

1. **Start the receiver** (on `host1`):

   ```bash
   python receiver.py <host2> <port1> <port2> <output_file>
   ```

   - `<host2>`: Hostname of the sender  
   - `<port1>`: Listening port of sender  
   - `<port2>`: Listening port of receiver  
   - `<output_file>`: File to write the received data  

---

2. **Start the sender** (on `host2`):

   ```bash
   python sender.py <host1> <port2> <port1> <timeout_value> <input_file>
   ```

   - `<host1>`: Hostname of the receiver  
   - `<port2>`: Listening port of receiver  
   - `<port1>`: Listening port of sender  
   - `<timeout_value>`: Timeout interval (milliseconds)  
   - `<input_file>`: File to be transferred  

---

## Notes

- All programs require **Python 3.10.12**.  
- Ensure that all specified ports are available before starting.  
- Use the `network_emulator` if you want to test the sender/receiver under packet loss and delay conditions.  
