import unittest
import json
from app import app
from io import StringIO
import csv

class FlaskTestCase(unittest.TestCase):
    
    # Set up the test client and load sample users before each test
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        
        # Set up some initial users for testing
        self.sample_users = {
            '1001': {'user_id': '1002', 'country': 'USA', 'balance': '500.00'},
            '1005': {'user_id': '1005', 'country': 'USA', 'balance': '300.00'}
        }

        # Write the sample users to a CSV file to simulate existing users
        with open('usersSubTask1.csv', mode='w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=['user_id', 'country', 'balance'])
            writer.writeheader()
            for user_id, user_data in self.sample_users.items():
                writer.writerow(user_data)

    # Tear down the test after each test case
    def tearDown(self):
        # Any cleanup can be added here, e.g., deleting temporary files
        pass
        # Test for successful JSON transfer
    def test_transfer_success(self):
        payload = {
            "sender_id": "1001",
            "receiver_id": "1005",
            "amount": 100.00,
            "currency": "USD"
        }
        response = self.app.post('/transfer', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Successful transaction', response.data)

    # Test for transfer with invalid balance
    def test_transfer_invalid_balance(self):
        payload = {
            "sender_id": "1001",
            "receiver_id": "1005",
            "amount": 600.00,  # Invalid amount because sender doesn't have enough balance
            "currency": "USD"
        }
        response = self.app.post('/transfer', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 512)
        self.assertIn(b'Invalid balance', response.data)

            # Test for successful XML transfer
    def test_xml_transfer_success(self):
        xml_data = """
        <Payment xmlns:xs="http://www.w3.org/2001/XMLSchema">
            <Payer>
                <SenderID>1001</SenderID>
                <CountryCodeSender>USA</CountryCodeSender>
            </Payer>
            <Payee>
                <ReceiverID>1005</ReceiverID>
                <CountryCodeReceiver>USA</CountryCodeReceiver>
            </Payee>
            <Amount>100.00</Amount>
        </Payment>
        """
        response = self.app.post('/xmltransfer', data=xml_data, content_type='application/xml')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Successful transaction', response.data)

    # Test for blacklisted country
    def test_xml_transfer_blacklisted_country(self):
        xml_data = """
        <Payment xmlns:xs="http://www.w3.org/2001/XMLSchema">
            <Payer>
                <SenderID>1001</SenderID>
                <CountryCodeSender>RUS</CountryCodeSender>
            </Payer>
            <Payee>
                <ReceiverID>1005</ReceiverID>
                <CountryCodeReceiver>USA</CountryCodeReceiver>
            </Payee>
            <Amount>100.00</Amount>
        </Payment>
        """
        response = self.app.post('/xmltransfer', data=xml_data, content_type='application/xml')
        self.assertEqual(response.status_code, 515)
        self.assertIn(b'Transaction rejected, blacklisted country involved', response.data)

            # Test for successful structured remittance transfer
    def test_remittance_structured(self):
        xml_data = """
        <Payment xmlns:xs="http://www.w3.org/2001/XMLSchema">
            <Payer>
                <SenderIBAN>IBAN123456789</SenderIBAN>
                <SenderID>1001</SenderID>
                <CountryCodeSender>USA</CountryCodeSender>
                <RemittanceStructured>Yes</RemittanceStructured>
                <RemittanceUnstructured>No</RemittanceUnstructured>
            </Payer>
            <Payee>
                <RecieverIBAN>IBAN987654321</RecieverIBAN>
                <ReceiverID>1005</ReceiverID>
                <CountryCodeReceiver>USA</CountryCodeReceiver>
            </Payee>
            <Amount>100.00</Amount>
        </Payment>
        """
        response = self.app.post('/remittance', data=xml_data, content_type='application/xml')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Successful transaction, fee applied', response.data)

    # Test for invalid remittance where sender and receiver IBANs are the same
    def test_remittance_same_iban(self):
        xml_data = """
        <Payment xmlns:xs="http://www.w3.org/2001/XMLSchema">
            <Payer>
                <SenderIBAN>IBAN123456789</SenderIBAN>
                <SenderID>1001</SenderID>
                <CountryCodeSender>USA</CountryCodeSender>
                <RemittanceStructured>Yes</RemittanceStructured>
                <RemittanceUnstructured>No</RemittanceUnstructured>
            </Payer>
            <Payee>
                <RecieverIBAN>IBAN123456789</RecieverIBAN>  <!-- Same IBAN as sender -->
                <ReceiverID>1005</ReceiverID>
                <CountryCodeReceiver>USA</CountryCodeReceiver>
            </Payee>
            <Amount>100.00</Amount>
        </Payment>
        """
        response = self.app.post('/remittance', data=xml_data, content_type='application/xml')
        self.assertEqual(response.status_code, 516)
        self.assertIn(b'Transaction rejected, sender and receiver IBAN cannot be the same', response.data)