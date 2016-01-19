# -*- coding: utf-8 -*-
##############################################################################
#    account_move_base_import module for Odoo
#    Copyright (C) 2014-2016 Akretion (http://www.akretion.com)
#    @author Mourad EL HADJ MIMOUNE <mourad.elhadj.mimoune@akretion.com>
#    @author Sébastien BEAU <sebastien.beau@akretion.com>
#    code factoring from account_statement_base_import of Camptocamp SA
#    Author Nicolas Bessi, Joel Grand-Guillaume
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import datetime
from .file_parser import FileParser
from file_parser import float_or_zero
from openerp.tools import ustr


class GenericFileParser(FileParser):
    """Standard parser that use a define format in csv or xls to import into a
    account move. This is mostely an example of how to proceed to create a
    new parser, but will also be useful as it allow to import a basic flat
    file.
    """

    def __init__(self, parse_name, ftype='csv', **kwargs):
        conversion_dict = {
            'ref': ustr,
            'name': ustr,
            'date': datetime.datetime,
            'debit': float_or_zero,
            'credit': float_or_zero,
            'account_id': ustr,
            }
        super(GenericFileParser, self).__init__(
            parse_name, ftype=ftype,
            extra_fields=conversion_dict,
            **kwargs)

    @classmethod
    def parser_for(cls, parser_name):
        """Used by the new_account_move_parser class factory. Return true if
        the providen name is generic_csvxls
        """
        return parser_name == 'generic_csvxls'

    def get_st_line_vals(self, line, *args, **kwargs):
        """
        This method must return a dict of vals that can be passed to create
        method of account move line in order to record it. It is the
        responsibility of every parser to give this dict of vals, so each one
        can implement his own way of recording the lines.
            :param:  line: a dict of vals that represent a line of
              result_row_list
            :return: dict of values to give to the create method of statement
              line, it MUST contain at least:
                {  'ref': value,
                    'name': value,
                    'date': value,
                    'debit': value,
                    'credit': value,
                    'account_id': value,
                }
        """
        return {
            'ref': line.get('ref', '/'),
            'name': line.get('name', line.get('ref', '/')),
            'date': line.get('date', datetime.datetime.now().date()),
            'debit': line.get('debit', 0.0),
            'debit': line.get('debit', 0.0),
            'account_id': line.get('account_id', ''),
        }
