"""Database access layer.

All Postgres reads and writes go through repository functions in this package.
Agent nodes never call SQLAlchemy directly. Queries are parameterized; raw SQL
outside this package is a review-blocking violation.
"""
