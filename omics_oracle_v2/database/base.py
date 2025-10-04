"""
Base SQLAlchemy model and database configuration.
"""

from sqlalchemy.orm import declarative_base

# Create the declarative base for all models
Base = declarative_base()
