# Category Icons
CATEGORY_ICONS = {
        "Rent/Mortgage": "app-assets/images/categories/Rent.png",
        "Electricity": 'app-assets/images/categories/Electricity.png',
        "Water": "app-assets/images/categories/Water-Bill.png",
        "Internet": "app-assets/images/categories/Internet.png",
        "New Car": "app-assets/images/categories/Car.png",
        "Insurance": "app-assets/images/categories/Insurance.png",
        "Cellphone": "app-assets/images/categories/Phone.png",
        "Netflix Subscription": "app-assets/images/categories/Netflix.png",
        "Amazon Prime Subscription": "app-assets/images/categories/Amazon.png",
        "Gym Membership": "app-assets/images/categories/Gym.png",
        "Groceries": "app-assets/images/categories/Shoping.png",
        "Eating Out": "app-assets/images/categories/dinner.png",
        "Gas / Transportation": "app-assets/images/categories/transport.png",
        "Entertainment": "app-assets/images/categories/entertainment.png",
        "Pets": "app-assets/images/categories/pet.png",
        "Kids/Children": "app-assets/images/categories/children.png",
        "Taxes": "app-assets/images/categories/taxes.png",
        "Car Maintenance": "app-assets/images/categories/car-maintenance.png",
        "Medical Expenses": "app-assets/images/categories/medical.png",
        "Gifts": "app-assets/images/categories/gift-box.png",
        "Holidays": "app-assets/images/categories/holiday.png",
        "Emergency Fund": "app-assets/images/categories/emergency-fund.png",
        "Phone": "app-assets/images/categories/Phone.png",
        "New House": "app-assets/images/categories/Rent.png",
        "New Phone": "app-assets/images/categories/new-phone.png",
        "Education": "app-assets/images/categories/college-fee.png",
        "Netflix Spotify Subscription": "app-assets/images/categories/Netflix.png",
        "Amazon Prime Spotify Subscription": "app-assets/images/categories/Amazon.png",
        "Hair": "app-assets/images/categories/salon.png",
        "Job": "app-assets/images/categories/job.png",
        "Business": "app-assets/images/categories/business.png",
        "Vacation": "app-assets/images/categories/vacation.png",
        "Electronic Items": "app-assets/images/categories/electronics.png",
        "Electronics": "app-assets/images/categories/electronics.png",
        "Public Transportation": "app-assets/images/categories/transport.png",
        "Retirement": "app-assets/images/categories/retirement.png",
        "Spotify Subscription": "app-assets/images/categories/spotify.png",
        "Bonus": "app-assets/images/categories/bonus.png",
        "Beauty": "app-assets/images/categories/beauty.png",
        "Clothes": "app-assets/images/categories/clothes-hanger.png",
        "Movies": "app-assets/images/categories/entertainment.png",
        "Interest": "app-assets/images/categories/interest-rate.png"
}
# To-do consisent symbols
# Currencies
CURRENCY_DICT = {
    '$': "US Dollar ($)",
    '€': 'Euro (€)',
    '₹': 'Indian rupee (₹)',
    '£': 'British Pound (£)',
    'CAD': "Canadian Dollar ($)"
}

# Price Scenario dict for Rental Properties
SCENARIO_DICT = {
        'best_case': "Best Case Scenario Purchase Price",
        'likely_case': 'Likely Case Scenario Purchase Price',
        'worst_case': 'Worst Case Scenario Purchase Price'
}

# Property Type list
PROPERTY_TYPE_LIST = [
        'Apartment',
        'Commercial',
        'Condo',
        'Duplex',
        'House',
        'Mixed-Use',
        'Other'
]

# Month-date Dict
MONTH_DATE_DICT = {
    '1': '1st', '2': '2nd', '3': '3rd', '4': '4th',
    '5': '5th', '6': '6th', '7': '7th', '8': '8th',
    '9': '9th', '10': '10th', '11': '11th', '12': '12th',
    '13': '13th', '14': '14th', '15': '15th', '16': '16th',
    '17': '17th', '18': '18th', '19': '19th', '20': '20th',
    '21': '21st', '22': '22nd', '23': '23rd', '24': '24th',
    '25': '25th', '26': '26th', '27': '27th', '28': '28th',
    '29': '29th', '30': '30th'
}

# Category List View Cosntants
SUB_CATEGORY_KEYS = [
    'Category', 'Budgetted Amount',
    'Monthly Transactions', 'Remaining Balance'
]

TRANSACTION_KEYS = [
    'S.No.', 'Date', 'Amount', 'Payee',
    'Account', 'Categories', 'Bill', 'Budget',
    'Cleared'
]

# Budget Page View-Constants
BUDGET_KEYS = ['Name', 'budgeted', 'Spent', 'Left']
BUDGET_LABELS = ['Total Spent', 'Total Left']

# Funds table keys
FUND_KEYS = [
    'S.No.', 'See Overtime Graph', 'Account Name', 'Current Balance',
    'Freeze Amount', 'Used Lock Fund', 'Available Fund', 'Action'
]

# Loan Types
LOAN_TYPES = [
    'Mortgage', 'Loan', 'Student Loan',
    'Personal Loan', 'Medical Debt', 'Other Debt'
]

# Mortgage Keys
MORTGAGE_KEYS = [
    'Month', 'Initial Balance', 'Payment',
    'Interest', 'Principle', 'Ending Balance'
]

# Property Keys
PROPERTY_KEYS = [
    'Properties', 'Address', 'Property Value',
    'Total Monthly Rent', 'Tenants/Owners', 'Open Maintenance'
]

# Maintainence Keys
MAINTENANCE_KEYS = ['Properties', 'Address', 'Request', 'Category', 'Status']

# Property Expenses Keys
PROPERTY_EXPENSES_KEYS = ['Properties', 'Category', 'Date', 'Request', 'Amount']

# Property Income Graph labels
INCOME_LABELS = ['Total Open Invoices', 'Overdue', 'Partially Paid', 'Fully Paid']

# Property Income Keys
INCOME_KEYS = ['Property', 'Unit', 'Amount', 'Paid', 'Balance']

# Invoice Keys
INVOICE_KEYS = ['Invoice Id', 'Due on', 'Paid on', 'Amount', 'Paid', 'Balance', 'Status']
