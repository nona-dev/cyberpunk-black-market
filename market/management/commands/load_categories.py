from django.core.management.base import BaseCommand
from market.models import Category

class Command(BaseCommand):
    help = 'Загрузка категорий'

    def handle(self, *args, **options):
        categories = [
            'Оружие',
            'Броня',
            'Киберимпланты',
            'Медицина',
            'Электроника',
            'Наркотики',
            'Информация',
            'Транспорт'
        ]
        
        for cat_name in categories:
            category, created = Category.objects.get_or_create(name=cat_name)
            if created:
                self.stdout.write(f'Создана категория: {cat_name}')
            else:
                self.stdout.write(f'Категория уже существует: {cat_name}')
        
        self.stdout.write(
            self.style.SUCCESS('Все категории успешно загружены!')
        )