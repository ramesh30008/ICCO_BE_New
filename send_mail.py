import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from os.path import basename
import datetime
import os
def send_mail_for_password_change(to_mail_id, token, user):
        mail_content = """
Dear %s,
<br><br>
We recieved a request for password change on your account. You can reset your password by clicking the link below.
<br><br>
<a style = "display: block; width: 130px; height: 25px; background: #199319; text-decoration: none;padding: 10px; text-align: center; border-radius: 5px; color: white; font-weight: bold; line-height: 25px;" href="http://64.227.14.236:3000/cqIDP/forgot-password?uuid=%s">Reset Password</a>
<br><br>
This link will expire in 10 minutes. After that, you'll need to submit a new request in order to reset your password. If you dont want to reset it, simply disregard this email.
<br><br>
Thank you,
<br>
BESCOM-DMS Team
<br><br>
*** This is an automatically generated email, please do not reply to this email *** """%(user, token)
        #The mail addresses and password
        sender_address = 'tablextract@cogniquest.ai'
        sender_pass = '1sj02is019$'
        #sender_address = 'cq.authenticate@gmail.com'
        #sender_pass = 'nathan@123'
        receiver_address = to_mail_id
        #Setup the MIME
        message = MIMEMultipart()
        message['From'] = sender_address
        message['To'] = receiver_address
        message['Subject'] = 'BESCOM-DMS:Forgot password recovery'   #The subject line
        #The body and the attachments for the mail
        message.attach(MIMEText(mail_content, 'html'))
        #Create SMTP session for sending the mail
        #session = smtplib.SMTP('smtp.gmail.com', 587) #use gmail with port
        session = smtplib.SMTP('smtp.office365.com', 587) #use gmail with port
        session.starttls() #enable security
        session.login(sender_address, sender_pass) #login with mail_id and password
        text = message.as_string()
        session.sendmail(sender_address, receiver_address, text)
        session.quit()
        print('Mail Sent')
        
def send_mail_for_password(to_mail_id, new_password):
        mail_content = """
<div style="border:1px black solid;padding-top:10px;   font-family: Arial, sans-serif; color: black;">
Dear user,
<br> 
Your password has been reset and the new password is <b>%s</b>
<br>
Please change your password on your login.
<br><br>
Warm Regards,
<br>
CogniQuest
<br><br>
*** This is an automatically generated email, please do not reply to this email *** </div>""" %new_password
	#The mail addresses and password
        sender_address = 'tablextract@cogniquest.ai'
        sender_pass = '1sj02is019$'
	#sender_address = 'cq.authenticate@gmail.com'
	#sender_pass = 'nathan@123'
        receiver_address = to_mail_id
	#Setup the MIME
        message = MIMEMultipart()
        message['From'] = sender_address
        message['To'] = receiver_address
        message['Subject'] = 'Your credentials was reset - CogniQuest'   #The subject line
        #The body and the attachments for the mail
        message.attach(MIMEText(mail_content, 'html'))
        #Create SMTP session for sending the mail
        #session = smtplib.SMTP('smtp.gmail.com', 587) #use gmail with port
        session = smtplib.SMTP('smtp.office365.com', 587) #use gmail with port
        session.starttls() #enable security
        session.login(sender_address, sender_pass) #login with mail_id and password
        text = message.as_string()
        session.sendmail(sender_address, receiver_address, text)
        session.quit()
        #print('Mail Sent')


def send_mail(to_mail_id, otp):
        mail_content = """
<div style="border:1px black solid;padding-top:10px;   font-family: Arial, sans-serif; color: black;">
<br> 
Use <b>%s</b> as one time password (OTP) to verify your email. Do not share this OTP to anyone for security reasons. Valid for 15 minutes.
<br><br>
Warm Regards,
<br>
CogniQuest
<br><br>
*** This is an automatically generated email, please do not reply to this email *** </div>""" %otp
        #The mail addresses and password
	#sender_address = 'cq.authenticate@gmail.com'
	#sender_pass = 'nathan@123'
        sender_address = 'tablextract@cogniquest.ai'
        sender_pass = '1sj02is019$'
        #receiver_address = 'mails.nathaniel@gmail.com'
        receiver_address = to_mail_id
	#Setup the MIME
        message = MIMEMultipart()
        message['From'] = sender_address
        message['To'] = receiver_address
        message['Subject'] = 'Please Verify Your Email Address - CogniQuest'   #The subject line
        #The body and the attachments for the mail
        message.attach(MIMEText(mail_content, 'html'))
        #Create SMTP session for sending the mail
        session = smtplib.SMTP('smtp.office365.com', 587) #use gmail with port
        #session = smtplib.SMTP('smtp.gmail.com', 587) #use gmail with port
        session.starttls() #enable security
        session.login(sender_address, sender_pass) #login with mail_id and password
        text = message.as_string()
        session.sendmail(sender_address, receiver_address, text)
        session.quit()
        print('Mail Sent')

def send_attachment(to_mail_id, note, f_name, sender_name, receiver_name, document_name, project_name):
        mail_content = """
Please find the Attached Document for your Reference:
<br><br>
    &nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbspSender Name: %s
<br><br>
    &nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbspReceiver Name: %s
<br><br>
    &nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbspDocument Name: %s
<br><br>
    &nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbspProject Name: %s
<br><br>
    &nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbspDate: %s
<br><br>
Thank you,
<br>
BESCOM-DMS Team
<br><br>
*** This is an automatically generated email, please do not reply to this email *** """%(sender_name, receiver_name, document_name, project_name,datetime.date.today())
        print("mail",to_mail_id,"note", note, f_name, sender_name, receiver_name, document_name, project_name,"hhhhhhhhhhhhhhhhhhh")
        #The mail addresses and password
        #sender_address = 'cq.authenticate@gmail.com'
        #sender_pass = 'nathan@123'
        sender_address = 'tablextract@cogniquest.ai'
        sender_pass = '1sj02is019$'
        #receiver_address = 'mails.nathaniel@gmail.com'
        receiver_address = to_mail_id
        #Setup the MIME
        message = MIMEMultipart()
        message['From'] = sender_address
        message['To'] = receiver_address
        message['Subject'] = '%s'%document_name   #The subject line
        #The body and the attachments for the mail
        message.attach(MIMEText(mail_content, 'html'))
        document_name = "%s/.%s"%(os.path.splitext(f_name.split("/")[-1])[0],os.path.splitext(f_name.split("/")[-1])[1])
        with open(f_name, "rb") as fil: 
            ext = f_name.split('.')[-1:]
            attachedfile = MIMEApplication(fil.read(), _subtype = ext)
            attachedfile.add_header(
            'content-disposition', 'attachment', filename=document_name )
        message.attach(attachedfile)
        #Create SMTP session for sending the mail
        session = smtplib.SMTP('smtp.office365.com', 587) #use gmail with port
        #session = smtplib.SMTP('smtp.gmail.com', 587) #use gmail with port
        session.starttls() #enable security
        session.login(sender_address, sender_pass) #login with mail_id and password
        text = message.as_string()
        session.sendmail(sender_address, receiver_address, text)
        session.quit()
        print('Mail Sent')
        return {"status": True, "msg":'Mail Sent successfully'}

if __name__=='__main__':
   #send_mail('mails.nathaniel@gmail.com', '1234')
   #send_mail_for_password('mails.nathaniel@gmail.com', '1111')
   #send_attachment("durgashree.s@cogniquest.ai", "note", "color_combination.txt", "sender_name", "receiver_name", "document_name","project_name")
   pass
