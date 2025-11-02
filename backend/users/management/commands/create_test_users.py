"""
Django management command to create test users
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Create test users for the application'

    def handle(self, *args, **options):
        # Test users data
        test_users = [
            {
                'username': 'admin',
                'email': 'admin@test.com',
                'password': 'admin123',
                'role': 'admin',
                'full_name': 'Admin User',
                'department': 'IT',
                'phone': '010-1234-5678',
            },
            {
                'username': 'manager',
                'email': 'manager@test.com',
                'password': 'manager123',
                'role': 'manager',
                'full_name': 'Manager User',
                'department': 'Management',
                'phone': '010-2345-6789',
            },
            {
                'username': 'viewer',
                'email': 'viewer@test.com',
                'password': 'viewer123',
                'role': 'viewer',
                'full_name': 'Viewer User',
                'department': 'General',
                'phone': '010-3456-7890',
            },
        ]

        self.stdout.write('Creating test users...\n')

        for user_data in test_users:
            username = user_data['username']

            # Check if user already exists
            if User.objects.filter(username=username).exists():
                self.stdout.write(self.style.WARNING(f'User "{username}" already exists. Skipping.'))
                continue

            # Create user
            password = user_data.pop('password')
            user = User.objects.create(**user_data)
            user.set_password(password)
            user.is_active = True
            user.save()

            self.stdout.write(self.style.SUCCESS(f'Created user "{username}" with role "{user.role}"'))

        self.stdout.write(self.style.SUCCESS('\n=== Test Users Created Successfully ==='))
        self.stdout.write('You can now login with:')
        self.stdout.write('  - admin / admin123')
        self.stdout.write('  - manager / manager123')
        self.stdout.write('  - viewer / viewer123')
