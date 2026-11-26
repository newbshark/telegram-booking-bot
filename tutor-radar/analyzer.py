import re
from typing import Dict, Any, Optional

CHANNELS = [
    "fivetutors",        # Специализированная биржа репетиторов (ученики, классы, запросы)
    "freelance_zakaz",   # Заявки на проекты, сайты для школ, Unity игры
    "zakazy_freelance",
    "freelance_orders",
    "it_zakazy",
    "zakazy_it"
]

IT_STEMS = [
    "информатик", "программирован", "кодинг", "unity", "юнити",
    "c#", "csharp", "си шарп", "сишарп", "python", "питон",
    "scratch", "скретч", "геймдев", "gamedev", "скрипт",
    "моддинг", "паскаль", "pascal"
]

TUTOR_STEMS = [
    "репетитор", "преподавател", "учител", "наставник", "ментор",
    "обучен", "урок", "научить", "подтянуть", "подготовк", "огэ", "егэ"
]

KIDS_STEMS = [
    "ребен", "ребят", "подрост", "сын", "доч", "мальчик", "девочк",
    "школьник", "класс", "начинающ", "с нуля", "детям", "детск"
]

PROJECT_STEMS = [
    "индивидуальн", "школьн", "иип", "паспорт проект", "для школ", "проект для школ"
]

STOP_STEMS = [
    # Не-IT школьные предметы
    "английск", "немецк", "французск", "китайск", "испанск",
    "биолог", "хими", "истори", "обществознан", "географ",
    "литератур", "музык", "вокал", "гитар", "фортепиано", "живопис", "логопед",
    
    # Резюме других репетиторов (самореклама)
    "#резюме", "ищу учеников", "набираю учеников", "я репетитор", "я преподаватель",
    "обо мне:", "о себе:", "мой стаж", "веду набор", "приглашаю на занятия",
    
    # Менеджеры, продажи, найм в штат, B2B
    "менеджер", "продаж", "отдел продаж", "копирайтер", "таргетолог", "smm",
    "вакансия", "в штат", "оклад", "полный день", "фуллтайм", "full-time",
    "испытательный срок", "middle", "senior", "lead", "зарплата от", "офис",
    "siemens", "hmi", "автоматизация строительной", "crm строительн", "металл",
    "промо-материал", "раздавать", "промоутер", "стенд", "фестивал", "выставк", "ивент",
    "lora", "controlnet", "саун",
    
    # Спам
    "казино", "crypto", "крипта", "ставка", "гэмблинг", "арбитраж", "битрикс", "1с"
]

PITCH_TUTOR = (
    "Здравствуйте! 👋 Я практикующий программист и частный наставник по разработке 3D-игр в Unity и программированию на C# для ребят 8–16 лет.\n\n"
    "Обучаю через живой интерес ребенка: с первого урока пишем рабочий код и создаем механики в играх. Провожу бесплатный 40-минутный вводный урок онлайн, где знакомимся и пишем первый скрипт.\n\n"
    "Подробнее обо мне, курсах и формате: https://vadim-tutor.web.app"
)

PITCH_PROJECT = (
    "Здравствуйте! 👋 Помогаю школьникам 9–11 классов с разработкой индивидуального проекта по информатике (ИИП) под ключ.\n\n"
    "Что входит:\n"
    "1. Реальный работающий IT-продукт (3D-игра на Unity, сайт или бот).\n"
    "2. Паспорт проекта, пояснительная записка и презентация к защите.\n"
    "3. Репетиция защиты с ребенком, чтобы ответить на любые вопросы комиссии на «5».\n\n"
    "Можем созвониться онлайн и обсудить вашу тему!"
)

PITCH_STUDENT = (
    "Здравствуйте! 👋 Могу помочь с реализацией проекта на C# / Unity. Я действующий разработчик с 4+ годами опыта. Сделаю аккуратный чистый код с подробными комментариями и объясню, как всё работает, чтобы вы легко защитили проект."
)

def analyze_lead(text: str) -> Optional[Dict[str, Any]]:
    tl = text.lower()
    
    # 1. Проверка стоп-слов
    for stop in STOP_STEMS:
        if stop in tl:
            return None

    # Обязательно наличие IT-контекста
    has_it = any(w in tl for w in IT_STEMS) or (('создать игру' in tl or 'разработать игру' in tl or 'сделать игру' in tl) and not 'настольн' in tl)
    has_tutor = any(w in tl for w in TUTOR_STEMS)
    has_kids = any(w in tl for w in KIDS_STEMS)
    has_school_proj = any(w in tl for w in PROJECT_STEMS) and ('проект' in tl or 'иип' in tl)

    cat = None
    title = ""
    pitch = ""

    # Проверка: Индивидуальный школьный проект
    if has_school_proj and (has_it or 'школ' in tl or 'информатик' in tl):
        cat = "SCHOOL_PROJECT"
        title = "🏆 ИНДИВИДУАЛЬНЫЙ ШКОЛЬНЫЙ ПРОЕКТ (ИИП)"
        pitch = PITCH_PROJECT
    
    # Проверка: Репетиторство по IT для ребенка
    elif has_tutor and (has_it or 'информатик' in tl):
        cat = "TUTOR_KIDS"
        title = "🎓 РЕПЕТИТОР ПО IT / ДЕТИ"
        pitch = PITCH_TUTOR
    
    # Проверка: Учебная разработка и геймдев (Unity / C#)
    elif ('unity' in tl or 'юнити' in tl or 'геймдев' in tl) or (has_it and any(w in tl for w in ['лабораторн', 'курсовая', 'курсовой', 'курсач', 'дипломн', 'практическ', 'дз', 'домашк'])):
        cat = "STUDENT_DEV"
        title = "💻 УЧЕБНАЯ РАЗРАБОТКА (UNITY / C#)"
        pitch = PITCH_STUDENT

    if not cat:
        return None

    author = extract_contact(text)

    return {
        "category": cat,
        "category_title": title,
        "pitch": pitch,
        "author": author,
        "text": text.strip()
    }

def extract_contact(text: str) -> str:
    m = re.search(r'(?:заказчик|контакт|писать|связь|отклик|лс|tg|telegram|автор)[:\s\n]+(?:https?://t\.me/|@)?([a-zA-Z0-9_]{4,32})', text, re.IGNORECASE)
    if m:
        c = m.group(1)
        if c.lower() not in ["channel", "admin", "bot", "group", "fivetutors"]:
            return c
    links = re.findall(r't\.me/([a-zA-Z0-9_]{4,32})', text)
    for l in links:
        if l.lower() not in ["share", "joinchat", "c", "addstickers", "fivetutors"]:
            return l
    mentions = re.findall(r'@([a-zA-Z0-9_]{4,32})', text)
    for m_user in mentions:
        if m_user.lower() not in ["channel", "bot", "here", "all", "fivetutors"]:
            return m_user
    return ""
