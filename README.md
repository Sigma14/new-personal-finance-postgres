# Personal Finance Backend Requirements & Setup

## Requirements

1. Python 3.7.4

2. Docker 20.10.3

3. Mongodb 4.4

## Docker Setup

1. Need to installed docker runtime engine on your server/Desktop.
   
   **windows:**
   ```shell
    https://docs.docker.com/desktop/install/windows-install/
   ```
   **linux:**
   ```shell
    https://docs.docker.com/desktop/install/linux-install/
   ```
   **mac:**
   ```shell
   https://docs.docker.com/desktop/install/mac-install/
   ```

2. Build docker containers.
   ```shell
   sudo docker-compose up --build
   ```

3. If **MongoDb** database does not exists please create database(**personal_finance**).

4. Again build docker containers. 
   ```shell
   sudo docker-compose up --build
   ```
5. Check all the containers are successfully running or not.
   ```shell
   sudo docker ps
   ```

## Admin Setup

1. Create admin credentials for the first time.

   ```shell
   sudo docker exec -it <CONTIANER_ID> bash
   
   # firstly migrate all the migration files using following cmd
   python manage.py migrate

   # Once you enter bash. Use the following command to set email and pass for the superuser / admin
   python manage.py createsuperuser
   ```

## Frontend Call

1. Login with **admin** credentials.

   ```shell
   http://localhost:8072/   
   ```

