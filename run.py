from server.app_factory import create_app


app = create_app()


if __name__ == "__main__":
    # Local dev run (Flask built-in server)
    # Flask runs on port 5000, Nginx proxies from port 80
    app.run(host="0.0.0.0", port=5000, debug=True)


