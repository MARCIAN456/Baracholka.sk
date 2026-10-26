import uuid
from datetime import date
from app.core.database import SessionLocal
from app.models.user import User
from app.models.item import Item, ItemCategory

# Список реалістичних товарів для барахолки з категоріями
SAMPLE_ITEMS = [
    ("Велосипед гірський Trek Marlin 5", "Гарний стан, дискові гальма, 29 колеса", 420.0, ItemCategory.SPORT.value),
    ("iPhone 13 128GB Midnight", "Батарея 88%, без подряпин, повний комплект", 390.0, ItemCategory.ELECTRONICS.value),
    ("Ноутбук Lenovo ThinkPad T14", "Intel i5, 16GB RAM, 512GB SSD, чудово для навчання", 480.0, ItemCategory.ELECTRONICS.value),
    ("Диван розкладний сірий ІКЕА", "Самовивіз, гарний стан, чистий", 130.0, ItemCategory.HOME.value),
    ("PlayStation 5 з двома геймпадами", "Ревізія з дисководом, працює тихо", 440.0, ItemCategory.ELECTRONICS.value),
    ("Монітор Dell 27 дюймів IPS", "FullHD, 75Hz, без битих пікселів", 110.0, ItemCategory.ELECTRONICS.value),
    ("Акустична гітара Yamaha F310", "Нові струни D'Addario, у комплекті чохол", 95.0, ItemCategory.OTHER.value),
    ("Зимова куртка The North Face", "Розмір M, дуже тепла, оригінал", 85.0, ItemCategory.FASHION.value),
    ("Кавомашина DeLonghi Magnifica", "Зернова, повністю обслужена", 210.0, ItemCategory.HOME.value),
    ("Офісне крісло ергономічне", "Регулювання попереку та підлокітників", 75.0, ItemCategory.HOME.value),
    ("Бездротові навушники Sony WH-1000XM4", "Ідеальне шумозаглушення, батарея тримає до 30 годин", 180.0, ItemCategory.ELECTRONICS.value),
    ("Електросамокат Xiaomi Pro 2", "Пробіг 400 км, запас ходу до 45 км", 260.0, ItemCategory.SPORT.value),
    ("Смарт-годинник Apple Watch SE 44mm", "Space Gray, ремінець спортивний", 150.0, ItemCategory.ELECTRONICS.value),
    ("Планшет iPad 9th Gen 64GB Space Gray", "У чохлі з першого дня, підтримує Apple Pencil", 230.0, ItemCategory.ELECTRONICS.value),
    ("Мікрохвильова піч Samsung", "23 літри, біокерамічне покриття, як нова", 60.0, ItemCategory.HOME.value),
    ("Пилосос робот Roborock S5 Max", "Вологе та сухе прибирання, керування з додатку", 170.0, ItemCategory.HOME.value),
    ("Стіл письмовий дерев'яний", "Розміри 120х60, стан ідеальний", 50.0, ItemCategory.HOME.value),
    ("Механічна клавіатура Keychron K2", "Перемикачі Brown, бездротова (Bluetooth)", 70.0, ItemCategory.ELECTRONICS.value),
    ("Рюкзак туристичний Osprey 40L", "Підходить для ручної поклажі, дуже зручний", 90.0, ItemCategory.SPORT.value),
    ("Телевізор LG 43 4K Smart TV", "WebOS, пульт Magic Remote у комплекті", 220.0, ItemCategory.ELECTRONICS.value),
    ("Фітнес-гантелі набірні (2x10 кг)", "Металеві, з замками", 40.0, ItemCategory.SPORT.value),
    ("Фотоапарат Canon EOS 2000D", "Об'єктив 18-55mm, сумка та флешка на 64GB", 290.0, ItemCategory.ELECTRONICS.value),
    ("Пральна машина Bosch Serie 4", "Завантаження 6 кг, 1200 об/хв, працює тихо", 190.0, ItemCategory.HOME.value),
    ("Дзеркало настінне в рамі", "Висота 150 см, ширина 50 см", 30.0, ItemCategory.HOME.value),
    ("Намет 3-місний кемпінговий Quechua", "Водостійкий, швидка збірка, стан нового", 65.0, ItemCategory.SPORT.value),
]

def seed_database():
    db = SessionLocal()
    try:
        # 1. Знаходимо користувача в базі, щоб прив'язати до нього товари
        user = db.query(User).first()
        if not user:
            print("❌ Спочатку зареєструй хоча б одного користувача через /register!")
            return

        print(f"👤 Знайдено користувача: {user.username} (ID: {user.id})")

        # 2. Додаємо товари з категоріями
        new_items = []
        for title, desc, price, category in SAMPLE_ITEMS:
            item = Item(
                id=uuid.uuid4(),
                title=title,
                description=desc,
                price=price,
                category=category,
                is_sold=False,
                createdAt=date.today(),
                user_id=user.id
            )
            new_items.append(item)

        db.add_all(new_items)
        db.commit()
        print(f"✅ Успішно додано {len(new_items)} тестових оголошень з різними категоріями!")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()