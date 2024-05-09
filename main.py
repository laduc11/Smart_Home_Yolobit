import threading
import time

import uart
import database


def receive_data_from_server():
    snapshot_database_changed = threading.Thread(target=database.database_changed)
    snapshot_database_changed.start()

    while True:
        if database.is_database_changed[0]:
            temp = database.prev_database[0]
            database.prev_database[0] = database.DASHBOARD.get()
            # print(f"data from realtime database\n{database.prev_database[0]}")
            for name in ['air_conditioner', 'open_door', 'fan_level', 'light']:
                if temp[name] != database.prev_database[0][name]:
                    uart.write_data(name, database.prev_database[0][name])
                    print(f"name: {name}\tvalue: {database.prev_database[0][name]}")
            database.is_database_changed[0] = False


def receive_data_from_uart():
    while True:
        data = uart.read_serial()
        for factor in data:
            print(f"factor: {factor}")
            database.update_dashboard(factor[0], factor[1])
            if factor[0] == 'open_door':
                if factor[1] == '1':
                    database.log_activity('open door')
                else:
                    database.log_activity('close door')


def update_time_for_circuit():
    while True:
        uart.send_time()
        time.sleep(30)


def main():
    print("gateway is running")

    uart.send_time()

    thread_for_server = threading.Thread(target=receive_data_from_server)
    thread_for_uart = threading.Thread(target=receive_data_from_uart)
    thread_update_time = threading.Thread(target=update_time_for_circuit)

    thread_for_server.start()
    thread_for_uart.start()
    thread_update_time.start()

    thread_for_server.join()
    thread_for_uart.join()
    thread_update_time.join()

    print("end")


if __name__ == '__main__':
    main()
