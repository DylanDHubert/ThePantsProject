# your_app/management/commands/rtree.py
from django.core.management.base import BaseCommand
from django.db import connections  # Import connections to handle multiple databases

class Command(BaseCommand):
    help = 'Create R-Tree index for mens_pants table in data.sqlite3'

    def handle(self, *args, **kwargs):
        # Use the 'data' database connection for data.sqlite3
        with connections['data'].cursor() as cursor:
            # Step 1: Create the R-Tree table if it doesn't exist
            cursor.execute('''
                CREATE VIRTUAL TABLE IF NOT EXISTS mens_pants_rtree
                USING rtree(id, x_min, x_max, y_min, y_max);
            ''')
            self.stdout.write(self.style.SUCCESS('R-Tree table created in data.sqlite3.'))

            # Step 2: Populate the R-Tree index with data from mens_pants
            cursor.execute('''
                INSERT OR IGNORE INTO mens_pants_rtree (id, x_min, x_max, y_min, y_max)
                SELECT rowid, x, x, y, y FROM mens_pants;
            ''')
            self.stdout.write(self.style.SUCCESS('R-Tree index populated in data.sqlite3.'))
