# Crypto Attribution Engine — Step 1: Ethereum TX Fetcher

A beginner-friendly Python script that fetches an Ethereum wallet's normal transaction history using the **Etherscan API V2**.

## Files

| File | Purpose |
|------|---------|
| `eth_txs.py` | Main script — accepts an address, fetches & prints transactions |
| `requirements.txt` | Python dependencies (`requests`, `python-dotenv`) |
| `.env.example` | Example environment variable template |
| `README.md` | This file |

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Get an Etherscan API key:**
   - Go to <https://etherscan.io/apis> and sign up for a free key.
   - Create a `.env` file in the project root:
     ```bash
     cp .env.example .env
     ```
   - Edit `.env` and replace `your_etherscan_api_key_here` with your key.

3. **Run the script:**
   ```bash
   python3 eth_txs.py 0xYourEthereumAddressHere
   ```

## How it works

- Accepts an Ethereum address as a command-line argument.
- Validates the address format (`0x` + 40 hex characters).
- Loads the API key from the `ETHERSCAN_API_KEY` environment variable (never hardcoded).
- Calls **Etherscan API V2** `account.txlist` endpoint with `chainid=1` for Ethereum Mainnet.
- Handles HTTP errors and Etherscan API errors gracefully.
- Prints each transaction: hash, sender, receiver, value (ETH), and timestamp.

## Notes

- The script fetches up to 10 transactions per page (default). Etherscan limits unauthenticated requests, but your API key raises the limit.
- Values are converted from wei to ETH (1 ETH = 10¹⁸ wei).
- If `to` field is empty, it's displayed as "Contract Creation".
- The `chainid=1` parameter restricts results to Ethereum Mainnet. Remove or change this parameter for other chains (testnet, polygon, etc.).