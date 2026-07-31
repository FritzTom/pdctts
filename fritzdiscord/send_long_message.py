import requests

def send_long_message(message, channel_id):
    
    file = open("./token", "r")
    token = file.read().strip()
    file.close()



    data = """--boundary
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
--boundary
Content-Disposition: form-data; name="files[0]"; filename="message.txt"
Content-Type: text/plain

"""







    res = requests.post(f"https://discord.com/api/v9/channels/{channel_id}/messages", headers={"Authorization":  token, "Content-type": "multipart/form-data; boundary=boundary"}, data=data + message + "\n--boundary--")
    return res.text
