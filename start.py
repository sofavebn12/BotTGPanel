"""
Запускает Flask веб-сервер и Telegram бота одновременно.
Usage: python start.py
"""
import os
import sys
import threading
import signal

# Ensure repo root is on sys.path
REPO_ROOT = os.path.abspath(os.path.dirname(__file__))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

print("[START] Starting BotTGPanel...")
print(f"[START] Repo root: {REPO_ROOT}")


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\n[START] Stopping services...")
    print("[START] All services stopped")
    sys.exit(0)


def run_web_server():
    """Run Flask web server in thread"""
    try:
        print("[WEB] Starting Flask server...")
        from server.app_factory import create_app
        app = create_app()
        app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
    except Exception as e:
        print(f"[WEB] [ERROR] {e}")


def run_bot():
    """Run Telegram bot in thread"""
    try:
        print("[BOT] Starting Telegram bot...")
        from server.bot.run_bot import run_bot
        run_bot()
    except Exception as e:
        print(f"[BOT] [ERROR] {e}")


def main():
    # Register signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    print("[START] ✅ Starting both services...")
    print("[START] Flask web server: http://0.0.0.0:5000 (proxied via Nginx on port 80)")
    print("[START] Telegram bot: Running")
    print("[START] Press Ctrl+C to stop all services")
    print("-" * 60)
    
    # Start Flask web server in thread
    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()
    
    # Start Telegram bot in thread
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    try:
        # Keep main thread alive
        web_thread.join()
        bot_thread.join()
    except KeyboardInterrupt:
        signal_handler(None, None)


if __name__ == "__main__":
    main()
