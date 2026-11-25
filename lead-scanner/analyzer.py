import re
from typing import Dict, Any, List

# Только каналы с РЕАЛЬНЫМИ разовыми заказами (никаких вакансий, курсов и рекрутеров)
PUBLIC_CHANNELS = [
    "freelance_zakaz",
    "zakazy_freelance",
    "freelance_feed",
    "it_zakazy",
    "zakazy_it",
    "freelance_orders",
    "tg_bots_dev"
]

PATTERNS = {
    "bot": re.compile(
        r"(\bтелеграм[- ]?бот[а-я]*\b|\bчат[- ]?бот[а-я]*\b|\bботы?\b|\bбота\b|\bботов\b|\bботу\b|\bботом\b|\b(tg|telegram)\s*bot\b|\baiogram\b|\btelebot\b|\bpyrogram\b)",
        re.IGNORECASE
    ),
    "parser": re.compile(
        r"(\bпарсер[а-я]*\b|\bпарсинг[а-я]*\b|\bпарсить\b|\bсбор\s+данных\b|\bвыгрузк[а-я]*\s+в\s+(excel|csv|таблиц[а-я]*)\b|\bscraping\b|\bscraper\b|\bbeautifulsoup\b|\bselenium\b)",
        re.IGNORECASE
    ),
    "automation": re.compile(
        r"(\bapi\b|\bинтеграц[а-я]*\s+по\s+api\b|\bchatgpt\b|\bcustom\s*gpt\b|\bdatamatrix\b|\bчестный\s*знак\b|\bавтоматизац[а-я]*\b|\bскрипт[а-я]*\s+на\s+python\b|\bpython[- ]?скрипт[а-я]*\b|\bgoogle\s*sheets\s*api\b|\bгугл[- ]?таблиц[а-я]*\s+автомат[а-я]*\b)",
        re.IGNORECASE
    ),
    "web": re.compile(
        r"(\bсверстать\b|\bверстк[а-я]*\b|\bквиз[а-я]*\b|\bлендинг[а-я]*\b|\bкалькулятор[а-я]*\s+цен[а-я]*\b|\bсайт[- ]?визитк[а-я]*\b|\bодностраничник[а-я]*\b|\btilda\b|\bтильд[а-я]*\b|\bсайт\s+под\s+ключ\b)",
        re.IGNORECASE
    )
}

# Жесткий стоп-лист: отсекаем резюме фрилансеров, найм в штат, холодные звонки и инфоцыган
STOP_WORDS = [
    # 1. Самореклама и резюме (когда фрилансер сам предлагает услуги)
    "#помогу", "#резюме", "ищу работу", "ищу проекты", "ищу клиентов", "ищу заказчиков",
    "обо мне", "о себе", "портфолио", "моё портфолио", "мое портфолио", "мой стек",
    "мои навыки", "я веб-дизайнер", "я дизайнер", "я верстальщик", "я разработчик", "я программист",
    "опыт работы:", "стэк:", "стек технологий", "открыт к предложениям",

    # 2. Найм на постоянку / в штат / офисы / агентства
    "вакансия", "в штат", "оклад", "полный день", "полная занятость", "фуллтайм", "full-time",
    "испытательный срок", "middle", "senior", "lead", "зарплата от", "офис", "гибрид",

    # 3. Непрофильные роли (продажники, дизайнеры карточек маркетплейсов, 3D, операторы)
    "3d", "3д", "моделирован", "скульпт", "zbrush", "блендер", "blender", "рендеринг",
    "менеджер по продажам", "менеджер по работе", "менеджер маркетплейс", "оператор", "ассистент",
    "холодные звонки", "инфографик", "карточки товара", "карточек товара", "оформить карточк",
    "таргетолог", "smm", "копирайтер", "рилс", "монтажер", "озвучка", "переводчик",

    # 4. Курсы, спам и реклама
    "школа", "курс", "обучение", "вебинар", "симулейтив", "стать аналитиком",
    "как перестать постоянно искать заказчиков", "перейти к боту", "попробуйте бота",
    "leadradar", "подпишитесь", "наш канал", "реклама", "агрегатор заказов",
    "казино", "crypto", "крипта", "ставка", "гэмблинг", "арбитраж",
    "без оплаты", "за процент", "в будущем озолотимся",
    "битрикс", "bitrix", "1с", "1c", "wordpress", "вордпресс"
]

INTENT_PATTERN = re.compile(
    r"(\bищу\b|\bнужен\b|\bнужна\b|\bнужно\b|\bтребуется\b|\bсделать\b|\bразработать\b|\bнаписать\b|\bсверстать\b|\bзаказ\b|\bбюджет\b|\bоплата\b|\bтз\b|\bкто\s+может\b|\bотклик\b)",
    re.IGNORECASE
)

def extract_contact(text: str) -> str:
    m = re.search(r'(?:заказчик|контакт|писать|связь|отклик|лс|tg|telegram|автор)[:\s\n]+(?:https?://t\.me/|@)?([a-zA-Z0-9_]{4,32})', text, re.IGNORECASE)
    if m:
        c = m.group(1)
        if c.lower() not in ["channel", "freelance", "admin", "bot", "group", "trasterr", "leadradar", "tgdev"]:
            return c
    links = re.findall(r't\.me/([a-zA-Z0-9_]{4,32})', text)
    for l in links:
        if l.lower() not in ["share", "joinchat", "c", "addstickers", "trasterr", "leadradar"]:
            return l
    mentions = re.findall(r'@([a-zA-Z0-9_]{4,32})', text)
    for m_user in mentions:
        if m_user.lower() not in ["channel", "bot", "here", "all", "trasterr", "leadradar"]:
            return m_user
    return ""

def analyze_job(text: str) -> Dict[str, Any]:
    text_lower = text.lower()

    found_stops = [word for word in STOP_WORDS if word in text_lower]
    if found_stops:
        return {
            "status": "REJECT",
            "reason": f"Стоп-лист / не заказ: {', '.join(found_stops)}",
            "category": "unknown",
            "score": 0,
            "proposal": None,
            "contact": ""
        }

    if not INTENT_PATTERN.search(text):
        return {
            "status": "SKIP",
            "reason": "Нет явного интента заказа",
            "category": "unknown",
            "score": 0,
            "proposal": None,
            "contact": ""
        }

    matched_category = None
    for cat, pattern in PATTERNS.items():
        if pattern.search(text):
            matched_category = cat
            break

    if not matched_category:
        return {
            "status": "SKIP",
            "reason": "Не относится к профильным нишам",
            "category": "unknown",
            "score": 0,
            "proposal": None,
            "contact": ""
        }

    proposal = generate_human_proposal(matched_category, text)
    contact = extract_contact(text)

    return {
        "status": "ACCEPT",
        "category": matched_category,
        "score": 85,
        "reason": f"Реальный подходящий заказ: '{matched_category}'",
        "proposal": proposal,
        "contact": contact
    }

def generate_human_proposal(category: str, raw_text: str) -> str:
    if category == "automation":
        return (
            "Добрый день! Занимаюсь автоматизацией и интеграциями на Python/API.\n"
            "Делаю связки с маркетплейсами, ChatGPT (Custom Actions), Google Sheets и базами данных.\n"
            "Логику сделаю надежной, без сбоев и с обработкой лимитов API. Напишите подробнее, какой сервис и формат отчетов в приоритете?"
        )
    elif category == "bot":
        return (
            "Добрый день! Увидел задачу по боту в тг.\n"
            "Делаю ботов на Python, логику и кнопки настрою как нужно, заявки могу выгружать в чат или гугл-таблицу.\n"
            "Могу показать похожий рабочий пример бота, чтобы оценили формат. Если актуально, напишите подробнее, что требуется по функционалу?"
        )
    elif category == "parser":
        return (
            "Добрый день! Увидел задачу по сбору данных.\n"
            "Пишу парсеры на Python, результат выгружу в чистый Excel или CSV без дублей.\n"
            "С какого сайта нужно собрать и какие поля требуются? Могу сделать быстрый тест на пару строк для проверки."
        )
    else:  # web
        return (
            "Добрый день! Увидел задачу по верстке.\n"
            "Верстаю быстро и адаптивно под мобильные, интерактив и отправку заявок настрою без проблем.\n"
            "Скиньте макет посмотреть, быстро сориентирую по сроку и цене."
        )
