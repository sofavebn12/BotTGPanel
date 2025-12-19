from server.app_factory import create_app


app = create_app()


if __name__ == "__main__":
    # Local dev run (Flask built-in server)
    # Use port 8000 for development (doesn't require root)
    app.run(host="0.0.0.0", port=80, debug=True)


