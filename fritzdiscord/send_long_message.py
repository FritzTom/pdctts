
def make_long_message(message):

    data = """--ajrxovpynwjszirwm
Content-Disposition: form-data; name="payload_json"
Content-Type: application/json

{
  "content": "Long message: ",
  "attachments": [{
      "id": 0,
      "description": "A long message which didn't fit in the 2000 character limit.",
      "filename": "message.txt"
  }]
}
--ajrxovpynwjszirwm
Content-Disposition: form-data; name="files[0]"; filename="message.txt"
Content-Type: text/plain

"""
    return "multipart/form-data; boundary=ajrxovpynwjszirwm", data + message + "\n--ajrxovpynwjszirwm--"
