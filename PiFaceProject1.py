import os
import pifacecad as p
import random
import smtplib
import sys
import time

cad = p.PiFaceCAD()

def authentication_numbers():
    return [random.randint(0, 9) for p in range(0, 4)]

def sending_mail(input):

    SERVER = 'smtp.gmail.com'
    FROM = 'tkdemoprojects@gmail.com'
    PASSW = 'pxxlkdhmbngmtwrs'
    TO = 'teemu.kukko@gmail.com'

    PORT = 587

    with smtplib.SMTP(SERVER, PORT) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()

        smtp.login(FROM, PASSW)    

        SUBJECT = 'Verification code'
        BODY = f'You are trying to open virtual locker.\n\n\nAuthentication code is: {input}'
        MESSAGE = f'Subject: {SUBJECT}\n\n{BODY}'

        smtp.sendmail(FROM, TO, MESSAGE)

def error_mail(input):

    SERVER = 'smtp.gmail.com'
    FROM = 'tkdemoprojects@gmail.com'
    PASSW = 'pxxlkdhmbngmtwrs'
    TO = 'teemu.kukko@gmail.com'

    PORT = 587

    with smtplib.SMTP(SERVER, PORT) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()

        smtp.login(FROM, PASSW)    

        SUBJECT = 'Unauthorized access try!'
        BODY = f'Somebody has tried to open Your locker, please enter safety code to activate lock again\n\nSafety code: {input}'
        MESSAGE = f'Subject: {SUBJECT}\n\n{BODY}'

        smtp.sendmail(FROM, TO, MESSAGE)

def control_lock(array):

    lock_numbers = [0, 0, 0, 0]
    error_counter = 0
    while 1:     
        # switch0
        if cad.switches[0].value == 1:
            lock_numbers[0] = lock_numbers[0] + 1
            if lock_numbers[0] > 9:
                lock_numbers[0] = 0
        # switch1
        if cad.switches[1].value == 1:
            lock_numbers[1] = lock_numbers[1] + 1
            if lock_numbers[1] > 9:
                lock_numbers[1] = 0
        # switch2
        if cad.switches[2].value == 1:
            lock_numbers[2] = lock_numbers[2] + 1
            if lock_numbers[2] > 9:
                lock_numbers[2] = 0
        # switch3
        if cad.switches[3].value == 1:
            lock_numbers[3] = lock_numbers[3] + 1
            if lock_numbers[3] > 9:
                lock_numbers[3] = 0
        
        #set cursor to column 0 on the second row
        cad.lcd.set_cursor(0, 1)
        cad.lcd.write("Code:{}".format(lock_numbers))

        if cad.switches[4].value == 1:
            if lock_numbers == array:
                return 1
            elif error_counter == 4:
                return 2
            else:
                cad.lcd.set_cursor(0, 1)
                cad.lcd.write("Wrong Code!     ")
                error_counter += 1
                print(error_counter)
                time.sleep(2)

def lock_open():
	cad.lcd.set_cursor(0, 1)
	cad.lcd.write("                ")
	

def lock_locked(): 
    counter = 0
	cad.lcd.set_cursor(0, 1)
	cad.lcd.write("Press: Btn4 x 4 ")
    while 1:
        cad.lcd.set_cursor(0, 1)
        cad.lcd.write("Press: {}         ".format(counter))
        if cad.switches[4].value == 1:
            counter += 1
            if counter == 4:
                break
    return 'Locked'

def restart_program():
    """Restarts the current program.
    Note: this function does not return. Any cleanup action (like
    saving data) must be done before calling this function."""
    python = sys.executable
    os.execl(python, python, * sys.argv)

def print_status(input):
    cad.lcd.set_cursor(0, 0)
    cad.lcd.write("Status: " + lock_status)
    cad.lcd.set_cursor(0, 1)

if __name__ == "__main__":

    cad.lcd.backlight_on()
    cad.lcd.cursor_off()
    lock_code = [9, 9, 7, 3]
    lock_status = "Locked"
    print_status(lock_status)

    status = control_lock(lock_code)
	""" 
	Controlling lock status after first phase 
	1 >> next phase and 2 >> safe mode
	"""
    if status == 1:
        lock_status = "Waiting"
        print_status(lock_status)
    elif status == 2:
        error_code = authentication_numbers()
        error_mail(error_code)
        while 1:
            if control_lock(error_code) == 1:
                restart_program()
            else:
                continue
    else:	#just in case if something odd happens
        cad.lcd.clear()                 # clear the screen (also sends the cursor home)
        exit()
    
    authentication = authentication_numbers()
    sending_mail(authentication)
	""" 
	Controlling lock status in authentication mode 
	1 >> open and 2 >> safe mode
	"""
    if control_lock(authentication) == 1:
        lock_status = "Open     "
        print_status(lock_status)
        lock_open()
    elif status == 2:
		error_code = authentication_numbers()
		error_mail(error_code)
		while 1:
			if control_lock(error_code) == 1:
				restart_program()
			else:
				continue
    else:	#just in case if something odd happens
        cad.lcd.clear()                 # clear the screen (also sends the cursor home)
        exit()
    
    time.sleep(5)
    lock_status = lock_locked()
    if lock_status == 'Locked':
        restart_program()
