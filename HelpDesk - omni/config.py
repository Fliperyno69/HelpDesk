import os


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'supersecretkey')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///helpdesk.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ADMIN_KEY = 'GuvvZHZ_J5Q0D8sE2Nh8MQ'
