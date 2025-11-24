import threading
import socket
import datetime
import json
import os
import sys
from flask import Flask, jsonify, request, send_from_directory, abort
from werkzeug.middleware.proxy_fix import ProxyFix


MAILBOX_FILE = "mailbox.json"
MAILBOX_LOCK = threading.Lock()
SMTP_HOST = "0.0.0.0"
SMTP_PORT = 2525
HTTP_HOST = "0.0.0.0"
HTTP_PORT = 8000
STATIC_DIR = "static"
# -----------------------------------

# Ensure mailbox exists
def ensure_mailbox():
    if not os.path.exists(MAILBOX_FILE):
        with open(MAILBOX_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, indent=2)

def load_mailbox():
    with MAILBOX_LOCK:
        with open(MAILBOX_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except Exception:
                return []

def save_mailbox(messages):
    with MAILBOX_LOCK:
        with open(MAILBOX_FILE, "w", encoding="utf-8") as f:
            json.dump(messages, f, indent=2, ensure_ascii=False)

def append_message(msg):
    msgs = load_mailbox()
    msgs.append(msg)
    save_mailbox(msgs)
    return msg

# ---------- SMTP server logic ----------
def handle_smtp_client(conn, addr):
    conn_file = conn.makefile("rw", newline="\r\n")
    def send_line(line):
        try:
            conn_file.write(line + "\r\n")
            conn_file.flush()
        except Exception:
            pass

    try:
        send_line("220 smtp-simulated.local Service ready")
        helo = None
        mail_from = None
        rcpt_to = []
        data_lines = []
        in_data = False

        while True:
            line = conn_file.readline()
            if not line:
                break
            line = line.rstrip("\r\n")
            # If currently reading DATA section
            if in_data:
                if line == ".":
                    # create message record
                    timestamp = datetime.datetime.utcnow().isoformat() + "Z"
                    subject = None
                    # find Subject: line (case-insensitive)
                    for l in data_lines:
                        if l.lower().startswith("subject:"):
                            subject = l.split(":",1)[1].strip()
                            break
                    body = "\n".join(data_lines)
                    msg = {
                        "id": int(datetime.datetime.utcnow().timestamp() * 1000),
                        "received_at": timestamp,
                        "helo": helo,
                        "from": mail_from,
                        "to": rcpt_to,
                        "subject": subject or "",
                        "body": body
                    }
                    append_message(msg)
                    send_line("250 OK queued as {}".format(msg["id"]))
                    # reset for next message in same session
                    mail_from = None
                    rcpt_to = []
                    data_lines = []
                    in_data = False
                    continue
                else:
                    data_lines.append(line)
                    continue

            if not line:
                continue

            parts = line.split(" ", 1)
            cmd = parts[0].upper()
            arg = parts[1] if len(parts) > 1 else ""

            if cmd in ("HELO", "EHLO"):
                helo = arg
                send_line("250 Hello {}".format(arg or ""))
            elif cmd == "MAIL":
                # expect: MAIL FROM:<address>
                if arg.upper().startswith("FROM:"):
                    mail_from = arg[5:].strip().lstrip("<").rstrip(">")
                    send_line("250 Sender OK")
                else:
                    send_line("501 Syntax: MAIL FROM:<address>")
            elif cmd == "RCPT":
                # expect: RCPT TO:<address>
                if arg.upper().startswith("TO:"):
                    recipient = arg[3:].strip().lstrip("<").rstrip(">")
                    rcpt_to.append(recipient)
                    send_line("250 Recipient OK")
                else:
                    send_line("501 Syntax: RCPT TO:<address>")
            elif cmd == "DATA":
                if not mail_from or not rcpt_to:
                    send_line("503 Need MAIL FROM and RCPT TO before DATA")
                else:
                    send_line("354 End data with <CR><LF>.<CR><LF>")
                    in_data = True
            elif cmd == "NOOP":
                send_line("250 OK")
            elif cmd == "RSET":
                mail_from = None
                rcpt_to = []
                data_lines = []
                in_data = False
                send_line("250 OK")
            elif cmd == "QUIT":
                send_line("221 Bye")
                break
            else:
                send_line("502 Command not implemented")
    except Exception as e:
        try:
            conn.sendall(f"451 Server error: {e}\r\n".encode())
        except Exception:
            pass
    finally:
        try:
            conn_file.close()
        except Exception:
            pass
        try:
            conn.close()
        except Exception:
            pass

def start_smtp_server(stop_event):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((SMTP_HOST, SMTP_PORT))
    sock.listen(8)
    print(f"[SMTP] Simulated SMTP server listening on {SMTP_HOST}:{SMTP_PORT}")
    try:
        while not stop_event.is_set():
            try:
                sock.settimeout(1.0)
                conn, addr = sock.accept()
            except socket.timeout:
                continue
            t = threading.Thread(target=handle_smtp_client, args=(conn, addr), daemon=True)
            t.start()
    except Exception as e:
        print("[SMTP] Server stopped:", e)
    finally:
        sock.close()

# ---------- Flask app (HTTP) ----------
ensure_mailbox()
app = Flask(__name__, static_folder=STATIC_DIR, static_url_path="/static")
app.wsgi_app = ProxyFix(app.wsgi_app)

@app.route("/")
def index():
    return send_from_directory(STATIC_DIR, "index.html")

@app.route("/api/messages", methods=["GET"])
def api_messages():
    msgs = load_mailbox()
    msgs_sorted = sorted(msgs, key=lambda m: m.get("received_at", ""), reverse=True)
    return jsonify(msgs_sorted)

@app.route("/api/messages/<int:msg_id>", methods=["GET"])
def api_message(msg_id):
    msgs = load_mailbox()
    for m in msgs:
        if m.get("id") == msg_id:
            return jsonify(m)
    abort(404)

@app.route("/api/send", methods=["POST"])
def api_send():
    data = request.json or {}
    mail_from = (data.get("from") or "").strip()
    to = data.get("to", "")
    subject = data.get("subject", "") or ""
    body = data.get("body", "") or ""
    if not mail_from or not to:
        return jsonify({"error": "'from' and 'to' required"}), 400
    if isinstance(to, str):
        recipients = [r.strip() for r in to.split(",") if r.strip()]
    elif isinstance(to, (list, tuple)):
        recipients = list(to)
    else:
        recipients = []
    timestamp = datetime.datetime.utcnow().isoformat() + "Z"
    msg = {
        "id": int(datetime.datetime.utcnow().timestamp() * 1000),
        "received_at": timestamp,
        "helo": "HTTP-SUBMIT",
        "from": mail_from,
        "to": recipients,
        "subject": subject,
        "body": body
    }
    append_message(msg)
    return jsonify({"ok": True, "id": msg["id"]})

@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory(STATIC_DIR, filename)

def start_http():
    print(f"[HTTP] Flask app serving on http://{HTTP_HOST}:{HTTP_PORT}")
    app.run(host=HTTP_HOST, port=HTTP_PORT, threaded=True)

# ---------- Run both servers ----------
if __name__ == "__main__":
    stop_event = threading.Event()
    smtp_thread = threading.Thread(target=start_smtp_server, args=(stop_event,), daemon=True)
    smtp_thread.start()
    try:
        start_http()
    except KeyboardInterrupt:
        print("Shutting down...")
        stop_event.set()
        sys.exit(0)
