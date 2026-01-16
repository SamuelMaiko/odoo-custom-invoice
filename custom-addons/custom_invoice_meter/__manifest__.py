{
    'name': 'Custom Invoice Meter Readings',
    'version': '1.0',
    'license': 'LGPL-3',
    'category': 'Accounting',
    'summary': 'Adds Previous, New, Actual columns to invoice lines',
    'depends': ['account'],
    'data': [
        'security/ir.model.access.csv',
        # Views and reports will be added later
    ],
    'installable': True,
    'application': False,
}
