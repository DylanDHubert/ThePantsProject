import csv
from django.core.management.base import BaseCommand
from server.models import FileCoordinate

class Command(BaseCommand):
    help = 'Import CSV data into the FileCoordinate model'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to the CSV file')

    def handle(self, *args, **kwargs):
        csv_file = kwargs['csv_file']
        with open(csv_file, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                # Create a new record in the 'data' database
                FileCoordinate.objects.using('data').create(
                    filename=row['filename'],
                    x=float(row['x']),  # Ensure x is treated as float
                    y=float(row['y'])   # Ensure y is treated as float
                )
        self.stdout.write(self.style.SUCCESS('Successfully imported data into file_coordinate'))