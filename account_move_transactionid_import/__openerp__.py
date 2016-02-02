# -*- encoding: utf-8 -*-
##############################################################################
#
#    account_bank_statement_import_mercanet module for Odoo
#    Copyright (C) 2014-2015 Akretion (http://www.akretion.com)
#    @author Mourad EL HADJ MIMOUNE <mourad.elhadj.mimoune@akretion.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name': 'Base Transaction import of account move',
    'version': '0.1',
    'license': 'AGPL-3',
    'author': 'Akretion',
    'website': 'http://www.akretion.com',
    'summary': 'Base Transaction import of account move from CSV files',
    'depends': ['account_move_base_import'],
    'data': [
        'account_view.xml',
    ],
    'installable': True,
}
