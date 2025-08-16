#testing for the checker files
from typing import Any
from django.core.management.base import BaseCommand, CommandParser
from django.contrib.auth import get_user_model
from datetime import date, timedelta
import secrets, string, random
from django.contrib.auth.models import AbstractUser