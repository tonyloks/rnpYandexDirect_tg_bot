# Бот для мониторинга статистики аккаунтов Яндекс Директ

Асинхронный телеграмм бот для мониторинга акаунтов Яндекс Директа. 


## Дополнительные услуги и поддержка

#### Техническая поддержка

Вы самостоятельно управляете настройкой и использование бота. Техподдержка не подразумевается.

#### Платная интеграция

Если вам нужна помощь с настройкой бота, вы можете обратиться ко мне:
[@poschitai](https://t.me/poschitai)  
Стоимость интеграции: 3000 ₽

#### Поддержать проект

Если бот оказался полезным, вы можете поддержать разработку донатом от 100р. на Yoomoney:  
[поблагодарить](https://yoomoney.ru/to/410011521226963)

#### Информация о расширенном курсе

Если вам понравился этот продукт, то приглашаю вас на мой курс по полноценной аналитке на стеке технологий ClickHouse и DataLens. 
Полная информация о курсе: [https://t.me/poschitai/275](https://t.me/poschitai/275)

## Инструкция по установке

Полную видео-инструкцию можно посмотреть тут:
[![Видео инструкция по установке]](https://vkvideo.ru/video7686053_456239128)

1. Команды для установки:
```bash
git clone https://github.com/tonyloks/rnpYandexDirect_tg_bot
cd rnpYandexDirect_tg_bot
sh install.sh
```

2. Добавляем токен от ТГ-бота
Вам необходимо в файл .env.local добавить токен по аналогии с .env.example. Если этого файла нет, то создайте его.

Итоговая строчка должна выглядеть так:
```
BOT_TOKEN=1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZ
```

3. Запускаем через пайтон
```bash
python3 main.py
```
Если отображется логика работы и бот откликается - то установка прошла успешно.

4. Запускаем через сервис

Проверяем статус сервиса:
```bash
sudo systemctl status rnpYandexDirect-bot.service 
```
Если сервис не запущен, то запускаем:
```bash
sudo systemctl start rnpYandexDirect-bot.service 
```
Если сервис запущен, то перезапускаем:
```bash
sudo systemctl restart rnpYandexDirect-bot.service 
```



## Инструкция по использованию
Для добавления аккаунта Яндекс Директ в бота, необходимо:
1. Получить токен доступа к API Яндекс Директ под нужным аккаунтом по ссылке: https://oauth.yandex.ru/authorize?response_type=token&client_id=db0084b785964e89908f2b32e246f1de

Как получать токен под разные типы аккаунтов:

*Прямой доступ* - Получаете токен по ссылке

*Агентский и представительский аккаунты* - Токен получаете на главный аккаунт, логины - конечные, откуда берем инфу

#### Важно! 

Сейчас есть баг при выгрузке с представительских аккаунтов, уже в процессе выяснения проблемы с тп Яндекса. 

2. Получить ID целей из Яндекс Метрики в формате: ```11111111,11111111,11111111```
3. Сделать форматирование строчки через ; где указывается логин;токен;ID целей через запятую
В итоге должно получиться так:
```
login;token;11111111,11111111,11111111
```

*Важно*:
Если у вас нет цели в аккаунте, то впишите ```11111111``` вместо ID целей.

## Обновление

Вы можете обновить бота, используя команды:
```bash
cd rnpYandexDirect_tg_bot
git pull
sudo systemctl restart rnpYandexDirect-bot.service 
```
Первая - выгрузит обновления, вторая перезапустит сервис.



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



## Использование и распространение

Вы можете использовать бота для личных. 
Разрешена доработка, распространение при указании авторства.
Использование в коммерческих целях запрещено.
Полная лицензия находится в файле [LICENSE](LICENSE).
