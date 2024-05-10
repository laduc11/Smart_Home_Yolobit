import threading
import time
import uart
import database


LOCK = threading.Lock()
LOG_FILE = open('output.log', 'w')
close_gateway = [False]


def receive_data_from_server():
    global close_gateway
    snapshot_database_changed = threading.Thread(target=database.database_changed)
    snapshot_database_changed.start()

    while not close_gateway[0]:
        if database.is_database_changed[0]:
            temp = database.prev_database[0]
            database.prev_database[0] = database.DASHBOARD.get()
            for name in ['air_conditioner', 'open_door', 'fan_level', 'light']:
                if temp[name] != database.prev_database[0][name]:
                    LOCK.acquire(blocking=True)
                    uart.write_data(name, database.prev_database[0][name])
                    print("Data from server is updated", file=LOG_FILE)
                    print(f"name: {name}\tvalue: {database.prev_database[0][name]}", file=LOG_FILE)
                    LOCK.release()
            database.is_database_changed[0] = False


def receive_data_from_uart():
    global close_gateway
    while not close_gateway[0]:
        data = uart.read_serial()
        for factor in data:
            print(f"factor: {factor}", file=LOG_FILE)
            database.update_dashboard(factor[0], factor[1])
            if factor[0] == 'open_door':
                if factor[1] == '1':
                    database.log_activity('open door')
                else:
                    database.log_activity('close door')


def update_time_for_circuit():
    global close_gateway
    while not close_gateway[0]:
        LOCK.acquire(blocking=True)
        uart.send_time()
        LOCK.release()
        time.sleep(30)


def send_password():
    global close_gateway
    while not close_gateway[0]:
        if not database.DASHBOARD.get()['open_door']:
            # door is close
            # allow user type password to open it
            password = input("Enter your password: ")
            LOCK.acquire(blocking=True)
            uart.write_data('password', password)
            LOCK.release()
        else:
            # door is open
            # allow user change the password or lock the door
            print("You can change your password or close the door")
            print("Type 1 to change your password and 2 to close the door")
            option = input("Enter your option: ")
            while option != '1' and option != '2':
                print("Invalid option")
                option = input("Enter your option: ")

            if option == '1':
                new_password = input("Enter your new password: ")
                LOCK.acquire(blocking=True)
                uart.write_data('change password', new_password)
                LOCK.release()
            elif option == '2':
                LOCK.acquire(blocking=True)
                uart.write_data('open_door', '0')
                database.update_dashboard('open_door', False)
                LOCK.release()
                pass
            pass


def main():
    global LOG_FILE
    print("gateway is running")

    uart.send_time()

    thread_for_server = threading.Thread(target=receive_data_from_server)
    thread_for_uart = threading.Thread(target=receive_data_from_uart)
    thread_update_time = threading.Thread(target=update_time_for_circuit)
    thread_for_password = threading.Thread(target=send_password)

    thread_for_server.start()
    thread_for_uart.start()
    thread_update_time.start()
    thread_for_password.start()

    thread_for_server.join()
    thread_for_uart.join()
    thread_update_time.join()
    thread_for_password.join()

    uart.SER.close()
    LOG_FILE.close()
    print("end")


if __name__ == '__main__':
    main()
