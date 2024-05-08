# database.py
from flask_sqlalchemy import SQLAlchemy

# Confirgure database connection locally

SQLALCHEMY_DATABASE_URI = "mysql+mysqlconnector://root:password123@localhost:3306/FD2024".format(
    username="root",
    password="password123",
    hostname="localhost",
    databasename="FD2024",
)

# Confirgure database connection for pythonanywhere

# SQLALCHEMY_DATABASE_URI = "mysql+mysqlconnector://tjg14:TJGfd2024@tjg14.mysql.pythonanywhere-services.com:3306/tjg14$FD2024".format(
#     username="tjg14",
#     password="TJGfd2024",
#     hostname="tjg14.mysql.pythonanywhere-services.com",
#     databasename="tjg14$FD2024",
# )

db = SQLAlchemy()