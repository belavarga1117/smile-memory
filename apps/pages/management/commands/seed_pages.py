"""Seed homepage content: hero slides, testimonials, trust badges, FAQs, and blog posts."""

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.blog.models import BlogCategory, BlogPost, Tag
from apps.pages.models import FAQ, HeroSlide, Testimonial, TrustBadge


class Command(BaseCommand):
    help = "Seed homepage content and sample blog posts"

    def handle(self, *args, **options):
        self._seed_hero_slides()
        self._seed_trust_badges()
        self._seed_testimonials()
        self._seed_faqs()
        self._seed_blog()
        self.stdout.write(self.style.SUCCESS("Homepage + blog seed data created."))

    def _seed_hero_slides(self):
        slides = [
            {
                "title": "Discover Japan's Cherry Blossoms",
                "title_th": "ค้นพบดอกซากุระแห่งญี่ปุ่น",
                "subtitle": "Experience the magic of sakura season with our curated group tours",
                "subtitle_th": "สัมผัสความมหัศจรรย์ของฤดูซากุระกับทัวร์กรุ๊ปคัดสรร",
                "cta_text": "View Japan Tours",
                "cta_text_th": "ดูทัวร์ญี่ปุ่น",
                "cta_url": "/tours/?destination=japan",
                "sort_order": 1,
            },
            {
                "title": "Explore the Wonders of China",
                "title_th": "สำรวจมหัศจรรย์แห่งจีน",
                "subtitle": "From the Great Wall to ancient temples — unforgettable adventures await",
                "subtitle_th": "จากกำแพงเมืองจีนถึงวัดโบราณ — การผจญภัยที่ไม่มีวันลืมรอคุณอยู่",
                "cta_text": "View China Tours",
                "cta_text_th": "ดูทัวร์จีน",
                "cta_url": "/tours/?destination=china",
                "sort_order": 2,
            },
            {
                "title": "Your Journey, Our Memory",
                "title_th": "การเดินทางของคุณ ความทรงจำของเรา",
                "subtitle": "Premium group tours across Asia and beyond at unbeatable prices",
                "subtitle_th": "ทัวร์กรุ๊ปพรีเมียมทั่วเอเชียและทั่วโลกในราคาที่ดีที่สุด",
                "cta_text": "Explore All Tours",
                "cta_text_th": "สำรวจทัวร์ทั้งหมด",
                "cta_url": "/tours/",
                "sort_order": 3,
            },
        ]
        for s in slides:
            HeroSlide.objects.get_or_create(title=s["title"], defaults=s)
        self.stdout.write(f"  Created {len(slides)} hero slides")

    def _seed_trust_badges(self):
        badges = [
            {
                "icon": "✈️",
                "value": "500+",
                "label": "Tour Packages",
                "label_th": "แพ็คเกจทัวร์",
                "sort_order": 1,
            },
            {
                "icon": "😊",
                "value": "10,000+",
                "label": "Happy Travelers",
                "label_th": "นักท่องเที่ยวมีความสุข",
                "sort_order": 2,
            },
            {
                "icon": "🌏",
                "value": "30+",
                "label": "Destinations",
                "label_th": "จุดหมายปลายทาง",
                "sort_order": 3,
            },
            {
                "icon": "⭐",
                "value": "4.9/5",
                "label": "Customer Rating",
                "label_th": "คะแนนจากลูกค้า",
                "sort_order": 4,
            },
        ]
        for b in badges:
            TrustBadge.objects.get_or_create(value=b["value"], defaults=b)
        self.stdout.write(f"  Created {len(badges)} trust badges")

    def _seed_testimonials(self):
        testimonials = [
            {
                "name": "Somchai P.",
                "name_th": "สมชาย พ.",
                "location": "Bangkok, Thailand",
                "quote": "Our Japan trip with Smile Memory was absolutely incredible! The itinerary was well-planned, hotels were great, and our guide was so knowledgeable. Will definitely book again.",
                "quote_th": "ทริปญี่ปุ่นกับ Smile Memory สุดยอดมาก! โปรแกรมวางแผนมาดี โรงแรมดี และไกด์มีความรู้มาก จะจองอีกแน่นอน",
                "tour_name": "Tokyo Osaka Classic",
                "rating": 5,
                "sort_order": 1,
            },
            {
                "name": "Sarah L.",
                "location": "Chiang Mai, Thailand",
                "quote": "Best value for money! We compared prices from many agencies and Smile Memory offered the best package. The China tour was well organized from start to finish.",
                "tour_name": "Beijing Great Wall",
                "rating": 5,
                "sort_order": 2,
            },
            {
                "name": "Nattaya K.",
                "name_th": "ณัฐญา ก.",
                "location": "Phuket, Thailand",
                "quote": "Very responsive team — they answered all my questions on LINE within minutes. The Turkey tour was a dream come true. Hotels, food, everything was top quality.",
                "quote_th": "ทีมตอบเร็วมาก — ตอบทุกคำถามทาง LINE ภายในไม่กี่นาที ทัวร์ตุรกีเหมือนฝันเป็นจริง โรงแรม อาหาร ทุกอย่างคุณภาพสุดยอด",
                "tour_name": "Turkey Highlights",
                "rating": 5,
                "sort_order": 3,
            },
            {
                "name": "Michael T.",
                "location": "Bangkok, Thailand",
                "quote": "This was my first group tour and I was nervous, but the Smile Memory team made everything smooth. Great communication before, during, and after the trip.",
                "tour_name": "Hong Kong Macau",
                "rating": 4,
                "sort_order": 4,
            },
            {
                "name": "Pranee S.",
                "name_th": "ปราณี ส.",
                "location": "Nonthaburi, Thailand",
                "quote": "ไปฮอกไกโดกับ Smile Memory ช่วงลาเวนเดอร์บาน สวยมากจริงๆ โรงแรม 4 ดาว อาหารอร่อย ไกด์ใส่ใจ แนะนำเลยค่ะ",
                "tour_name": "Hokkaido Lavender",
                "rating": 5,
                "sort_order": 5,
            },
            {
                "name": "David W.",
                "location": "Pattaya, Thailand",
                "quote": "Booked the Vietnam tour for my family. Everything was well arranged — flights, hotels, sightseeing. The kids loved it! Already planning our next trip with them.",
                "tour_name": "Vietnam Hanoi Sapa",
                "rating": 5,
                "sort_order": 6,
            },
        ]
        for t in testimonials:
            Testimonial.objects.get_or_create(name=t["name"], defaults=t)
        self.stdout.write(f"  Created {len(testimonials)} testimonials")

    def _seed_faqs(self):
        faqs = [
            {
                "question": "How do I book a tour?",
                "question_th": "จองทัวร์อย่างไร?",
                "answer": "Simply browse our tours, select the one you like, and submit an inquiry. Our team will confirm availability and send you booking details via email within 24 hours.",
                "answer_th": "เพียงเลือกดูทัวร์ เลือกทัวร์ที่ชอบ แล้วส่งแบบสอบถาม ทีมของเราจะยืนยันที่นั่งว่างและส่งรายละเอียดการจองทางอีเมลภายใน 24 ชั่วโมง",
                "sort_order": 1,
            },
            {
                "question": "What payment methods do you accept?",
                "question_th": "รับชำระเงินวิธีใดบ้าง?",
                "answer": "We accept bank transfers (Thai bank accounts). After your booking is confirmed, we'll provide our bank details along with payment instructions.",
                "answer_th": "เรารับชำระเงินผ่านการโอนเงินผ่านธนาคาร (บัญชีธนาคารไทย) หลังจากการจองได้รับการยืนยัน เราจะส่งรายละเอียดบัญชีธนาคารพร้อมคำแนะนำการชำระเงิน",
                "sort_order": 2,
            },
            {
                "question": "Can I cancel or change my booking?",
                "question_th": "สามารถยกเลิกหรือเปลี่ยนแปลงการจองได้หรือไม่?",
                "answer": "Cancellations are subject to the following fees based on days before departure: more than 45 days — deposit only (50%); 30–44 days — 50% of total price; 15–29 days — 75%; 0–14 days or no-show — no refund. Refunds are processed within 30 calendar days of cancellation confirmation. Some tours may have different policies — we will confirm at booking. To request a change or cancellation, contact us at baifern@smilememorytravel.com.",
                "answer_th": "การยกเลิกมีค่าธรรมเนียมตามจำนวนวันก่อนออกเดินทาง: มากกว่า 45 วัน — สูญเสียมัดจำ (50%); 30–44 วัน — 50% ของราคารวม; 15–29 วัน — 75%; 0–14 วัน หรือไม่มาปรากฏตัว — ไม่คืนเงิน การคืนเงินดำเนินการภายใน 30 วันตามปฏิทินนับจากวันยืนยันการยกเลิก บางทัวร์อาจมีเงื่อนไขต่างออกไป — เราจะยืนยันเมื่อทำการจอง",
                "sort_order": 3,
            },
            {
                "question": "What if Smile Memory cancels my tour?",
                "question_th": "หาก Smile Memory ยกเลิกทัวร์ของฉัน จะเกิดอะไรขึ้น?",
                "answer": "If we or our wholesaler partner cancel a confirmed booking for commercial reasons (including insufficient passenger numbers), we will notify you as soon as possible and offer either a full refund of all amounts paid, or a replacement departure of equivalent value — the choice is yours. Cancellations due to force majeure (natural disasters, pandemics, government travel bans) are handled separately per our Terms of Service.",
                "answer_th": "หากเราหรือพาร์ทเนอร์บริษัทขายส่งต้องยกเลิกการจองที่ยืนยันแล้วด้วยเหตุผลทางธุรกิจ (รวมถึงกรณีจำนวนผู้เดินทางไม่ครบ) เราจะแจ้งให้ทราบโดยเร็วที่สุด และเสนอทางเลือก: คืนเงินทั้งหมดที่ชำระแล้ว หรือวันเดินทางทดแทนที่มีมูลค่าเทียบเท่า — เป็นสิทธิ์ของคุณในการเลือก กรณียกเลิกเนื่องจากเหตุสุดวิสัย (ภัยธรรมชาติ โรคระบาด คำสั่งห้ามเดินทาง) ดำเนินการตามเงื่อนไขการให้บริการของเรา",
                "sort_order": 4,
            },
            {
                "question": "Do I need a visa for the tour?",
                "question_th": "ต้องทำวีซ่าสำหรับทัวร์หรือไม่?",
                "answer": "Visa requirements depend on your nationality and destination. We'll inform you about visa requirements when your booking is confirmed. For some destinations, we can assist with group visa applications.",
                "answer_th": "ข้อกำหนดวีซ่าขึ้นอยู่กับสัญชาติและจุดหมายปลายทาง เราจะแจ้งให้ทราบเกี่ยวกับข้อกำหนดวีซ่าเมื่อการจองได้รับการยืนยัน สำหรับบางจุดหมาย เราสามารถช่วยยื่นวีซ่ากรุ๊ปได้",
                "sort_order": 5,
            },
            {
                "question": "What is included in the tour price?",
                "question_th": "ราคาทัวร์รวมอะไรบ้าง?",
                "answer": "Most packages include accommodation, daily meals (as per itinerary), local transportation, and entrance fees. Round-trip flights are included in many packages but not all — the exact inclusions and exclusions are listed on each tour page and confirmed in your quotation. Tips, personal expenses, and optional activities are typically not included.",
                "answer_th": "แพ็กเกจส่วนใหญ่รวมที่พัก อาหารตามโปรแกรม การเดินทางภายใน และค่าเข้าชมสถานที่ ตั๋วเครื่องบินไป-กลับรวมในบางแพ็กเกจแต่ไม่ใช่ทั้งหมด — รายละเอียดที่รวมและไม่รวมระบุในหน้าทัวร์และยืนยันในใบเสนอราคา ค่าทิป ค่าใช้จ่ายส่วนตัว และกิจกรรมเสริมโดยทั่วไปไม่รวมในราคา",
                "sort_order": 6,
            },
            {
                "question": "Is travel insurance included?",
                "question_th": "รวมประกันการเดินทางหรือไม่?",
                "answer": "Travel insurance is not included in the tour price. We strongly recommend purchasing travel insurance before your trip. We can recommend insurance providers upon request.",
                "answer_th": "ประกันการเดินทางไม่รวมในราคาทัวร์ เราแนะนำอย่างยิ่งให้ซื้อประกันการเดินทางก่อนเดินทาง เราสามารถแนะนำบริษัทประกันได้",
                "sort_order": 7,
            },
            {
                "question": "What is the group size?",
                "question_th": "ขนาดกรุ๊ปเท่าไหร่?",
                "answer": "Group sizes typically range from 15–40 people depending on the tour. You can see available seats for each departure date on the tour detail page. If a minimum number of passengers is not reached for a departure, the wholesaler may cancel that date — in which case we will offer a full refund or an alternative departure.",
                "answer_th": "ขนาดกรุ๊ปโดยทั่วไปอยู่ที่ 15–40 คน ขึ้นอยู่กับทัวร์ คุณสามารถดูที่นั่งว่างสำหรับแต่ละวันเดินทางได้ในหน้ารายละเอียดทัวร์ หากจำนวนผู้เดินทางไม่ครบตามที่กำหนดสำหรับวันเดินทางใด บริษัทขายส่งอาจยกเลิกวันนั้น — ในกรณีดังกล่าวเราจะเสนอคืนเงินทั้งหมดหรือวันเดินทางทดแทน",
                "sort_order": 8,
            },
            {
                "question": "How do I contact you?",
                "question_th": "ติดต่อได้อย่างไร?",
                "answer": "You can reach us via LINE (fastest), phone, email, or the contact form on our website. Our team typically responds within a few hours during business hours.",
                "answer_th": "คุณสามารถติดต่อเราทาง LINE (เร็วที่สุด) โทรศัพท์ อีเมล หรือแบบฟอร์มติดต่อบนเว็บไซต์ ทีมของเราตอบกลับภายในไม่กี่ชั่วโมงในเวลาทำการ",
                "sort_order": 9,
            },
            {
                "question": "Is Smile Memory a tour operator?",
                "question_th": "Smile Memory เป็นบริษัทนำเที่ยวหรือตัวแทนจำหน่าย?",
                "answer": "No — Smile Memory Tour Co., Ltd. is a licensed tour reseller (TAT License 11/08172), not a tour operator. We act as an intermediary: we source and sell group tour packages from licensed wholesalers (Zego, GS25, Go365, Real Journey). The wholesaler operates the tour itself (hotels, transport, guides). This means we can negotiate competitive prices and handle your booking, while the operational experience is delivered by our vetted wholesaler partners.",
                "answer_th": "ไม่ใช่ — บริษัท สไมล์ เมมโมรี่ ทัวร์ จำกัด เป็นตัวแทนจำหน่ายทัวร์ที่ได้รับอนุญาต (ใบอนุญาตนำเที่ยว 11/08172) ไม่ใช่บริษัทนำเที่ยวโดยตรง เราทำหน้าที่เป็นตัวกลาง: จำหน่ายแพ็กเกจทัวร์กรุ๊ปจากบริษัทขายส่งที่ได้รับอนุญาต (Zego, GS25, Go365, Real Journey) การดำเนินงานทัวร์จริง (โรงแรม รถ มัคคุเทศก์) เป็นหน้าที่ของบริษัทขายส่ง เราช่วยคุณได้ราคาดีและดูแลการจอง ขณะที่ประสบการณ์ทัวร์จริงส่งมอบโดยพาร์ทเนอร์ขายส่งที่ผ่านการคัดกรองของเรา",
                "sort_order": 10,
            },
        ]
        for f in faqs:
            FAQ.objects.update_or_create(question=f["question"], defaults=f)
        self.stdout.write(f"  Upserted {len(faqs)} FAQs")

    def _seed_blog(self):
        # Categories
        cats = {
            "tips": BlogCategory.objects.get_or_create(
                slug="travel-tips",
                defaults={
                    "name": "Travel Tips",
                    "name_th": "เคล็ดลับการเดินทาง",
                    "sort_order": 1,
                },
            )[0],
            "guides": BlogCategory.objects.get_or_create(
                slug="destination-guides",
                defaults={
                    "name": "Destination Guides",
                    "name_th": "คู่มือจุดหมายปลายทาง",
                    "sort_order": 2,
                },
            )[0],
            "news": BlogCategory.objects.get_or_create(
                slug="travel-news",
                defaults={
                    "name": "Travel News",
                    "name_th": "ข่าวท่องเที่ยว",
                    "sort_order": 3,
                },
            )[0],
        }

        # Tags
        tag_names = [
            "Japan",
            "China",
            "Korea",
            "Packing",
            "Budget",
            "Food",
            "Culture",
            "Photography",
        ]
        tags = {}
        for t in tag_names:
            tags[t.lower()], _ = Tag.objects.get_or_create(
                slug=t.lower(), defaults={"name": t}
            )

        now = timezone.now()

        posts = [
            {
                "title": "10 Essential Packing Tips for Group Tours in Asia",
                "title_th": "10 เคล็ดลับจัดกระเป๋าสำหรับทัวร์กรุ๊ปในเอเชีย",
                "slug": "packing-tips-group-tours-asia",
                "excerpt": "Packing for a group tour doesn't have to be stressful. Here are our top tips to help you pack smart and travel light.",
                "excerpt_th": "การจัดกระเป๋าสำหรับทัวร์กรุ๊ปไม่จำเป็นต้องเครียด นี่คือเคล็ดลับยอดเยี่ยมที่จะช่วยให้คุณจัดกระเป๋าอย่างชาญฉลาด",
                "body_th": """## จัดกระเป๋าอย่างชาญฉลาด เดินทางอย่างมีความสุข

ทัวร์กรุ๊ปเป็นหนึ่งในวิธีที่ดีที่สุดในการสำรวจเอเชีย แต่การจัดกระเป๋าอย่างถูกวิธีสามารถสร้างหรือทำลายประสบการณ์ของคุณได้ นี่คือ 10 เคล็ดลับยอดเยี่ยม:

### 1. ตรวจสอบสภาพอากาศ
ตรวจสอบพยากรณ์อากาศสำหรับจุดหมายปลายทางของคุณก่อนออกเดินทาง 1 สัปดาห์ เอเชียมีสภาพภูมิอากาศหลากหลาย ตั้งแต่ฤดูใบไม้ผลิที่เย็นสบายในโตเกียวถึงความร้อนชื้นในกรุงเทพ

### 2. แต่งกายแบบ Layering
แม้จะไปจุดหมายปลายทางที่อบอุ่น รถโค้ชและร้านอาหารที่มีเครื่องปรับอากาศอาจเย็นได้ เตรียมเสื้อแจ็คเก็ตเบาๆ หรือเสื้อคาร์ดิแกนที่สวมทับได้ง่าย

### 3. รองเท้าที่ใส่สบาย
คุณจะต้องเดินเยอะในทัวร์กรุ๊ป ลองสวมรองเท้าก่อนออกเดินทาง — ตุ่มพองไม่สนุกแน่ในวันที่ 2 ของวันหยุด

### 4. ของใช้ขนาดเดินทาง
โรงแรมในทัวร์กรุ๊ปมักให้สิ่งพื้นฐาน แต่ควรเตรียมของจำเป็นขนาดพกพาเพื่อประหยัดพื้นที่กระเป๋า

### 5. พาวเวอร์แบงก์และอแดปเตอร์
เก็บโทรศัพท์ให้มีแบตเตอรี่เต็มสำหรับถ่ายรูป! เตรียมพาวเวอร์แบงก์ที่ดี (อย่างน้อย 10,000 mAh) และตรวจสอบว่าต้องใช้อแดปเตอร์ปลั๊กสำหรับจุดหมายปลายทางหรือไม่

### 6. ถ่ายสำเนาเอกสารสำคัญ
เก็บสำเนาหนังสือเดินทาง วีซ่า ประกัน และการยืนยันการจองในกระเป๋าแยกต่างหากจากตัวจริง

### 7. ขนมระหว่างทาง
การเดินทางด้วยรถโค้ชยาวๆ เป็นเรื่องปกติในทัวร์กรุ๊ป เตรียมขนมเบาๆ และขวดน้ำที่ใช้ซ้ำได้

### 8. กระเป๋าเดย์แพค
กระเป๋าเป้ขนาดเล็กหรือกระเป๋าสะพายข้างสำหรับท่องเที่ยวรายวันเป็นสิ่งจำเป็น ทิ้งกระเป๋าหลักไว้ที่โรงแรม

### 9. ยา
เตรียมยาตามใบสั่งแพทย์ บวกกับยาพื้นฐาน เช่น ยาแก้ปวด ยาแก้เมารถ และยาแก้ท้องเสีย

### 10. เว้นที่ว่างสำหรับของฝาก
อย่าบรรจุกระเป๋าเต็มเกินไป — คุณจะต้องการพื้นที่สำหรับของขวัญและของที่ระลึกขากลับ!

ขอให้เดินทางโดยสวัสดิภาพ! 🌏""",
                "body": """## Pack Smart, Travel Happy

Group tours are one of the best ways to explore Asia — but packing the right way can make or break your experience. Here are our top 10 tips:

### 1. Check the Weather
Always check the weather forecast for your destination a week before departure. Asia's climate varies dramatically — from Tokyo's cool springs to Bangkok's tropical heat.

### 2. Pack Layers
Even in warm destinations, air-conditioned coaches and restaurants can be chilly. Bring a light jacket or cardigan that you can easily layer.

### 3. Comfortable Walking Shoes
You'll be doing a lot of walking on group tours. Break in your shoes before the trip — blisters are no fun on day 2 of your vacation.

### 4. Travel-Size Toiletries
Hotels on group tours usually provide basics, but bring your own essentials in travel sizes to save luggage space.

### 5. Power Bank & Adapter
Keep your phone charged for photos! Bring a good power bank (at least 10,000 mAh) and check if you need a plug adapter for your destination.

### 6. Photocopy Important Documents
Keep copies of your passport, visa, insurance, and booking confirmation in a separate bag from the originals.

### 7. Snacks for the Bus
Long coach rides are common on group tours. Pack some light snacks and a reusable water bottle.

### 8. Day Bag
A small backpack or crossbody bag for daily sightseeing is essential. Leave your main luggage at the hotel.

### 9. Medication
Bring any prescription medications plus basics like painkillers, motion sickness pills, and stomach remedies.

### 10. Leave Room for Souvenirs
Don't pack your suitcase to the brim — you'll want space for gifts and souvenirs on the way back!

Happy travels! 🌏""",
                "category": cats["tips"],
                "tag_names": ["packing", "budget"],
                "status": "published",
                "published_at": now - timezone.timedelta(days=5),
                "author_name": "Smile Memory Team",
            },
            {
                "title": "First-Timer's Guide to Japan: What to Know Before You Go",
                "title_th": "คู่มือญี่ปุ่นสำหรับมือใหม่: สิ่งที่ต้องรู้ก่อนไป",
                "slug": "first-timers-guide-japan",
                "excerpt": "Planning your first trip to Japan? Here's everything you need to know — from etiquette to food to the best seasons to visit.",
                "excerpt_th": "วางแผนเที่ยวญี่ปุ่นครั้งแรก? นี่คือทุกอย่างที่คุณต้องรู้ — ตั้งแต่มารยาทถึงอาหารถึงฤดูกาลที่ดีที่สุด",
                "body_th": """## การเดินทางญี่ปุ่นครั้งแรกของคุณ

ญี่ปุ่นเป็นหนึ่งในจุดหมายปลายทางที่ได้รับความนิยมสูงสุดสำหรับนักท่องเที่ยวไทย และด้วยเหตุผลที่ดี นี่คือคู่มือฉบับสมบูรณ์สำหรับมือใหม่

### เวลาที่ดีที่สุดในการเยี่ยมชม

- **ฤดูใบไม้ผลิ (มี.ค.-พ.ค.)**: ฤดูดอกซากุระ สวยงามแต่แออัดและราคาสูงกว่า
- **ฤดูใบไม้ร่วง (ต.ค.-พ.ย.)**: ใบไม้เปลี่ยนสีสวยงาม คำแนะนำอันดับหนึ่งของเรา
- **ฤดูร้อน (มิ.ย.-ส.ค.)**: ร้อนและชื้น แต่เป็นฤดูกาลเทศกาล
- **ฤดูหนาว (ธ.ค.-ก.พ.)**: ดีสำหรับสกีที่ฮอกไกโด หนาวแต่มีเสน่ห์

### มารยาทพื้นฐานในญี่ปุ่น

- **การโค้งคำนับ**: การโค้งเล็กน้อยเมื่อทักทายหรือขอบคุณเป็นที่ชื่นชม
- **ถอดรองเท้า**: ถอดรองเท้าเมื่อเข้าบ้าน ร้านอาหารบางแห่ง และวัด
- **เงียบบนรถไฟ**: พูดเบาๆ และปิดเสียงโทรศัพท์
- **ทิป**: ไม่เป็นธรรมเนียมในญี่ปุ่น และอาจถือว่าหยาบคาย!
- **ตะเกียบ**: อย่าปักตะเกียบตั้งในข้าว (เป็นธรรมเนียมงานศพ)

### อาหารที่ต้องลอง

1. **ราเม็ง** — แต่ละภูมิภาคมีสไตล์ของตัวเอง
2. **ซูชิ** — คาเตงซูชิ (ซูชิสายพาน) สนุกและราคาไม่แพง
3. **ทาโกยากิ** — ลูกชิ้นหมึกชื่อดังจากโอซาก้า
4. **มัทฉะ** — ชาเขียวในทุกรูปแบบ!
5. **วากิว** — ถ้างบประมาณอนุญาต ลองเนื้อวัวญี่ปุ่นแท้

### เคล็ดลับด้านการเงิน

- ญี่ปุ่นยังคงเป็นสังคมเงินสดเป็นหลัก — พกเยน
- ตู้ ATM 7-Eleven รับบัตรต่างประเทศ
- ร้านค้าหลายแห่งมีบริการคืนภาษีสำหรับการซื้อสินค้าเกิน ¥5,000

### การเดินทาง

- ทัวร์กรุ๊ปจัดการการเดินทางทั้งหมด ซึ่งเป็นข้อได้เปรียบอย่างมาก
- หากสำรวจด้วยตนเอง รับบัตร Suica/Pasmo สำหรับรถไฟ
- ดาวน์โหลด Google Maps แบบออฟไลน์สำหรับเมืองที่จะไปเยือน

ญี่ปุ่นเป็นจุดหมายปลายทางที่น่าทึ่งที่ผสมผสานประเพณีโบราณกับความทันสมัยล้ำสมัย ไม่ว่าจะไปครั้งแรกหรือครั้งที่ห้า ยังคงมีสิ่งใหม่ๆ ให้ค้นพบเสมอ""",
                "body": """## Your First Trip to Japan

Japan is consistently one of the most popular destinations for Thai travelers — and for good reason. Here's your complete first-timer's guide.

### Best Time to Visit

- **Spring (March-May)**: Cherry blossom season. Beautiful but crowded and pricier.
- **Autumn (October-November)**: Stunning fall foliage. Our top recommendation.
- **Summer (June-August)**: Hot and humid. Festival season.
- **Winter (December-February)**: Great for skiing in Hokkaido. Cold but magical.

### Japanese Etiquette Basics

- **Bowing**: A slight bow when greeting or thanking someone is appreciated.
- **Shoes Off**: Remove shoes when entering homes, some restaurants, and temples.
- **Quiet on Trains**: Keep your voice down and phone on silent mode.
- **Tipping**: Not customary in Japan — and can even be considered rude!
- **Chopsticks**: Never stick them upright in rice (this is a funeral custom).

### Must-Try Foods

1. **Ramen** — Every region has its own style
2. **Sushi** — Conveyor belt sushi (kaiten-zushi) is fun and affordable
3. **Takoyaki** — Osaka's famous octopus balls
4. **Matcha** — Green tea everything!
5. **Wagyu** — If your budget allows, try real Japanese beef

### Money Tips

- Japan is still largely a cash society — carry yen
- 7-Eleven ATMs accept international cards
- Tax-free shopping is available at many stores for purchases over ¥5,000

### Getting Around

- Group tours handle all transportation, which is a huge advantage
- If exploring on your own, get a Suica/Pasmo card for trains
- Download Google Maps offline for your destination cities

Japan is an incredible destination that blends ancient traditions with cutting-edge modernity. Whether it's your first or fifth visit, there's always something new to discover.""",
                "category": cats["guides"],
                "tag_names": ["japan", "culture", "food"],
                "status": "published",
                "published_at": now - timezone.timedelta(days=12),
                "author_name": "Smile Memory Team",
            },
            {
                "title": "Best Street Food in China: A Province-by-Province Guide",
                "title_th": "อาหารริมทางที่ดีที่สุดในจีน: คู่มือแต่ละมณฑล",
                "slug": "best-street-food-china",
                "excerpt": "China's street food scene is legendary. From Beijing's hutongs to Chengdu's spicy alleys, here's what to eat and where.",
                "excerpt_th": "อาหารริมทางของจีนเป็นตำนาน จากหูถงปักกิ่งถึงตรอกเผ็ดเฉิงตู นี่คือสิ่งที่ต้องกินและที่ไหน",
                "body_th": """## การผจญภัยอาหารริมทางของจีน

อาหารจีนเป็นหนึ่งในอาหารที่หลากหลายที่สุดในโลก และวิธีที่ดีที่สุดในการสัมผัสคือผ่านอาหารริมทาง

### ปักกิ่ง
- **เจียนปิ่ง (煎饼)**: แพนเค้กเค็มพร้อมไข่ แครกเกอร์กรอบ และซอส — อาหารเช้าชื่อดังของปักกิ่ง
- **ไม้แกะแกะ (羊肉串)**: เนื้อแกะย่างรสยี่หร่า เหมาะที่สุดที่ตลาดกลางคืนหวังฝู่จิ่ง
- **จาเจี่ยงเมี่ยน (炸酱面)**: เส้นหนาพร้อมซอสถั่วเหลือง — อาหารปลอบโยนใจ

### เฉิงตู (เสฉวน)
- **เมาโต้วฝู่**: เต้าหู้นิ่มในน้ำมันพริกร้อน มาลา
- **ตั้นตั้นเมี่ยน**: เส้นงาเผ็ดที่จะทำให้คุณเหงื่อออก
- **หม้อไฟ**: หม้อน้ำซุปพริกของเสฉวน — ต้องลองกินเป็นกลุ่ม

### เซี่ยงไฮ้
- **เสี่ยวหลงเปา (小笼包)**: เกี๊ยวน้ำซุป — ระวัง ร้อนข้างใน!
- **เส้นน้ำมันหอมหัวใหญ่**: เรียบง่ายแต่อร่อยมาก
- **เซิงเจียนเปา**: เกี๊ยวหมูทอดก้นกรอบ

### ซีอาน
- **โรวเจียโม่ (肉夹馍)**: "แฮมเบอร์เกอร์จีน" กับเนื้อตุ๋นในขนมปังแบน
- **เส้น Biang Biang**: เส้นมือดึงกว้างๆ พร้อมน้ำมันพริก
- **หยางโหรวเพาโม**: ขนมปังในซุปแกะ — สูตรเด็ดจากย่านมุสลิม

### เคล็ดลับการผจญภัยอาหารริมทาง
1. ตามคนท้องถิ่น — คิวยาวมักหมายถึงอาหารอร่อย
2. พกเงินสด — ร้านค้าริมทางส่วนใหญ่ไม่รับบัตร
3. เริ่มต้นด้วยรสเบาหากไม่ชินกับอาหารเผ็ด
4. ทัวร์กรุ๊ปมักรวมทัวร์อาหาร — ใช้ประโยชน์จากสิ่งนี้!

การกินสำรวจจีนเป็นหนึ่งในความสุขยิ่งใหญ่ของการเดินทางที่นั่น อย่ากลัวที่จะลองสิ่งใหม่!""",
                "body": """## China's Street Food Adventure

Chinese cuisine is one of the world's most diverse — and the best way to experience it is through street food.

### Beijing
- **Jianbing (煎饼)**: Savory crepe with egg, crispy cracker, and sauce — the quintessential Beijing breakfast
- **Lamb Skewers (羊肉串)**: Cumin-spiced grilled lamb, best enjoyed at Wangfujing Night Market
- **Zhajiangmian (炸酱面)**: Thick noodles with soybean paste — comfort food at its best

### Chengdu (Sichuan)
- **Mapo Tofu**: Silky tofu in fiery, numbing chili oil
- **Dan Dan Noodles**: Spicy sesame noodles that will make you sweat
- **Hotpot**: Sichuan's famous boiling pot of chili broth — a must-do group dining experience

### Shanghai
- **Xiaolongbao (小笼包)**: Soup dumplings — be careful, they're hot inside!
- **Scallion Oil Noodles**: Simple but incredibly satisfying
- **Shengjianbao**: Pan-fried pork buns with a crispy bottom

### Xi'an
- **Roujiamo (肉夹馍)**: Chinese "hamburger" with braised meat in flatbread
- **Biang Biang Noodles**: Wide, hand-pulled noodles with chili oil
- **Yangrou Paomo**: Bread soaked in lamb soup — the Muslim Quarter specialty

### Tips for Street Food Adventures
1. Follow the locals — long queues usually mean great food
2. Carry cash — most street vendors don't accept cards
3. Start mild if you're not used to spicy food
4. Group tours often include food tours — take advantage of them!

Eating your way through China is one of the great pleasures of traveling there. Don't be afraid to try something new!""",
                "category": cats["guides"],
                "tag_names": ["china", "food", "culture"],
                "status": "published",
                "published_at": now - timezone.timedelta(days=20),
                "author_name": "Smile Memory Team",
            },
            {
                "title": "5 Reasons Why Group Tours Are Perfect for Solo Travelers",
                "title_th": "5 เหตุผลทำไมทัวร์กรุ๊ปเหมาะสำหรับนักเดินทางเดี่ยว",
                "slug": "group-tours-perfect-solo-travelers",
                "excerpt": "Think group tours are only for families and couples? Think again. Here's why solo travelers love group tours.",
                "excerpt_th": "คิดว่าทัวร์กรุ๊ปเหมาะสำหรับครอบครัวและคู่รักเท่านั้น? คิดใหม่ นี่คือเหตุผลที่นักเดินทางเดี่ยวชอบทัวร์กรุ๊ป",
                "body_th": """## การเดินทางเดี่ยว + ทัวร์กรุ๊ป = คู่ที่ลงตัว

หลายคนคิดว่าทัวร์กรุ๊ปเหมาะสำหรับครอบครัวหรือคู่รักเท่านั้น แต่นักเดินทางเดี่ยวสามารถได้รับประโยชน์สูงสุดจากทัวร์กรุ๊ป นี่คือเหตุผล:

### 1. ความปลอดภัยในหมู่คณะ
การเดินทางคนเดียวในประเทศที่ไม่คุ้นเคยอาจน่ากลัว ทัวร์กรุ๊ปให้ความปลอดภัยในตัว — มีคนรอบข้างเสมอ มีไกด์ที่พูดภาษาท้องถิ่น และมีตารางเวลาที่วางแผนไว้

### 2. ไม่เครียดกับการวางแผน
ความท้าทายที่ยิ่งใหญ่ที่สุดของการเดินทางเดี่ยวคือการวางแผนทุกอย่างเอง กับทัวร์กรุ๊ป ทุกอย่างตั้งแต่เที่ยวบินถึงโรงแรมถึงกิจกรรมรายวันถูกจัดการแล้ว คุณแค่มาและสนุก

### 3. คุ้มค่า
นักเดินทางเดี่ยวมักจ่ายมากกว่า — ค่าเพิ่มสำหรับห้องเดี่ยว แท็กซี่คนเดียว ฯลฯ ทัวร์กรุ๊ปแบ่งค่าใช้จ่ายในหมู่กลุ่ม และหลายแห่งเสนออัตราค่าเพิ่มห้องเดี่ยวที่สมเหตุสมผล

### 4. พบเพื่อนใหม่
ทัวร์กรุ๊ปเป็นหนึ่งในวิธีที่ง่ายที่สุดในการพบนักท่องเที่ยวที่มีความคิดเหมือนกัน นักเดินทางเดี่ยวหลายคนสร้างมิตรภาพตลอดชีวิตจากทัวร์

### 5. เข้าถึงประสบการณ์พิเศษ
ประสบการณ์บางอย่างมีเฉพาะสำหรับกลุ่ม — การจองร้านอาหารพิเศษ การเข้าถึงเบื้องหลัง กิจกรรมราคากลุ่ม ในฐานะนักเดินทางเดี่ยวในทัวร์กรุ๊ป คุณได้รับสิทธิพิเศษทั้งหมดนี้

### เคล็ดลับสำหรับนักเดินทางเดี่ยวในทัวร์กรุ๊ป

- **เปิดใจและเป็นมิตร** — แนะนำตัวเองในวันแรก
- **เลือกทัวร์ที่เหมาะสม** — มองหาทัวร์ที่มีกิจกรรมหลากหลายและเวลาอิสระ
- **สื่อสารกับเอเจนต์ของคุณ** — แจ้งความชอบของคุณ
- **สนุกกับความสมดุล** — กิจกรรมกลุ่มตอนกลางวัน เวลาส่วนตัวตอนเย็น

ที่ Smile Memory เราต้อนรับนักเดินทางเดี่ยวในทุกทัวร์ ติดต่อเราเพื่อหาทัวร์กรุ๊ปที่สมบูรณ์แบบสำหรับการผจญภัยเดี่ยวครั้งต่อไปของคุณ!""",
                "body": """## Solo Travel + Group Tours = Perfect Match

Many people think group tours are only for families or couples, but solo travelers can benefit the most from them. Here's why:

### 1. Safety in Numbers
Traveling alone in unfamiliar countries can feel daunting. Group tours provide built-in safety — you always have people around, a guide who speaks the local language, and an organized itinerary.

### 2. No Planning Stress
One of the biggest challenges of solo travel is planning everything yourself. With a group tour, everything from flights to hotels to daily activities is arranged. You just show up and enjoy.

### 3. Cost Effective
Solo travelers often pay more — single room supplements, taxi rides alone, etc. Group tours spread costs across the group, and many offer reasonable single supplement rates.

### 4. Make New Friends
Group tours are one of the easiest ways to meet like-minded travelers. Many solo travelers end up making lifelong friends on tours.

### 5. Access to Experiences
Some experiences are only available to groups — special restaurant reservations, behind-the-scenes access, bulk-rate activities. As a solo traveler on a group tour, you get all these perks.

### Tips for Solo Travelers on Group Tours

- **Be open and friendly** — introduce yourself on the first day
- **Choose the right tour** — look for tours with a mix of activities and free time
- **Communicate with your agent** — let them know your preferences
- **Enjoy the balance** — group activities during the day, personal time in the evenings

At Smile Memory, we welcome solo travelers on every tour. Contact us to find the perfect group tour for your next solo adventure!""",
                "category": cats["tips"],
                "tag_names": ["budget"],
                "status": "published",
                "published_at": now - timezone.timedelta(days=30),
                "author_name": "Smile Memory Team",
            },
            {
                "title": "Photography Tips for Your Asia Tour: Capture the Perfect Shot",
                "title_th": "เคล็ดลับถ่ายรูปสำหรับทัวร์เอเชีย: ถ่ายภาพสมบูรณ์แบบ",
                "slug": "photography-tips-asia-tour",
                "excerpt": "From temple selfies to food photography, here's how to get Instagram-worthy photos on your group tour.",
                "excerpt_th": "จากเซลฟี่วัดถึงถ่ายรูปอาหาร นี่คือวิธีถ่ายรูปสวยๆ สำหรับ Instagram ในทัวร์กรุ๊ปของคุณ",
                "body_th": """## บันทึกความทรงจำที่คงทน

รูปถ่ายทัวร์ของคุณจะเป็นของที่ระลึกที่มีค่าที่สุด นี่คือวิธีทำให้รูปถ่ายยอดเยี่ยม แม้จะใช้แค่กล้องโทรศัพท์

### "Golden Hour" คือเพื่อนที่ดีที่สุดของคุณ
ชั่วโมงหลังพระอาทิตย์ขึ้นและก่อนตกให้แสงที่สวยงาม อบอุ่นที่สุด วางแผนให้อยู่ที่จุดที่มีวิวสวยงามในช่วงเวลานี้

### เคล็ดลับการจัดองค์ประกอบภาพ
- **กฎสามส่วน**: วางวัตถุออกจากตรงกลางเพื่อภาพที่น่าสนใจกว่า
- **เส้นนำทาง**: ใช้ถนน แม่น้ำ หรือเส้นทางเพื่อดึงสายตาเข้าสู่ภาพ
- **สิ่งที่น่าสนใจในพื้นหน้า**: รวมบางอย่างในพื้นหน้าเพื่อความลึก

### การถ่ายภาพวัดและศาลเจ้า
- ถอดรองเท้าและหมวกก่อนเข้า
- ถามก่อนถ่ายภาพผู้คนหรือพระ
- ภาพมุมกว้างจับความยิ่งใหญ่ ภาพระยะใกล้จับรายละเอียด
- ไปวัดยอดนิยมตอนเช้าตรู่เพื่อหลีกเลี่ยงฝูงชน

### การถ่ายภาพอาหาร
- แสงธรรมชาติดีกว่าแฟลชเสมอ
- ถ่ายจากด้านบนสำหรับสไตล์ flat-lay
- รวมตะเกียบ มือ หรือบริบทเพื่อความเป็นธรรมชาติมากขึ้น
- ถ่ายรูปเร็ว — ไม่มีใครชอบอาหารเย็น!

### เคล็ดลับถ่ายรูปในทัวร์กรุ๊ป
- คุ้นเคยกับเพื่อนร่วมทัวร์ — คนมากขึ้นหมายถึงโอกาสถ่ายรูปมากขึ้น
- ถามไกด์เกี่ยวกับจุดถ่ายรูปที่ดีที่สุด
- ถ่ายทั้งทิวทัศน์และภาพ candid
- สำรองข้อมูลรูปถ่ายทุกคืนไปยัง cloud

### อุปกรณ์จำเป็น
- **กล้องโทรศัพท์** ดีเพียงพอสำหรับสถานการณ์ส่วนใหญ่
- **พาวเวอร์แบงก์** — แบตหมด = ไม่มีรูปถ่าย
- **เซลฟี่สติ๊ก/ขาตั้งขนาดเล็ก** — สำหรับภาพกลุ่มโดยไม่ต้องขอคนแปลกหน้า
- **ผ้าเช็ดเลนส์** — ความชื้นและรอยนิ้วมือเป็นศัตรู

กล้องที่ดีที่สุดคือกล้องที่คุณมีอยู่กับตัว อย่าใช้เวลาถ่ายรูปมากจนลืมสนุกกับช่วงเวลานั้น!""",
                "body": """## Capture Memories That Last

Your tour photos will be your most treasured souvenirs. Here's how to make them great — even with just a phone camera.

### Golden Hour is Your Best Friend
The hour after sunrise and before sunset gives the most beautiful, warm light. Plan to be at scenic spots during these times.

### Composition Tips
- **Rule of Thirds**: Place subjects off-center for more interesting photos
- **Leading Lines**: Use roads, rivers, or pathways to draw the eye into the photo
- **Foreground Interest**: Include something in the foreground for depth

### Temple & Shrine Photography
- Remove your shoes and hat before entering
- Ask before photographing people or monks
- Wide-angle shots capture the grandeur; close-ups capture the details
- Visit popular temples early morning to avoid crowds

### Food Photography
- Natural light always beats flash
- Shoot from above for flat-lay style
- Include chopsticks, hands, or context for a more authentic feel
- Take the photo quickly — no one likes cold food!

### Group Tour Photo Tips
- Befriend your fellow travelers — more people means more photo opportunities
- Ask the guide about the best photo spots
- Take both scenery AND candid shots
- Back up your photos every night to cloud storage

### Essential Gear
- **Phone camera** is absolutely fine for most situations
- **Power bank** — dead battery = zero photos
- **Selfie stick/mini tripod** — for group shots without asking strangers
- **Lens wipes** — humidity and fingerprints are the enemy

The best camera is the one you have with you. Don't spend so much time photographing that you forget to enjoy the moment!""",
                "category": cats["tips"],
                "tag_names": ["photography"],
                "status": "published",
                "published_at": now - timezone.timedelta(days=45),
                "author_name": "Smile Memory Team",
            },
        ]

        for p in posts:
            tag_list = p.pop("tag_names", [])
            post, created = BlogPost.objects.get_or_create(slug=p["slug"], defaults=p)
            if created:
                for tn in tag_list:
                    if tn in tags:
                        post.tags.add(tags[tn])
        self.stdout.write(f"  Created {len(posts)} blog posts")
