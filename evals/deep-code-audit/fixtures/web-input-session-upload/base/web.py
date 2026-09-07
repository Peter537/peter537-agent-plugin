from pathlib import Path


def search(connection, term):
    return connection.execute(
        "SELECT id, display_name, recovery_token FROM users WHERE display_name = '" + term + "'"
    ).fetchall()


def greeting(display_name):
    return "<html><body>Hello " + display_name + "</body></html>"


def session_headers(sid):
    return {"Set-Cookie": "session=" + sid + "; Path=/"}


def upload(filename, data):
    path = Path("uploads") / filename
    path.write_bytes(data)
    return str(path)
