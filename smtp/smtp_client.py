# smtp_client.py
import socket
import sys

HOST = "127.0.0.1"
PORT = 2525

def send_smtp_session(from_addr, to_addrs, data_lines):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))
    f = s.makefile("rw", newline="\r\n")
    def read_line():
        return f.readline().rstrip("\r\n")
    def send_line(line):
        f.write(line + "\r\n")
        f.flush()
    print(read_line())  # banner
    send_line("HELO example.com")
    print(read_line())
    send_line(f"MAIL FROM:<{from_addr}>")
    print(read_line())
    for r in to_addrs:
        send_line(f"RCPT TO:<{r}>")
        print(read_line())
    send_line("DATA")
    print(read_line())
    for l in data_lines:
        send_line(l)
    send_line(".")
    print(read_line())
    send_line("QUIT")
    print(read_line())
    f.close()
    s.close()

if __name__ == "__main__":
    # Example usage:
    from_addr = "alice@example.com"
    to_addrs = ["bob@example.com"]
    data_lines = [
        "Subject: Hello from simulated SMTP",
        "From: alice@example.com",
        "To: bob@example.com",
        "",
        "This is a test message stored in mailbox.json via simulated SMTP server.",
        "Best,",
        "Alice"
    ]
    send_smtp_session(from_addr, to_addrs, data_lines)
