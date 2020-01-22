import pifacecad
from time import sleep
from threading import Barrier

import random
import smtplib

class Lock(object):
    def __init__(self):
        self.cad = pifacecad.PiFaceCAD()
        self.cad.lcd.backlight_on()
        self.authMode = 1 # 0 => Safe code / 1 => 1st auth / 2 => 2nd auth
        self.lockCode = [1, 1, 1, 1] # First auth code
        self.authCode = [0, 0, 0, 0]
        self.lockNumbers = [0, 0, 0, 0]
        self.end_barrier = Barrier(2) # Create two barriers to hold up the threads 
        self.errCounter = 0
        self.lockingCounter = 0

        self.cad.lcd.set_cursor(0, 0)
        self.lockStatus = "Locked"
        self.write_display("Status: {}".format(self.lockStatus), cursor_row = 0)
        self.write_display(self.lockNumbers, cursor_row = 1, input_code=True)

        self.server = 'smtp.gmail.com'
        self.sender = 'tkdemoprojects@gmail.com'
        self.passwd = 'pxxlkdhmbngmtwrs'
        self.receiver = 'matti.krusviita@edu.turkuamk.fi'

        self.port = 587

    # Control and validate lock number sequence
    def control_lock(self, event):
        if self.lockStatus == "Unlocked":
            if event.pin_num == 4: # Only switch4 will increase the counter
                self.lockingCounter += 1
                self.write_display("Locking in: {}".format(str(4 - self.lockingCounter)), cursor_row = 1)
            if self.lockingCounter >= 4: # Locking the lock, reset values
                self.lockingCounter = 0
                self.authMode = 1
                self.lockStatus = "Locked"
                self.write_display("Status: {}".format(self.lockStatus), cursor_row = 0) # Update upper row
                self.lockNumbers = [0, 0, 0, 0]
                self.write_display(self.lockNumbers, cursor_row = 1, input_code=True) # Update lower row
                self.end_barrier.wait()
        else:
            # switch0
            if event.pin_num == 0:
                self.lockNumbers[0] = self.lockNumbers[0] + 1
                if self.lockNumbers[0] > 9:
                    self.lockNumbers[0] = 0
            # switch1
            if event.pin_num == 1:
                self.lockNumbers[1] = self.lockNumbers[1] + 1
                if self.lockNumbers[1] > 9:
                    self.lockNumbers[1] = 0
            # switch2
            if event.pin_num == 2:
                self.lockNumbers[2] = self.lockNumbers[2] + 1
                if self.lockNumbers[2] > 9:
                    self.lockNumbers[2] = 0
            # switch3
            if event.pin_num == 3:
                self.lockNumbers[3] = self.lockNumbers[3] + 1
                if self.lockNumbers[3] > 9:
                    self.lockNumbers[3] = 0

            # Validate if lock number sequence is correct
            if event.pin_num == 4:
                if self.authCode == self.lockNumbers:
                    if self.authMode == 0: # Safe code input correct
                        self.authMode = 1
                        self.authCode = self.lockCode
                        self.errCounter = 0
                        self.lockNumbers = [0, 0, 0, 0]
                        self.write_display("Correct!", cursor_row = 1)
                        sleep(2)
                        self.lockStatus = "Locked"
                    elif self.authMode == 1: # 1st auth input correct
                        self.authMode += 1
                        self.lockStatus = "Waiting"
                        self.lockNumbers = [0, 0, 0, 0]
                        self.write_display("Correct!", cursor_row = 1)
                        sleep(2)
                        self.end_barrier.wait()      
                    elif self.authMode == 2: # 2nd auth input correct
                        self.authMode += 1
                        self.lockStatus = "Unlocked"
                        self.write_display("Open!", cursor_row = 1)
                        self.end_barrier.wait()
                    self.write_display("Status: {}".format(self.lockStatus), cursor_row = 0)
                else:
                    self.errCounter += 1
                    self.write_display("Wrong Code!  x{}".format(str(self.errCounter)), cursor_row = 1)
                    sleep(2)
                    if self.errCounter >= 4: # Go to error mode
                        self.authMode = 0
                        self.end_barrier.wait()
                        self.write_display("Insert safe code {}".format(str(self.errCounter)), cursor_row = 1)
                        sleep(2)
            if self.authMode != 3: # When opened (authMode = 3), we won't show lockNumbers
                self.write_display(self.lockNumbers, cursor_row = 1, input_code=True)
        
    # Create event listener to react button events
    def button_event_listener(self):
        if self.authMode == 1:
            self.authCode = self.lockCode
        self.listener = pifacecad.SwitchEventListener(chip=self.cad)
        for i in range(5):
            self.listener.register(i, pifacecad.IODIR_FALLING_EDGE, self.control_lock)
        self.listener.activate()

        self.end_barrier.wait()
        self.listener.deactivate()

    def write_display(self, text, cursor_row, input_code=False):
        # cursor_row "0" => upper row, "1" => lower row 
        try:
            if input_code:
                output = " ".join(list(map(str,text)))
            else:
                output = str(text)
        except:
            output = "error"    
        # Check and fill trailing spaces with empty spaces
        output_lenght = len(output)
        while output_lenght < 16:
            output_lenght += 1
        output = output.ljust(output_lenght)
        # Set cursor and write the row
        self.cad.lcd.set_cursor(0, cursor_row)
        self.cad.lcd.write(output) 
    
    # Generate random auth.numbers
    def authentication_numbers(self):
        return [random.randint(0, 9) for p in range(0, 4)]

    # Create email message for second and backlock authentication
    def create_email(self):
        self.authCode = self.authentication_numbers()
        if self.authMode:
            SUBJECT = 'Verification code'
            BODY = f'You are trying to open virtual locker.\n\n\nAuthentication code is: {self.authCode}'
        else:
            SUBJECT = 'Unauthorized access try!'
            BODY = f'Somebody has tried to open Your locker, please enter safety code to activate lock again\n\nSafety code: {self.authCode}'
        message = f'Subject: {SUBJECT}\n\n{BODY}'
        print(message)
        self.send_mail(message)

    def send_mail(self, message):
        SERVER = self.server
        FROM = self.sender
        PASSW = self.passwd
        TO = self.receiver
        PORT = self.port
        with smtplib.SMTP(SERVER, PORT) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
            smtp.login(FROM, PASSW)    
            smtp.sendmail(FROM, TO, message)

    def main(self):
        while True:
            self.button_event_listener()
            if self.authMode == 0 or self.authMode == 2:
                self.create_email()       
        print("exit")

if __name__ == "__main__":
    job = Lock()
    job.main()