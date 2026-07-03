from django.core.management.base import BaseCommand
from coffes.models import MenuItem, User


class Command(BaseCommand):
    help = 'Add or refresh the Sip Smart cafe menu'

    def handle(self, *args, **options):
        admin_user = User.objects.filter(is_staff=True).first()
        menu_items = [
            ('Brownie', 'Dense chocolate brownie with a soft fudgy center.', 149, '/static/images/menu/brownie.png'),
            ('Blueberry Muffin', 'Fresh bakery muffin with sweet blueberry notes.', 129, '/static/images/menu/blueberry-muffin.png'),
            ('Cappuccino', 'Espresso, steamed milk, and foam with a balanced cafe taste.', 149, '/static/images/menu/cappuccino.png'),
            ('Cold Coffee', 'Chilled coffee blended smooth and served cafe style.', 169, '/static/images/menu/cold-coffee.png'),
            ('French Fries', 'Crispy golden fries served hot for a quick snack.', 129, '/static/images/menu/french-fries.png'),
            ('Espresso', 'Strong single-shot coffee with a rich crema finish.', 99, '/static/images/menu/espresso.png'),
            ('Hot Chocolate', 'Velvety cocoa drink topped with a smooth finish.', 149, '/static/images/menu/hot-chocolate.png'),
            ('Paneer Tikka Sandwich', 'Spiced paneer filling grilled between fresh bread.', 199, '/static/images/menu/paneer-tikka-sandwich.png'),
            ('Veg Sandwich', 'Grilled vegetable sandwich with cafe-style seasoning.', 169, '/static/images/menu/veg-sandwich.png'),
            ('Samosa', 'Golden crispy samosa served as a classic cafe snack.', 79, '/static/images/menu/samosa.png'),
        ]

        keep_names = [item[0] for item in menu_items]
        MenuItem.objects.exclude(name__in=keep_names).update(availability=False)

        created = 0
        updated = 0
        for name, description, price, image_url in menu_items:
            _, was_created = MenuItem.objects.update_or_create(
                name=name,
                defaults={
                    'description': description,
                    'price': price,
                    'image_url': image_url,
                    'image': '',
                    'availability': True,
                    'added_by': admin_user,
                },
            )
            created += int(was_created)
            updated += int(not was_created)

        self.stdout.write(
            self.style.SUCCESS(f'Sip Smart menu ready. Created: {created}, updated: {updated}.')
        )
