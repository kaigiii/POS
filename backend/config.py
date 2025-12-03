
import os
import secrets

class Config:
	# Prefer DATABASE_URL (Postgres on Render) but fall back to local sqlite for dev
	SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///pos.db'
	SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_urlsafe(32)
	SQLALCHEMY_TRACK_MODIFICATIONS = False
