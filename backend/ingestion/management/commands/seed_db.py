from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from ingestion.models import Client

class Command(BaseCommand):
    help = 'Seeds the database with a default superuser and a demo client.'

    def handle(self, *args, **options):
        self.stdout.write('Seeding database...')
        
        # 1. Create Superuser / Analyst
        username = 'admin'
        email = 'admin@breatheesg.com'
        password = 'admin'
        
        if not User.objects.filter(username=username).exists():
            User.objects.create_superuser(username=username, email=email, password=password)
            self.stdout.write(self.style.SUCCESS(f"Superuser '{username}' successfully created with password '{password}'."))
        else:
            self.stdout.write(f"Superuser '{username}' already exists. Skipping.")

        # 2. Create Demo Client
        client_name = 'Acme Corporation'
        client_slug = 'acme'
        
        client, created = Client.objects.get_or_create(
            slug=client_slug,
            defaults={'name': client_name}
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f"Demo client '{client_name}' successfully created."))
        else:
            self.stdout.write(f"Demo client '{client_name}' already exists. Skipping.")
            
        self.stdout.write(self.style.SUCCESS('Database seeding completed successfully.'))
