# -*- coding: utf-8 -*-
# © 2014-2016 Akretion (http://www.akretion.com)
#   @author Mourad EL HADJ MIMOUNE <mourad.elhadj.mimoune@akretion.com>
#   @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Base Import move auto completion',
    'version': '8.0.0.1',
    'license': 'AGPL-3',
    'author': 'Akretion',
    'website': 'http://www.akretion.com',
    'summary': 'Base Import move auto completion based on transactionID',
    'depends': [
                'account_move_base_import',
                'base_transaction_id',
    ],
    'data': [
        'views/account_view.xml',
    ],
    'installable': True,
}
