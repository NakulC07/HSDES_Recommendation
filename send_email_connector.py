#!/usr/bin/env python
from email.message import EmailMessage
import mimetypes
import smtplib
import traceback
import re
import sys
import os
import getpass
import tempfile

html_escape_table = {
    "&": "&amp;",
    '"': "&quot;",
    "'": "&apos;",
    ">": "&gt;",
    "<": "&lt;",
    " ": "&nbsp;",
    "\r\n": "<br />\n",
    "\n": "<br />\n",
    }

BACKUP_SMTP_SERVER = "smtp.intel.com"
DEFAULT_SMTP_SERVER = "ecsmtp.ienvor.intel.com"
DEFAULT_SMTPAUTH_SERVER = "smtpauth.intel.com"

# Try with smtp and, if it fails, go to smtpauth. Will interactively ask for user and password if not provided.
AUTH_MODE_ENABLE_IF_FAILS = "ENABLE_IF_FAILS"
# Will directly to to smtpauth mode. Will interactively ask for user and password if not provided.
AUTH_MODE_ENABLED         = "ENABLED"
# Don't use smtpauth
AUTH_MODE_DISABLED        = "DISABLED"

_known_auth_modes = (AUTH_MODE_DISABLED,
                     AUTH_MODE_ENABLED,
                     AUTH_MODE_ENABLE_IF_FAILS)


def html_format_span(text, style=None, id=None, escapeText = True, skip_newline = True):
    result = "<span "
    if style != None:
        result += 'style="%s"'%style
    if id != None:
        result += 'id="%s"'%id
    if escapeText:
        text = html_escape(text)
    result += ">%s</span>"%(text, )
    if not skip_newline:
        result += "\n"
    return result

def _html_format_url(url, text, escapeText = True):
    if escapeText:
        text = html_escape(text)
    result = '<a href="%s">%s</a>\n'%(url, text)
    return result

_re_escape_code = re.compile("##[xX]{0,1}[0-9a-fA-F]+##")
def html_escape(text):
    """Produce entities within text."""
    # Keep html smileys
    missing_text = text
    result = ""
    while len(missing_text) > 0:
        match = _re_escape_code.search(missing_text)
        if match == None:
            result += "".join(html_escape_table.get(c,c) for c in missing_text)
            missing_text = ""
        else:
            pre = missing_text[:match.start()]
            post = missing_text[match.end():]
            # Convert to int to make sure it is an integer
            num = match.group()[2:-2].lower()
            try:
                if num.startswith("x"):
                    escape_code = "&#%i;"%(int(num[1:], 16))
                else:
                    escape_code = "&#%i;"%(int(num))
            except:
                print("   ERROR: Could not convert to int the HTML code %s"%(repr(num), ))
                escape_code = ""
            result += pre
            result += escape_code
            missing_text = post
    
    return result

def _explode_addresses(addresses):
    if type(addresses) is str:
        addrs = [addr.strip() for addr in addresses.replace(";",",").split(",")]
    else:
        addrs = addresses
    for i in range(len(addrs)):
        assert len(addrs[i]) > 0, "Got an empty email address"
        if not "@" in addrs[i]:
            addrs[i] = addrs[i] + "@an.intel.com"
    return addrs

def sendEmail(toaddr, 
              fromaddr, 
              subjectText, 
              bodyText, 
              smtpServer = DEFAULT_SMTP_SERVER, 
              smtpAuthServer = DEFAULT_SMTPAUTH_SERVER, 
              attachments=[], 
              htmlText = None, 
              total_file_size_warn_email = 10*(1024**2),
              auth_mode = AUTH_MODE_ENABLE_IF_FAILS,
              smtpauth_user = None,
              smtpauth_pass = None,
              try_smtp_bakckup = True,
              ):
    assert auth_mode in _known_auth_modes, "Bad auth_mode: %s"%(auth_mode,)
              
    if bodyText == None and htmlText is not None:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(htmlText, features="lxml")
        plainBodyText = soup.get_text()
    else:
        plainBodyText = bodyText
        
    toaddr = _explode_addresses(toaddr)
        
    # Create the container email message.
    msg = EmailMessage()
    msg['Subject'] = subjectText
    msg['From'] = fromaddr
    msg['To'] = toaddr
    msg.preamble = 'The cake is a lie!'
    msg.set_content(plainBodyText)
    if htmlText is not None:
        msg.add_alternative(htmlText, subtype='html')
    msg.make_mixed()
    
    warnings = ""
    total_file_size = 0
    for path in attachments:
        path = os.path.abspath(path)
        if not os.path.isfile(path):
            err = "File %s does not exist, cannot attach\n"%(path)
            print(" WARNING: %s"%(err,))
            warnings += "\n%s"%err
            continue
        # Guess the content type based on the file's extension.  Encoding
        # will be ignored, although we should check for simple things like
        # gzip'd or compressed files.
        ctype, encoding = mimetypes.guess_type(path)
        if ctype is None or encoding is not None:
            # No guess could be made, or the file is encoded (compressed), so
            # use a generic bag-of-bits type.
            ctype = 'application/octet-stream'
        maintype, subtype = ctype.split('/', 1)
        print("   DEBUG: Attaching file %s as %s/%s"%(path, maintype, subtype))
        total_file_size += os.stat(path).st_size
        with open(path, 'rb') as fp:
            filename = os.path.basename(path)
            if os.path.splitext(filename)[1].lower() == ".ini":
                # Suck it McAfee
                filename = os.path.splitext(filename)[0] + ".not_an_ini_file"
            msg.add_attachment(fp.read(),
                               maintype=maintype,
                               subtype=subtype,
                               filename=filename)
    
    if total_file_size_warn_email is not None and total_file_size > total_file_size_warn_email:
        print(" WARNING: Total attachement sizes (%.3fMB) exceeds %.3fMB (warning threshold)."
                     " Sending a warning email without attachments in case the file does not make it!"%(
                        total_file_size/(1024**2), total_file_size_warn_email/(1024**2),))
        
        if bodyText == None:
            newBodyText = None
        else:
            newBodyText = "WARNING: The original email had an attacement of %.2fMB in size.\nSending this COPY of the original email in case the full email does not make it!\n\n"%(total_file_size/(1024**2), ) + bodyText
        
        if htmlText == None:
            newHtmlText = None
        else:
            head, body = htmlText.split("<body>")
            head = head + "<body>" + html_format_span("WARNING:  The original email had an attacement of %.2fMB in size.\nSending this COPY of the original email in case the full email does not make it!\n\n"%(total_file_size/(1024**2), ), style="color:#F00;font-weight:bold;")
            newHtmlText = head + body
        
        sendEmail(toaddr = toaddr,
                  fromaddr = fromaddr,
                  subjectText = "WARNING Attachement > 10MB |" + subjectText,
                  bodyText = newBodyText,
                  smtpServer = smtpServer, 
                  htmlText = newHtmlText,
                  auth_mode = auth_mode,
                  smtpauth_user = smtpauth_user,
                  smtpauth_pass = smtpauth_pass,
                  try_smtp_bakckup = try_smtp_bakckup,
                  )
    
    if warnings != "":
        msg.add_attachment(warnings.encode(), 
                           maintype = "text",
                           subtype = "plain",
                           filename = "WARNINGS.txt")

    mode = "SMTP" if auth_mode in (AUTH_MODE_DISABLED, AUTH_MODE_ENABLE_IF_FAILS) else "SMTPAUTH"
    idx = -1
    while True:
        idx += 1
        if mode == "SMTP":
            success = _send_smtp_email(smtpServer, msg)
            if success:
                break
            if try_smtp_bakckup and smtpServer != BACKUP_SMTP_SERVER:
                print(" WARNING: Failed to send email using default SMTP server. Trying now with backup server.")
                smtpServer = BACKUP_SMTP_SERVER
            elif auth_mode == AUTH_MODE_DISABLED:
                raise Exception("Failed to send email using auth-less SMTP. Won't try to use auth mode.")
            elif auth_mode == AUTH_MODE_ENABLE_IF_FAILS:
                print(" WARNING: Failed to send email using auth-less SMTP. Trying not with authenticated mode.")
                print("    INFO: Why? Because IT restricts auth-less SMTP servers on some networks but not in all of them :/")
                mode = "SMTPAUTH"
            else:
                raise Exception("Internal error: %s"%(auth_mode,))
        elif mode == "SMTPAUTH":
            success = _send_smtpauth_email(smtpAuthServer, msg, smtpauth_user, smtpauth_pass)
            if success:
                break
            if auth_mode == AUTH_MODE_ENABLE_IF_FAILS:
                raise Exception("Failed to send email, tried both auth-less SMPT and auth SMTP mode")
            raise Exception("Failed to send email using SMTP auth mode")
        else:
            raise Exception("internal error: %s"%(mode,))
        
def _send_smtpauth_email(smtpServer, msg, user = None, password = None):
    if user is None:
        user = os.getlogin()
        u = input("Provide user for email server [%s]: "%(user,))
        if u != "":
            user = u
    if password is None:
        password = getpass.getpass("Provide password for user '%s': "%(user,))
    try:
        print("    INFO: Sending email with %s"%(smtpServer,))
        with smtplib.SMTP(smtpServer, 587) as s:
            #s.set_debuglevel(1)
            s.connect(smtpServer, 587)
            s.ehlo()
            s.starttls()
            s.ehlo()
            s.login(user, password)
            s.send_message(msg)
    except (smtplib.SMTPRecipientsRefused, smtplib.SMTPHeloError,
            smtplib.SMTPSenderRefused, smtplib.SMTPDataError, Exception) as ex:
        print('   ERROR: Trouble sending email using %s. SMTP Auth server did not like something: %s'%(smtpServer, ex,))
        print("   DEBUG: %s"%(traceback.format_exc(),))
        return False
    print("    INFO: Successfully sent email using %s"%(smtpServer,))
    return True
        
def _send_smtp_email(smtpServer, msg):
    try:
        print("    INFO: Sending email with %s"%(smtpServer,))
        with smtplib.SMTP(smtpServer) as s:
            s.send_message(msg)
    except (smtplib.SMTPRecipientsRefused, smtplib.SMTPHeloError,
            smtplib.SMTPSenderRefused, smtplib.SMTPDataError, Exception) as ex:
        print('   ERROR: Trouble sending email using %s. SMTP server did not like something: %s'%(smtpServer, ex,))
        print("   DEBUG: %s"%(traceback.format_exc(),))
        return False
    print("    INFO: Successfully sent email using %s"%(smtpServer,))    
    return True

def demo_create_dummy_files():
    files = []
    
    tmpdir = tempfile.mktemp()
    os.mkdir(tmpdir)
    
    # Python version
    files.append(os.path.join(tmpdir,"python_version.txt"))
    with open(files[-1], "w") as fh:
        fh.write(sys.version)
    
    # loaded python modules
    modules = sys.modules.copy()
    files.append(os.path.join(tmpdir,"loaded_modules.txt"))
    with open(files[-1], "w") as fh:
        for module_name, module in modules.items():
            if module_name in sys.builtin_module_names:
                fh.write("%40s: <built in>\n"%(module_name,))
            else:
                if hasattr(module,"__file__"):
                    fh.write("%40s: %s\n"%(module_name, module.__file__))
                else:
                    fh.write("%40s: <UKNOWN>\n"%(module_name,))
    
    # python path
    files.append(os.path.join(tmpdir,"python_path.txt"))
    with open(files[-1], "w") as fh:
        fh.write("\n".join([os.path.abspath(p) for p in sys.path]))
    
    # environment variables
    files.append(os.path.join(tmpdir,"environment_vars.txt"))
    with open(files[-1], "w") as fh:
        fh.write("\n".join(["%40s: %s"%(k,v) for k,v in os.environ.items()]))
    
    return files

def demo_main():
    while True:
        email_addresses = input("Give me one or more addresses to send a demo email to. You can give full email addresses or idsds (your windows user). Separate multiple addresses/users by comma: ")
        if email_addresses != "": break
        print("Try again!!!")
    
    # create some dummy files to send on the email
    files = demo_create_dummy_files()
    
    # Plain text email
    print("\n------- Sending plain text email -------")
    sendEmail(toaddr = email_addresses, 
              fromaddr = "ive.genai.demo.email@intel.com", 
              subjectText = "[PLAIN] Demo email from send_email_connector.py - Plain text", 
              bodyText = '''This is only a simple demo email to demonstrate the capabilities of the send email connector.
You can use this demo to send your own emails.''', 
              attachments=files,
              )
    
    
    # HTML email
    print("\n------- Sending HTML email -------")
    body = '''<header>
<style>
body {
  font-family: Arial, Helvetica, sans-serif;
  word-wrap: break-word;
  word-break: break-all;
}
#title{
  color:#084;
  font-weight:bold;
}
#pass1{
  color:#A0A;
  font-weight:bold;
}
#pass2{
  color:#0AA;
  font-weight:bold;
}
#pass3{
  color:#AA0;
  font-weight:bold;
}
#warning{
  color:#F40;
  font-weight:bold;
}
#demotable {
  font-family: Arial, Helvetica, sans-serif;
  border-collapse: collapse;
  width: 100%;
}

#demotable td, #demotable th {
  border: 1px solid #ddd;
  padding: 8px;
}

#demotable tr:nth-child(even){background-color: #f2f2f2;}

#demotable tr:hover {background-color: #ddd;}

#demotable th {
  padding-top: 12px;
  padding-bottom: 12px;
  text-align: left;
  background-color: #04AA6D;
  color: white;
}
</style>
<body>
'''

    body += html_escape("This is only a simple demo email to demonstrate the capabilities of the send email connector.\n\n")
    
    body += html_format_span("This uses title style", id="title")
    
    body += html_format_span(" and this uses warning style\n", id="warning")
    
    text = "This uses alternating styles!!!\n"
    password_styles = ("pass1", "pass2", "pass3")
    style_index = 0
    for char in text:
        body += html_format_span(char, id=password_styles[style_index], skip_newline=True)
        style_index = (style_index + 1) % len(password_styles)

    # Icon codes can be decimal or hex (with x prefix)
    body += html_escape("\nAnd, for some reason, we support icons: ##127769## ##127929## ##x1f30e##\n")
    
    body += html_escape("\n\nAnd this is how to insert a table:\n\n")
    
    body += '''
<table id="demotable">
  <tr>
    <th>Team</th>
    <th>Contact</th>
    <th>Site</th>
  </tr>
  <tr>
    <td>Processor Development</td>
    <td>some.employee@intel.com</td>
    <td>FM</td>
  </tr>
  <tr>
    <td>SOC Development</td>
    <td>another.employee@intel.com</td>
    <td>SC</td>
  </tr>
  <tr>
    <td>Electrical Validation</td>
    <td>third.employee@intel.com</td>
    <td>ZPN</td>
  </tr>
  <tr>
    <td>Electrical Validation</td>
    <td>fourth.employee@intel.com</td>
    <td>ZPN</td>
  </tr>
  <tr>
    <td>Costumer Support</td>
    <td>costumer.employee@intel.com</td>
    <td>PDX</td>
  </tr>
</table>'''
    
    body += "\n</body>"

    sendEmail(toaddr = email_addresses, 
              fromaddr = "ive.genai.demo.email@intel.com", 
              subjectText = "[HTML] Demo email from send_email_connector.py - HTML", 
              bodyText = None,
              htmlText = body,
              attachments=files,
              )

if __name__ == "__main__":
    demo_main()
    