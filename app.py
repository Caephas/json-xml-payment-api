from flask import Flask, request, jsonify
import csv
from lxml import etree


app = Flask(__name__)

# Load users from CSV
def load_users(filename):
    users = {}
    with open(filename, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            users[row['user_id']] = row
    return users

# Save updated users to CSV
def save_users(users, filename):
    fieldnames = ['user_id', 'country', 'balance']
    with open(filename, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for user_id, user_data in users.items():
            writer.writerow(user_data)

# Load usersSubTask1.csv at startup
users = load_users('usersSubTask1.csv')

@app.route('/transfer', methods=['POST'])
def transfer():
    data = request.get_json()
    
    sender_id = data['sender_id']
    receiver_id = data['receiver_id']
    amount = data['amount']
    currency = data['currency']
    
    # Check if sender or receiver exists
    if sender_id not in users:
        return jsonify({"error": "Invalid sender account ID, transaction was not processed"}), 513
    
    if receiver_id not in users:
        return jsonify({"error": "Invalid receiver account ID, transaction was not processed"}), 514
    
    # Check sender balance
    sender_balance = float(users[sender_id]['balance'])
    if sender_balance < amount:
        return jsonify({"error": "Invalid balance, transaction was not processed"}), 512
    
    # Process transaction
    users[sender_id]['balance'] = str(sender_balance - amount)
    users[receiver_id]['balance'] = str(float(users[receiver_id]['balance']) + amount)
    
    # Save updated users
    save_users(users, 'users.csv')
    
    return jsonify({"message": "Successful transaction, users.csv has been appended"}), 200

# Sample function to handle XML transfer
@app.route('/xmltransfer', methods=['POST'])
def xml_transfer():
    xml_data = request.data
    root = etree.fromstring(xml_data)

    # Extract details from the XML
    sender_id = root.find('.//SenderID').text
    receiver_id = root.find('.//ReceiverID').text
    amount = float(root.find('.//Amount').text)
    country_code_sender = root.find('.//CountryCodeSender').text
    country_code_receiver = root.find('.//CountryCodeReceiver').text

    # Blacklisted countries
    blacklisted_countries = ["RUS", "PRK", "IRN"]
    
    # Check blacklisted countries
    if country_code_sender in blacklisted_countries or country_code_receiver in blacklisted_countries:
        return jsonify({"error": "Transaction rejected, blacklisted country involved"}), 515

    # The rest of the logic is similar to the previous transfer route
    if sender_id not in users:
        return jsonify({"error": "Invalid sender account ID, transaction was not processed"}), 513
    
    if receiver_id not in users:
        return jsonify({"error": "Invalid receiver account ID, transaction was not processed"}), 514
    
    sender_balance = float(users[sender_id]['balance'])
    if sender_balance < amount:
        return jsonify({"error": "Invalid balance, transaction was not processed"}), 512

    users[sender_id]['balance'] = str(sender_balance - amount)
    users[receiver_id]['balance'] = str(float(users[receiver_id]['balance']) + amount)

    save_users(users, 'users.csv')
    
    return jsonify({"message": "Successful transaction, users.csv has been appended"}), 200

@app.route('/remittance', methods=['POST'])
def remittance_transfer():
    # Parse XML data from the request
    xml_data = request.data
    root = etree.fromstring(xml_data)

    # Extract elements from the XML based on schema
    sender_iban = root.find('.//Payer/SenderIBAN').text  # Corrected the XPath
    receiver_iban = root.find('.//Payee/RecieverIBAN').text  # Corrected the XPath
    sender_id = root.find('.//Payer/SenderID').text  # Adjusted based on the schema
    receiver_id = root.find('.//Payee/ReceiverID').text  # Adjusted based on the schema
    amount = float(root.find('.//Amount').text)

    # Handle remittance tags
    remittance_structured = root.find('.//Payer/RemittanceStructured').text
    remittance_unstructured = root.find('.//Payer/RemittanceUnstructured').text

    # Check if sender and receiver IBAN are the same
    if sender_iban == receiver_iban:
        return jsonify({"error": "Transaction rejected, sender and receiver IBAN cannot be the same"}), 516
    
    # Calculate transaction fee
    fee = 0.0
    if remittance_structured == 'Yes':  # 1% fee for structured remittance
        fee = amount * 0.01
    elif remittance_unstructured == 'Yes':  # 1.5% fee for unstructured remittance
        fee = amount * 0.015

    total_amount = amount + fee

    # Check if the sender exists
    if sender_id not in users:
        return jsonify({"error": "Invalid sender account ID, transaction was not processed"}), 513
    
    # Check if the receiver exists
    if receiver_id not in users:
        return jsonify({"error": "Invalid receiver account ID, transaction was not processed"}), 514
    
    # Check sender's balance
    sender_balance = float(users[sender_id]['balance'])
    if sender_balance < total_amount:
        return jsonify({"error": "Invalid balance, transaction was not processed"}), 512

    # Process transaction
    users[sender_id]['balance'] = str(sender_balance - total_amount)
    users[receiver_id]['balance'] = str(float(users[receiver_id]['balance']) + amount)

    # Save updated users data
    save_users(users, 'users.csv')

    return jsonify({"message": f"Successful transaction, fee applied: {fee}, users.csv has been updated"}), 200

if __name__ == '__main__':
    app.run(debug=True)