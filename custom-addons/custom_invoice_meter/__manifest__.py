{
    'name': 'Custom Invoice Meter Readings',
    'version': '1.0',
    'license': 'LGPL-3',
    'category': 'Accounting',
    'summary': 'Adds Previous, New, Actual columns to invoice lines',
    'depends': ['account', 'account_payment', 'product', 'stock'],
    'data': [
        'security/ir.model.access.csv',

        # views
        'views/invoice_move_line_views.xml',
        'views/product_views.xml',
        'views/utility_meter_views.xml',
        'views/utility_meter_menu.xml',

        # reports
        'reports/invoice_report_views.xml',
    ],
    'installable': True,
    'application': False,
}
