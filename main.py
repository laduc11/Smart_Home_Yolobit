import threading
import time
import uart
import database
import cv2
import face_recognition.face as model


# define global variable
LOCK = threading.Lock()
close_gateway = [False]
camera_on = [False]
picture_from_camera = []
result_from_model = []
user_password = "1016"
enable_faceID = [True]
NUMBER_OF_FACES = 10


def receive_data_from_server(file_name):
    global close_gateway

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
    start_time = time.time()
    while not close_gateway[0]:
        if time.time() - start_time > 30:
            start_time = time.time()
            LOCK.acquire(blocking=True)
            uart.send_time(file_name)
            # log activities to file
            with open(file_name, mode='a') as file:
                print("sending time", file=file)
            LOCK.release()


def process_command_door():
    global close_gateway, enable_faceID
    while not close_gateway[0]:
        if database.DASHBOARD.get()['open_door']:
            enable_faceID[0] = True
            activities_when_door_opened()
        else:
            activities_when_door_closed()


def activities_when_door_closed():
    global enable_faceID
    # door is close
    print("The door is closed. Choose the way to open the door")
    print("1. Type the password")
    print("2. Use face recognition")
    print("If you want to close the gateway, please type close")
    option = input("Enter your option: ")
    if option == 'close':
        # close gateway
        close_gateway[0] = True
        database.stop_check_database[0] = True
    else:
        if option == '1':
            # allow user type password to open it
            password = input("Enter your password: ")
            verify_password(password)
        elif option == '2' and enable_faceID[0]:
            is_open = turn_on_camera()
            if not is_open:
                enable_faceID[0] = False
                database.log_activity(activity_name='Phát hiện người lạ cố gắng mở khóa cửa', actor='Unknown')
        else:
            print("Invalid option")


def activities_when_door_opened():
    global user_password
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
        user_password = new_password
        LOCK.release()
    elif option == '2':
        LOCK.acquire(blocking=True)
        uart.write_data('open_door', '0')
        database.update_dashboard('open_door', '0')
        database.log_activity('Đóng cửa')
        LOCK.release()


def verify_password(password):
    if password == user_password:
        LOCK.acquire(blocking=True)
        uart.write_data('open_door', '1')
        database.update_dashboard('open_door', '1')
        database.log_activity('Cửa được mở bằng mật khẩu')
        LOCK.release()
    else:
        print("Wrong password")


def turn_on_camera():
    # delete all old picture
    LOCK.acquire(blocking=True)
    while len(picture_from_camera) > 0:
        picture_from_camera.pop()
    LOCK.release()
    # delete all old results
    LOCK.acquire(blocking=True)
    while len(result_from_model) > 0:
        result_from_model.pop()
    LOCK.release()
    # turn on camera and stream the video real time
    camera = cv2.VideoCapture(0)
    # set flag camera to True
    LOCK.acquire(blocking=True)
    camera_on[0] = True
    LOCK.release()
    counter = NUMBER_OF_FACES
    # stream video using open-cv
    while True:
        ret, frame = camera.read()
        cv2.imshow('camera', frame)  # show a frame
        if len(result_from_model) > 0:
            # get result after run model recognize face
            LOCK.acquire(blocking=True)
            name, is_known = result_from_model[-1]
            LOCK.release()
            if is_known:
                # if finding best face, return the name of person who open the door
                print(f"person unlock the door: {name}")
                # send command unlock through uart and history message to firebase
                LOCK.acquire(blocking=True)
                uart.write_data('open_door', '1')
                LOCK.release()
                database.log_activity('Đã xác minh khuôn mặt để mở cửa', actor=name)
                database.update_dashboard('open_door', '1')
                break
            else:
                counter -= 1
            result_from_model.pop()
        if counter == 0:
            break
        # save the frame to recognize face
        if len(picture_from_camera) == 0:
            LOCK.acquire(blocking=True)
            picture_from_camera.append(frame)
            LOCK.release()
        # turn off camera by pressing q button
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    camera.release()  # turn off the camera
    # set flag camera to False
    LOCK.acquire(blocking=True)
    camera_on[0] = False
    LOCK.release()
    cv2.destroyAllWindows()
    if counter == 0:
        return False
    return True


def open_door_with_face_recognition():
    while not close_gateway[0]:
        if camera_on[0] and len(picture_from_camera) > 0:
            name, is_known = model.recognize(pic=picture_from_camera[0], threshold=0.9)
            LOCK.acquire(blocking=True)
            result_from_model.append((name, is_known))
            picture_from_camera.pop(0)
            LOCK.release()


def main():
    print("gateway is running")
    # log activities to output.log
    log_file = "output.log"
    # clear file
    with open(log_file, mode='w') as file:
        file.write("")

    uart.send_time(log_file)

    thread_for_server = threading.Thread(target=receive_data_from_server, args=(log_file,))
    thread_for_uart = threading.Thread(target=receive_data_from_uart, args=(log_file,))
    thread_update_time = threading.Thread(target=update_time_for_circuit, args=(log_file,))
    thread_for_password = threading.Thread(target=process_command_door)
    thread_for_recognize_face = threading.Thread(target=open_door_with_face_recognition)
    snapshot_database_changed = threading.Thread(target=database.database_changed)

    thread_for_server.start()
    thread_for_uart.start()
    thread_update_time.start()
    thread_for_password.start()
    thread_for_recognize_face.start()
    snapshot_database_changed.start()

    thread_for_server.join()
    thread_for_uart.join()
    thread_update_time.join()
    thread_for_password.join()
    thread_for_recognize_face.join()
    snapshot_database_changed.join()

    print("gateway is closed")


if __name__ == '__main__':
    main()
