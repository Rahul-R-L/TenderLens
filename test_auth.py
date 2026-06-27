from database.db_postgres import (
    email_exists,
    get_user_by_email
)

print(email_exists("tenderlens191@gmail.com"))

print(get_user_by_email("tenderlens191@gmail.com"))