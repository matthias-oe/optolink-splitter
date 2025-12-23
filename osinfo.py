from datetime import datetime
from logger_util import logger

import settings_ini
import json
import psutil
import mqtt_util

def get_osinfo(**ignored):
    #datetime.now().weekday()
    metrics = {
        'cpu_percent': psutil.cpu_percent(interval=1),
        'cpu_load': list(psutil.getloadavg()),  # [1min, 5min, 15min]
        'cpu_temp': next((t.current for t in psutil.sensors_temperatures().get('cpu_thermal', [])), None),
        'ram_percent': psutil.virtual_memory().percent,
        'disk_percent': psutil.disk_usage('/').percent,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    mqtt_util.mqtt_client.publish(settings_ini.mqtt_topic + "/splitter_cpu_percent", metrics['cpu_percent'], qos=0, retain=False)
    mqtt_util.mqtt_client.publish(settings_ini.mqtt_topic + "/splitter_cpu_load", json.dumps(metrics['cpu_load']), qos=0, retain=False)
    if metrics['cpu_temp'] is not None:
        mqtt_util.mqtt_client.publish(settings_ini.mqtt_topic + "/splitter_cpu_temp", metrics['cpu_temp'], qos=0, retain=False)
    mqtt_util.mqtt_client.publish(settings_ini.mqtt_topic + "/splitter_ram_percent", metrics['ram_percent'], qos=0, retain=False)
    mqtt_util.mqtt_client.publish(settings_ini.mqtt_topic + "/splitter_disk_percent", metrics['disk_percent'], qos=0, retain=False)
    mqtt_util.mqtt_client.publish(settings_ini.mqtt_topic + "/splitter_timestamp", metrics['timestamp'], qos=0, retain=False)  
    
    return 1
