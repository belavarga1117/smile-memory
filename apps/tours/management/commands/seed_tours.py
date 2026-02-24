"""Seed database with sample tour data for development."""

from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand

from apps.tours.models import (
    Airline,
    Category,
    Destination,
    ItineraryDay,
    Tour,
    TourDeparture,
)


class Command(BaseCommand):
    help = "Seed database with sample tour data"

    def handle(self, *args, **options):
        self.stdout.write("Seeding tour data...")

        # Airlines
        airlines = {}
        for code, name, name_th in [
            ("TG", "Thai Airways", "การบินไทย"),
            ("CX", "Cathay Pacific", "คาเธ่ย์แปซิฟิค"),
            ("VZ", "Thai VietJet", "ไทยเวียตเจ็ท"),
            ("SL", "Thai Lion Air", "ไทยไลอ้อนแอร์"),
            ("JL", "Japan Airlines", "เจแปนแอร์ไลน์"),
            ("KE", "Korean Air", "โคเรียนแอร์"),
            ("TK", "Turkish Airlines", "เตอร์กิชแอร์ไลน์"),
            ("EK", "Emirates", "เอมิเรตส์"),
        ]:
            obj, _ = Airline.objects.get_or_create(
                code=code, defaults={"name": name, "name_th": name_th}
            )
            airlines[code] = obj

        # Destinations (countries)
        destinations = {}
        for name, name_th, slug, iso2, iso3 in [
            ("Japan", "ญี่ปุ่น", "japan", "JP", "JPN"),
            ("South Korea", "เกาหลีใต้", "south-korea", "KR", "KOR"),
            ("China", "จีน", "china", "CN", "CHN"),
            ("Hong Kong", "ฮ่องกง", "hong-kong", "HK", "HKG"),
            ("Vietnam", "เวียดนาม", "vietnam", "VN", "VNM"),
            ("Taiwan", "ไต้หวัน", "taiwan", "TW", "TWN"),
            ("Turkey", "ตุรกี", "turkey", "TR", "TUR"),
            ("Switzerland", "สวิตเซอร์แลนด์", "switzerland", "CH", "CHE"),
            ("Italy", "อิตาลี", "italy", "IT", "ITA"),
            ("France", "ฝรั่งเศส", "france", "FR", "FRA"),
        ]:
            obj, _ = Destination.objects.get_or_create(
                slug=slug,
                defaults={
                    "name": name,
                    "name_th": name_th,
                    "country_code_iso2": iso2,
                    "country_code_iso3": iso3,
                    "is_featured": True,
                },
            )
            destinations[slug] = obj

        # Categories
        categories = {}
        for name, name_th, slug, icon in [
            ("Cultural", "วัฒนธรรม", "cultural", "🏛"),
            ("Beach", "ชายหาด", "beach", "🏖"),
            ("Adventure", "ผจญภัย", "adventure", "🧗"),
            ("City", "เมือง", "city", "🏙"),
            ("Nature", "ธรรมชาติ", "nature", "🌿"),
            ("Luxury", "หรูหรา", "luxury", "💎"),
            ("Food & Wine", "อาหารและไวน์", "food-wine", "🍷"),
        ]:
            obj, _ = Category.objects.get_or_create(
                slug=slug, defaults={"name": name, "name_th": name_th, "icon": icon}
            )
            categories[slug] = obj

        # Tour data
        tours_data = [
            {
                "title": "Tokyo Osaka Classic 6D4N",
                "title_th": "โตเกียว โอซาก้า คลาสสิค 6วัน4คืน",
                "product_code": "ZGJPN-2501TG",
                "slug": "tokyo-osaka-classic-6d4n",
                "highlight": "Visit iconic Mt. Fuji, explore Shibuya & Shinjuku, taste authentic ramen, see Osaka Castle and Dotonbori.",
                "highlight_th": "เยือนภูเขาไฟฟูจิ สำรวจชิบูย่าและชินจูกุ ชิมราเมนต้นตำรับ ชมปราสาทโอซาก้าและโดทงโบริ",
                "description": "Experience the best of Japan with this classic Tokyo-Osaka itinerary. From the neon-lit streets of Shinjuku to the historic temples of Kyoto, this tour covers all the must-see highlights.",
                "destinations": ["japan"],
                "categories": ["cultural", "city", "food-wine"],
                "airline_code": "TG",
                "duration_days": 6,
                "duration_nights": 4,
                "hotel_stars_min": 3,
                "hotel_stars_max": 4,
                "total_meals": 8,
                "plane_meals": True,
                "price_from": Decimal("35900"),
                "locations": ["Tokyo", "Hakone", "Mt. Fuji", "Kyoto", "Osaka"],
                "includes": "Round-trip flights (Thai Airways)\n4 nights hotel accommodation\n8 meals as per itinerary\nAll transfers and transportation\nEnglish/Thai speaking guide\nAll entrance fees",
                "excludes": "Travel insurance\nPersonal expenses\nTips for guide and driver\nMeals not mentioned",
                "departures": [
                    {
                        "date_offset": 30,
                        "price": Decimal("35900"),
                        "seats": 25,
                        "deposit": Decimal("10000"),
                    },
                    {
                        "date_offset": 45,
                        "price": Decimal("36900"),
                        "seats": 25,
                        "deposit": Decimal("10000"),
                    },
                    {
                        "date_offset": 60,
                        "price": Decimal("34900"),
                        "seats": 25,
                        "deposit": Decimal("10000"),
                        "promo": Decimal("32900"),
                    },
                ],
                "itinerary": [
                    {
                        "day": 1,
                        "title": "Bangkok → Tokyo (Narita)",
                        "title_th": "กรุงเทพฯ → โตเกียว (นาริตะ)",
                        "desc": "Depart from Suvarnabhumi Airport to Tokyo Narita. Arrive and transfer to hotel.",
                        "breakfast": "P",
                        "lunch": "N",
                        "dinner": "Y",
                        "dinner_desc": "Japanese welcome dinner",
                        "hotel": "Shinjuku Washington Hotel",
                        "stars": 4,
                    },
                    {
                        "day": 2,
                        "title": "Tokyo City Tour",
                        "title_th": "ทัวร์โตเกียว",
                        "desc": "Visit Meiji Shrine, Harajuku, Shibuya Crossing, and Asakusa Senso-ji Temple. Shopping at Shinjuku.",
                        "breakfast": "Y",
                        "lunch": "Y",
                        "lunch_desc": "Ramen lunch",
                        "dinner": "N",
                        "hotel": "Shinjuku Washington Hotel",
                        "stars": 4,
                    },
                    {
                        "day": 3,
                        "title": "Mt. Fuji & Hakone",
                        "title_th": "ภูเขาไฟฟูจิ & ฮาโกเน่",
                        "desc": "Day trip to Mt. Fuji 5th Station. Visit Hakone and take the ropeway with views of Lake Ashi.",
                        "breakfast": "Y",
                        "lunch": "Y",
                        "dinner": "Y",
                        "dinner_desc": "Shabu shabu buffet",
                        "hotel": "Hakone Onsen Hotel",
                        "stars": 4,
                    },
                    {
                        "day": 4,
                        "title": "Hakone → Kyoto → Osaka",
                        "title_th": "ฮาโกเน่ → เกียวโต → โอซาก้า",
                        "desc": "Bullet train to Kyoto. Visit Kinkaku-ji (Golden Pavilion) and Fushimi Inari Shrine. Transfer to Osaka.",
                        "breakfast": "Y",
                        "lunch": "Y",
                        "dinner": "N",
                        "hotel": "Hotel Monterey Osaka",
                        "stars": 4,
                    },
                    {
                        "day": 5,
                        "title": "Osaka City Tour",
                        "title_th": "ทัวร์โอซาก้า",
                        "desc": "Visit Osaka Castle, Dotonbori, and Shinsaibashi Shopping Street. Free time for shopping.",
                        "breakfast": "Y",
                        "lunch": "N",
                        "dinner": "Y",
                        "dinner_desc": "Takoyaki & Okonomiyaki dinner",
                        "hotel": "Hotel Monterey Osaka",
                        "stars": 4,
                    },
                    {
                        "day": 6,
                        "title": "Osaka → Bangkok",
                        "title_th": "โอซาก้า → กรุงเทพฯ",
                        "desc": "Free morning for shopping at Rinku Premium Outlets. Transfer to Kansai Airport for return flight.",
                        "breakfast": "Y",
                        "lunch": "N",
                        "dinner": "P",
                    },
                ],
            },
            {
                "title": "Seoul Explorer 5D3N",
                "title_th": "โซล เอ็กซ์พลอเรอร์ 5วัน3คืน",
                "product_code": "ZGKOR-2502KE",
                "slug": "seoul-explorer-5d3n",
                "highlight": "Gyeongbokgung Palace, N Seoul Tower, Myeongdong shopping, Korean BBQ experience, K-pop culture tour.",
                "description": "Immerse yourself in Korean culture, cuisine, and K-pop. Visit historic palaces, shop in trendy districts, and taste the best Korean BBQ in Seoul.",
                "destinations": ["south-korea"],
                "categories": ["cultural", "city", "food-wine"],
                "airline_code": "KE",
                "duration_days": 5,
                "duration_nights": 3,
                "hotel_stars_min": 4,
                "hotel_stars_max": 4,
                "total_meals": 6,
                "plane_meals": True,
                "price_from": Decimal("25900"),
                "locations": ["Seoul", "Nami Island"],
                "includes": "Round-trip flights (Korean Air)\n3 nights hotel\n6 meals\nAll transfers\nGuide\nEntrance fees",
                "excludes": "Travel insurance\nPersonal expenses\nTips",
                "departures": [
                    {
                        "date_offset": 20,
                        "price": Decimal("25900"),
                        "seats": 30,
                        "deposit": Decimal("8000"),
                    },
                    {
                        "date_offset": 40,
                        "price": Decimal("26900"),
                        "seats": 30,
                        "deposit": Decimal("8000"),
                    },
                ],
                "itinerary": [
                    {
                        "day": 1,
                        "title": "Bangkok → Seoul (Incheon)",
                        "desc": "Arrive Seoul. Transfer to hotel in Myeongdong area.",
                        "breakfast": "P",
                        "lunch": "N",
                        "dinner": "Y",
                        "dinner_desc": "Korean BBQ",
                        "hotel": "Lotte City Hotel Myeongdong",
                        "stars": 4,
                    },
                    {
                        "day": 2,
                        "title": "Seoul Palace & Culture Tour",
                        "desc": "Gyeongbokgung Palace, Bukchon Hanok Village, Insadong Art Street, N Seoul Tower.",
                        "breakfast": "Y",
                        "lunch": "Y",
                        "dinner": "N",
                        "hotel": "Lotte City Hotel Myeongdong",
                        "stars": 4,
                    },
                    {
                        "day": 3,
                        "title": "Nami Island Day Trip",
                        "desc": "Visit Nami Island and Petite France. Evening shopping at Dongdaemun.",
                        "breakfast": "Y",
                        "lunch": "Y",
                        "dinner": "N",
                        "hotel": "Lotte City Hotel Myeongdong",
                        "stars": 4,
                    },
                    {
                        "day": 4,
                        "title": "Shopping & K-pop",
                        "desc": "K-Star Road in Gangnam, COEX Mall, Lotte World Tower observation deck. Myeongdong free shopping.",
                        "breakfast": "Y",
                        "lunch": "N",
                        "dinner": "Y",
                        "dinner_desc": "Samgyeopsal dinner",
                        "hotel": "Lotte City Hotel Myeongdong",
                        "stars": 4,
                    },
                    {
                        "day": 5,
                        "title": "Seoul → Bangkok",
                        "desc": "Morning free time. Transfer to Incheon Airport.",
                        "breakfast": "Y",
                        "lunch": "P",
                        "dinner": "N",
                    },
                ],
            },
            {
                "title": "Hong Kong Macau 4D3N",
                "title_th": "ฮ่องกง มาเก๊า 4วัน3คืน",
                "product_code": "ZGHKG-2413CX",
                "slug": "hong-kong-macau-4d3n",
                "highlight": "Ngong Ping 360, Big Buddha, Victoria Peak, Macau Venetian, dim sum feast.",
                "description": "The best of Hong Kong and Macau in 4 days. Ride the Ngong Ping cable car, visit the Big Buddha, explore Victoria Peak, and cross to Macau for the Venetian.",
                "destinations": ["hong-kong"],
                "categories": ["city", "food-wine"],
                "airline_code": "CX",
                "duration_days": 4,
                "duration_nights": 3,
                "hotel_stars_min": 4,
                "hotel_stars_max": 4,
                "total_meals": 5,
                "plane_meals": True,
                "price_from": Decimal("17900"),
                "locations": ["Hong Kong", "Macau", "Lantau Island"],
                "includes": "Round-trip flights (Cathay Pacific)\n3 nights hotel\n5 meals\nAll transfers\nGuide",
                "excludes": "Travel insurance\nPersonal expenses\nTips",
                "departures": [
                    {
                        "date_offset": 15,
                        "price": Decimal("17900"),
                        "seats": 24,
                        "deposit": Decimal("8000"),
                    },
                    {
                        "date_offset": 35,
                        "price": Decimal("18900"),
                        "seats": 24,
                        "deposit": Decimal("8000"),
                    },
                    {
                        "date_offset": 50,
                        "price": Decimal("17900"),
                        "seats": 24,
                        "deposit": Decimal("8000"),
                        "promo": Decimal("15900"),
                    },
                ],
                "itinerary": [
                    {
                        "day": 1,
                        "title": "Bangkok → Hong Kong",
                        "desc": "Arrive Hong Kong. Avenue of Stars, Victoria Harbour light show.",
                        "breakfast": "P",
                        "lunch": "N",
                        "dinner": "Y",
                        "hotel": "Harbour Plaza",
                        "stars": 4,
                    },
                    {
                        "day": 2,
                        "title": "Hong Kong Island Tour",
                        "desc": "Victoria Peak, Repulse Bay, Aberdeen fishing village, Stanley Market.",
                        "breakfast": "Y",
                        "lunch": "Y",
                        "lunch_desc": "Dim sum lunch",
                        "dinner": "N",
                        "hotel": "Harbour Plaza",
                        "stars": 4,
                    },
                    {
                        "day": 3,
                        "title": "Ngong Ping & Macau",
                        "desc": "Ngong Ping 360, Big Buddha, Po Lin Monastery. Ferry to Macau: Ruins of St. Paul's, Venetian.",
                        "breakfast": "Y",
                        "lunch": "N",
                        "dinner": "Y",
                        "hotel": "Harbour Plaza",
                        "stars": 4,
                    },
                    {
                        "day": 4,
                        "title": "Hong Kong → Bangkok",
                        "desc": "Morning shopping at Tsim Sha Tsui. Transfer to airport.",
                        "breakfast": "Y",
                        "lunch": "P",
                        "dinner": "N",
                    },
                ],
            },
            {
                "title": "Vietnam Hanoi Sapa 5D4N",
                "title_th": "เวียดนาม ฮานอย ซาปา 5วัน4คืน",
                "product_code": "ZGVNM-2505VZ",
                "slug": "vietnam-hanoi-sapa-5d4n",
                "highlight": "Ha Long Bay cruise, Sapa rice terraces, Hanoi Old Quarter, Trang An boat ride.",
                "description": "Discover northern Vietnam from Hanoi's charming Old Quarter to the stunning rice terraces of Sapa and the emerald waters of Ha Long Bay.",
                "destinations": ["vietnam"],
                "categories": ["nature", "cultural", "adventure"],
                "airline_code": "VZ",
                "duration_days": 5,
                "duration_nights": 4,
                "hotel_stars_min": 3,
                "hotel_stars_max": 4,
                "total_meals": 10,
                "plane_meals": False,
                "price_from": Decimal("14900"),
                "locations": ["Hanoi", "Ha Long Bay", "Sapa", "Ninh Binh"],
                "includes": "Round-trip flights (Thai VietJet)\n4 nights hotel\n10 meals\nHa Long Bay cruise\nAll transfers\nGuide",
                "excludes": "Travel insurance\nVisa on arrival fee\nPersonal expenses",
                "departures": [
                    {
                        "date_offset": 25,
                        "price": Decimal("14900"),
                        "seats": 30,
                        "deposit": Decimal("5000"),
                    },
                    {
                        "date_offset": 55,
                        "price": Decimal("15900"),
                        "seats": 30,
                        "deposit": Decimal("5000"),
                    },
                ],
                "itinerary": [
                    {
                        "day": 1,
                        "title": "Bangkok → Hanoi",
                        "desc": "Arrive Hanoi. Walking tour of the Old Quarter, Hoan Kiem Lake.",
                        "breakfast": "N",
                        "lunch": "N",
                        "dinner": "Y",
                        "dinner_desc": "Vietnamese pho dinner",
                        "hotel": "Hanoi La Siesta",
                        "stars": 4,
                    },
                    {
                        "day": 2,
                        "title": "Hanoi → Ha Long Bay",
                        "desc": "Drive to Ha Long Bay. Cruise among thousands of limestone karsts, kayaking, cave exploration.",
                        "breakfast": "Y",
                        "lunch": "Y",
                        "lunch_desc": "Seafood lunch on cruise",
                        "dinner": "Y",
                        "hotel": "Ha Long Bay Cruise",
                        "stars": 4,
                    },
                    {
                        "day": 3,
                        "title": "Ha Long → Sapa",
                        "desc": "Morning tai chi on deck. Transfer to Sapa. Visit Cat Cat Village.",
                        "breakfast": "Y",
                        "lunch": "Y",
                        "dinner": "Y",
                        "hotel": "Sapa Highland Resort",
                        "stars": 3,
                    },
                    {
                        "day": 4,
                        "title": "Sapa Rice Terraces",
                        "desc": "Trek through rice terraces, visit Hmong villages. Return to Hanoi via highway.",
                        "breakfast": "Y",
                        "lunch": "Y",
                        "dinner": "Y",
                        "dinner_desc": "Bun cha dinner",
                        "hotel": "Hanoi La Siesta",
                        "stars": 4,
                    },
                    {
                        "day": 5,
                        "title": "Hanoi → Bangkok",
                        "desc": "Ho Chi Minh Mausoleum, Temple of Literature. Transfer to airport.",
                        "breakfast": "Y",
                        "lunch": "Y",
                        "dinner": "N",
                    },
                ],
            },
            {
                "title": "Turkey Highlights 10D7N",
                "title_th": "ตุรกี ไฮไลท์ 10วัน7คืน",
                "product_code": "ZGTUR-2506TK",
                "slug": "turkey-highlights-10d7n",
                "highlight": "Istanbul Blue Mosque, Cappadocia hot air balloon, Pamukkale terraces, Ephesus ancient ruins.",
                "description": "A comprehensive tour of Turkey's greatest treasures — from Istanbul's majestic mosques to Cappadocia's fairy chimneys and the ancient ruins of Ephesus.",
                "destinations": ["turkey"],
                "categories": ["cultural", "adventure", "nature"],
                "airline_code": "TK",
                "duration_days": 10,
                "duration_nights": 7,
                "hotel_stars_min": 4,
                "hotel_stars_max": 5,
                "total_meals": 18,
                "plane_meals": True,
                "price_from": Decimal("45900"),
                "locations": [
                    "Istanbul",
                    "Cappadocia",
                    "Pamukkale",
                    "Ephesus",
                    "Antalya",
                ],
                "includes": "Round-trip flights (Turkish Airlines)\n7 nights 4-5 star hotel\n18 meals\nDomestic flights\nAll transfers and entrance fees\nGuide",
                "excludes": "Travel insurance\nHot air balloon (optional)\nPersonal expenses",
                "departures": [
                    {
                        "date_offset": 40,
                        "price": Decimal("45900"),
                        "seats": 20,
                        "deposit": Decimal("15000"),
                    },
                    {
                        "date_offset": 70,
                        "price": Decimal("47900"),
                        "seats": 20,
                        "deposit": Decimal("15000"),
                    },
                ],
                "itinerary": [],
            },
            {
                "title": "Switzerland Classic 8D5N",
                "title_th": "สวิตเซอร์แลนด์ คลาสสิค 8วัน5คืน",
                "product_code": "ZGCHE-2507EK",
                "slug": "switzerland-classic-8d5n",
                "highlight": "Jungfraujoch Top of Europe, Lake Lucerne cruise, Interlaken, Zurich Old Town.",
                "description": "Experience the breathtaking Swiss Alps, pristine lakes, and charming cities. Ride to the top of Jungfraujoch and cruise on Lake Lucerne.",
                "destinations": ["switzerland"],
                "categories": ["nature", "luxury"],
                "airline_code": "EK",
                "duration_days": 8,
                "duration_nights": 5,
                "hotel_stars_min": 4,
                "hotel_stars_max": 4,
                "total_meals": 12,
                "plane_meals": True,
                "price_from": Decimal("69900"),
                "locations": [
                    "Zurich",
                    "Lucerne",
                    "Interlaken",
                    "Jungfraujoch",
                    "Bern",
                ],
                "includes": "Round-trip flights (Emirates via Dubai)\n5 nights 4-star hotel\n12 meals\nSwiss Travel Pass\nAll transfers\nGuide",
                "excludes": "Travel insurance\nSchengen visa fee\nPersonal expenses",
                "departures": [
                    {
                        "date_offset": 50,
                        "price": Decimal("69900"),
                        "seats": 20,
                        "deposit": Decimal("20000"),
                    },
                ],
                "itinerary": [],
            },
            {
                "title": "Taiwan Round Island 5D4N",
                "title_th": "ไต้หวัน รอบเกาะ 5วัน4คืน",
                "product_code": "ZGTWN-2508SL",
                "slug": "taiwan-round-island-5d4n",
                "highlight": "Taipei 101, Jiufen Old Street, Sun Moon Lake, Taroko Gorge, night markets.",
                "description": "Circle Taiwan's greatest hits — from Taipei's vibrant night markets to the stunning Taroko Gorge and scenic Sun Moon Lake.",
                "destinations": ["taiwan"],
                "categories": ["cultural", "city", "food-wine"],
                "airline_code": "SL",
                "duration_days": 5,
                "duration_nights": 4,
                "hotel_stars_min": 3,
                "hotel_stars_max": 4,
                "total_meals": 8,
                "plane_meals": False,
                "price_from": Decimal("19900"),
                "locations": [
                    "Taipei",
                    "Jiufen",
                    "Sun Moon Lake",
                    "Taichung",
                    "Hualien",
                ],
                "includes": "Round-trip flights (Thai Lion Air)\n4 nights hotel\n8 meals\nAll transfers\nGuide",
                "excludes": "Travel insurance\nPersonal expenses\nTips",
                "departures": [
                    {
                        "date_offset": 20,
                        "price": Decimal("19900"),
                        "seats": 30,
                        "deposit": Decimal("7000"),
                    },
                    {
                        "date_offset": 45,
                        "price": Decimal("20900"),
                        "seats": 30,
                        "deposit": Decimal("7000"),
                    },
                ],
                "itinerary": [],
            },
            {
                "title": "Italy Classic 9D6N",
                "title_th": "อิตาลี คลาสสิค 9วัน6คืน",
                "product_code": "ZGITA-2509EK",
                "slug": "italy-classic-9d6n",
                "highlight": "Rome Colosseum, Vatican, Florence Duomo, Venice gondola, Leaning Tower of Pisa.",
                "description": "The ultimate Italian experience — from Rome's ancient ruins to Florence's Renaissance art and Venice's romantic canals.",
                "destinations": ["italy"],
                "categories": ["cultural", "luxury", "food-wine"],
                "airline_code": "EK",
                "duration_days": 9,
                "duration_nights": 6,
                "hotel_stars_min": 4,
                "hotel_stars_max": 4,
                "total_meals": 14,
                "plane_meals": True,
                "price_from": Decimal("59900"),
                "locations": ["Rome", "Florence", "Pisa", "Venice", "Milan"],
                "includes": "Round-trip flights (Emirates)\n6 nights 4-star hotel\n14 meals\nAll transfers and train tickets\nGuide",
                "excludes": "Travel insurance\nSchengen visa\nGondola ride (optional)\nPersonal expenses",
                "departures": [
                    {
                        "date_offset": 55,
                        "price": Decimal("59900"),
                        "seats": 20,
                        "deposit": Decimal("20000"),
                    },
                ],
                "itinerary": [],
            },
            {
                "title": "Hokkaido Lavender 7D5N",
                "title_th": "ฮอกไกโด ลาเวนเดอร์ 7วัน5คืน",
                "product_code": "ZGJPN-2510TG",
                "slug": "hokkaido-lavender-7d5n",
                "highlight": "Farm Tomita lavender fields, Blue Pond, Otaru Canal, Sapporo beer garden, fresh seafood market.",
                "description": "Summer in Hokkaido — endless lavender fields, fresh seafood, charming port towns, and the vibrant city of Sapporo.",
                "destinations": ["japan"],
                "categories": ["nature", "food-wine"],
                "airline_code": "TG",
                "duration_days": 7,
                "duration_nights": 5,
                "hotel_stars_min": 3,
                "hotel_stars_max": 4,
                "total_meals": 10,
                "plane_meals": True,
                "price_from": Decimal("42900"),
                "locations": ["Sapporo", "Furano", "Biei", "Otaru", "Noboribetsu"],
                "includes": "Round-trip flights (Thai Airways)\n5 nights hotel\n10 meals\nAll transfers\nGuide\nEntrance fees",
                "excludes": "Travel insurance\nPersonal expenses\nTips",
                "departures": [
                    {
                        "date_offset": 60,
                        "price": Decimal("42900"),
                        "seats": 25,
                        "deposit": Decimal("15000"),
                    },
                    {
                        "date_offset": 75,
                        "price": Decimal("44900"),
                        "seats": 25,
                        "deposit": Decimal("15000"),
                        "promo": Decimal("39900"),
                    },
                ],
                "itinerary": [],
            },
            {
                "title": "Beijing Great Wall 5D4N",
                "title_th": "ปักกิ่ง กำแพงเมืองจีน 5วัน4คืน",
                "product_code": "ZGCHN-2511TG",
                "slug": "beijing-great-wall-5d4n",
                "highlight": "Great Wall of China, Forbidden City, Temple of Heaven, Peking duck feast.",
                "description": "Walk on the Great Wall, explore the Forbidden City, and feast on authentic Peking duck in China's historic capital.",
                "destinations": ["china"],
                "categories": ["cultural", "city"],
                "airline_code": "TG",
                "duration_days": 5,
                "duration_nights": 4,
                "hotel_stars_min": 4,
                "hotel_stars_max": 5,
                "total_meals": 8,
                "plane_meals": True,
                "price_from": Decimal("18900"),
                "locations": ["Beijing"],
                "includes": "Round-trip flights (Thai Airways)\n4 nights hotel\n8 meals\nAll transfers\nGuide\nVisa assistance",
                "excludes": "Visa fee\nTravel insurance\nPersonal expenses",
                "departures": [
                    {
                        "date_offset": 30,
                        "price": Decimal("18900"),
                        "seats": 30,
                        "deposit": Decimal("8000"),
                    },
                    {
                        "date_offset": 50,
                        "price": Decimal("19900"),
                        "seats": 30,
                        "deposit": Decimal("8000"),
                    },
                ],
                "itinerary": [],
            },
        ]

        for td in tours_data:
            tour, created = Tour.objects.get_or_create(
                slug=td["slug"],
                defaults={
                    "title": td["title"],
                    "title_th": td.get("title_th", ""),
                    "product_code": td.get("product_code"),
                    "highlight": td.get("highlight", ""),
                    "highlight_th": td.get("highlight_th", ""),
                    "description": td.get("description", ""),
                    "short_description": td.get("highlight", "")[:500],
                    "airline": airlines.get(td.get("airline_code")),
                    "duration_days": td.get("duration_days"),
                    "duration_nights": td.get("duration_nights"),
                    "hotel_stars_min": td.get("hotel_stars_min"),
                    "hotel_stars_max": td.get("hotel_stars_max"),
                    "total_meals": td.get("total_meals"),
                    "plane_meals": td.get("plane_meals", False),
                    "price_from": td.get("price_from"),
                    "locations": td.get("locations", []),
                    "includes": td.get("includes", ""),
                    "excludes": td.get("excludes", ""),
                    "status": Tour.Status.PUBLISHED,
                    "is_featured": td.get("slug")
                    in [
                        "tokyo-osaka-classic-6d4n",
                        "hong-kong-macau-4d3n",
                        "turkey-highlights-10d7n",
                        "hokkaido-lavender-7d5n",
                    ],
                    "source": "seed",
                },
            )

            if not created:
                self.stdout.write(f"  Skipping existing: {tour.title}")
                continue

            # Destinations
            for dest_slug in td.get("destinations", []):
                if dest_slug in destinations:
                    tour.destinations.add(destinations[dest_slug])

            # Categories
            for cat_slug in td.get("categories", []):
                if cat_slug in categories:
                    tour.categories.add(categories[cat_slug])

            # Departures
            today = date.today()
            for dep in td.get("departures", []):
                dep_date = today + timedelta(days=dep["date_offset"])
                ret_date = dep_date + timedelta(days=td.get("duration_days", 5) - 1)
                TourDeparture.objects.create(
                    tour=tour,
                    departure_date=dep_date,
                    return_date=ret_date,
                    price_adult=dep["price"],
                    price_child=dep["price"] - Decimal("2000"),
                    price_child_no_bed=dep["price"] - Decimal("3000"),
                    price_infant=dep["price"] - Decimal("5000"),
                    price_single_supplement=Decimal("5000"),
                    deposit=dep.get("deposit", Decimal("10000")),
                    group_size=dep.get("seats", 25),
                    seats_available=dep.get("seats", 25),
                    status=TourDeparture.PeriodStatus.AVAILABLE,
                    price_adult_promo=dep.get("promo"),
                    departure_airport="SUVARNABHUMI",
                )

            # Itinerary
            for it in td.get("itinerary", []):
                ItineraryDay.objects.create(
                    tour=tour,
                    day_number=it["day"],
                    title=it["title"],
                    title_th=it.get("title_th", ""),
                    description=it.get("desc", ""),
                    breakfast=it.get("breakfast", ""),
                    breakfast_description=it.get("breakfast_desc", ""),
                    lunch=it.get("lunch", ""),
                    lunch_description=it.get("lunch_desc", ""),
                    dinner=it.get("dinner", ""),
                    dinner_description=it.get("dinner_desc", ""),
                    hotel_name=it.get("hotel", ""),
                    hotel_stars=it.get("stars"),
                )

            action = "Created" if created else "Updated"
            self.stdout.write(f"  {action}: {tour.title}")

        self.stdout.write(
            self.style.SUCCESS(f"\nDone! {Tour.objects.count()} tours in database.")
        )
