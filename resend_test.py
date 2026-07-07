from auth import resend, APP_NAME

response = resend.Emails.send({
    "from": f"{APP_NAME} <noreply@tenderlens.in>",
    "to": ["rahulrl191@gmail.com"],
    "subject": "Test",
    "html": "<h1>Hello</h1>"
})

print(response)