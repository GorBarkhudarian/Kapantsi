# -*- coding: utf-8 -*-
import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from issues.models import Issue, IssueStatusHistory
from voting.models import Vote

User = get_user_model()

ISSUES_DATA = [
    {
        'title_hy': 'Հիմնական փողոցի ճանապարհի վնաս',
        'title_en': 'Main street road damage',
        'description_hy': 'Կապան-Երևան ճանապարհի կենտրոնական հատվածում մեծ փոսեր կան, որոնք վտանգ են ներկայացնում մեքենաների համար։ Անհրաժեշտ է շտապ վերանորոգում։',
        'description_en': 'Large potholes on the Kapan-Yerevan road. Dangerous for vehicles. Urgent repair needed.',
        'category': 'road', 'status': 'in_progress', 'area': 'city',
        'lat': 39.2070, 'lon': 46.4062, 'address': 'Կապան-Երևան ճանապարհ',
    },
    {
        'title_hy': 'Ջրամատակարարման խափանում Բաղրամյան փողոցում',
        'title_en': 'Water supply break on Baghramyan street',
        'description_hy': 'Բաղրամյան 12 հասցեում ջրամատակարարման խափանում է տեղի ունեցել 3 օր տևողությամբ։ Բնակիչները ջուր չեն ստանում։',
        'description_en': 'Water supply cut at Baghramyan 12 for 3 days. Residents have no water.',
        'category': 'water', 'status': 'under_review', 'area': 'city',
        'lat': 39.2055, 'lon': 46.4071, 'address': 'Բաղրամյան 12, Կապան',
    },
    {
        'title_hy': 'Փողոցային լուսավորության համակարգի խափանում կենտրոնական վայրում',
        'title_en': 'Street lighting malfunction near central square',
        'description_hy': 'Հրապարակից մինչև կամուրջ ամբողջ լուսավորության համակարգը խափանվել է։ Բնակիչները զգուշանում են գիշերը։',
        'description_en': 'All street lights from central square to bridge are off. Residents feel unsafe at night.',
        'category': 'electricity', 'status': 'pending', 'area': 'city',
        'lat': 39.2080, 'lon': 46.4045, 'address': 'Կենտրոնական հրապարակ, Կապան',
    },
    {
        'title_hy': 'Աղբի անկանոն համակարգի խափանում Շահումյան փողոցում',
        'title_en': 'Irregular garbage collection on Shahumyan street',
        'description_hy': 'Շահումյան 5 հասցեում Աղբի անկանոն համակարգի խափանում է տեղի ունեցել։ Աղբը վերջինս է կուտակվում փողոցի վրա։',
        'description_en': 'Irregular garbage collection on Shahumyan street. Waste is piling up in the street.',
        'category': 'waste', 'status': 'completed', 'area': 'city',
        'lat': 39.2063, 'lon': 46.4055, 'address': 'Շահումյան 5, Կապան',
    },
    {
        'title_hy': 'Հետիոտնային անցման բացակայություն դպրոցի տարածքում։',
        'title_en': 'No pedestrian crossing near school',
        'description_hy': 'Թիվ 3 դպրոցի տարածքում հետիոտնային անցումը բացակայում է։ Երեխաները անվտանգ կերպով չեն կարողանում անցնոել փողոցը',
        'description_en': 'No pedestrian crossing near School No.3. Children cross in dangerous conditions every day.',
        'category': 'safety', 'status': 'pending', 'area': 'city',
        'lat': 39.2091, 'lon': 46.4038, 'address': 'Թիվ 3 Դպրոց, Կապան',
    },
    {
        'title_hy': 'Գեղանուշ գյուղ տանող ճանապարհի քանդվածություն',
        'title_en': 'Geghanush village access road damaged',
        'description_hy': 'Գեղանուշ գյուղ տանող ճանապարհի քանդվածությունան պատճառով գյուղը կտրված է մնացել։ Ձմռանը անցանելի չէ։',
        'description_en': 'Road to Geghanush village is completely damaged. Impassable in winter months.',
        'category': 'road', 'status': 'under_review', 'area': 'village', 'village_name': 'Geghanush',
        'lat': 39.2405, 'lon': 46.3598, 'address': 'Գեղանուշ, Սյունիկ',
    },
    {
        'title_hy': 'Դավիթ Բեկ գյուղում ջրամատակարարման խափանում',
        'title_en': 'Davit Bek: main water pipe leakage',
        'description_hy': 'Դավիթ Բեկ գյուղում ջրամատակարարումը խափանվել է հիմնական ջրատարի ճաքի պատճառով։ Ջուրը կեղտոտվել է, իսկ բնակիչները ջուր չունեն։',
        'description_en': 'Main water pipe cracked in Davit Bek village. Water is wasted and residents have no supply.',
        'category': 'water', 'status': 'in_progress', 'area': 'village', 'village_name': 'Davit Bek',
        'lat': 39.2698, 'lon': 46.3205, 'address': 'Դավիթ Բեկ, Կապան',
    },
    {
        'title_hy': 'Տաթեվ գյուղում ամենօրյա էլեկտրության անջատում',
        'title_en': 'Tatev village: daily electricity cuts',
        'description_hy': 'Տաթեվ գյուղում էլեկտրությունը անջատվում է ամեն օր 4-6 ժամանակի համար։ Բնակիչներին տրվող նախազգուշացումներ չկան։',
        'description_en': 'Electricity cut daily for 4-6 hours in Tatev village. No advance notice given to residents.',
        'category': 'electricity', 'status': 'rejected', 'area': 'village', 'village_name': 'Tatev',
        'lat': 39.3802, 'lon': 46.2398, 'address': 'Տաթեվ, Սյունիկ',
    },
    {
        'title_hy': 'Շինուհայր գյուղում անօրինական ավտոտնակի կառուցում',
        'title_en': 'Shinuhayr: illegal dumping site',
        'description_hy': 'Շինուհայր գյուղում անօրինական ավտոտնակի կառուցում է տեղի ունեցել։ Ամենօրյա աղմուկը խանգարու; է գյուղացիների անդորրը։',
        'description_en': 'An illegal dump has formed near Shinuhayr village entrance. Environmental hazard.',
        'category': 'waste', 'status': 'pending', 'area': 'village', 'village_name': 'Shinuhayr',
        'lat': 39.1803, 'lon': 46.2802, 'address': 'Շինուհայր, Սյունիկ',
    },
    {
        'title_hy': 'Կապպանի Հրապարակի կամրջի վթարային իրավիճակ',
        'title_en': 'Main bridge renovation urgently needed',
        'description_hy': 'Կապանի Հրապարակի կամուրջը վթարային վիճակում է։ Կամուրջի բետոնը լուրջ վնասված է, ինչը վտանգ է ներկայացնում հետիոտնների և մեքենաների համար։',
        'description_en': 'The main bridge concrete is severely damaged. Dangerous for pedestrians and vehicles.',
        'category': 'safety', 'status': 'in_progress', 'area': 'city',
        'lat': 39.2075, 'lon': 46.4070, 'address': 'Կապանի Հրապարակ, Կապան',
    },
    {
        'title_hy': 'Կենտրոնական պուրակի հաշմանդամների լիֆտը կոտրվել է',
        'title_en': 'Central park disability lift out of order',
        'description_hy': 'Կենտրոնական պուրակի հաշմանդամ անձանց համար լիֆտը կոտրվել է արդեն 2 ամիս։ Վերանորոգման գործերը նախատեսված չեն, իրավիճակը անհանդուրժելի է։',
        'description_en': 'Disability lift in central park broken for 2 months. No repair scheduled.',
        'category': 'other', 'status': 'pending', 'area': 'city',
        'lat': 39.2060, 'lon': 46.4050, 'address': 'Կենտրոնական պուրակ, Կապան',
    },
    {
        'title_hy': 'Կոյուղու խցանում Ազատության 7 հասցեում',
        'title_en': 'Sewage blockage flooding the street',
        'description_hy': 'Ազատության 7 հասցեում խցանվել է կոյուղը։ Անձրևի պատճառով կոյուղից հեռացված է ջուրը, իսկ կոյուղին պարզապես դարձել է մի հեռացման հետևանքով։',
        'description_en': 'Sewage blockage flooding the street at Azatutyan 7. Health hazard.',
        'category': 'water', 'status': 'completed', 'area': 'city',
        'lat': 39.2042, 'lon': 46.4066, 'address': 'Ազատության 7, Կապան',
    },
    {
        'title_hy': 'Արծրունյաց փողոց. ծառերի կտրում',
        'title_en': 'Artsrunyats street: overgrown dangerous trees',
        'description_hy': 'Արծրունյաց փողոցի ծառերը մեծ եւ անկառավարելի են դարձել եւ ծածկում են ճանապարհային նշանները։ Վտանգ կա մեքենաների համար։',
        'description_en': 'Overgrown trees on Artsrunyats street blocking road signs and causing danger.',
        'category': 'other', 'status': 'under_review', 'area': 'city',
        'lat': 39.2088, 'lon': 46.4042, 'address': 'Արծրունյաց փողոց, Կապան',
    },
    {
        'title_hy': 'Արդվի խաչմերուկում ճանապարհային նշանները բացակայում են',
        'title_en': 'Missing road signs at Ardvi intersection',
        'description_hy': 'Արդվի խաչմերուկում ճանապարհային նշանները բացակայում են։ Վտանգ է ներկայացնում հետիոտների և մեքենաների համար։',
        'description_en': 'Road signs missing at Ardvi intersection. Accidents increasing. Urgent action needed.',
        'category': 'road', 'status': 'pending', 'area': 'city',
        'lat': 39.2050, 'lon': 46.4080, 'address': 'Արդվի խաչմերուկ, Կապան',
    },
    {
        'title_hy': 'Վթարային շենք Բաղրամյան 45 հասցեում',
        'title_en': 'Emergency building condition at Baghramyan 45',
        'description_hy': 'Բաղրամյան 45 շենքն ամրացնող կառուցվածքը կարգավորվել է։ Բնակիչները վտանգվում են կոլապսի հետևանքով։',
        'description_en': 'Building at Baghramyan 45 needs urgent structural work. Residents fear collapse.',
        'category': 'safety', 'status': 'in_progress', 'area': 'city',
        'lat': 39.2030, 'lon': 46.4060, 'address': 'Բաղրամյան 45, Կապան',
    },
    {
        'title_hy': 'Ջրատարի աշխատանքի խափանում Սյունիքի գյուղում',
        'title_en': 'Syunik village: irrigation channel blocked',
        'description_hy': 'Սյունիքի գյուղում ջրատարի աշխատանքը խափանվել է։ Ֆերմերները չեն կարողանում ջուր տանել դաշտերին։',
        'description_en': 'Irrigation channel in Syunik village blocked by debris. Farmers cannot water fields.',
        'category': 'water', 'status': 'pending', 'area': 'village', 'village_name': 'Syunik',
        'lat': 39.1502, 'lon': 46.3502, 'address': 'Սյունիքի գյուղ, Սյունիք',
    },
    {
        'title_hy': 'Կենտրոնական հրապարակի սալիկների վերանորոգման անհրաժեշտություն',
        'title_en': 'Central square paving stones raised and shifted',
        'description_hy': 'Կենտրոնական հրապարակի սալիկները տեղարվել են, ստեղծելով անհարմարություններ բնակիչների համար։',
        'description_en': 'Central square paving stones have shifted creating tripping hazards. Repair needed.',
        'category': 'road', 'status': 'completed', 'area': 'city',
        'lat': 39.2078, 'lon': 46.4048, 'address': 'Կապանի հրապարակ, Կապան',
    },
    {
        'title_hy': 'Կիրովի պուրակ, մանկանական խաղահրապարակի վնասվածություն',
        'title_en': 'Kirov Park playground equipment broken',
        'description_hy': 'Կիրովի պուրակում մանկանական խաղահրապարակի ճոճանակներն ու սահնակները ամբողջությամբ վնասված են և վտանգավոր երեխաների համար։',
        'description_en': 'Swings and slide in Kirov Park are completely broken and dangerous for children.',
        'category': 'other', 'status': 'pending', 'area': 'city',
        'lat': 39.2065, 'lon': 46.4035, 'address': 'Կիրովի պուրակ, Կապան',
    },
    {
        'title_hy': 'Դավիթ Բեկ փողոցում գիշերային լուսավորության համակարգը շարքից դուրս է եկել, ինչը խաթարում է փողոցի բնակիչների բնականոն կյանքը և անվտանգության։',
        'title_en': 'The street lighting system on Davit Bek Street is out of order, disrupting residents daily life and safety.',
        'description_hy': 'Դավիթ Բեկ փողոցի գիշերային լուսավորության համակարգը շարքից դուրս է եկել, ինչը խաթարում է փողոցի բնակիչների բնականոն կյանքը և անվտանգությունը։',
        'description_en': 'Davit Bek village and access road completely dark at night. Major safety concern.',
        'category': 'electricity', 'status': 'under_review', 'area': 'village', 'village_name': 'Davit Bek',
        'lat': 39.2705, 'lon': 46.3198, 'address': 'Դավիթ Բեկի 6, 7, 8 հասցեներ։',
    },
    {
        'title_hy': 'Դեպի Կապանի հիվանդանոց տանող ճանապարհը անմխիթար վիճակում է, ինչը բերում է շտապ օգնության ուշացումների',
        'title_en': 'The road leading to the Kapan hospital is in poor condition, which causes delays for emergency services.',
        'description_hy': 'Դեպի Կապանի հիվանդանոց տանող ճանապարհը գտնվում է անմխիթար վիճակում, որը հանգամանք է հանդիսանում շտապ օգնության ուշացման համար։',
        'description_en': 'Road to Kapan hospital is very badly damaged. Ambulances are delayed reaching patients.',
        'category': 'road', 'status': 'in_progress', 'area': 'city',
        'lat': 39.2095, 'lon': 46.4025, 'address': 'Հայաստան, 3301, Սյունիքի մարզ, Կապան Մելիք-Ստեփանյան փող., 13 շենք',
    },
]


class Command(BaseCommand):
    help = 'Seed the database with sample data for Kapantsi'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('Seeding Kapantsi database...'))

        # Admin users
        admins = []
        for username, first, last, nid in [
            ('admin_kapan', 'Aram', 'Grigoryan', '00000001'),
            ('admin_municipality', 'Lilit', 'Petrosyan', '00000002'),
        ]:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'first_name': first, 'last_name': last,
                    'email': f'{username}@kapan.am',
                    'national_id': nid, 'role': 'admin',
                    'verified': True, 'is_staff': True, 'is_superuser': True,
                    'phone': '+374-094-000000', 'address': 'Kapan, Syunik, Armenia',
                }
            )
            if created:
                user.set_password('admin123')
                user.save()
            self.stdout.write(f'  Admin: {username} / admin123')
            admins.append(user)

        # Citizen users
        citizens = []
        citizen_data = [
            ('hayk_sargsyan',     'Hayk',     'Sargsyan',     '10000001'),
            ('ani_petrosyan',     'Ani',      'Petrosyan',    '10000002'),
            ('david_grigoryan',   'David',    'Grigoryan',    '10000003'),
            ('nare_hovhannisyan', 'Nare',     'Hovhannisyan', '10000004'),
            ('armen_mkrtchyan',   'Armen',    'Mkrtchyan',    '10000005'),
            ('siranush_zakaryan', 'Siranush', 'Zakaryan',     '10000006'),
            ('tigran_avagyan',    'Tigran',   'Avagyan',      '10000007'),
            ('mariam_hakobyan',   'Mariam',   'Hakobyan',     '10000008'),
            ('suren_gevorgyan',   'Suren',    'Gevorgyan',    '10000009'),
            ('lusin_babayan',     'Lusin',    'Babayan',      '10000010'),
        ]
        for username, first, last, nid in citizen_data:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'first_name': first, 'last_name': last,
                    'email': f'{username}@mail.am',
                    'national_id': nid, 'role': 'citizen',
                    'verified': True,
                    'phone': f'+374-077-{nid[-6:]}',
                    'address': 'Kapan, Syunik, Armenia',
                }
            )
            if created:
                user.set_password('citizen123')
                user.save()
            self.stdout.write(f'  Citizen: {username} / citizen123')
            citizens.append(user)

        all_reporters = citizens + admins

        # Issues
        issues = []
        for i, data in enumerate(ISSUES_DATA):
            reporter = all_reporters[i % len(all_reporters)]
            issue, created = Issue.objects.update_or_create(
                title_en=data['title_en'],
                defaults={
                    'title_hy': data['title_hy'],
                    'description_hy': data['description_hy'],
                    'description_en': data.get('description_en', ''),
                    'category': data['category'],
                    'status': data['status'],
                    'area': data['area'],
                    'village_name': data.get('village_name', ''),
                    'latitude': data['lat'],
                    'longitude': data['lon'],
                    'location_address': data.get('address', ''),
                    'created_by': reporter,
                }
            )
            if created:
                self.stdout.write(f'  Issue #{issue.pk}: {issue.title_en[:50]}')
                if issue.status != 'pending':
                    IssueStatusHistory.objects.get_or_create(
                        issue=issue,
                        new_status=issue.status,
                        defaults={
                            'old_status': 'pending',
                            'changed_by': admins[0],
                            'note': 'Status updated by Kapan municipality.',
                        }
                    )
            issues.append(issue)

        # Votes
        vote_count = 0
        random.seed(42)
        for citizen in citizens:
            for issue in random.sample(issues, min(5, len(issues))):
                _, created = Vote.objects.get_or_create(user=citizen, issue=issue)
                if created:
                    vote_count += 1

        self.stdout.write(f'  Votes created: {vote_count}')
        self.stdout.write(self.style.SUCCESS('\nDone! Kapantsi seeded successfully.'))
        self.stdout.write(self.style.WARNING('\nLogin credentials:'))
        self.stdout.write('  Admin:   admin_kapan / admin123')
        self.stdout.write('  Admin:   admin_municipality / admin123')
        self.stdout.write('  Citizen: hayk_sargsyan / citizen123')
        self.stdout.write('  Citizen: ani_petrosyan / citizen123')
