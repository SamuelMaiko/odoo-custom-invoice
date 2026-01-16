{
    'name': 'Custom Invoice Meter Readings',
    'version': '1.0',
    'license': 'LGPL-3',
    'category': 'Accounting',
    'summary': 'Adds Previous, New, Actual columns to invoice lines',
    'depends': ['account', 'account_payment'],
    'data': [
        'security/ir.model.access.csv',

        # views
        'views/invoice_move_line_views.xml',

        # Views and reports will be added later
    ],
    'installable': True,
    'application': False,
}
