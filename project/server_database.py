from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime


class ServerDB:
    Base = declarative_base()

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

    class Contacts(Base):
        __tablename__ = 'contacts'
        id = Column(Integer, primary_key=True)
        client = Column(Integer, ForeignKey('clients.id'))
        contact = Column(Integer, ForeignKey('clients.id'))

        def __init__(self, client, contact):
            self.client = client
            self.contact = contact

    class HistoryAction(Base):
        __tablename__ = 'history_action'
        id = Column(Integer, primary_key=True)
        client = Column(Integer, ForeignKey('clients.id'))
        sent = Column(Integer)
        received = Column(Integer)

        def __init__(self, client):
            self.client = client
            self.sent = 0
            self.received = 0

    def __init__(self, path):
        self.engine = create_engine(f'sqlite:///{path}', echo=False, pool_recycle=7200,
                                    connect_args={'check_same_thread': False})

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

            history_client = self.HistoryAction(connected_client.id)
            self.session.add(history_client)

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
        clients = self.session.query(self.Clients.login, self.Clients.last_connect).all()
        return [client[0] for client in clients]

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

    def add_contact(self, client_name, contact_name):
        client = self.session.query(self.Clients).filter_by(login=client_name).first()
        contact = self.session.query(self.Clients).filter_by(login=contact_name).first()
        if not self.session.query(self.Contacts).filter_by(client=client.id,
                                                           contact=contact.id).first():
            new_contact = self.Contacts(client.id, contact.id)
            self.session.add(new_contact)
            self.session.commit()

    def delete_contact(self, client_name, contact_name):
        client = self.session.query(self.Clients).filter_by(login=client_name).one()
        contact = self.session.query(self.Clients).filter_by(login=contact_name).one()

        if not contact:
            return

        self.session.query(self.Contacts).filter_by(client=client.id, contact=contact.id).delete()
        self.session.commit()

    def contacts_list(self, name):
        client = self.session.query(self.Clients).filter_by(login=name).first()
        contacts = self.session.query(self.Clients.login).\
            join(self.Contacts, self.Contacts.contact == self.Clients.id).\
            filter_by(client=client.id).all()

        return [contact[0] for contact in contacts]

    def modification_action_history(self, sender, receiver):
        sender = self.session.query(self.Clients).filter_by(login=sender).one()
        receiver = self.session.query(self.Clients).filter_by(login=receiver).one()

        self.session.query(self.HistoryAction).filter_by(client=sender.id).one().sent += 1
        self.session.query(self.HistoryAction).filter_by(client=receiver.id).one().received += 1

        self.session.commit()

    def message_history(self):
        query = self.session.query(
            self.Clients.login,
            self.Clients.last_connect,
            self.HistoryAction.sent,
            self.HistoryAction.received
        ).join(self.Clients)

        return query.all()


if __name__ == '__main__':
    db = ServerDB('server_base.db3')
    db.client_login('client_1', '127.0.0.1', 7777)
    db.client_login('client_2', '127.0.0.1', 7777)
    db.client_login('client_3', '127.0.0.1', 7777)
    print(db.clients_list())
    db.client_logout('client_2')
    print(db.active_clients_list())
    print(db.history_clients_list('client_1'))

    db.add_contact('client_1', 'client_2')
    db.add_contact('client_1', 'client_3')

    print(db.contacts_list('client_1'))
    db.modification_action_history('client_1', 'client_2')
    db.modification_action_history('client_1', 'client_3')
    db.modification_action_history('client_2', 'client_1')
