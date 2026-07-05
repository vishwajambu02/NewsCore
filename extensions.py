import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask_sqlalchemy import SQLAlchemy
from flask_caching import Cache

db = SQLAlchemy()
cache = Cache()

import os
import sys
...
from extensions import db, cache # <--- BUT THEN TRIES TO IMPORT THEM FROM A SEPARATE FILE LATER!