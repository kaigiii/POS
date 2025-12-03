
import os
import secrets

class Config:
	SQLALCHEMY_DATABASE_URI = 'sqlite:///pos.db'
	SECRET_KEY = secrets.token_urlsafe(32)
	SQLALCHEMY_TRACK_MODIFICATIONS = False
