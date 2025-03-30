from django.core.management.base import BaseCommand
from core.models import Currency, CourseTier, Course, CoursePrice
from django.utils.timezone import now

class Command(BaseCommand):
    help = 'Sets up the initial course data with tiers and pricing'

    def handle(self, *args, **options):
        self.stdout.write("Setting up course data...")
        
        # Create or get currencies
        tzs, _ = Currency.objects.get_or_create(
            code='TZS', 
            name='Tanzanian Shilling', 
            symbol='TSh'
        )
        usd, _ = Currency.objects.get_or_create(
            code='USD', 
            name='US Dollar', 
            symbol='$'
        )
        kes, _ = Currency.objects.get_or_create(
            code='KES', 
            name='Kenyan Shilling', 
            symbol='KSh'
        )
        eur, _ = Currency.objects.get_or_create(
            code='EUR', 
            name='Euro', 
            symbol='€'
        )
        self.stdout.write(self.style.SUCCESS('Currencies created/updated'))

        # Create course tiers
        warrior_tier, _ = CourseTier.objects.get_or_create(
            name='basic',
            defaults={
                'description': 'Warrior\'s Path - Step into your power',
                'order': 1
            }
        )
        champion_tier, _ = CourseTier.objects.get_or_create(
            name='standard',
            defaults={
                'description': 'Champion\'s Edge - Sharpen your skills and dominance',
                'order': 2
            }
        )
        king_tier, _ = CourseTier.objects.get_or_create(
            name='premium',
            defaults={
                'description': 'King\'s Throne - Rule with ultimate confidence',
                'order': 3
            }
        )
        self.stdout.write(self.style.SUCCESS('Course tiers created/updated'))

        # Create the main course
        alpha_course, created = Course.objects.get_or_create(
            title='Alpha Males Class',
            defaults={
                'short_description': 'Master male performance and dominance',
                'description': 'Master the art of male performance, control, and dominance—unlock lasting stamina, confidence, and techniques to fully satisfy your woman.',
                'image': 'course_images/alpha_males.jpg',
                'created_at': now(),
                'updated_at': now(),
                'featured': True,
                'is_active': True,
                'tier': warrior_tier  # Default tier
            }
        )

        # Add all tiers to the course's available tiers
        alpha_course.available_tiers.add(warrior_tier, champion_tier, king_tier)
        alpha_course.save()
        
        if created:
            self.stdout.write(self.style.SUCCESS('Alpha Males Class course created'))
        else:
            self.stdout.write(self.style.SUCCESS('Alpha Males Class course updated'))

        # Create prices for all tiers
        tier_prices = [
            # Warrior's Path (basic tier)
            (warrior_tier, tzs, 10000.00),
            (warrior_tier, usd, 10.00),
            (warrior_tier, kes, 490.00),
            (warrior_tier, eur, 10.00),
            
            # Champion's Edge (standard tier)
            (champion_tier, tzs, 50000.00),
            (champion_tier, usd, 50.00),
            (champion_tier, kes, 2450.00),
            (champion_tier, eur, 50.00),
            
            # King's Throne (premium tier)
            (king_tier, tzs, 100000.00),
            (king_tier, usd, 100.00),
            (king_tier, kes, 4900.00),
            (king_tier, eur, 100.00)
        ]

        for tier, currency, amount in tier_prices:
            CoursePrice.objects.get_or_create(
                tier=tier,
                currency=currency,
                defaults={'amount': amount}
            )
        
        self.stdout.write(self.style.SUCCESS('All pricing data created/updated'))
        self.stdout.write(self.style.SUCCESS('Course data setup completed successfully!'))