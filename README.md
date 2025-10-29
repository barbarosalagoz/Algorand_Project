# 🎟️ Event Ticketing dApp on Algorand (Python Full-Stack)

> **A decentralized event ticketing platform** powered by **Algorand**, written in **Python**, and visualized with a **React/Vite** frontend.  
> A full-stack experiment turned debugging odyssey — where blockchain logic was easy, but Python itself became the final boss.

---

## 🧩 The Vision

The goal of this project was simple yet ambitious:  
to create a **trustless event ticketing system** on Algorand where **each ticket is a unique NFT (ASA)**, minted and distributed directly from a **smart contract** — no middlemen, no double-spends, no fraud.

The architecture combines:
- 🧠 **Smart Contracts** in Python 3.12 using `algopy` and `puyapy`
- ⚙️ **Deployment Engine** via `algokit` with a custom `__main__.py` runner
- 💻 **Frontend** in React + Vite + TypeScript connected to **Pera Wallet**

Everything worked perfectly… until Windows decided otherwise.

---

## 🧱 System Design (Simplified)

| Layer | Technology |
|-------|-------------|
| **Blockchain** | Algorand (LocalNet) |
| **Smart Contracts** | Python 3.12 • algopy • puyapy |
| **Build / Deploy** | algokit + custom runner |
| **Package Manager** | poetry |
| **Frontend** | React + Vite + TypeScript |
| **Wallet Integration** | @txnlab/use-wallet • @perawallet/connect |
| **Containerization** | Docker (LocalNet node) |

---

## ⚙️ Core Components

### 🧠 Smart Contract

Defined in  
`/projects/EventTicketing-contracts/smart_contracts/event_ticketing/contract.py`

**Global State**
- `event_name` – string title  
- `ticket_price` – UInt64 (microAlgos)  
- `total_tickets` – UInt64 supply  
- `tickets_sold` – UInt64 counter  
- `ticket_asa_id` – UInt64 ASA ID  

**Functions**
1. **`create_application`** – initializes immutable event data.  
2. **`mint_tickets`** – creator-only call that mints the NFT ticket ASA.  
3. **`buy_ticket`** – atomic group logic validating payment & transferring 1 NFT to buyer.

### 🧰 Deployment Workflow

Custom `__main__.py` handles:
- Compilation → `algokit compile py`  
- Client generation → `event_ticketing_client.py`  
- Deployment → calls `deploy_config.py`, funds contract (0.2 ALGO), mints tickets, logs state  

---

## 🧭 The Developer Journey – *A Single Saga of Triumphs & Terrors*

From the outside, this looked like an ordinary blockchain project.  
Under the hood, it became an operating-system exorcism.

### 🧱 Stage 1: Logical Integrity – The Proxy Ghost

**Error:**  
`use of storage proxy before definition`

**Cause:**  
`algopy` requires both type hints and proxy instantiation.  
Without an `__init__` initializing each `GlobalState` variable, Algopy panics.

**Fix:**  
Added explicit proxy definitions:
```python
def __init__(self):
    self.event_name = GlobalState(String)
    self.ticket_price = GlobalState(UInt64)
    self.total_tickets = GlobalState(UInt64)
    self.tickets_sold = GlobalState(UInt64)
    self.ticket_asa_id = GlobalState(UInt64)
