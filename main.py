import threading
import time
import uart
import database
import cv2
import face_recognition.face as model
# import face_recognition.save_pic as update_data


LOCK = threading.Lock()
close_gateway = [False]
turn_on_camera = [False]


def receive_data_from_server(file_name):
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
                    with open(file_name, mode='a') as file:
                        print("Data from server is updated", file=file)
                        print(f"name: {name}\tvalue: {database.prev_database[0][name]}", file=file)
                    LOCK.release()
            database.is_database_changed[0] = False


def receive_data_from_uart(file_name):
    global close_gateway
    while not close_gateway[0]:
        data = uart.read_serial()
        for factor in data:
            LOCK.acquire(blocking=True)
            with open(file_name, mode='a') as file:
                print(f"factor: {factor}", file=file)
            LOCK.release()
            database.update_dashboard(factor[0], factor[1])
            if factor[0] == 'open_door':
                if factor[1] == '1':
                    database.log_activity('open door')
                else:
                    database.log_activity('close door')


def update_time_for_circuit(file_name):
    global close_gateway
    while not close_gateway[0]:
        LOCK.acquire(blocking=True)
        uart.send_time()
        # log activities to file
        with open(file_name, mode='a') as file:
            print("sending time", file=file)
        LOCK.release()
        time.sleep(30)


def send_password():
    global close_gateway
    while not close_gateway[0]:
        if not database.DASHBOARD.get()['open_door']:
            # door is close
            print("The door is closed. Choose the way to open the door")
            print("1. Type the password")
            print("2. Use face recognition")
            option = input("Enter your option: ")
            if option == 'close':
                close_gateway[0] = True
                continue

            while option != '1' and option != '2':
                print("Invalid option")
                option = input("Enter your option: ")

            if option == '1':
                # allow user type password to open it
                password = input("Enter your password: ")
                LOCK.acquire(blocking=True)
                uart.write_data('password', password)
                LOCK.release()
            elif option == '2':
                # call function to detect face before camera
                # return True if correct face else return False
                # input: camera, timeout
                # timeout: run until stop_flag is raised if timeout = -1
                #          else run camera within timeout (s)

                camera = cv2.VideoCapture(0)
                while True:
                    ret, frame = camera.read()
                    cv2.imshow('camera', frame)
                    name, is_known = model.recognize(pic=frame, threshold=0.1)
                    if is_known:
                        print(name)
                        # break
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                camera.release()
                cv2.destroyAllWindows()
        else:
            # door is open
            # allow user change the password or lock the door
            print("The door is opened. Choose your option:")
            print("1. Change your password")
            print("2. Close the door")
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


def open_door_with_face_recognition():
    pass


def main():
    print("gateway is running")
    # log activities to output.log
    log_file = "output.log"

    uart.send_time()

    thread_for_server = threading.Thread(target=receive_data_from_server, args=(log_file,))
    thread_for_uart = threading.Thread(target=receive_data_from_uart, args=(log_file,))
    thread_update_time = threading.Thread(target=update_time_for_circuit, args=(log_file,))
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
    print("end")


if __name__ == '__main__':
    main()
