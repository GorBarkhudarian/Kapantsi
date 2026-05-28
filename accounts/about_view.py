# -*- coding: utf-8 -*-
from django.shortcuts import render


# ---------------------------------------------------------------------------
# Structured content for the About page — all three languages
# ---------------------------------------------------------------------------

SECTIONS_HY = [
    {
        'title': 'Քաղաքացու ահազանգից՝ դեպի լուծում',
        'body': (
            'Ժամանակակից քաղաքային կառավարման համակարգերում հաճախ նկատվում է, որ բնակիչների ձայնը բավարար չափով չի ' 
            'հասնում որոշում կայացնող մարմիններին։ Կապանցի-ն փորձում է հենց այդ բացը լրացնել՝ ստեղծելով մի միջավայր, ' 
            'որտեղ յուրաքանչյուր քաղաքացի կարող է արտահայտել իր մտահոգությունները, տալ առաջարկներ և մասնակցել համայնքի ' 
            'զարգացման գործընթացին՝ թափանցիկ և պարզ ձևաչափով։'
        ),
    },
    {
        'title': 'Գրանցման և նույնականացման գործընթաց',
        'body': (
            'Հարթակի միջոցով Կապանի բնակիչները հնարավորություն են ստանում գրանցվելու և անցնելու նույնականացման '
            'գործընթաց, որը հիմնված է անձնագրի կամ նույնականացման քարտի տվյալների վրա։ Այս քայլը կարևոր է, քանի որ '
            'ապահովում է համակարգի վստահելիությունը և կանխում է կեղծ օգտատերերի կամ կրկնակի քվեարկությունների '
            'հնարավորությունը։ Միայն նույնականացում անցած բնակիչներն կարող են լիարժեք օգտվել հարթակի հնարավորություններից։ '
        ),
    },
    {
        'title': 'Խնդերի ներկայացում և քաղաքացիական մասնակցություն',
        'body': (
            'Հաստատումից հետո օգտատերը դառնում է համայնքային գործընթացների ակտիվ մասնակից։ Նա կարող է ներկայացնել ' 
            'իր բնակավայրում առկա խնդիրները՝ լինի դա ճանապարհային վիճակ, ենթակառուցվածքային խնդիր, բնապահպանական ' 
            'հարց կամ հանրային ծառայությունների հետ կապված դժվարություն։ Յուրաքանչյուր խնդիր ներկայացվում է պարզ ' 
            'ձևաչափով՝ նկարագրությամբ, անհրաժեշտության դեպքում լուսանկարներով և քարտեզային նշումով։ '
        ),
    },
    {
        'title': 'Քվեարկություն և առաջնահերթությունների որոշում ',
        'body': (
            'Բացի խնդիրների ներկայացումից, քաղաքացիները կարող են նաև քվեարկել արդեն գոյություն ունեցող խնդիրների ' 
            'օգտին։ Այս մեխանիզմը թույլ է տալիս հասկանալ, թե որ խնդիրներն են ավելի առաջնահերթ համայնքի համար։ '
            'Քվեարկության համակարգը կառուցված է այնպես, որ յուրաքանչյուր օգտատեր ունի մեկ քվե յուրաքանչյուր խնդրի '
            'համար, ինչը ապահովում է արդարություն և հավասար մասնակցություն։ '
        ),
    },
    {
        'title': 'Խնդերի կարգավիճակի հետևման համակարգ ',
        'body': (     
            'Հարթակում յուրաքանչյուր խնդիր անցնում է տարբեր փուլերով՝ սկսած գրանցումից մինչև լուծում։ '
            'Այն կարող է լինել ուսումնասիրման փուլում, ընթացքի մեջ, լուծված կամ մերժված։ Այս կարգավիճակային համակարգը ' 
            'թույլ է տալիս քաղաքացիներին մշտապես հետևել իրենց բարձրացրած խնդիրների ընթացքին և տեսնել, թե ինչպես են '
            'դրանք շարժվում դեպի լուծում։ '
        ),
    },
    {
        'title': 'Քարտեզային համակարգ ',
        'body': (
            'Հատուկ ուշադրություն է դարձված նաև քարտեզային համակարգին։ Կապան քաղաքի և շրջանի իրական քարտեզի վրա '
            'օգտատերերը կարող են տեսնել խնդիրների աշխարհագրական բաշխումը, նշել կոնկրետ վայրեր և հասկանալ, թե որ ' 
            'հատվածներում են առավել շատ խնդիրներ կենտրոնացած։ Սա ոչ միայն հեշտացնում է վերլուծությունը, այլ նաև '
            'օգնում է քաղաքային իշխանություններին ավելի նպատակային լուծումներ գտնել։ '
        ),
    },
    {
        'title': 'Նոր մշակույթ ',
        'body': (
            'Կապանցի-ն պարզապես տեխնոլոգիական համակարգ չէ։ Այն փորձ է ստեղծել նոր մշակույթ համայնքային մասնակցության մեջ, ' 
            'որտեղ յուրաքանչյուր քաղաքացի ունի հնարավորություն լինել լսելի և ազդեցություն ունենալ իր քաղաքի և համայնքի զարգացման գործընթացում։ '
        ),
    },
]

SECTIONS_EN = [
    {
        'title': 'Civic decisions and the voice of residents ',
        'body': (
            'In modern urban governance systems, it is often observed that residents\' voices do not adequately '
            'reach decision-making bodies. Kapantsi attempts to fill exactly that gap by creating an environment '
            'where every citizen can express their concerns, suggestions and participate in the process of community '
            'development in a transparent and understandable format. '
        ),
    },
    {
        'title': 'Registration and identification process',
        'body': (
            'Through the platform, residents of Kapan have the opportunity to register and go through an '
            'identification process based on passport or ID card data. This step is important because it ensures '
            'the credibility of the system and prevents the possibility of fake users or duplicate votes. Only '
            'real, verified residents can fully use the platform\'s capabilities.'
        ),
    },
    {
        'title': 'Reporting issues and civic participation',
        'body': (
            'After verification, the user becomes an active participant in community processes. They can present '
            'issues in their area of residence — whether it is road conditions, infrastructure problems, '
            'environmental issues or difficulties related to public services. Each issue is presented in a simple '
            'format — with a description, photographs if necessary, and a map marker.'
        ),
    },
    {
        'title': 'Voting and determining priorities',
        'body': (
            'In addition to presenting problems, citizens can also vote for already existing issues. This mechanism '
            'makes it possible to understand which problems are more of a priority for the community. The voting '
            'system is built so that each user has one vote for each issue, which ensures fairness and equal '
            'participation.'
        ),
    },
    {
        'title': 'Issue status tracking system',
        'body': (
            'On the platform, each issue goes through its life stages — from registration to resolution. It can be '
            'under review, in progress, resolved or rejected. This status system allows citizens to continuously '
            'monitor the progress of their raised issues and see how they are moving toward resolution.'
        ),
    },
    {
        'title': 'Map system',
        'body': (
            'Special attention is also given to the map system. On the actual map of Kapan city and district, '
            'users can see the geographic distribution of problems, mark specific locations and understand in '
            'which areas the most problems are concentrated. This not only facilitates analysis but also helps '
            'city authorities find more targeted solutions.'
        ),
    },
    {
        'title': 'A new culture of participation',
        'body': (
            'Kapantsi is not just a technological system. It is an attempt to create a new culture of community '
            'participation, where every citizen has the opportunity to be heard, to have influence, and to play '
            'a direct role in the process of their city\'s development.'
        ),
    },
]

SECTIONS_FR = [
    {
        'title': 'Décisions civiques et voix des résidents',
        'body': (
            'Dans les systèmes modernes de gouvernance urbaine, on observe souvent que la voix des habitants '
            'n\'atteint pas suffisamment les organes décisionnels. Kapantsi tente précisément de combler ce manque '
            'en créant un environnement où chaque citoyen peut exprimer ses préoccupations, ses suggestions et '
            'participer au processus de développement communautaire de manière transparente et compréhensible.'
        ),
    },
    {
        'title': 'Inscription et processus d\'identification',
        'body': (
            'Grâce à la plateforme, les résidents de Kapan ont la possibilité de s\'inscrire et de passer par un '
            'processus d\'identification basé sur les données du passeport ou de la carte d\'identité. Cette étape '
            'est importante car elle garantit la crédibilité du système et empêche la possibilité de faux '
            'utilisateurs ou de votes en double. Seuls les vrais résidents vérifiés peuvent pleinement utiliser '
            'les fonctionnalités de la plateforme.'
        ),
    },
    {
        'title': 'Signalement de problèmes et participation citoyenne',
        'body': (
            'Après vérification, l\'utilisateur devient un participant actif dans les processus communautaires. '
            'Il peut présenter les problèmes dans son lieu de résidence — qu\'il s\'agisse de l\'état des routes, '
            'de problèmes d\'infrastructure, de questions environnementales ou de difficultés liées aux services '
            'publics. Chaque problème est présenté dans un format simple — avec une description, des photos si '
            'nécessaire, et un marqueur sur la carte.'
        ),
    },
    {
        'title': 'Vote et détermination des priorités',
        'body': (
            'En plus de présenter des problèmes, les citoyens peuvent également voter pour des problèmes déjà '
            'existants. Ce mécanisme permet de comprendre quels problèmes sont prioritaires pour la communauté. '
            'Le système de vote est construit de sorte que chaque utilisateur ait une voix pour chaque problème, '
            'ce qui garantit l\'équité et la participation égale.'
        ),
    },
    {
        'title': 'Système de suivi des statuts',
        'body': (
            'Sur la plateforme, chaque problème passe par ses étapes de vie — de l\'enregistrement à la '
            'résolution. Il peut être en cours d\'examen, en cours de traitement, résolu ou rejeté. Ce système '
            'de statut permet aux citoyens de suivre en permanence l\'avancement de leurs problèmes soulevés et '
            'de voir comment ils progressent vers une résolution.'
        ),
    },
    {
        'title': 'Système cartographique',
        'body': (
            'Une attention particulière est également accordée au système de carte. Sur la carte réelle de la '
            'ville et du district de Kapan, les utilisateurs peuvent voir la distribution géographique des '
            'problèmes, marquer des endroits spécifiques et comprendre dans quels secteurs les problèmes sont '
            'les plus concentrés. Cela facilite non seulement l\'analyse, mais aide également les autorités '
            'municipales à trouver des solutions plus ciblées.'
        ),
    },
    {
        'title': 'Une nouvelle culture de participation',
        'body': (
            'Kapantsi n\'est pas seulement un système technologique. C\'est une tentative de créer une nouvelle '
            'culture de participation communautaire, où chaque citoyen a la possibilité d\'être entendu, '
            'd\'avoir de l\'influence et de jouer un rôle direct dans le processus de développement de sa ville.'
        ),
    },
]


def about_view(request):
    """
    Render the About page.

    Sections are loaded from the database (AboutSection model) if any exist.
    Falls back to the hardcoded SECTIONS_* constants when the database is
    empty — e.g. before the seed management command has been run.
    """
    from accounts.models import AboutSection

    def _db_or_fallback(lang, fallback):
        db_sections = list(
            AboutSection.get_sections_for_language(lang).values('title', 'body')
        )
        return db_sections if db_sections else fallback

    return render(request, 'about.html', {
        'sections_hy': _db_or_fallback('hy', SECTIONS_HY),
        'sections_en': _db_or_fallback('en', SECTIONS_EN),
        'sections_fr': _db_or_fallback('fr', SECTIONS_FR),
    })
