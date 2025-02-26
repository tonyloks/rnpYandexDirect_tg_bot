# Бот для мониторинга статистики аккаунтов Яндекс Директ

Асинхронный телеграмм бот для получения мониторинга акаунтов Яндекс Директа. 

## Использование и распространение

Вы можете использовать бота для личных и коммерческих целей.
Полная лицензия находится в файле [LICENSE](LICENSE).

## Дополнительные услуги и поддержка

### Техническая поддержка

Вы самостоятельно управляете настройкой и использование бота. Техподдержка не подразумевается.

### Платная интеграция

Если вам нужна помощь с настройкой бота, вы можете обратиться ко мне:
[@poschitai](https://t.me/poschitai)  
Стоимость интеграции: 3000 ₽

### Поддержать проект

Если бот оказался полезным, вы можете поддержать разработку донатом от 100р. на Yoomoney:  
[поблагодарить](https://yoomoney.ru/to/410011521226963)

### Информация о расширенном курсе

Если вам понравился этот продукт, то приглашаю вас на мой курс по полноценной аналитке на стеке технологий ClickHouse и DataLens. 
Полная информация о курсе: [https://t.me/poschitai/275](https://t.me/poschitai/275)

## Инструкция по установке

1. Клонируйте репозиторий
2. Установите зависимости: `pip install -r requirements.txt`
3. Настройте токен бота в `settings/bot.py`
4. Запустите бота: `python main.py`

## 📋 Требования
- Python 3.9+
- SQLite


## Инструкция по использованию
Для добавления аккаунта Яндекс Директ в бота, необходимо:
1. Получить токен доступа к API Яндекс Директ по ссылке: https://oauth.yandex.ru/authorize?response_type=token&client_id=db0084b785964e89908f2b32e246f1de
2. Получить ID целей из Яндекс Метрики в формате: ```11111111,11111111,11111111```
3. Сделать форматирование строчки через ; где указывается логин;токен;ID целей через запятую

*Важно*:
Если у вас нет цели в аккаунте, то впишите ```11111111``` вместо ID целей.


## Разработчикам

Проект построен по модульному принципу:

### База данных [`/database`](database/README.md)
- Хранение данных аккаунтов
- Асинхронные операции с SQLite
- Автоматическая валидация

### Коннекторы [`/connectors`](connectors/README.md)
- Интеграция с API рекламных систем
- Асинхронные запросы
- Обработка ошибок

### Перечисления [`/enums`](enums/README.md)
- Типизация источников данных
- Валидация значений
- Централизованное управление

### Модели [`/models`](models/README.md)
- Pydantic модели данных
- Валидация и сериализация
- Типизация данных

### Модули [`/modules`](modules/README.md)
- Построители отчетов
- Форматирование данных
- Обработка статистики

### Сервисы [`/services`](services/README.md)
- Бизнес-логика
- Обработка отчетов
- Управление данными

### Настройки [`/settings`](settings/README.md)
- Конфигурация компонентов
- Параметры отчетов
- Пороговые значения


### 🔧 Добавление новых систем

Подробные инструкции по добавлению новых рекламных систем:
1. [Добавление коннектора](connectors/README.md)
2. [Создание моделей](models/README.md)
3. [Реализация построителя отчетов](modules/README.md)
4. [Настройка параметров](settings/README.md)


[⬆️ Вернуться наверх](#бот-для-мониторинга-статистики-аккаунтов-яндекс-директ)



