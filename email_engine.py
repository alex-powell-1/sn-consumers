import creds
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.application import MIMEApplication
from barcode_engine import generate_barcode
from error_handler import ProcessInErrorHandler, LeadFormErrorHandler
from email.utils import formataddr
from jinja2 import Template
import os


class Email:
    name = creds.Company.name
    address = creds.Gmail.Sales.username
    pw = creds.Gmail.Sales.password

    def render(
        to_name,
        to_address,
        subject,
        content,
        mode='mixed',
        logo=False,
        image=None,
        image_name=None,
        barcode=None,
        attachment=False,
    ):
        msg = MIMEMultipart(mode)
        msg['From'] = formataddr((Email.name, Email.address))
        msg['To'] = formataddr((to_name, to_address))
        msg['Subject'] = subject

        msg_html = MIMEText(content, 'html')
        msg.attach(msg_html)

        if logo:
            with open(creds.Company.logo, 'rb') as logo_file:
                logo = logo_file.read()
                msg_logo = MIMEImage(logo, 'jpg')
                msg_logo.add_header('Content-ID', '<image1>')
                msg_logo.add_header('Content-Disposition', 'inline', filename='Logo.jpg')
                msg.attach(msg_logo)

        if image is not None:
            if image_name is not None:
                image_name = image_name
            else:
                image_name = 'product.jpg'

            with open(image, 'rb') as item_photo:
                product = item_photo.read()
                msg_product_photo = MIMEImage(product, 'jpg')
                msg_product_photo.add_header('Content-ID', '<image2>')
                msg_product_photo.add_header('Content-Disposition', 'inline', filename=image_name)
                msg.attach(msg_product_photo)

        if barcode is not None:
            with open(barcode, 'rb') as item_photo:
                product = item_photo.read()
                msg_barcode = MIMEImage(product, 'png')
                msg_barcode.add_header('Content-ID', '<image3>')
                msg_barcode.add_header('Content-Disposition', 'inline', filename='barcode.png')
                msg.attach(msg_barcode)

        if attachment:
            with open(creds.Marketing.DesignLeadForm.pdf_attachment, 'rb') as file:
                pdf = file.read()
                attached_file = MIMEApplication(_data=pdf, _subtype='pdf')
                attached_file.add_header(
                    _name='content-disposition',
                    _value='attachment',
                    filename=f'{creds.Marketing.DesignLeadForm.pdf_name}',
                )
                msg.attach(attached_file)

        return msg

    def send(
        recipients_list,
        subject,
        content,
        mode='mixed',
        logo=False,
        image=None,
        image_name=None,
        barcode=None,
        attachment=False,
        staff=False,
    ):
        def send_mail(to_address, message):
            with smtplib.SMTP('smtp.gmail.com', port=587) as connection:
                connection.ehlo()
                connection.starttls()
                connection.ehlo()
                connection.login(user=Email.address, password=Email.pw)
                connection.sendmail(Email.address, to_address, message.as_string().encode('utf-8'))
                connection.quit()

        if staff:
            # Dictionary of recipients in creds config
            for person in recipients_list:
                to_name = creds.Company.staff[person]['full_name']
                to_address = creds.Company.staff[person]['email']
                msg = Email.render(
                    to_name=to_name,
                    to_address=to_address,
                    subject=subject,
                    content=content,
                    mode=mode,
                    logo=logo,
                    image=image,
                    image_name=image_name,
                    barcode=barcode,
                    attachment=attachment,
                )
                send_mail(to_address=to_address, message=msg)
        else:
            # General Use
            for k, v in recipients_list.items():
                to_name = k
                to_address = v
                msg = Email.render(
                    to_name=to_name,
                    to_address=to_address,
                    subject=subject,
                    content=content,
                    mode=mode,
                    logo=logo,
                    image=image,
                    image_name=image_name,
                    barcode=barcode,
                    attachment=attachment,
                )
                send_mail(to_address=to_address, message=msg)

    class Customer:
        class GiftCard:
            def send(name, email, gc_code, amount, eh=ProcessInErrorHandler):
                """Sends gift card to customer"""
                email = 'alex@settlemyrenursery.com'

                recipient = {name: email}

                try:
                    amount = int(amount)
                except ValueError:
                    eh.logger.error(f'Error converting {amount} to int.')

                print(f'Sending Gift Card to {name} at {email}')

                with open('./templates/gift_card.html', 'r') as file:
                    template_str = file.read()

                jinja_template = Template(template_str)

                generate_barcode(data=gc_code, filename=gc_code)

                subject = "You've received a gift card!"

                email_data = {
                    'title': subject,
                    'name': name,
                    'gc_code': gc_code,
                    'amount': amount,
                    'company': creds.Company.name,
                    'company_url': creds.Company.url,
                    'company_phone': creds.Company.phone,
                    'company_address_line_1': creds.Company.address_html_1,
                    'company_address_line_2': creds.Company.address_html_2,
                }

                email_content = jinja_template.render(email_data)

                barcode = f'{creds.Company.barcodes}/{gc_code}.png'

                Email.send(
                    recipients_list=recipient,
                    subject=subject,
                    content=email_content,
                    image='./setup/images/gift_card.jpg',
                    image_name='gift_card.jpg',
                    mode='related',
                    logo=True,
                    barcode=barcode,
                )

                os.remove(barcode)

        class DesignLead:
            def send(first_name, email, eh=LeadFormErrorHandler):
                """Send email and PDF to customer in response to request for design information."""
                recipient = {first_name: email}

                with open('./templates/design_lead/customer_email.html', 'r') as file:
                    template_str = file.read()

                jinja_template = Template(template_str)

                data = creds.Marketing.DesignLeadForm

                email_data = {
                    'title': data.email_subject,
                    'greeting': f'Hi {first_name},',
                    'service': data.service,
                    'company': creds.Company.name,
                    'list_items': data.list_items,
                    'signature_name': data.signature_name,
                    'signature_title': data.signature_title,
                    'company_phone': creds.Company.phone,
                    'company_url': creds.Company.url,
                    'company_reviews': creds.Company.reviews,
                    'unsubscribe_endpoint': f'{creds.API.endpoint}{creds.API.Route.unsubscribe}?email={email}',
                }

                email_content = jinja_template.render(email_data)

                Email.send(
                    recipients_list=recipient,
                    subject=data.email_subject,
                    content=email_content,
                    mode='mixed',
                    logo=False,
                    attachment=data.pdf_attachment,
                )
