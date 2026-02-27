# RELAY — P2P File Transfer

A browser-based peer-to-peer file transfer app. **Files travel directly between browsers** — your server only handles the WebRTC handshake (signaling), never the file data.

## How It Works

```
Browser A ──(offer/answer/ICE)──► Python Server ──► Browser B
Browser A ◄────────── WebRTC DataChannel ─────────► Browser B
                        (direct P2P, file data)
```

1. **Sender** opens the app and clicks "Generate Room Code"
2. **Receiver** opens the app on any device and enters the code
3. A WebRTC connection is established (browser ↔ browser)
4. Sender drops files → they transfer directly to Receiver
5. Receiver clicks **↓ Save** to download each file

## Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the server
```bash
python server.py
```

The app is now available at **http://localhost:8000**

### 3. Share access
- **Same machine / LAN**: Open two browser tabs or share your local IP (`http://192.168.x.x:8000`) with devices on the same network.
- **Over the internet**: Put the server behind a reverse proxy (nginx, Caddy) with HTTPS, or deploy to a host like Railway, Render, or Fly.io.

> **Note:** For internet transfers across different networks, WebRTC may need a TURN server if direct P2P fails due to strict NAT/firewalls. See [Metered.ca](https://www.metered.ca/tools/openrelay/) for a free TURN server you can add to `ICE_CONFIG` in `index.html`.

## Project Structure

```
p2p-fileshare/
├── server.py          # FastAPI signaling server (WebSockets)
├── requirements.txt
└── static/
    └── index.html     # Full frontend (WebRTC + UI)
```

## Technical Notes

- **Signaling**: FastAPI WebSocket server relays WebRTC `offer`, `answer`, and `ICE candidates` between peers
- **Transfer**: WebRTC `RTCDataChannel` with 16 KB chunks + back-pressure control
- **Max file size**: Limited only by browser memory (works great up to several GB with chunking)
- **Security**: All WebRTC connections are DTLS-encrypted by default
