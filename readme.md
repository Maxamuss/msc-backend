# Running the backend

1. Create and run the docker containers:

```bash
docker-compose up -d --build
```

2. Initalise data
```
docker-compose exec web python manage.py initialise
```

3. If prompted to login use: 
email: admin@email.com
password: superuser

4. Make sure frontend is running: https://github.com/Maxamuss/msc-frontend/
