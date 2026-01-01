from dotenv import load_dotenv
import os

# Load .env from project root
load_dotenv()

# Secrets and configuration
SECRET_KEY = os.getenv("SECRET_KEY", "")  # Set in .env (required for JWT in production)
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", str(60 * 24)))

# Algorand / blockchain
ALGONODE_URL = os.getenv("ALGONODE_URL", "https://testnet-api.algonode.cloud")
ALGOD_TOKEN = os.getenv("ALGOD_TOKEN", "")
ALGORAND_ADDRESS = os.getenv("ALGORAND_ADDRESS", "")
ALGORAND_MNEMONIC = os.getenv("ALGORAND_MNEMONIC", "")

# External APIs
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

# Frontend (Vite)
# Note: Vite requires client-side env vars to be prefixed with VITE_
VITE_API_URL = os.getenv("VITE_API_URL", "http://localhost:8000")
