from django.core.management.base import BaseCommand
from core.pesapal import PesaPal

class Command(BaseCommand):
    help = 'Register IPN URL with PesaPal'

    def handle(self, *args, **options):
        pesapal = PesaPal()
        ipn_id = pesapal.register_ipn_url()
        
        if ipn_id:
            self.stdout.write(self.style.SUCCESS(f'Successfully registered IPN with ID: {ipn_id}'))
            # Store this IPN ID in your settings or database
        else:
            self.stdout.write(self.style.ERROR('Failed to register IPN URL'))