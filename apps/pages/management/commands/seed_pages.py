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
                "answer": "Cancellation and change policies vary by tour and departure date. Please contact us as soon as possible if you need to make changes. Cancellation fees may apply depending on how close to the departure date.",
                "answer_th": "นโยบายการยกเลิกและเปลี่ยนแปลงแตกต่างกันตามทัวร์และวันเดินทาง กรุณาติดต่อเราโดยเร็วที่สุดหากต้องการเปลี่ยนแปลง อาจมีค่าธรรมเนียมการยกเลิกขึ้นอยู่กับระยะเวลาก่อนวันเดินทาง",
                "sort_order": 3,
            },
            {
                "question": "Do I need a visa for the tour?",
                "question_th": "ต้องทำวีซ่าสำหรับทัวร์หรือไม่?",
                "answer": "Visa requirements depend on your nationality and destination. We'll inform you about visa requirements when your booking is confirmed. For some destinations, we can assist with group visa applications.",
                "answer_th": "ข้อกำหนดวีซ่าขึ้นอยู่กับสัญชาติและจุดหมายปลายทาง เราจะแจ้งให้ทราบเกี่ยวกับข้อกำหนดวีซ่าเมื่อการจองได้รับการยืนยัน สำหรับบางจุดหมาย เราสามารถช่วยยื่นวีซ่ากรุ๊ปได้",
                "sort_order": 4,
            },
            {
                "question": "What is included in the tour price?",
                "question_th": "ราคาทัวร์รวมอะไรบ้าง?",
                "answer": "Typically includes flights, accommodation, meals (as specified in the itinerary), local transportation, and sightseeing. Each tour page lists exactly what's included and excluded.",
                "answer_th": "โดยทั่วไปรวมตั๋วเครื่องบิน ที่พัก อาหาร (ตามที่ระบุในโปรแกรม) การเดินทางภายใน และการเที่ยวชม แต่ละทัวร์จะระบุรายละเอียดว่ารวมและไม่รวมอะไรบ้าง",
                "sort_order": 5,
            },
            {
                "question": "Is travel insurance included?",
                "question_th": "รวมประกันการเดินทางหรือไม่?",
                "answer": "Travel insurance is not included in the tour price. We strongly recommend purchasing travel insurance before your trip. We can recommend insurance providers upon request.",
                "answer_th": "ประกันการเดินทางไม่รวมในราคาทัวร์ เราแนะนำอย่างยิ่งให้ซื้อประกันการเดินทางก่อนเดินทาง เราสามารถแนะนำบริษัทประกันได้",
                "sort_order": 6,
            },
            {
                "question": "What is the group size?",
                "question_th": "ขนาดกรุ๊ปเท่าไหร่?",
                "answer": "Group sizes typically range from 15-40 people depending on the tour. You can see available seats for each departure date on the tour detail page.",
                "answer_th": "ขนาดกรุ๊ปโดยทั่วไปอยู่ที่ 15-40 คน ขึ้นอยู่กับทัวร์ คุณสามารถดูที่นั่งว่างสำหรับแต่ละวันเดินทางได้ในหน้ารายละเอียดทัวร์",
                "sort_order": 7,
            },
            {
                "question": "How do I contact you?",
                "question_th": "ติดต่อได้อย่างไร?",
                "answer": "You can reach us via LINE (fastest), phone, email, or the contact form on our website. Our team typically responds within a few hours during business hours.",
                "answer_th": "คุณสามารถติดต่อเราทาง LINE (เร็วที่สุด) โทรศัพท์ อีเมล หรือแบบฟอร์มติดต่อบนเว็บไซต์ ทีมของเราตอบกลับภายในไม่กี่ชั่วโมงในเวลาทำการ",
                "sort_order": 8,
            },
        ]
        for f in faqs:
            FAQ.objects.get_or_create(question=f["question"], defaults=f)
        self.stdout.write(f"  Created {len(faqs)} FAQs")

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
