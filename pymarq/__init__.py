import socket
import struct


class ViewMarq:
    # Color Constants
    GREEN = "<GRN>"
    RED = "<RED>"
    AMBER = "<AMB>"

    def __init__(self, ip, port=502):
        self.ip = ip
        self.port = port
        self.display_id = 1
        self.line_height = 8  # 0, 8, 16...

    def _send_command(self, ascii_cmd):
        """Internal: Wraps ASCII in Modbus TCP and sends it."""
        if not ascii_cmd.endswith('\r'):
            ascii_cmd += '\r'
        data = bytearray(ascii_cmd.encode('ascii'))
        # Pad if odd length
        if len(data) % 2 != 0:
            data.append(0x00)
        # Byte Swap
        for i in range(0, len(data), 2):
            data[i], data[i+1] = data[i+1], data[i]
        # Build Header
        header = struct.pack('>HHHBBHHB',
                             1, 0, 7 + len(data), 255,
                             16, 10999, len(data) // 2, len(data))
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(2)
                s.connect((self.ip, self.port))
                s.sendall(header + data)
                s.recv(1024)
        except Exception as e:
            print(f"[ViewMarq Error] {e}")

    def write(self, content, color="<GRN>"):
        """
        Smart write function.
        Accepts:
          - A simple string: "Hello"
          - A multi-line string: "Line 1\\nLine 2"
          - A list of strings: ["Line 1", "Line 2"]
        """
        # 1. Standardize input into a list of lines
        if isinstance(content, list):
            lines = content
        else:
            # splitlines() handles \n, \r, and \r\n automatically
            lines = str(content).splitlines()
        # 2. Build the command string
        cmd = f"<ID {self.display_id}><CLR>{color}"

        for i, line in enumerate(lines):
            y_pos = i * self.line_height
            # <POS X Y> - X is always 0 (left), Y increments by 8
            cmd += f"<POS 0 {y_pos}><T>{line}</T>"

        # 3. Send
        self._send_command(cmd)
