from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime


class ServerDB:
    Base = declarative_base()
    engine = create_engine('sqlite:///server_base.db3', echo=True)

    class Clients(Base):
        __tablename__ = 'clients'
        id = Column(Integer, primary_key=True)
        login = Column(String, unique=True)
        last_connect = Column(DateTime)

        def __init__(self, login):
            self.login = login
            self.last_connect = datetime.now()

    class ActiveClients(Base):
        __tablename__ = 'active_clients'
        id = Column(Integer, primary_key=True)
        client = Column(Integer, ForeignKey('clients.id'), unique=True)
        ip_address = Column(String)
        port = Column(Integer)
        time_connect = Column(DateTime)

        def __init__(self, client, ip_address, port):
            self.client = client
            self.ip_address = ip_address
            self.port = port
            self.time_connect = datetime.now()

    class HistoryClients(Base):
        __tablename__ = 'history_clients'
        id = Column(Integer, primary_key=True)
        client = Column(Integer, ForeignKey('clients.id'))
        ip_address = Column(String)
        port = Column(Integer)
        event = Column(String)
        event_time = Column(DateTime)

        def __init__(self, client, ip_address, port, event):
            self.client = client
            self.ip_address = ip_address
            self.port = port
            self.event = event
            self.event_time = datetime.now()

    def __init__(self):
        self.engine = create_engine('sqlite:///server_base.db3', echo=False, pool_recycle=7200)

        self.Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

        self.session.query(self.ActiveClients).delete()
        self.session.commit()

    def client_login(self, username, ip_address, port):
        new_connect = self.session.query(self.Clients).filter_by(login=username)

        if new_connect.count():
            connected_client = new_connect.first()
            connected_client.last_connect = datetime.now()
        else:
            connected_client = self.Clients(username)
            self.session.add(connected_client)
            self.session.commit()

        active_client = self.ActiveClients(connected_client.id, ip_address, port)
        self.session.add(active_client)

        history = self.HistoryClients(connected_client.id, ip_address, port, event='connect')
        self.session.add(history)

        self.session.commit()

    def client_logout(self, username):

        disconnected_client = self.session.query(self.Clients).filter_by(login=username).first()
        dc_active_client = self.session.query(self.ActiveClients).filter_by(client=disconnected_client.id).first()

        history = self.HistoryClients(disconnected_client.id,
                                      dc_active_client.ip_address,
                                      dc_active_client.port,
                                      event='disconnect')
        self.session.add(history)

        self.session.query(self.ActiveClients).filter_by(client=disconnected_client.id).delete()

        self.session.commit()

    def clients_list(self):
        query = self.session.query(self.Clients.login, self.Clients.last_connect)
        return query.all()

    def active_clients_list(self):
        query = self.session.query(
            self.Clients.login,
            self.ActiveClients.ip_address,
            self.ActiveClients.port,
            self.ActiveClients.time_connect
            ).join(self.Clients)
        return query.all()

    def history_clients_list(self, username=None):
        query = self.session.query(self.Clients.login,
                                   self.HistoryClients.event,
                                   self.HistoryClients.event_time,
                                   self.HistoryClients.ip_address,
                                   self.HistoryClients.port
                                   ).join(self.Clients)
        if username:
            query = query.filter(self.Clients.login == username)
        return query.all()


if __name__ == '__main__':
    db = ServerDB()
    print(db.clients_list())
    print(db.active_clients_list())
    print(db.history_clients_list('client_1'))
