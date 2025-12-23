'''
   Copyright 2024 philippoo66
   
   Licensed under the GNU GENERAL PUBLIC LICENSE, Version 3 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       https://www.gnu.org/licenses/gpl-3.0.html

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
'''
import os
import importlib
import json
from typing import Optional, Any, Dict, Tuple
from logger_util import logger
import c_polllist

def get_env(key: str, default: Any, type_converter=None) -> Any:
    """Universal ENV-Getter mit Type-Conversion."""
    env_value = os.environ.get(key)
    if env_value is not None:
        if type_converter:
            return type_converter(env_value)
        return env_value
    return default

def bool_env(value: str) -> bool:
    return value.lower() in ('true', '1', 'yes', 'on')

def int_env(value: str) -> int:
    try:
        return int(value)
    except ValueError:
        raise ValueError(f"Invalid integer for env var: {value}")

def float_env(value: str) -> float:
    value = value.replace(',', '.')
    try:
        return float(value)
    except ValueError:
        raise ValueError(f"Invalid float for env var: {value}")

def dict_env(value: str, default: dict) -> dict:
    """JSON-String zu Dict"""
    try:
        return json.loads(value) if value else default
    except json.JSONDecodeError:
        print(f"Warning: Invalid JSON in {value}, using default")
        return default

def plugins_env(value: str) -> dict:
    if not value:
        return {}
    plugins = {}
    for item in value.split(','):
        parts = item.split(':')
        if len(parts) >= 4:
            name, module, func, interval = parts[0:4]
            plugins[name] = {
                'module': module,
                'func': func,
                'interval': int(interval)
            }
    return plugins


def build_plugin_registry(plugins):
    plugin_registry = {}
    for name, config in plugins.items():
        try:
            if(os.path.exists(config['module']+".py")):
                logger.info(f"import {config['module']}")
                module = importlib.import_module(config['module'])
            else:
                 print(f"could not load plugin {name}: {config['module']+".py"} does not exist")
                 continue
            func = getattr(module, config['func'])
            plugin_registry[name] = {
                'module': module,
                'func': func,
                'interval': config['interval']
            }
            print(f"{name}: {config['module']}.{config['func']} every {config['interval']}")
        except (ImportError, AttributeError) as e:
            print(f"could not load plugin {name}: {e}")
    return plugin_registry

# Serial Ports +++++++++++++++++++
port_optolink = get_env('OPTO_PORT', '/dev/ttyUSB0')
port_vitoconnect = get_env('VITOCONNECT_PORT', '/dev/ttyAMA0')
vs2timeout = get_env('VS2_TIMEOUT', 120, int_env)
vs1protocol = get_env('VS1_PROTOCOL', False, bool_env)

# MQTT Connection ++++++++++++++++
mqtt = get_env('MQTT_BROKER', "192.168.0.123:1883")
mqtt_user = get_env('MQTT_USER', None)
mqtt_logging = get_env('MQTT_LOGGING', False, bool_env)

# MQTT Topics ++++++++++++++++++++
mqtt_topic = get_env('MQTT_TOPIC', "Vito")
mqtt_listen = get_env('MQTT_LISTEN', "Vito/cmnd")
mqtt_respond = get_env('MQTT_RESPOND', "Vito/resp")
mqtt_fstr = get_env('MQTT_FSTR', "{dpname}")
mqtt_retain = get_env('MQTT_RETAIN', False, bool_env)
mqtt_no_redundant = get_env('MQTT_NO_REDUNDANT', False, bool_env)

# TCP/IP ++++++++++++++++++++++++++
tcpip_port = get_env('TCPIP_PORT', 65234, int_env)

# Optolink Communication Timing +++
fullraw_eot_time = get_env('FULLRAW_EOT_TIME', 0.05, float_env)
fullraw_timeout = get_env('FULLRAW_TIMEOUT', 2, float_env)
olbreath = get_env('OL_BREATH', 0.05, float_env)

# Optolink Logging +++++++++++++++
log_vitoconnect = get_env('LOG_VITOCONNECT', False, bool_env)
show_opto_rx = get_env('SHOW_OPTO_RX', True, bool_env)
viconn_to_mqtt = get_env('VICONN_TO_MQTT', True, bool_env)
no_logger_file = get_env('NO_LOGGER_FILE', False, bool_env)

# Data Formatting ++++++++++++++++
max_decimals = get_env('MAX_DECIMALS', 4, int_env)
data_hex_format = get_env('DATA_HEX_FORMAT', '02x')
resp_addr_format = get_env('RESP_ADDR_FORMAT', 'x')

# Viessdata Utilities ++++++++++++
write_viessdata_csv = get_env('WRITE_VIESS_DATA_CSV', False, bool_env)
viessdata_csv_path = get_env('VIESS_DATA_CSV_PATH', "")
buffer_to_write = get_env('BUFFER_TO_WRITE', 60, int_env)
dec_separator = get_env('DEC_SEPARATOR', ",")

# Plugins ++++++++++++++++++++
#wo1c_energy = get_env('WO1C_ENERGY', 0, int_env)
plugins = get_env('PLUGINS', '', plugins_env)
plugin_registry = build_plugin_registry(plugins)

# 1. Alle Plugins laden

# 1-Wire Sensors +++++++++++++++++
# TODO: convert ENV to correct struct 
# w1sensors = get_env('W1_SENSORS', {}, dict_env)

# A typical sensor for temperature could be DS18B20; please mind that GPIO must be enabled for 1-Wire sensors (see Optolink-Splitter Wiki),
# Dictionary for 1-Wire sensor configuration (default: empty dictionary),
w1sensors = {                  
    # Addr: ('<w1_folder/sn>', '<slave_type>'),,   # entry format
#     0xFFF4: ('28-3ce1d4438fd4', 'ds18b20'),,     # Example sensor (highest known Optolink Address is 0xFF17),
#     0xFFFd: ('28-3ce1d443a4ed', 'ds18b20'),,     # Another example sensor
}


# Polling interval (seconds), 0 for continuous, -1 to disable (default: 30)
poll_interval = get_env('POLL_INTERVAL', 30, int_env)
poll_item_module = get_env('POLL_ITEM_MODULE', None)

if poll_item_module is None: # Datapoints defined here will be polled
    poll_items = [                  
        # ([PollCycle,] Name, DpAddr, Length [, Scale/Type [, Signed]),
           # PollCycle:   Optional entry to allow the item to be polled only every x-th cycle
           # Name:        Datapoint name, published to MQTT as {dpname}; Best practices recommendation: Always use lowercase Names for consistency and compatibility.
           # DpAddr:      Address used to read the datapoint value (hex with '0x' or decimal)
           # Length:      Number of bytes to read
           # Scale/Type:  Optional; if omitted, value returns as a hex byte string without '0x'. See Wiki for details
           # Signed:      Numerical data will interpreted as signed (True) or unsigned (False, default is False if not explicitly set)
       
        # Example for Vitocalxxx-G with Vitotronic 200 (Typ WO1C) (from 04/2012)
        ("error", 0x0491, 1, 1, False),
        ("outside_temperature", 0x0101, 2, 0.1, True),
        ("hk1_mode", 0xB000, 1, 1, False),			# betriebsart bit 4,5,6,7 comfort  bit 1 spar bit 0
        ("hk1_requested_temperature", 0xA406, 2, 0.01, False),
        ("hk1_normal_temperature", 0x2000, 2, 0.1, False),
        ("hk1_reduced_temperature", 0x2001, 2, 0.1, False),
        ("hk1_party_temperature", 0x2022, 2, 0.1, False),
        ("hk1_temperature", 0x0116, 2, 0.1, False),
        ("hk1_pump", 0x048D, 1, 1, False),
        ("hk1_supply_temperature", 0x010A, 2, 0.1, False),
        ("hk1_supply_target_temperature", 0x1800, 2, 0.1, False),
        ("hk2_mode", 0xB001, 1, 1, False),
        ("hk2_requested_temperature", 0xA446, 2, 0.01, False),
        ("hk2_normal_temperature", 0x3000, 2, 0.1, False),
        ("hk2_reduced_temperature", 0x3001, 2, 0.1, False),
        ("hk2_party_temperature", 0x3022, 2, 0.1, False),
        ("hk2_temperature", 0x0117, 2, 0.1, False),
        ("hk2_pump", 0x048E, 1, 1, False),
        ("hk2_supply_temperature", 0x0114, 2, 0.1, False),
        ("hk2_supply_target_temperature", 0x1801, 2, 0.1, False),
        ("buffer_temperature", 0x010B, 2, 0.1, False),
        ("nc_cooling", 0x0492, 1, 1, False),
        ("primary_supply_temperature", 0xB400, 3, 'b:0:1', 0.1, True), # Datalänge 3,Byte 0-1 Temperatur, Byte 3 Sensorstatus: 0-OK, 6-Nicht vorhanden
        ("primary_return_temperature", 0xB401, 3, 'b:0:1', 0.1, True),
        ("secondary_supply_temperature", 0xB402, 3, 'b:0:1', 0.1, True),
        ("secondary_return_temperature", 0xB403, 3, 'b:0:1', 0.1, True),
        ("liquid_gas_temperature", 0xB404, 3, 'b:0:1', 0.1, True),
        ("evaporation_temperature", 0xB407, 3, 'b:0:1', 0.1, True),
        ("condensation_temperature", 0xB408, 3, 'b:0:1', 0.1, True),
        ("suction_gas_temperature", 0xB409, 3, 'b:0:1', 0.1, True),
        ("hot_gas_temperature", 0xB40A, 3, 'b:0:1', 0.1, True),
        ("superheating_target", 0xB40B, 3, 'b:0:1', 0.1, True),
        ("superheating", 0xB40D, 3, 'b:0:1', 0.1, True),
        ("suction_gas_pressure", 0xB410, 3, 'b:0:1', 0.1, True),
        ("hot_gas_pressure", 0xB411, 3, 'b:0:1', 0.1, True),
        ("primary_pump", 0xB420, 2, 1, False),
        ("secondary_pump", 0xB421, 2, 1, False),
        ("compressor", 0xB423, 2, 1, False),
        ("expansion_valve", 0xB424, 2, 1, False),
        ("nc_supply_temperature", 0x0119, 2, 0.1, False),
        ("nc_supply_target_temperature", 0x1804, 2, 0.1, False),
        ("eheater_power", 0x1909, 1, 3000, False),
        ("eheater_3_energy", 0x0588, 4,  0.0008333, False),
        ("eheater_6_energy", 0x0589, 4,  0.0016667, False),
        ("thermal_energy", 0x1640, 4, 0.1, False),
        ("electrical_energy", 0x1660, 4, 0.1, False),
        ("thermal_power", 0x16A0, 4, 1, False),
        ("electrical_power", 0x16A4, 4, 1, False),
        (60, "cop", 0x1680, 1, 0.1, False), # Poll every 60th poll cycle (if poll_interval = 30 => 60 x 30 = every 30 minutes)

        # Example for Vitodens 300 B3HB
        # ("Anlagenzeit", 0x088E, 8, 'vdatetime'),
        # ("AussenTemp", 0x0800, 2, 0.1, True),
        # ("KesselTemp", 0x0802, 2, 0.1, False),
        # ("SpeicherTemp", 0x0804, 2, 0.1, False),
        # ("AbgasTemp", 0x0808, 2, 0.1, False),
        # ("AussenTemp_fltrd", 0x5525, 2, 0.1, True),
        # ("AussenTemp_dmpd", 0x5523, 2, 0.1, True),
        # ("AussenTemp_mixed", 0x5527, 2, 0.1, True),
        # ("Eingang STB-Stoerung", 0x0A82, 1, 1, False),
        # ("Brennerstoerung", 0x0884, 1, 1, False),
        # ("Fehlerstatus Brennersteuergeraet", 0x5738, 1, 1, False),
        # ("Brennerstarts", 0x088A, 4, 1, False),
        # ("Betriebsstunden", 0x08A7, 4, 2.7777778e-4, False),  # 1/3600
        # ("Stellung Umschaltventil", 0x0A10, 1, 1, False),
        # ("Ruecklauftemp_calcd", 0x0C20, 2, 0.01, False),
        # ("Pumpenleistung", 0x0A3C, 1, 1, False),
        # ("Volumenstrom", 0x0C24, 2, 0.1, False),  # eigentlich scale 1 aber für Viessdata Grafik
        # ("KesselTemp_soll", 0x555A, 2, 0.1, False),
        # ("BrennerLeistung", 0xA38F, 1, 0.5, False),
        # ("BrennerModulation", 0x55D3, 1, 1, False),
        # ("Status", 0xA152, 2, 1, False),
        # ("SpeicherTemp_soll_akt", 0x6500, 2, 0.1, False),
        # ("Speicherladepumpe", 0x6513, 1, 1, False),
        # ("Zirkulationspumpe", 0x6515, 2, 1, False),

        # # ByteBit filter examples
        # ("Frostgefahr, aktuelle RTS etc", 0x2500, 22, 'b:0:21::raw'),
        # ("Frostgefahr", 0x2500, 22, 'b:16:16', 'bool'),
        # ("RTS_akt", 0x2500, 22, 'b:12:13', 0.1, True),
        # ("VL_Soll_M2", 0x3500, 22, 'b:17:18', 0.1, True),
        
        # # 1-wire
        # ("SpeicherTemp_oben", 0xFFFd),
        # ("RuecklaufTemp_Sensor", 0xFFF4),
    ]
else:
    if(os.path.exists(poll_item_module + ".py")):
            logger.info(f"import {poll_item_module}.py")
            user_defined = importlib.import_module(poll_item_module)
            poll_items = user_defined.poll_items

# for global use
poll_list = c_polllist.cPollList(poll_items)


