from http.server import HTTPServer, BaseHTTPRequestHandler
from http.cookies import SimpleCookie
from urllib.parse import urlparse
from email.parser import BytesParser
from io import BytesIO
import psycopg2
import bs4
import secrets
import ssl

conn = None
try:
    conn = psycopg2.connect("dbname=postgres user=postgres")
except (Exception, psycopg2.DatabaseError) as error:
    print(error)

sessions = {}

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        if "Cookie" in self.headers:
            cookie = self.headers["Cookie"]
            cookie_components = dict(cc.split("=", 1) for cc in cookie.splitlines())
            token = cookie_components["token"]
            user = self.find_session(token)
            if user:
                self.end_headers()
                self.login_success(user)
                return
        self.end_headers()
        with open("index.html", "rb") as index:
            self.wfile.write(index.read())

    def do_POST(self):
        self.send_response(200)
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length).decode()
        try:
            query_components = dict(qc.split("=", 1) for qc in body.splitlines())
            logout = query_components.get("logout", "False")
            if logout == "True":
                if "Cookie" in self.headers:
                    cookie = self.headers["Cookie"]
                    cookie_components = dict(cc.split("=", 1) for cc in cookie.splitlines())
                    token = cookie_components["token"]
                    sessions.pop(token)
                    cookie = SimpleCookie()
                    cookie["token"] = ""
                    cookie["token"]['path'] = "/"
                    cookie["token"]['expires'] = "Thu, 01 Jan 1970 00:00:00 GMT"
                    self.send_header("Set-Cookie", cookie.output(header='', sep=''))
                    self.end_headers()
            username = query_components.get("username", None)
            password = query_components.get("password", None)
            user = self.find_user(username, password)
            if user:
                cookie = SimpleCookie()
                while True:
                    token = secrets.token_urlsafe()
                    if token not in sessions:
                        cookie["token"] = token
                        sessions[token] = username
                        break
                self.send_header("Set-Cookie", cookie.output(header='', sep=''))
                self.end_headers()
                self.login_success(user)
                return
        except ValueError:
            pass
        self.end_headers()
        with open("index.html", "rb") as index:
            self.wfile.write(index.read())
    
    def login_success(self, username):
        with open("loggedin.html", "rb") as successpage:
            soup = bs4.BeautifulSoup(successpage, features="html.parser")
            soup.find(id='loginMessage').string.replace_with("Logged in as %s" % username)
            self.wfile.write(str(soup).encode('utf-8'))

    def find_user(self, username, password):
        if username and password:
            cur = conn.cursor()
            cur.execute("SELECT username FROM users WHERE username='%s' AND password='%s'" % (username, password))
            user = cur.fetchone()
            cur.close()
            return user

    def find_session(self, token):
        if token in sessions:
            return sessions[token]
        else:
            return None

httpd = HTTPServer(('192.168.43.239', 8000), SimpleHTTPRequestHandler)
httpd.serve_forever()

import atexit
@atexit.register
def goodbye():
    if conn is not None:
        conn.close()