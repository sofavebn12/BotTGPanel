from server.app_factory import create_app


app = create_app()


if __name__ == "__main__":
    # Local dev run (Flask built-in server)
    # Bind to all interfaces, but use an internal port (2052); Nginx listens on 80 and proxies to this port
    app.run(host="0.0.0.0", port=80, debug=True)


