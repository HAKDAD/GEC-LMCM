import MySQLdb
import sshtunnel

sshtunnel.SSH_TIMEOUT = 5.0
sshtunnel.TUNNEL_TIMEOUT = 5.0

with sshtunnel.SSHTunnelForwarder(
    ('127.0.0.1', 5000),  # Replace with the SSH server's address
    ssh_username='admin12122',
    ssh_password='2/fLDPtm$5H8rWC',
    remote_bind_address=('admin12122.mysql.pythonanywhere-services.com', 3306),
) as tunnel:
    connection = MySQLdb.connect(
        user='admin12122',
        passwd='vamsi123',
        host='127.0.0.1',
        port=tunnel.local_bind_port,
        db='admin12122$GEC',
    )
    
    # Now you can use the 'connection' object to interact with the MySQL database.

# Make sure to handle exceptions and close the connection when done.
