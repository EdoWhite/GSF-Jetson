"""
AKA Sender
"""

import socket
import cv2
import sys
import argparse

def get_frames(rgb_path, depth_path):
    # Load RGB frame
    rgb_frame = cv2.imread(rgb_path, cv2.IMREAD_COLOR)  # Load as a color image
    if rgb_frame is None:
        raise ValueError(f"Failed to load RGB frame from {rgb_path}")

    # Load Depth frame
    depth_frame = cv2.imread(depth_path, cv2.IMREAD_UNCHANGED)  # Load without any color conversion
    if depth_frame is None:
        raise ValueError(f"Failed to load Depth frame from {depth_path}")

    # Encode the frames before sending
    ret, encoded_rgb_frame = cv2.imencode('.jpg', rgb_frame)
    if not ret:
        raise ValueError("Failed to encode RGB frame")

    ret, encoded_depth_frame = cv2.imencode('.jpg', depth_frame)
    if not ret:
        raise ValueError("Failed to encode Depth frame")

    return encoded_rgb_frame.tobytes(), encoded_depth_frame.tobytes()

def send_frames(host, port):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))

    while True:
        rgb_frame, depth_frame = get_frames("./INFERENCE/rgb/sample/0001_0/00001.jpg", "./INFERENCE/depth/sample/0001_0/00001.jpg")
        
        # Sending RGB Frame
        client_socket.sendall(b'RGB')
        client_socket.sendall(rgb_frame)

        # Sending Depth Frame
        client_socket.sendall(b'DEPTH')
        client_socket.sendall(depth_frame)

        if cv2.waitKey(1) & 0xFF == ord('0'):
            break

    # Sending the termination flag
    client_socket.sendall(b'STOP')

    # Receiving the inference result
    label = client_socket.recv(1024)
    print(f"Received label: {label.decode()}")

    client_socket.close()

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Send frames over a network.')
    parser.add_argument('--receiver_ip', type=str, required=True, help='Receiver host IP')
    parser.add_argument('--port', type=int, required=True, help='Port number for communication.')
    args = parser.parse_args()
    port = args.port
    ip = args.receiver_ip

    HOST, PORT = ip, port
    send_frames(HOST, PORT)
