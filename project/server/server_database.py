from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Text
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
        pub_key = Column(Text)
        password_hash = Column(String)

        def __init__(self, login, password_hash):
            self.login = login
            self.last_connect = datetime.now()
            self.password_hash = password_hash
            self.pub_key = None

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

    def add_user(self, name, passwd_hash):
        user_row = self.Clients(name, passwd_hash)
        self.session.add(user_row)
        self.session.commit()
        history_row = self.HistoryAction(user_row.id)
        self.session.add(history_row)
        self.session.commit()

    def remove_user(self, name):
        client = self.session.query(self.Clients).filter_by(login=name).first()
        self.session.query(self.ActiveClients).filter_by(client=client.id).delete()
        self.session.query(self.HistoryAction).filter_by(client=client.id).delete()
        self.session.query(self.HistoryClients).filter_by(client=client.id).delete()
        self.session.query(self.Contacts).filter_by(contact=client.id).delete()
        self.session.query(self.Clients).filter_by(login=name).delete()
        self.session.commit()

    def get_hash(self, name):
        client = self.session.query(self.Clients).filter_by(login=name).first()
        return client.password_hash

    def get_pubkey(self, name):
        user = self.session.query(self.Clients).filter_by(login=name).first()
        return user.pub_key

    def check_user(self, name):
        if self.session.query(self.Clients).filter_by(login=name).count():
            return True
        else:
            return False

    def client_login(self, username, ip_address, port, key):
        new_connect = self.session.query(self.Clients).filter_by(login=username)

        if new_connect.count():
            connected_client = new_connect.first()
            connected_client.last_connect = datetime.now()
            if connected_client.pub_key != key:
                connected_client.pub_key = key
        else:
            raise ValueError('Пользователь не зарегистрирован.')

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
    db.add_user('client_1', "123")
    db.add_user('client_2', "123")
    db.add_user('client_3', "123")
    db.check_user('client_1')
    db.client_login('client_1', '127.0.0.1', 7777, "123")
    db.client_login('client_2', '127.0.0.1', 7777, "123")
    db.client_login('client_3', '127.0.0.1', 7777, "123")
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
