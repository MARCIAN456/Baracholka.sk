import uuid
from datetime import date
from app.core.database import SessionLocal
from app.models.user import User
from app.models.item import Item, ItemCategory, ItemStatus

SAMPLE_ITEMS = [
    ("Trek Marlin 5 mountain bike", "Good condition, disc brakes, 29-inch wheels", 420.0, ItemCategory.SPORT.value),
    ("iPhone 13 128GB Midnight", "Battery 88%, no scratches, full set included", 390.0, ItemCategory.ELECTRONICS.value),
    ("Lenovo ThinkPad T14 laptop", "Intel i5, 16GB RAM, 512GB SSD, great for studying", 480.0, ItemCategory.ELECTRONICS.value),
    ("IKEA grey sofa bed", "Pickup only, good condition, clean and no smells", 130.0, ItemCategory.HOME.value),
    ("PlayStation 5 + 2 controllers", "Disc edition, runs quietly, all cables included", 440.0, ItemCategory.ELECTRONICS.value),
    ("Dell 27-inch IPS monitor", "Full HD, 75Hz, no dead pixels, original stand", 110.0, ItemCategory.ELECTRONICS.value),
    ("Yamaha F310 acoustic guitar", "New D'Addario strings, carrying case included", 95.0, ItemCategory.OTHER.value),
    ("The North Face winter jacket", "Size M, very warm, original, worn two seasons", 85.0, ItemCategory.FASHION.value),
    ("DeLonghi Magnifica espresso", "Bean-to-cup machine, fully serviced and descaled", 210.0, ItemCategory.HOME.value),
    ("Ergonomic office chair", "Adjustable lumbar support and armrests, black mesh", 75.0, ItemCategory.HOME.value),
    ("Sony WH-1000XM4 headphones", "Excellent noise cancelling, battery lasts 30 hours", 180.0, ItemCategory.ELECTRONICS.value),
    ("Xiaomi Pro 2 electric scooter", "400 km mileage, range up to 45 km, new tyres", 260.0, ItemCategory.SPORT.value),
    ("Apple Watch SE 44mm", "Space Gray, sport band, battery health 92%", 150.0, ItemCategory.ELECTRONICS.value),
    ("iPad 9th Gen 64GB Space Gray", "Kept in a case since day one, supports Apple Pencil", 230.0, ItemCategory.ELECTRONICS.value),
    ("Samsung microwave oven", "23 litres, ceramic enamel interior, like new", 60.0, ItemCategory.HOME.value),
    ("Roborock S5 Max robot vacuum", "Wet and dry cleaning, controlled from the app", 170.0, ItemCategory.HOME.value),
    ("Wooden writing desk", "Size 120x60 cm, perfect condition, solid wood", 50.0, ItemCategory.HOME.value),
    ("Keychron K2 keyboard", "Mechanical, Brown switches, wireless Bluetooth", 70.0, ItemCategory.ELECTRONICS.value),
    ("Osprey 40L travel backpack", "Fits as cabin luggage, very comfortable to carry", 90.0, ItemCategory.SPORT.value),
    ("LG 43-inch 4K Smart TV", "WebOS, Magic Remote included, wall mount included", 220.0, ItemCategory.ELECTRONICS.value),
    ("Adjustable dumbbells 2x10 kg", "Metal plates with secure locks, barely used", 40.0, ItemCategory.SPORT.value),
    ("Canon EOS 2000D camera", "18-55mm lens, bag and 64GB memory card included", 290.0, ItemCategory.ELECTRONICS.value),
    ("Bosch Serie 4 washing machine", "6 kg load, 1200 rpm, quiet and fully working", 190.0, ItemCategory.HOME.value),
    ("Wall mirror with frame", "Height 150 cm, width 50 cm, wooden frame", 30.0, ItemCategory.HOME.value),
    ("Quechua 3-person tent", "Waterproof, quick setup, condition like new", 65.0, ItemCategory.SPORT.value),
]

def seed_database():
    db = SessionLocal()
    try:
        user = db.query(User).first()
        if not user:
            print("No users found. Register one via /api/v1/auth/register first.")
            return

        print(f"Using user: {user.username} (ID: {user.id})")

        new_items = []
        for title, desc, price, category in SAMPLE_ITEMS:
            item = Item(
                id=uuid.uuid4(),
                title=title,
                description=desc,
                price=price,
                category=category,
                is_sold=False,
                status=ItemStatus.ACCEPTED.value,
                createdAt=date.today(),
                user_id=user.id
            )
            new_items.append(item)

        db.add_all(new_items)
        db.commit()
        print(f"Added {len(new_items)} sample items.")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
