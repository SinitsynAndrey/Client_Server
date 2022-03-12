from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime


class ClientDB:
    Base = declarative_base()

    class KnownUsers(Base):
        __tablename__ = 'known_users'
        id = Column(Integer, primary_key=True)
        username = Column(String, unique=True)

        def __init__(self, username):
            self.username = username

    class Contacts(Base):
        __tablename__ = 'contacts'
        id = Column(Integer, primary_key=True)
        name = Column(String, unique=True)

        def __init__(self, name):
            self.name = name

    class HistoryMessages(Base):
        __tablename__ = 'history_messages'
        id = Column(Integer, primary_key=True)
        contact = Column(String)
        status = Column(String)
        message = Column(String)
        message_time = Column(DateTime)

        def __init__(self, contact, status, message):
            self.contact = contact
            self.status = status
            self.message = message
            self.message_time = datetime.now()

    def __init__(self, name):
        self.engine = create_engine(f'sqlite:///client_{name}_base.db3', echo=False, pool_recycle=7200,
                                    connect_args={'check_same_thread': False})

        self.Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

        self.session.query(self.Contacts).delete()
        self.session.commit()

    def add_contact(self, name):
        if not self.session.query(self.Contacts).filter_by(name=name).first():
            new_contact = self.Contacts(name)
            self.session.add(new_contact)
            self.session.commit()

    def del_contact(self, name):
        if self.session.query(self.Contacts).filter_by(name=name).first():
            self.session.query(self.Contacts).filter_by(name=name).delete()
            self.session.commit()

    def save_message(self, contact, status, message):
        message_row = self.HistoryMessages(contact, status, message)
        self.session.add(message_row)
        self.session.commit()

    def get_contacts(self):
        return [contact[0] for contact in self.session.query(self.Contacts.name).all()]

    def add_users(self, users_list):
        self.session.query(self.KnownUsers).delete()
        for user in users_list:
            user_row = self.KnownUsers(user)
            self.session.add(user_row)
        self.session.commit()

    def get_users(self):
        return [user[0] for user in self.session.query(self.KnownUsers.username).all()]

    def check_user(self, user):
        if self.session.query(self.KnownUsers).filter_by(username=user).count():
            return True
        else:
            return False

    def check_contact(self, contact):
        if self.session.query(self.Contacts).filter_by(name=contact).count():
            return True
        else:
            return False

    def get_history(self, contact):
        query = self.session.query(self.HistoryMessages).filter_by(contact=contact).all()
        return [(history_row.contact, history_row.status, history_row.message, history_row.message_time)
                for history_row in query]


if __name__ == '__main__':
    db = ClientDB('i')
    db.add_contact('mike')
    db.get_contacts()

