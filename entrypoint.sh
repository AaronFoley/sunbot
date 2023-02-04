#!/bin/bash

# Apply Database migrations
alembic upgrade head

exec "$@"
