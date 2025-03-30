from django.core.management.base import BaseCommand
from core.models import CoursePrice, CourseTier, Currency

class Command(BaseCommand):
    help = 'Populate missing course prices in the database'

    def handle(self, *args, **kwargs):
        # Prices for the courses, including TZS
        prices = {
            'basic': {'USD': 10, 'KES': 490, 'EUR': 10, 'TZS': 10000},
            'standard': {'USD': 50, 'KES': 2450, 'EUR': 50, 'TZS': 50000},
            'premium': {'USD': 100, 'KES': 4900, 'EUR': 100, 'TZS': 100000},
        }

        # Retrieve course tiers and currencies from the database
        tiers = {tier.name: tier for tier in CourseTier.objects.all()}
        currencies = {currency.code: currency for currency in Currency.objects.all()}

        # Delete existing prices to avoid duplication
        CoursePrice.objects.all().delete()
        self.stdout.write(self.style.SUCCESS("Existing prices deleted successfully."))

        # Insert new prices, including TZS
        for tier_name, price_data in prices.items():
            tier = tiers.get(tier_name)
            if not tier:
                self.stdout.write(self.style.ERROR(f"Tier '{tier_name}' not found, skipping..."))
                continue

            for currency_code, amount in price_data.items():
                currency = currencies.get(currency_code)
                if not currency:
                    self.stdout.write(self.style.ERROR(f"Currency '{currency_code}' not found, skipping..."))
                    continue

                # Create new course price entries
                CoursePrice.objects.create(tier=tier, currency=currency, amount=amount)
                self.stdout.write(self.style.SUCCESS(f"Added price: {tier.get_name_display()} - {currency.code} {amount}"))

        self.stdout.write(self.style.SUCCESS("Price update complete!"))
