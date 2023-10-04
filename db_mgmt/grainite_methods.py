import requests

def get_cost_by_sub(payload):
    url = "http://20.169.138.117:5100/GetCostBySub"
    response = requests.post(url, json=payload)
    res_dict = response.json()
    return res_dict.get("data", [])

if __name__ == "__main__":
    payload = {
    "sub_id":"afb3f2d0-f6fc-4391-b9db-bf2cde678ccf",
    "date_range":["2023-04-10", "2023-04-25"]
}
    get_cost_by_sub(payload)
