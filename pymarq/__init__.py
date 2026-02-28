import socket
import struct
import time


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
        """
        Internal: Wraps ASCII in Modbus TCP and sends it.
        Automatically fragments messages larger than Modbus limits.
        """
        # 1. Prepare the full ASCII payload
        if not ascii_cmd.endswith('\r'):
            ascii_cmd += '\r'
            
        data = bytearray(ascii_cmd.encode('ascii', 'ignore'))
        
        # 2. Pad to even length (Modbus registers are 16-bit)
        if len(data) % 2 != 0:
            data.append(0x00)
            
        # 3. Perform Byte Swapping (Little Endian to Big Endian for Modbus)
        for i in range(0, len(data), 2):
            data[i], data[i+1] = data[i+1], data[i]

        # 4. Fragment and Send
        # Modbus "Write Multiple Registers" (FC16) is limited to ~250 bytes per packet.
        # We use a safe chunk size of 200 bytes (100 registers).
        CHUNK_SIZE = 200
        BASE_ADDR = 10999 # 411000 offset
        
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(2)
                s.connect((self.ip, self.port))
                
                # Loop through the data in chunks
                for i in range(0, len(data), CHUNK_SIZE):
                    chunk = data[i : i + CHUNK_SIZE]
                    
                    # Calculate the memory address offset for this chunk
                    # (Each register holds 2 bytes, so we divide index by 2)
                    current_addr = BASE_ADDR + (i // 2)
                    
                    # Build Modbus Header
                    # TransID(1), Proto(0), Len(6+bytes), Unit(255), FC(16), Addr, RegQty, ByteCount
                    header = struct.pack('>HHHBBHHB',
                                         1, 0, 7 + len(chunk), 255,
                                         16, current_addr, len(chunk) // 2, len(chunk))
                                         
                    s.sendall(header + chunk)
                    
                    # Receive response (transaction ID, protocol, len, unit, fc, addr, qty)
                    s.recv(1024)
                    
        except Exception as e:
            print(f"[ViewMarq Error] {e}")
        finally:
            time.sleep(0.01)

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

    def write_lines(self, lines):
        """
        Writes a list of lines to the display.
        Each item in the list corresponds to a physical line (row).
        
        Items can be:
          - str: "Hello" (Defaults to static, green)
          - tuple: ("Text", Scroll_Bool, Direction, Speed, Color)
            e.g. ("News Alert", True, "left", "fast", ViewMarq.RED)
        """
        cmd = f"<ID {self.display_id}><CLR>"
        
        # Maps for human-readable strings to ASCII commands
        speed_map = {"slow": "S", "medium": "M", "fast": "F"}
        dir_map = {"left": "SL", "right": "SR", "up": "SU", "down": "SD"}

        for i, line_data in enumerate(lines):
            # 1. Set Defaults
            text = ""
            scroll = False
            direction = "left"
            speed = "medium"
            color = "<GRN>"

            # 2. Parse Input (Handle String vs Tuple)
            if isinstance(line_data, str):
                text = line_data
            elif isinstance(line_data, (tuple, list)):
                # Safely unpack tuple indices
                text = line_data[0]
                if len(line_data) > 1: scroll = line_data[1]
                if len(line_data) > 2 and line_data[2]: direction = line_data[2]
                if len(line_data) > 3 and line_data[3]: speed = line_data[3]
                if len(line_data) > 4 and line_data[4]: color = line_data[4]

            # 3. Calculate Geometry (Auto-layout based on line index)
            # Line 0 = Y 0-7, Line 1 = Y 8-15, etc.
            y_start = i * self.line_height
            y_end = y_start + (self.line_height - 1)
            
            # 4. Build Command
            # Define Window -> Set Mode (Scroll vs Static) -> Set Color -> Set Text
            cmd += f"<WIN 0 {y_start} 287 {y_end}>"
            
            if scroll:
                d_cmd = dir_map.get(str(direction).lower(), "SL")
                s_cmd = speed_map.get(str(speed).lower(), "M")
                cmd += f"<{d_cmd}><S {s_cmd}>"
            else:
                cmd += "<LJ>" # Static Left Justify
                
            cmd += f"{color}<T>{text}</T>"

        self._send_command(cmd)

    def scroll(self, content, direction="left", speed="medium", color="<GRN>", pause=0, justify="center"):
        """
        Scrolls text across the display. Supports \n for multi-line scrolling.
        
        :param content: The string to display (supports \n) or a list of strings.
        :param direction: 'left', 'right', 'up', 'down'
        :param speed: 'slow', 'medium', 'fast'
        :param color: Text color (e.g., ViewMarq.GREEN)
        :param pause: Pause time in seconds (0 for continuous scrolling without pausing)
        :param justify: Justification during pause. 
                        Horizontal: 'left', 'center', 'right'
                        Vertical: 'top', 'bottom'
        """
        # 1. Map Speed
        speed_map = {"slow": "S", "medium": "M", "fast": "F"}
        s_cmd = f"<S {speed_map.get(speed.lower(), 'M')}>"
        
        # 2. Map Direction
        dir_map = {"left": "SL", "right": "SR", "up": "SU", "down": "SD"}
        d_cmd = dir_map.get(direction.lower(), "SL")
        
        # 3. Build the scrolling effect command (with or without pause)
        if pause > 0:
            just_map = {
                "left": "LJ", "center": "CJ", "right": "RJ",
                "top": "TOP", "bottom": "BOT"
            }
            j_cmd = just_map.get(justify.lower())
            
            # Enforce valid justification for the chosen direction
            if d_cmd in ["SU", "SD"] and j_cmd not in ["TOP", "BOT"]:
                j_cmd = "TOP"
            elif d_cmd in ["SL", "SR"] and j_cmd not in ["LJ", "CJ", "RJ"]:
                j_cmd = "CJ"
                
            effect_cmd = f"<{d_cmd} {j_cmd} {int(pause)}>"
        else:
            effect_cmd = f"<{d_cmd}>"
            
        # 4. Start constructing the command
        cmd = f"<ID {self.display_id}><CLR>{s_cmd}{effect_cmd}{color}"
        
        # 5. Standardize input into a list of lines (handles the \n)
        if isinstance(content, list):
            lines = content
        else:
            lines = str(content).splitlines()
            
        # 6. Append each line with its specific Y position
        for i, line in enumerate(lines):
            if line: # Skip empty lines (like the one before your \n) but still advance the Y position
                y_pos = i * self.line_height
                cmd += f"<POS 0 {y_pos}><T>{line}</T>"
                
        # 7. Send the command
        self._send_command(cmd)

    def clear(self):
        """Clear the display."""
        self._send_command(f"<ID {self.display_id}><CLR>")

    def draw_rect(self, x, y, width, height, color="<GRN>"):
        color_map = {"<GRN>": 0, "<RED>": 1, "<AMB>": 2,
                     "GREEN": 0, "RED": 1, "AMBER": 2,
                     "GRN": 0, "AMB": 2}
        
        color_n = color_map.get(color.strip("<>").upper(), 0)

        cmd = f"<ID {self.display_id}><MTN {color_n} {x} {y} {width} {height}>"

        self._send_command(cmd)

    def put_pixel(self, x, y, color="<GRN>"):
        """Draw a single pixel."""
        cmd = f"<ID {self.display_id}><WIN {x} {y} {x} {y}><POS {x} {y}><CS 2>{color}<T>W</T>"
        self._send_command(cmd)
