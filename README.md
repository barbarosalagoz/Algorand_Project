# 🎟️ Event Ticketing dApp on Algorand (Python Full-Stack)

> **A decentralized event ticketing system** built on **Algorand**, powered by **Python smart contracts**, and visualized through a **React/Vite** front-end.  
> Currently in **development / on hold** due to a severe Windows-based Python environment anomaly.

---

## 🧠 Overview

This project is a **full-stack dApp** for **creating and selling event tickets as Algorand Standard Assets (ASAs)** — functioning effectively as **NFT-based tickets**.

The backend smart contract (written in Python 3.12 using `algopy` and `puyapy`) defines the core business logic of ticket creation, minting, and sales.  
The frontend (React + Vite + TypeScript) connects to Pera Wallet on LocalNet and interacts with the deployed contract in real time.

---

## ⚙️ Project Status

**Status:** `Development / On Hold`  
**Reason:** A persistent, low-level environment hijack on Windows that disrupts Python dependency resolution inside the project’s virtual environment.

Even though:
- All 77 dependencies were correctly installed inside `.venv`
- `poetry install` confirmed full environment integrity
- The `site-packages` directory physically contained all required packages

…the project’s **active interpreter (`.venv\Scripts\python.exe`)** fails to import any module — behaving as if it were referencing a *ghost* Python 3.13 installation from the Microsoft Store.

Result:  
`ModuleNotFoundError` on every import — even for core dependencies like `dotenv`, `algokit_utils`, and `algosdk`.

---

## 💡 Architecture

### 🔩 Smart Contract (Backend – `/projects/EventTicketing-contracts/smart_contracts/event_ticketing/contract.py`)

#### **Initialization (`__init__` + `create_application`)**
The contract defines immutable global states:

| Key | Type | Description |
|------|------|-------------|
| `event_name` | `String` | The event’s title |
| `ticket_price` | `UInt64` | Price per ticket (in microAlgos) |
| `total_tickets` | `UInt64` | Total number of tickets to be minted |
| `tickets_sold` | `UInt64` | Live counter (starts at 0) |
| `ticket_asa_id` | `UInt64` | The ASA ID of the NFT tickets |

The contract sets these values immutably and assigns the creator as the global administrator.

#### **Minting Tickets (`mint_tickets`)**
- Callable **only** by the creator (`Global.creator_address`)  
- Mints all `total_tickets` as an ASA (NFT collection)
- All ASA management addresses (`manager`, `reserve`, `freeze`, `clawback`) are set to the contract itself  
- The newly created `asset_id` is written into `ticket_asa_id`

#### **Buying Tickets (`buy_ticket`)**
- Executed within an **atomic transaction group**
- Validates:
  - Not sold out (`tickets_sold < total_tickets`)
  - Sale started (`ticket_asa_id != 0`)
  - Payment amount == `ticket_price`
  - Payment → contract address
- On success:
  - Sends 1 ticket (NFT) to the buyer via an inner `AssetTransfer`
  - Increments `tickets_sold`

---

### 🧰 Deployment Logic

#### `__main__.py`
A **custom build-deploy runner**, replacing the default `algokit project deploy`.  
It automates:

1. **Build**
   - `algokit compile py` → compile `contract.py`
   - Generate typed client → `event_ticketing_client.py`
   - Add `__init__.py` files to make importable packages

2. **Deploy**
   - Load `deploy_config.py`
   - Create Algorand LocalNet client
   - Convert dispenser account → `AccountTransactionSigner`
   - Inject signer into `EventTicketingClient`
   - Execute deployment + mint + funding + verification

#### `deploy_config.py`
- Calls `create_application` with event params  
- Funds the new app with 0.2 ALGO (0.1 min balance + 0.1 ASA creation fee)  
- Calls `mint_tickets`  
- Logs final global state

---

### 🎨 Frontend (React + Vite + TypeScript)

- Integrates `@txnlab/use-wallet` and `@perawallet/connect`  
- Connects to LocalNet and fetches Global State  
- Displays event details in a clean UI:
  - Event name  
  - Ticket price  
  - Total tickets / Sold / Remaining  
  - ASA ID  

---

## 🧱 Technology Stack

| Layer | Technology |
|-------|-------------|
| **Blockchain** | Algorand (LocalNet) |
| **Framework** | AlgoKit |
| **Smart Contracts** | Python 3.12 + algopy + puyapy |
| **Package Manager** | poetry |
| **Frontend** | React + Vite + TypeScript |
| **Wallet Integration** | Pera Wallet via @txnlab/use-wallet |
| **Containerization** | Docker (LocalNet node) |

---

## 🧩 Installation & Setup

### 1️⃣ Prerequisites
