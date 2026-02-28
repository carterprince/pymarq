import socket
import struct
import time
import re

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
        
        # Regex to identify ViewMarq tags vs actual text content
        # Matches: <RED>, <GRN>, <AMB>, <BL N/S/M/F>, <CS 0-99>
        self._tag_pattern = re.compile(r'(<(?:GRN|RED|AMB|BL [NSMF]|CS \d+)>)', re.IGNORECASE)

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
        CHUNK_SIZE = 200
        BASE_ADDR = 10999 # 411000 offset
        
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(2)
                s.connect((self.ip, self.port))
                
                for i in range(0, len(data), CHUNK_SIZE):
                    chunk = data[i : i + CHUNK_SIZE]
                    current_addr = BASE_ADDR + (i // 2)
                    
                    # TransID(1), Proto(0), Len(6+bytes), Unit(255), FC(16), Addr, RegQty, ByteCount
                    header = struct.pack('>HHHBBHHB',
                                         1, 0, 7 + len(chunk), 255,
                                         16, current_addr, len(chunk) // 2, len(chunk))
                                         
                    s.sendall(header + chunk)
                    s.recv(1024) # Receive response
                    
        except Exception as e:
            print(f"[ViewMarq Error] {e}")
        finally:
            time.sleep(0.01)

    def _parse_rich(self, text):
        """
        Parses a string, identifying ViewMarq tags and wrapping raw text in <T> tags.
        Input:  "<RED>Hello <GRN>World"
        Output: "<RED><T>Hello </T><GRN><T>World</T>"
        """
        result = ""
        parts = self._tag_pattern.split(str(text))
        
        for part in parts:
            if not part:
                continue
            
            # If it matches a known tag, append it raw (uppercased)
            if self._tag_pattern.match(part):
                result += part.upper()
            # Otherwise, it's text content, wrap in <T>
            else:
                result += f"<T>{part}</T>"
        return result

    def write(self, content, color="<GRN>"):
        """
        Writes text to the display. Supports inline tags (e.g. <RED>).
        Accepts string, multi-line string, or list of strings.
        """
        if isinstance(content, list):
            lines = content
        else:
            lines = str(content).splitlines()

        cmd = f"<ID {self.display_id}><CLR>{color}"

        for i, line in enumerate(lines):
            y_pos = i * self.line_height
            # Parse line for tags before adding to command
            parsed_line = self._parse_rich(line)
            cmd += f"<POS 0 {y_pos}>{parsed_line}"

        self._send_command(cmd)

    def write_lines(self, lines):
        """
        Writes specific lines with specific settings.
        Text supports inline tags.
        """
        cmd = f"<ID {self.display_id}><CLR>"
        
        speed_map = {"slow": "S", "medium": "M", "fast": "F"}
        dir_map = {"left": "SL", "right": "SR", "up": "SU", "down": "SD"}

        for i, line_data in enumerate(lines):
            # Defaults
            text = ""
            scroll = False
            direction = "left"
            speed = "medium"
            color = "<GRN>"

            # Parse Input
            if isinstance(line_data, str):
                text = line_data
            elif isinstance(line_data, (tuple, list)):
                text = line_data[0]
                if len(line_data) > 1: scroll = line_data[1]
                if len(line_data) > 2 and line_data[2]: direction = line_data[2]
                if len(line_data) > 3 and line_data[3]: speed = line_data[3]
                if len(line_data) > 4 and line_data[4]: color = line_data[4]

            y_start = i * self.line_height
            y_end = y_start + (self.line_height - 1)
            
            cmd += f"<WIN 0 {y_start} 287 {y_end}>"
            
            if scroll:
                d_cmd = dir_map.get(str(direction).lower(), "SL")
                s_cmd = speed_map.get(str(speed).lower(), "M")
                cmd += f"<{d_cmd}><S {s_cmd}>"
            else:
                cmd += "<LJ>" 
            
            # Parse text for tags
            parsed_text = self._parse_rich(text)
            cmd += f"{color}{parsed_text}"

        self._send_command(cmd)

    def scroll(self, content, direction="left", speed="medium", color="<GRN>", pause=0, justify="center"):
        """
        Scrolls text across the display. Supports inline tags (e.g. <RED>).
        """
        speed_map = {"slow": "S", "medium": "M", "fast": "F"}
        s_cmd = f"<S {speed_map.get(speed.lower(), 'M')}>"
        
        dir_map = {"left": "SL", "right": "SR", "up": "SU", "down": "SD"}
        d_cmd = dir_map.get(direction.lower(), "SL")
        
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
            
        cmd = f"<ID {self.display_id}><CLR>{s_cmd}{effect_cmd}{color}"
        
        if isinstance(content, list):
            lines = content
        else:
            lines = str(content).splitlines()
            
        for i, line in enumerate(lines):
            if line:
                y_pos = i * self.line_height
                parsed_line = self._parse_rich(line)
                cmd += f"<POS 0 {y_pos}>{parsed_line}"
                
        self._send_command(cmd)

    def clear(self):
        """Clear the display."""
        self._send_command(f"<ID {self.display_id}><CLR>")

    def draw_rect(self, x, y, width, height, color="<GRN>"):
        """Draws a rectangle outline."""
        color_map = {"<GRN>": 0, "<RED>": 1, "<AMB>": 2,
                     "GREEN": 0, "RED": 1, "AMBER": 2,
                     "GRN": 0, "AMB": 2}
        
        color_n = color_map.get(color.strip("<>").upper(), 0)
        cmd = f"<ID {self.display_id}><MTN {color_n} {x} {y} {width} {height}>"
        self._send_command(cmd)

    def put_pixel(self, x, y, color="<GRN>"):
        """Draws a single pixel."""
        cmd = f"<ID {self.display_id}><WIN {x} {y} {x} {y}><POS {x} {y}><CS 2>{color}<T>W</T>"
        self._send_command(cmd)
