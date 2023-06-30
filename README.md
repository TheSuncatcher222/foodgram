# __Foodgram__

###### Твой личный продуктовый помощник.

___

### Введение

Foodgram - это веб-приложение, которое поможет вам найти новинки в мире рецептов, а также публиковать свои собственные шедевры. Помимо этого вы можете составлять свою личную коллекцию избранных кулинарных произведений, подписываться на авторов, планировать покупки в магазине и многое другое. Foodgram - идеальный инструмент для тех, кто ищет вдохновение в кулинарии и хочет упростить свою повседневную жизнь.

___

### Описание проекта

Foodgram представляет собой продуктовый помощник, который позволяет пользователям публиковать и искать рецепты.

Каждый рецепт содержит:
\- название;
\- расчетное время приготовления (в минутах);
\- перечень ингредиентов с указанием наименования и дозировки;
\- текстовое описание-инструкцию;
\- теги, которые позволяют быстро фильтровать рецепты;
\- изображение-превью

Пользователи могут добавлять рецепты в избранное, подписываться на авторов и просматривать все их рецепты в разделе "Мои подписки". Также имеется возможность добавлять рецепты в корзину и скачивать файл CSV, содержащий суммарный список ингредиентов для рецептов в корзине.

Foodgram предоставляет удобный и интуитивно понятный интерфейс для управления рецептами и упрощает покупку необходимых продуктов.

Также взаимодействие с приложением возможно осуществлять через API запросы.

___

### Технологии

Foodgram разработан с использованием следующих технологий:

- [Python] (v.3.11) - целевой язык программирования backend
- [Django] (v.4.1) - высокоуровневый веб-фреймворк
- [Django REST framework] (v.3.12.4) - инструмент для создания Web API
- [Simple JWT] (v.2.1.0) - плагин, предоставляющий JSON Web Token аутентификацию для Django REST Framework, разработанную в соответствии со стандартом RFC 7519
- [Gunicorn] (v.20.1) - Python WSGI HTTP-сервер для UNIX
- [Nginx] - HTTP-сервер и обратный прокси-сервер
- [PostgreSQL] (v.13.10) - объектно-реляционная база данных
- [Docker] (v.24.0) - инструмент для автоматизирования процессов разработки, доставки и запуска приложений в контейнерах
- [NodeJS] (v.13.12) - это среда выполнения JavaScript
- [JavaScript] - мультипарадигменный язык программирования frontend
- [React] - библиотека JavaScript для разработки пользовательских интерфейсов (UI) веб-приложений

![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54) ![Django](https://img.shields.io/badge/django-%23092E20.svg?style=for-the-badge&logo=django&logoColor=white) ![DjangoREST](https://img.shields.io/badge/DJANGO-REST-ff1709?style=for-the-badge&logo=django&logoColor=white&color=ff1709&labelColor=gray) ![JWT](https://img.shields.io/badge/JWT-black?style=for-the-badge&logo=JSON%20web%20tokens) ![Gunicorn](https://img.shields.io/badge/gunicorn-%298729.svg?style=for-the-badge&logo=gunicorn&logoColor=white) ![Postgres](https://img.shields.io/badge/postgres-%23316192.svg?style=for-the-badge&logo=postgresql&logoColor=white) ![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white) ![Nginx](https://img.shields.io/badge/nginx-%23009639.svg?style=for-the-badge&logo=nginx&logoColor=white) ![NodeJS](https://img.shields.io/badge/node.js-6DA55F?style=for-the-badge&logo=node.js&logoColor=white) ![JavaScript](https://img.shields.io/badge/javascript-%23323330.svg?style=for-the-badge&logo=javascript&logoColor=%23F7DF1E) ![React](https://img.shields.io/badge/react-%2320232a.svg?style=for-the-badge&logo=react&logoColor=%2361DAFB)

___

### Развертывание

Запуск в контейнере DockerHub и организация CI/CD с помощью GitHub Actions

### 1. Создание и развертка контейнеров проекта:

Форкнуть репозиторий, сконировать и перейти в рабочую корневую папку `foodgram-project-react`

Переименовать .env.example в .env и заполнить по шаблону:

```
mv .env.example .env
nano .env
```

Убедиться, что сервис (демон) Docker активен в системе:

```
# Для Linux
sudo systemctl status docker
# Для Windows и MacOS вызвать диспетчер задач и убедиться, что процесс(ы) Docker Desktop запущен(ы)
```

Развернуть контейнерное пространство:

(!) если развертка происходит впервые:

- необходимо открыть docker-compose.yml и запенить для каждого из контейнеров `backend`,  `frontend`, `gateway` способ выбора образа с `image` на `build` - таким образом будут созданы исходные docker образы проекта
- впоследствии возможно создать свои образы `backend`,  `frontend`, `gateway` и использовать параметр `image`

```
nano docker-compose.yml
```
```
....
backend:
   ...foodgram
   # эту строку строку ниже:
   image: <username>/foodgram_backend
   # заменить на:
   build: ./backend/
   ...
frontend:
   ...
   # эту строку строку ниже:
   image: <username>foodgram_frontend
   # заменить на:
   build: ./frontend/
   ...
gateway:
   ...
   # эту строку строку ниже:
   image: <username>/foodgram_gateway
   # заменить на:
   build: ./nginx/
   ...
```

Развернуть контейнерную группу в виде фонового демона:

```
docker compose up -d
```

Настроить миграции backend:

```
docker compose exec backend python manage.py makemigrations foodgram_app
docker compose exec backend python manage.py migrate
```

Настроить Ваш сервер на отправку запросов к сайту Foodgram на порт 8000 (согласно настройке образа `nginx`).
   
2. Создания CI/CD на GitHub Actions

Создать в корне проекта скрытую директиву для размещения файла с инструкциями для GitHub Actions:

```
mkdir .github/workflows
```

Переместить файл `foodgram_workflow.yml` в созданную директорию:

```
mv foodgram_workflow.yml ./.github/workflows/foodgram_workflow.yml
```

Перейти в раздел с проектом на GutHub -> Settings -> Secrets and variables -> actions

В разделе `secrets` создать (кнопка `New repository secret`) следующие "секреты":
- DOCKERHUB_USERNAME - имя пользователя DockerHub аккаунта
- DOCKERHUB_PASSWORD - пароль от DockerHub аккаунта
- SSH_HOST - ваш публичный IP сервера*
- SSH_KEY - SSH-ключ доступа к серверу*, начиная с `-----BEGIN OPENSSH PRIVATE KEY-----` и заканчивая `-----END OPENSSH PRIVATE KEY-----`
- SSH_USERNAME - имя пользователя учетной записи на сервере*
- SSH_PASSPHRASE - пароль учетной записи на сервере*
- TELEGRAM_BOT_TOKEN - токен Telegram Bot**, который будет уведомлять об успешном деплое проекта на сервере
- TELEGRAM_ME_ID - ID пользователя Telegram, которому бот будет присылать сообщения

\* под сервером имеется ввиду сервер, на котором разворачивается Foodgram
\*\* если уведомления в телеграм не нужны, необходимо из `foodgram_workflow.yml` удалить задание `send_message_telegram`

3. Результаты работы

Теперь при каждом обновлении ветки main репозитория:
- запустятся автотесты приложения `backend`
- автоматически обновятся контейнеры `backend`, `frontend`, `gateway`
- контейнеры отправятся на DockerHub облако
- контейнеры скачаются с DockerHub облако на сервер и перезапустятся

### 2. Взаимодействие по API:
Веб-приложение позволяет взаимодействовать с базой данных также посредством публичного API. Полная документация доступна в отдельном контейнере.

Перейти в папку с инфраструктурой:
```
cd infra
```

Развернуть контейнерную группу в виде фонового демона:
```
docker compose up -d
```

При выполнении этой команде сервис frontend, описанный в docker-compose.yml подготовит файлы, необходимые для работы frontend-приложения, а затем прекратит свою работу.

Проект запустится на адресе http://localhost, увидеть спецификацию API вы сможете по адресу http://localhost/api/docs/.

Некоторые примеры API запросов и ответов:

- получение списка рецептов

```
### GET: список ингредиентов.
GET http://foodgram.com/api/ingredients/ HTTP/1.1
Content-Type: application/json
Authorization: Token cee91dc5e2f232fc50cad1e7b706f9b52d2c689d
```
```
HTTP/1.1 200 OK
Server: nginx
Content-Type: application/json
...

{
  "count": 7,
  "next": "http://foodgram.com/api/v1/recipes/?page=2",
  "previous": null,
  "results": [
    {
      "id": 7,
      "tags": [
        {
          "id": 1,
          "name": "фрукты",
          "color": "#000000",
          "slug": "fruits"
        }
        ...
      ],
      "author": {
        "email": "iVan@email.com",
        "id": 1,
        "username": "iVan",
        "first_name": "Иван",
        "last_name": "Иванов",
        "is_subscribed": false
      },
      "ingredients": [
        {
          "id": 1,
          "name": "вишня",
          "measurement_unit": "г",
          "amount": 777.0
        }
        ...
      ],
      "is_favorited": false,
      "is_in_shopping_cart": false,
      "name": "Клубника в сливках",
      "image": "http://foodgram.com/media/recipes/images/image_LMcH2py.jpeg",
      "text": "Тут текст рецепта",
      "cooking_time": 15
    },
    ...
  ]
}
```

- запрос на получение токена

```
POST http://foodgram.com/api/v1/auth/token/login/ HTTP/1.1
Content-Type: application/json

{
    "email": "iVan@email.com",
    "password": "12345"
}
```
```
HTTP/1.1 200 OK
Server: nginx
Content-Type: application/json
...

{
  "auth_token": "aaAAaa111A1A1aa"
}
```

- получение списка ингредиентов из рецептов в корзине

```
### GET: скачать корзину в CSV.
GET http://foodgram.com/api/recipes/download_shopping_cart/ HTTP/1.1
Content-Type: application/json
Authorization: Token a8bf69c882f620d322ff504c6d21ccfcc28b46e9
```

```
HTTP/1.1 200 OK
Server: nginx
Content-Type: text/csv
...

name,measurement_unit,amount
клубника,г,777.0
ежевика,г,222.0
...
```

___

### LICENCE

MIT 
**Free Software, Hell Yeah!**

Created by [Altair21817]

[Altair21817]: <https://github.com/altair21817/>

[Docker]: <https://www.docker.com/>
[Django]: <https://www.djangoproject.com/>
[Django REST framework]: <https://https://www.django-rest-framework.org/>
[Gunicorn]: <https://gunicorn.org/>
[JavaScript]: <https://www.ecma-international.org/publications-and-standards/standards/ecma-262/>
[Nginx]: <https://nginx.org/>
[NodeJS]: <https://nodejs.org/en>
[PostgreSQL]: <https://www.postgresql.org/>
[Python]: <https://www.python.org/>
[React]: <https://react.dev/>
[Simple JWT]: <https://django-rest-framework-simplejwt.readthedocs.io/>
