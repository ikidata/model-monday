import requests

def get_weather(city: str) -> str:  
    '''
    Common weather REST API
    '''
    url = f"https://wttr.in/{city}?format=j1"  
    try:  
        response = requests.get(url)  
        response.raise_for_status()  # Raise an HTTPError for bad responses  
        current_condition = response.json()['current_condition'][0]  
        return f"Weather in {city} is {current_condition['weatherDesc'][0]['value']}, {current_condition['temp_C']}°C"
    except requests.exceptions.RequestException as e:  
        print(f"Error fetching weather data: {e}")  
        return None 