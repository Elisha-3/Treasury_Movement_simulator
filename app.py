from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime, date
import math
# import locale

app = Flask(__name__)
app.secret_key = 'secret_key_for_session'

# locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

# Static FX rates
FX_RATES = {
    ("USD", "KES"): 130,
    ("KES", "USD"): 1/130,
    ("NGN", "USD"): 1/1000,
    ("USD", "NGN"): 1000,
    ("KES", "NGN"): 7,
    ("NGN", "KES"): 1/7,
}

# Virtual Accounts data
accounts = {
    "Mpesa_KES_1": {"currency": "KES", "balance": 500000},
    "Bank_KES_2": {"currency": "KES", "balance": 12000000},
    "Wallet_KES_3": {"currency": "KES", "balance": 450000},
    "Bank_USD_1": {"currency": "USD", "balance": 80000},
    "Bank_USD_2": {"currency": "USD", "balance": 35000},
    "Mobile_USD_3": {"currency": "USD", "balance": 15000},
    "Bank_NGN_1": {"currency": "NGN", "balance": 2000000},
    "Mpesa_NGN_2": {"currency": "NGN", "balance": 3500000},
    "Wallet_NGN_3": {"currency": "NGN", "balance": 1800000},
    "Flutterwave_NGN_4": {"currency": "NGN", "balance": 2500000},
}

# List for storing transaction logs
transaction_log = []

@app.route('/')
def index():
    page = int(request.args.get('page', 1))
    per_page = 10
    total_logs = len(transaction_log)
    total_pages = math.ceil(total_logs / per_page)
    start = (page - 1) * per_page
    end = start + per_page
    logs_to_display = transaction_log[::-1][start:end]

    return render_template('index.html', accounts=accounts, logs=logs_to_display, page=page, total_pages=total_pages,)

@app.route('/transfer', methods=['POST'])
def transfer():
    source = request.form['source']
    destination = request.form['destination']
    amount = float(request.form['amount'])
    note = request.form.get('note', '')

    if source == destination:
        flash("Source and destination accounts cannot be the same.", "error")
        return redirect(url_for('index'))

    if amount <= 0:
        flash("Please enter a valid amount.", "error")
        return redirect(url_for('index'))

    src_currency = accounts[source]['currency']
    dst_currency = accounts[destination]['currency']
    src_balance = accounts[source]['balance']

    # FX support based on static rates
    converted_amount = amount
    if src_currency != dst_currency:
        rate_key = (src_currency, dst_currency)
        if rate_key not in FX_RATES:
            flash("Unsupported currency conversion.", "error")
            return redirect(url_for('index'))
        converted_amount = amount * FX_RATES[rate_key]

    if amount > src_balance:
        flash("Insufficient funds in source account.", "error")
        return redirect(url_for('index'))

    transfer_date = request.form['transfer_date']
    today = date.today().isoformat()

    if transfer_date > today:
        # Log as scheduled, do NOT move funds
        transaction_log.append({
            'timestamp': transfer_date,
            'from': source,
            'to': destination,
            'amount': amount,
            'converted_amount': converted_amount,
            'from_currency': src_currency,
            'to_currency': dst_currency,
            'note': note,
            'status': 'scheduled'
        })
        flash("Transfer scheduled.", "success")
        return redirect(url_for('index'))
    else:
        accounts[source]['balance'] -= amount
        accounts[destination]['balance'] += converted_amount

        transaction_log.append({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "from": source,
            "to": destination,
            "amount": amount,
            "converted_amount": converted_amount,
            "from_currency": src_currency,
            "to_currency": dst_currency,
            "note": note,
            "status": 'success'
        })

        flash("Transfer successful.", "success")
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
