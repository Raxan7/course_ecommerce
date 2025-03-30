from core.models import CoursePrice, CourseTier, Currency

# Define pricing structure
prices = {
    'basic': {'USD': 10, 'KES': 490, 'EUR': 10},
    'standard': {'USD': 50, 'KES': 2450, 'EUR': 50},
    'premium': {'USD': 100, 'KES': 4900, 'EUR': 100},
}

# Fetch existing tiers and currencies
tiers = {tier.name: tier for tier in CourseTier.objects.all()}
currencies = {currency.code: currency for currency in Currency.objects.all()}

# Insert missing prices
for tier_name, price_data in prices.items():
    tier = tiers.get(tier_name)
    if not tier:
        print(f"Tier '{tier_name}' not found, skipping...")
        continue

    for currency_code, amount in price_data.items():
        currency = currencies.get(currency_code)
        if not currency:
            print(f"Currency '{currency_code}' not found, skipping...")
            continue

        # Ensure the price does not already exist
        if not CoursePrice.objects.filter(tier=tier, currency=currency).exists():
            CoursePrice.objects.create(tier=tier, currency=currency, amount=amount)
            print(f"Added price: {tier.get_name_display()} - {currency.code} {amount}")
        else:
            print(f"Price already exists: {tier.get_name_display()} - {currency.code} {amount}")

print("Price update complete!")
