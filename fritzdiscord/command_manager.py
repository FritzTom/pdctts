import requests

def add_command(token :str, application_id :str, name :str, type :int, description :str|None = None, options :list|None = None) -> str:
    url = f"https://discord.com/api/v9/applications/{application_id}/commands"
    json = {
        "name": name,
        "type": type
    }
    if description is not None: json["description"] = description
    if options is not None: json["options"] = options
    headers = {"Authorization": f"Bot {token}"}
    res = requests.post(url, headers=headers, json=json)
    data = res.json()
    return data


def delete_command(token :str, application_id : str, command_id :str):
    url = f"https://discord.com/api/v9/applications/{application_id}/commands/{command_id}"
    headers = {"Authorization": f"Bot {token}"}
    res = requests.delete(url, headers=headers)
    if res.status_code == 204:
        return True
    return res.json()


def get_commands(token :str, application_id :str):
    url = f"https://discord.com/api/v9/applications/{application_id}/commands"
    headers = {"Authorization": f"Bot {token}"}
    res = requests.get(url, headers=headers)
    return res.json()