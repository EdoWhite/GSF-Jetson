"""
AKA Receiver
Receives the frames, save them on the disk, run inference, notify sender by trasnmitting the label
"""

import socket
import os
import argparse
import cv2
import numpy as np
import time

def inference():
    # Implement the inference logic here
    # Placeholder return
    return 0

def save_frame(frame, folder):
    if not os.path.exists(folder):
        os.makedirs(folder)

    # Assuming frame is a numpy array
    filename = os.path.join(folder, f"frame_{int(time.time())}.jpg")
    cv2.imwrite(filename, frame)

def receive_and_assemble_frame(conn):
    # First, receive the length of the frame
    length = conn.recv(16)  # Assuming the length is sent in 16 bytes
    length = int(length.decode().strip())
    
    # Receive the actual frame
    frame_data = b''
    while len(frame_data) < length:
        packet = conn.recv(4096)
        if not packet: break
        frame_data += packet
    
    # Convert the bytes to a numpy array
    frame = np.frombuffer(frame_data, dtype=np.uint8)
    frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)  # Adjust the flag based on the frame type
    return frame

def receive_frames(host, port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(1)
    conn, addr = server_socket.accept()

    while True:
        data = conn.recv(1024)
        if not data:
            break

        if data == b'RGB':
            rgb_frame = conn.recv(1024)  # Adjust buffer size as needed
            save_frame(rgb_frame, 'rgb_frames')

        elif data == b'DEPTH':
            depth_frame = conn.recv(1024)  # Adjust buffer size as needed
            save_frame(depth_frame, 'depth_frames')

        elif data == b'STOP':
            label = inference()
            conn.sendall(str(label).encode())
            break

    conn.close()
    server_socket.close()

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Receive frames over a network.')
    parser.add_argument('--ports', nargs='+', type=int, required=True, help='List of port numbers for communication with cameras.')
    args = parser.parse_args()
    receiver_ports = args.ports

    HOST, PORT = "0.0.0.0", receiver_ports  # Bind to all interfaces
    receive_frames(HOST, PORT)
