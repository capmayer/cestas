Usefull Commands
======================================================================

Build images::

    docker-compose -f local.yml build

Bring things alive::

    docker-compose -f local.yml up -d

Shut the machines off::

    docker-compose -f local.yml down

What happen?::

    docker-compose -f local.yml logs

Make migrations::

    docker-compose -f local.yml run --rm django python manage.py makemigrations

Migrate::

    docker-compose -f local.yml run --rm django python manage.py migrate

Superuser::

    docker-compose -f local.yml run --rm django python manage.py createsuperuser

To build and serve docs, use the commands::

    docker-compose -f local.yml up docs


In project folder, run those commands:
`alias dbuild="docker-compose -f local.yml build"`
`alias dup="docker-compose -f local.yml up -d"`
`alias ddown="docker-compose -f local.yml down"`
`alias dmigrate="docker-compose -f local.yml run --rm django python manage.py migrate"`
`alias dmake="docker-compose -f local.yml run --rm django python manage.py makemigrations"`
`alias dsuperuser="docker-compose -f local.yml run --rm django python manage.py createsuperuser"`
