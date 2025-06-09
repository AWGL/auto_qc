from django.core.management.base import BaseCommand
from django.core import serializers
import json

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('fixture', nargs='+', type=str)
        
    def handle(self, *args, **options):
        for fixture_file in options['fixture']:
            self.stdout.write(f'Loading {fixture_file}...')
            
            # Read the fixture
            with open(fixture_file, 'r') as f:
                objects = json.load(f)
            
            # Process each object separately
            for obj in objects:
                model = obj['model']
                try:
                    # Deserialize and save a single object
                    instance = list(serializers.deserialize('json', json.dumps([obj])))[0]
                    instance.save()
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'  Failed to load {model} object: {str(e)}'))
                    # Continue with next object
                    continue