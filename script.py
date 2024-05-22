import os
import time

session_folder = '/FD24mySQL/flask_session'  # The folder where the session files are stored
session_lifetime = 9000

for filename in os.listdir(session_folder):
    file_path = os.path.join(session_folder, filename)
    if os.path.getmtime(file_path) < time.time() - session_lifetime:
        os.remove(file_path)