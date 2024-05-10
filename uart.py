import serial.tools.list_ports
import time
import datetime


def get_port():
    return "COM2"
    # ports = serial.tools.list_ports.comports()
    # n = len(ports)
    # comm_port = "None"
    # for i in range(0, n):
    #     port = ports[i]
    #     str_port = str(port)
    #     # print(str_port)
    #     if "SERIAL" in str_port:
    #         split_port = str_port.split(" ")
    #         comm_port = (split_port[0])
    # return comm_port


COMMAND_FROM_CIRCUIT = {
    "humidity": "humid",
    "temperature": "temp",
    "brightness": "lux",
    "door": "open_door"
}
COMMAND_FROM_SERVER = {
    "password": "password",
    "change password": "change password",
    "fan_level": "fan",
    "light": "light",
    "air_conditioner": "air conditioner",
    "open_door": "door",
    "day": "day",
    "month": "month",
    "year": "year",
    "hour": "hour",
    "minute": "minute"
}
message_from_uart = ""
SER = serial.Serial(port=get_port(), baudrate=115200)
start_time = time.time()


def process_data(data):
    data = data.replace("!", "")
    data = data.replace("#", "")
    split_data = data.split(":")
    name_field = split_data[0]
    value_field = split_data[1]
    return COMMAND_FROM_CIRCUIT[name_field], value_field


def read_serial():
    global message_from_uart
    number_bytes_read = SER.inWaiting()
    if number_bytes_read > 0:
        message_from_uart = message_from_uart + SER.read(number_bytes_read).decode("utf-8")

    result = []
    while '!' in message_from_uart and '#' in message_from_uart:
        start = message_from_uart.index('!')
        end = message_from_uart.index('#')
        message_to_process = message_from_uart[start:end + 1]
        result += [process_data(message_to_process)]
        if end == len(message_from_uart) - 1:
            message_from_uart = ""
        else:
            message_from_uart = message_from_uart[end + 1:]
    return result


def write_data(name=None, value=None):
    name_in_circuit = COMMAND_FROM_SERVER[name]
    if isinstance(value, bool):
        value = "1" if value else "0"
    if not isinstance(value, str):
        value = str(value)
    SER.write(('!' + name_in_circuit + ':' + value + '#').encode())


def get_time(return_second=False):
    now = datetime.datetime.now()
    day = str(now.day)
    month = str(now.month)
    year = str(now.year)
    hour = str(now.hour)
    minute = str(now.minute)
    second = str(now.second)
    if len(day) == 1:
        day = "0" + day
    if len(month) == 1:
        month = "0" + month
    if len(hour) == 1:
        hour = "0" + hour
    if len(minute) == 1:
        minute = "0" + minute
    if len(second) == 1:
        second = "0" + second

    if return_second:
        return day, month, year, hour, minute, second
    return day, month, year, hour, minute


def send_time():
    global start_time
    if time.time() - start_time > 10:
        day, month, year, hour, minute = get_time()
        write_data("day", day)
        write_data("month", month)
        write_data("year", year)
        write_data("hour", hour)
        write_data("minute", minute)
        start_time = time.time()
