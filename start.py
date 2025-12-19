"""
Запускает Flask веб-сервер, Telegram бота и Nginx одновременно.
Usage: python start.py
"""
import os
import sys
import threading
import signal
import subprocess
import time

# Ensure repo root is on sys.path
REPO_ROOT = os.path.abspath(os.path.dirname(__file__))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

print("[START] Starting BotTGPanel...")
print(f"[START] Repo root: {REPO_ROOT}")

# Global process reference
nginx_process = None


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    global nginx_process
    print("\n[START] Stopping services...")
    if nginx_process:
        print("[NGINX] Stopping Nginx...")
        nginx_process.terminate()
        try:
            nginx_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            nginx_process.kill()
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


def run_nginx():
    """Run Nginx as subprocess"""
    global nginx_process
    try:
        print("[NGINX] Starting Nginx...")
        nginx_conf = os.path.join(REPO_ROOT, "nginx", "nginx.conf")
        
        if not os.path.exists(nginx_conf):
            print(f"[NGINX] [WARNING] Config not found: {nginx_conf}")
            print("[NGINX] [WARNING] Nginx will not start. Install and configure Nginx manually.")
            return
        
        # Start Nginx with custom config
        nginx_process = subprocess.Popen(
            ["nginx", "-c", nginx_conf, "-g", "daemon off;"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        print("[NGINX] Nginx started successfully on port 80")
        
        # Monitor Nginx process
        nginx_process.wait()
        
    except FileNotFoundError:
        print("[NGINX] [ERROR] Nginx not installed. Install with: sudo apt-get install nginx")
    except PermissionError:
        print("[NGINX] [ERROR] Permission denied. Nginx on port 80 requires sudo.")
        print("[NGINX] [INFO] Run with: sudo python start.py")
    except Exception as e:
        print(f"[NGINX] [ERROR] {e}")


def main():
    # Register signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    print("[START] ✅ Starting all services...")
    print("[START] Nginx: http://0.0.0.0:80")
    print("[START] Flask web server: http://0.0.0.0:5000 (proxied via Nginx on port 80)")
    print("[START] Telegram bot: Running")
    print("[START] Press Ctrl+C to stop all services")
    print("-" * 60)
    
    # Start Nginx in separate thread
    nginx_thread = threading.Thread(target=run_nginx, daemon=True)
    nginx_thread.start()
    
    # Give Nginx time to start
    time.sleep(1)
    
    # Start Flask web server in thread
    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()
    
    # Start Telegram bot in thread
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    try:
        # Keep main thread alive
        nginx_thread.join()
        web_thread.join()
        bot_thread.join()
    except KeyboardInterrupt:
        signal_handler(None, None)


if __name__ == "__main__":
    main()
