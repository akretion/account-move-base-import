# -*- coding: utf-8 -*-
# © 2014-2016 Akretion (http://www.akretion.com)
#   @author Mourad EL HADJ MIMOUNE <mourad.elhadj.mimoune@akretion.com>
#   @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Base Import Mercanet in account move',
    'version': '0.1',
    'license': 'AGPL-3',
    'author': 'Akretion',
    'website': 'http://www.akretion.com',
    'summary': 'Base Import Mercanet to account move from CSV files',
    'depends': [
                'account_move_base_import',
                'account_move_base_import_remittance',
                'base_transaction_id',
    ],
    'data': [
        'views/account_view.xml',
    ],
    'installable': True,
}
