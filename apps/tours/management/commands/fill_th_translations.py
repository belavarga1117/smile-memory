"""Fill missing Thai translations for Destination, Category, and Airline models."""

from django.core.management.base import BaseCommand

from apps.tours.models import Airline, Category, Destination

DESTINATION_TH = {
    "America": "อเมริกา",
    "Australia": "ออสเตรเลีย",
    "China": "จีน",
    "Egypt": "อียิปต์",
    "England": "อังกฤษ",
    "Europe": "ยุโรป",
    "France": "ฝรั่งเศส",
    "Georgia": "จอร์เจีย",
    "Hong Kong": "ฮ่องกง",
    "Hungary": "ฮังการี",
    "India": "อินเดีย",
    "Italy": "อิตาลี",
    "Japan": "ญี่ปุ่น",
    "Jordan": "จอร์แดน",
    "Kazakhstan": "คาซัคสถาน",
    "Macao": "มาเก๊า",
    "Nepal": "เนปาล",
    "Philippines": "ฟิลิปปินส์",
    "Scandinavia": "สแกนดิเนเวีย",
    "Singapore": "สิงคโปร์",
    "South Africa": "แอฟริกาใต้",
    "South Korea": "เกาหลีใต้",
    "Switzerland": "สวิตเซอร์แลนด์",
    "Taiwan": "ไต้หวัน",
    "Turkey": "ตุรกี",
    "Turkiye": "ตุรกี",
    "Vietnam": "เวียดนาม",
    # Common destinations from wholesaler imports
    "Thailand": "ไทย",
    "Cambodia": "กัมพูชา",
    "Laos": "ลาว",
    "Myanmar": "เมียนมาร์",
    "Malaysia": "มาเลเซีย",
    "Indonesia": "อินโดนีเซีย",
    "Bali": "บาหลี",
    "Phuket": "ภูเก็ต",
    "Chiang Mai": "เชียงใหม่",
    "Krabi": "กระบี่",
    "Dubai": "ดูไบ",
    "Maldives": "มัลดีฟส์",
    "Sri Lanka": "ศรีลังกา",
    "Bangladesh": "บังกลาเทศ",
    "Pakistan": "ปากีสถาน",
    "Russia": "รัสเซีย",
    "Greece": "กรีซ",
    "Spain": "สเปน",
    "Portugal": "โปรตุเกส",
    "Germany": "เยอรมนี",
    "Austria": "ออสเตรีย",
    "Czech Republic": "สาธารณรัฐเช็ก",
    "Czechia": "เช็กเกีย",
    "Netherlands": "เนเธอร์แลนด์",
    "Belgium": "เบลเยียม",
    "Poland": "โปแลนด์",
    "Croatia": "โครเอเชีย",
    "Iceland": "ไอซ์แลนด์",
    "Norway": "นอร์เวย์",
    "Sweden": "สวีเดน",
    "Finland": "ฟินแลนด์",
    "Denmark": "เดนมาร์ก",
    "United Kingdom": "สหราชอาณาจักร",
    "Scotland": "สกอตแลนด์",
    "Ireland": "ไอร์แลนด์",
    "Morocco": "โมร็อกโก",
    "Kenya": "เคนยา",
    "Tanzania": "แทนซาเนีย",
    "South America": "อเมริกาใต้",
    "Brazil": "บราซิล",
    "Peru": "เปรู",
    "Mexico": "เม็กซิโก",
    "Canada": "แคนาดา",
    "New Zealand": "นิวซีแลนด์",
    "Uzbekistan": "อุซเบกิสถาน",
    "Azerbaijan": "อาเซอร์ไบจาน",
    "Armenia": "อาร์เมเนีย",
    "Israel": "อิสราเอล",
    "Saudi Arabia": "ซาอุดีอาระเบีย",
    "Qatar": "กาตาร์",
    "Oman": "โอมาน",
    "Bhutan": "ภูฏาน",
    "Tibet": "ทิเบต",
    "Mongolia": "มองโกเลีย",
}

CATEGORY_TH = {
    "Adventure": "ผจญภัย",
    "Beach": "ชายหาด",
    "City": "เมือง",
    "Cultural": "วัฒนธรรม",
    "Food & Wine": "อาหารและไวน์",
    "Luxury": "หรูหรา",
    "Nature": "ธรรมชาติ",
    "Shopping": "ช้อปปิ้ง",
    "Honeymoon": "ฮันนีมูน",
    "Family": "ครอบครัว",
    "Group Tour": "ทัวร์กรุ๊ป",
    "Private Tour": "ทัวร์ส่วนตัว",
    "Budget": "ประหยัด",
    "Cruise": "ล่องเรือ",
    "Ski & Snow": "สกีและหิมะ",
}

AIRLINE_TH = {
    "Thai Airways": "การบินไทย",
    "Thai Lion Air": "ไทยไลออนแอร์",
    "Bangkok Airways": "บางกอกแอร์เวย์ส",
    "AirAsia": "แอร์เอเชีย",
    "Thai AirAsia": "ไทยแอร์เอเชีย",
    "Nok Air": "นกแอร์",
    "VietJet Air": "เวียตเจ็ทแอร์",
    "Korean Air": "โคเรียนแอร์",
    "Asiana Airlines": "อาซีอาน่าแอร์ไลน์ส",
    "Japan Airlines": "เจแปนแอร์ไลน์ส",
    "All Nippon Airways": "ออลนิปปอนแอร์เวย์ส",
    "ANA": "เอเอ็นเอ",
    "JAL": "เจเอแอล",
    "Cathay Pacific": "คาเธ่ย์แปซิฟิก",
    "Singapore Airlines": "สิงคโปร์แอร์ไลน์ส",
    "Malaysia Airlines": "มาเลเซียแอร์ไลน์ส",
    "Eva Air": "อีวาแอร์",
    "China Airlines": "ไชน่าแอร์ไลน์ส",
    "China Eastern": "ไชน่าอีสเทิร์น",
    "China Southern": "ไชน่าเซาเทิร์น",
    "Air China": "แอร์ไชน่า",
    "Emirates": "เอมิเรตส์",
    "Qatar Airways": "กาตาร์แอร์เวย์ส",
    "Turkish Airlines": "เตอร์กิชแอร์ไลน์ส",
    "Etihad Airways": "เอทิฮัดแอร์เวย์ส",
    "Lufthansa": "ลุฟท์ฮันซา",
    "Air France": "แอร์ฟรองซ์",
    "British Airways": "บริติชแอร์เวย์ส",
    "Swiss International": "สวิสอินเตอร์เนชันแนล",
    "Royal Jordanian": "รอยัลจอร์แดเนียน",
    "IndiGo": "อินดิโก้",
    "Air India": "แอร์อินเดีย",
    "Scoot": "สกู๊ต",
    "Jeju Air": "เจจูแอร์",
    "Jin Air": "จินแอร์",
    "T'way Air": "ทีเวย์แอร์",
    "Philippine Airlines": "ฟิลิปปินส์แอร์ไลน์ส",
    "Cebu Pacific": "เซบูแปซิฟิก",
    "Garuda Indonesia": "การูด้าอินโดนีเซีย",
    "Vietnam Airlines": "เวียตนามแอร์ไลน์ส",
    "Bamboo Airways": "แบมบูแอร์เวย์ส",
    "Finnair": "ฟินแอร์",
    "SAS": "เอสเอเอส",
    "Various Airlines": "หลายสายการบิน",
    "TBA": "ยังไม่กำหนด",
    # IATA codes (stored by scraper imports)
    "3U": "เสฉวนแอร์ไลน์ส",      # Sichuan Airlines
    "5J": "เซบูแปซิฟิก",          # Cebu Pacific
    "AI": "แอร์อินเดีย",           # Air India
    "AQ": "9 แอร์",               # 9 Air
    "BR": "อีวาแอร์",             # Eva Air
    "CA": "แอร์ไชน่า",            # Air China
    "CI": "ไชน่าแอร์ไลน์ส",       # China Airlines
    "CZ": "ไชน่าเซาเทิร์น",       # China Southern
    "DR": "รุยลี่แอร์ไลน์ส",      # Ruili Airlines
    "E9": "อีเอ็นไอแอร์",         # ENI Air
    "ET": "เอธิโอเปียนแอร์ไลน์ส", # Ethiopian Airlines
    "EU": "เฉิงตูแอร์ไลน์ส",      # Chengdu Airlines
    "EY": "เอทิฮัดแอร์เวย์ส",     # Etihad Airways
    "FD": "ไทยแอร์เอเชีย",        # Thai AirAsia
    "FM": "เซี่ยงไฮ้แอร์ไลน์ส",   # Shanghai Airlines
    "GF": "กัลฟ์แอร์",            # Gulf Air
    "GJ": "กรีนแลนด์แอร์",        # Loong Air (GJ)
    "HO": "จุนเหยาแอร์ไลน์ส",     # Juneyao Airlines
    "HU": "ไหหนานแอร์ไลน์ส",      # Hainan Airlines
    "HX": "ฮ่องกงแอร์ไลน์ส",      # Hong Kong Airlines
    "JX": "สตาร์ลักซ์แอร์ไลน์ส",  # Starlux Airlines
    "KC": "แอร์อัสตาน่า",          # Air Astana
    "KY": "คุนหมิงแอร์ไลน์ส",     # Kunming Airlines
    "LX": "สวิสอินเตอร์เนชันแนล",  # SWISS
    "MM": "พีชแอวิเอชัน",          # Peach Aviation
    "MU": "ไชน่าอีสเทิร์น",        # China Eastern
    "NH": "ออลนิปปอนแอร์เวย์ส",    # ANA
    "NX": "แอร์มาเก๊า",           # Air Macau
    "OS": "ออสเตรียนแอร์ไลน์ส",    # Austrian Airlines
    "OZ": "อาซีอาน่าแอร์ไลน์ส",   # Asiana Airlines
    "QR": "กาตาร์แอร์เวย์ส",       # Qatar Airways
    "QW": "บลูวิงแอร์ไลน์ส",       # Blue Wing / Qingdao Airlines
    "RJ": "รอยัลจอร์แดเนียน",      # Royal Jordanian
    "SC": "ชานตงแอร์ไลน์ส",        # Shandong Airlines
    "SQ": "สิงคโปร์แอร์ไลน์ส",     # Singapore Airlines
    "SV": "เซาดี",                 # Saudia
    "UQ": "ยูเนี่ยนแอร์",           # Union Air (UQ)
    "VJ": "เวียตเจ็ทแอร์",         # VietJet Air
    "VN": "เวียตนามแอร์ไลน์ส",     # Vietnam Airlines
    "XJ": "ไทยแอร์เอเชียเอ็กซ์",   # Thai AirAsia X
}


class Command(BaseCommand):
    help = "Fill missing Thai translations for Destination, Category, and Airline"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be updated without saving",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN — nem ment semmit\n"))

        self._fill_model(Destination, "name", "name_th", DESTINATION_TH, dry_run)
        self._fill_model(Category, "name", "name_th", CATEGORY_TH, dry_run)
        self._fill_model(Airline, "name", "name_th", AIRLINE_TH, dry_run)

    def _fill_model(self, model, en_field, th_field, mapping, dry_run):
        model_name = model.__name__
        updated = 0
        skipped = 0
        unknown = []

        for obj in model.objects.all():
            en_value = getattr(obj, en_field)
            th_value = getattr(obj, th_field)

            if th_value:
                skipped += 1
                continue

            if en_value in mapping:
                new_th = mapping[en_value]
                if not dry_run:
                    setattr(obj, th_field, new_th)
                    obj.save(update_fields=[th_field])
                self.stdout.write(f"  {'[DRY] ' if dry_run else ''}✅ {model_name}: {en_value} → {new_th}")
                updated += 1
            else:
                unknown.append(en_value)

        self.stdout.write(
            self.style.SUCCESS(f"\n{model_name}: {updated} frissítve, {skipped} már megvolt")
        )
        if unknown:
            self.stdout.write(
                self.style.WARNING(f"  Ismeretlen (kézi fordítás kell): {', '.join(unknown)}")
            )
