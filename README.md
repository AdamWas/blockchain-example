# Blockchain Certificate System

A REST API for issuing and verifying educational certificates using a custom blockchain and IPFS.

Built with **FastAPI**, **SQLAlchemy** (SQLite), and a from-scratch Python blockchain.

---

## Project Structure

```
app/
  main.py              # FastAPI entry point, logging config, global error handler
  config.py            # Centralised settings
  database.py          # SQLAlchemy engine & session

  models/
    certificate.py     # SQLAlchemy Certificate model

  schemas/
    certificate.py     # Pydantic request/response schemas
    verification.py
    blockchain.py

  services/
    certificate_service.py   # Issuance orchestration (hash, IPFS, chain, DB)
    blockchain_service.py    # Lazy blockchain singleton & helpers
    ipfs_service.py          # IPFS upload wrapper (graceful fallback)
    verification_service.py  # Verification with block-integrity checks

  blockchain/
    block.py           # Block data structure & SHA-256 hashing
    blockchain.py      # Chain management, mining, validation, thread-safe I/O

  api/
    health.py          # GET /health (includes DB & chain diagnostics)
    certificates.py    # POST /certificates, GET /certificates/{id}
    verification.py    # POST /certificates/verify/file, POST /certificates/verify/id
    blockchain.py      # GET /blockchain, GET /blockchain/validate

  utils/
    hashing.py         # Shared SHA-256 helper
```

---

## Prerequisites

- **Python 3.11+**
- **IPFS daemon** (optional — the app works without it; uploads are skipped gracefully)

---

## Getting Started

### 1. Create a virtual environment and install dependencies

```bash
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Start the IPFS daemon (optional)

```bash
ipfs daemon
```

If IPFS is not running, certificates will still be issued but the `ipfs_cid` field will be `null`.

### 3. Run the FastAPI server

```bash
uvicorn app.main:app --reload
```

The server starts at **http://127.0.0.1:8000**.

### 4. Explore the API

Open **http://127.0.0.1:8000/docs** for the interactive Swagger UI.

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Liveness probe |
| `POST` | `/certificates` | Issue a new certificate (multipart/form-data) |
| `GET` | `/certificates/{certificate_id}` | Retrieve certificate metadata |
| `POST` | `/certificates/verify/file` | Verify by uploading the original file |
| `POST` | `/certificates/verify/id` | Verify by certificate UUID |
| `GET` | `/blockchain` | View the full blockchain |
| `GET` | `/blockchain/validate` | Validate blockchain integrity |

---

## How It Works

1. An institution **issues** a certificate by uploading a PDF with student details.
2. The file is **hashed** (SHA-256) and optionally **uploaded to IPFS**.
3. A **blockchain transaction** is created and a new block is mined.
4. Certificate metadata is **persisted in SQLite**.
5. Anyone can **verify** a certificate by re-uploading the file or using its UUID — the system checks the database, confirms the transaction exists on the blockchain, and verifies the containing block's integrity.

---

## Configuration

Environment variables (all optional — sensible defaults are provided):

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///certificates.db` | SQLAlchemy connection string |
| `BLOCKCHAIN_FILE` | `blockchain.json` | Path to the chain's JSON file |
| `IPFS_API_URL` | `/ip4/127.0.0.1/tcp/5001` | IPFS HTTP API multiaddr |
| `MINING_DIFFICULTY` | `2` | Number of leading zeros required for proof-of-work |
