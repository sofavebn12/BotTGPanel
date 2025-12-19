"""
Entry point to run the Telegram bot.
Usage: python run_bot.py
"""
import os
import sys

# Ensure repo root is on sys.path
REPO_ROOT = os.path.abspath(os.path.dirname(__file__))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

print(f"[BOT] Python version: {sys.version}")
print(f"[BOT] Working directory: {os.getcwd()}")
print(f"[BOT] Script location: {__file__}")
print(f"[BOT] Repo root: {REPO_ROOT}")

from server.bot.run_bot import run_bot

if __name__ == "__main__":
    print("[BOT] Entry point: Starting bot...")
    run_bot()

