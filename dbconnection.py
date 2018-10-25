from flask_mysqldb import MySQL

def connection():
	conn = MySQL.connect(host= 'localhost', username= 'root', password= '', db= 'flaskapp')

	c = conn.cursor(dictionary=True)

	return c, conn