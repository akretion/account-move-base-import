# -*- encoding: utf-8 -*-
##############################################################################
#
#    account_move_base_import module for Odoo
#    Copyright (C) 2014-2016 Akretion (http://www.akretion.com)
#    @author Mourad EL HADJ MIMOUNE <mourad.elhadj.mimoune@akretion.com>
#    @author Sébastien BEAU <sebastien.beau@akretion.com>
#    some code are refactoing form account_statement_base_completion and
#    account_statement_base_import of Camptocamp SA and ported to v8.
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
import sys
import traceback
import datetime
from openerp import fields, models, _
from .parser import new_account_move_parser
from openerp.tools.config import config
import psycopg2
import simplejson
from openerp.exceptions import except_orm

class AccountJournal(models.Model):
    _inherit = "account.journal"

    def _get_import_type_selection(self):
        """This is the method to be inherited for adding the imprt type"""
        return [('move_line', 'Move lines')]

    def __get_import_type_selection(self):
        """ Call method which can be inherited """
        return self._get_import_type_selection()

    def _get_import_parser_selection(self):
        """This is the method to be inherited for adding the parser"""
        return [('generic_csvxls', 'Generic csv xls')]

    def __get_import_parser_selection(self):
        """ Call method which can be inherited """
        return self._get_import_parser_selection()

    import_ok = fields.Boolean(
            'Used for import',
            help="Check to use this journal to import account move")
    import_type = fields.Selection(
            __get_import_type_selection,
            'Import type',
            required=False,
            help="Choose here which import type you want to import "
                 "account mouve.")
    import_parser = fields.Selection(
            __get_import_parser_selection,
            'Import parser',
            required=False,
            help="Choose here which parser you want to import "
                 "account mouve.")
    import_balance_check = fields.Boolean(
            'Balance check',
            help="Balance check befor import account move")


class AccountMove(models.Model):
    _inherit = "account.move"

    def prepare_move_lines_vals(self, parser_vals, move_id, journal_id):
        """Hook to build the values of a line from the parser returned values.
        At least it fullfill the move_id. Overide it to add your own
        completion if needed.

        :param dict of vals from parser for account.move.line
          (called by parser.get_st_line_vals)
        :param int/long move_id: ID of the concerned account.move
        :return: dict of vals that will be passed to create method of
          move line.
        """
        move_line_obj = self.env['account.move.line']
        values = parser_vals
        values['move_id'] = move_id
        values['journal_id'] = journal_id
        date = values.get('date')
        period_memoizer = self._context.get('period_memoizer') or {}
        if period_memoizer.get(date):
            values['period_id'] = period_memoizer[date]
        else:
            periods = self.env['account.period'].find(dt=values.get('date'))
            values['period_id'] = periods and periods[0].id or False
            period_memoizer[date] = periods and periods[0].id or False
        values = move_line_obj._add_missing_default_values(values)
        return values

    def prepare_move_vals(self, journal_id, result_row_list, parser):
        """Hook to build the values of the move from the parser and
        the journal.
        """
        vals = {'journal_id': journal_id}
        vals.update(parser.get_st_vals())
        return vals

    def multi_move_import(self, journal_id, file_stream, ftype="csv"):
        """Create multiple moves from values given by the parser for
        the given journal.

        :param int/long journal_id: ID of the journal used to import the file
        :param filebuffer file_stream: binary of the providen file
        :param char: ftype represent the file exstension (csv by default)
        :return: list: list of the created account.mouve
        """
        if not journal_id:
            raise except_orm(
                _("No acount journal!"),
                _("You must provide a valid acount journal to import an "
                  "account move!"))
        import pdb; pdb.set_trace()
        parser = new_account_move_parser(journal_id, ftype=ftype)
        res = []
        for result_rowjournal_obj_list in parser.parse(file_stream):
            move_id = self._move_import(
                journal_id, parser, file_stream, ftype=ftype)
            res.append(move_id)
        return res

    def _move_import(self, journal_id, parser, file_stream, ftype="csv"):
        """Create a account move with the given journal and parser. It will
        fullfill the account move with the values of the file providen, but
        will not complete data (like finding the partner, or the right
        analytic account). This will be done in a second step with the
                completion rules.

        :param journal_id : The journal_id used to import the file
        :param parser: the parser
        :param filebuffer file_stream: binary of the providen file
        :param char: ftype represent the file exstension (csv by default)
        :return: ID of the created account.move
        """
        move_obj = self.env['account.move']
        move_line_obj = self.env['account.move.line']
        attachment_obj = self.env['ir.attachment']
        result_row_list = parser.result_row_list
        # Check all key are present in account.move.line!!
        if not result_row_list:
            raise except_orm(_("Nothing to import"), _("The file is empty"))
        parsed_cols = parser.get_st_line_vals(result_row_list[0]).keys()
        for col in parsed_cols:
            if col not in move_line_obj._columns:
                raise except_orm(
                    _("Missing column!"),
                    _("Column %s you try to import is not present in the "
                      "move line!") % col)
        move_vals = self.prepare_move_vals(
            journal_id.id, result_row_list, parser)
        move_id = move_obj.create(move_vals)
        try:
            # Record every line in the account move
            move_store = []
            for line in result_row_list:
                parser_vals = parser.get_st_line_vals(line)
                values = self.prepare_move_lines_vals(
                    parser_vals, move_id.id, journal_id.id)
                move_store.append(values)
            # Hack to bypass ORM poor perfomance....
            move_line_obj._insert_lines(move_store)
            self._write_extra_move_lines(
                parser, result_row_list, journal_id, move_id)
            attachment_data = {
                'name': 'move file',
                'datas': file_stream,
                'datas_fname': "%s.%s" % (datetime.datetime.now().date(),
                                          ftype),
                'res_model': 'account.move',
                'res_id': move_id,
            }
            attachment_obj.create(attachment_data)
            # déplacer dans le module base completion
            # # If user ask to launch completion at end of import, do it!
            # if journal_id.launch_import_completion:
            #     move_obj.button_auto_completion([move_id])
            # Write the needed log infos on profile
            self.write_logs_after_import(journal_id.id,
                                         move_id,
                                         len(result_row_list))
        except Exception:
            error_type, error_value, trbk = sys.exc_info()
            st = "Error: %s\nDescription: %s\nTraceback:" % (
                error_type.__name__, error_value)
            st += ''.join(traceback.format_tb(trbk, 30))
            # TODO we should catch correctly the exception with a python
            # Exception and only re-catch some special exception.
            # For now we avoid re-catching error in debug mode
            if config['debug_mode']:
                raise
            raise except_orm(_("move import error"),
                             _("The move cannot be created: %s") % st)
        return move_id


class AccountMoveline(models.Model):
    _inherit = "account.move.line"

    def _get_available_columns(self, move_store,
                               include_serializable=False):
        """Return writeable by SQL columns"""
        move_line_obj = self.env['account.move.line']
        model_cols = move_line_obj._columns
        import pdb; pdb.set_trace()
        avail = [
            k for k, col in model_cols.iteritems()
        ]
        keys = [k for k in move_store[0].keys() if k in avail]
        # TODO manage sparse fields if exists..
        # if include_serializable:
        #     for k, col in model_cols.iteritems():
        #         if k in move_store[0].keys() and \
        #                 isinstance(col, fields.sparse) and \
        #                 col.serialization_field not in keys and \
        #                 col._type == 'char':
        #             keys.append(col.serialization_field)
        keys.sort()
        return keys

    def _prepare_insert(self, move, cols):
        """ Apply column formating to prepare data for SQL inserting
        Return a copy of move
        """
        st_copy = move
        for k, col in st_copy.iteritems():
            if k in cols:
                st_copy[k] = self._columns[k]._symbol_set[1](col)
        return st_copy

    def _prepare_manyinsert(self, move_store, cols):
        """ Apply column formating to prepare multiple SQL inserts
        Return a copy of move_store
        """
        values = []
        for move in move_store:
            values.append(self._prepare_insert(move, cols))
        return values

    def _serialize_sparse_fields(self, cols, move_store):
        """ Serialize sparse fields values in the target serialized field
        Return a copy of smove_store
        """
        move_line_obj = self.env['account.move.line']
        model_cols = move_line_obj._columns
        sparse_fields = dict(
            [(k, col) for k, col in model_cols.iteritems() if isinstance(
                col, fields.sparse) and col._type == 'char'])
        values = []
        for move in move_store:
            to_json_k = set()
            st_copy = move.copy()
            for k, col in sparse_fields.iteritems():
                if k in st_copy:
                    to_json_k.add(col.serialization_field)
                    serialized = st_copy.setdefault(
                        col.serialization_field, {})
                    serialized[k] = st_copy[k]
            for k in to_json_k:
                st_copy[k] = simplejson.dumps(st_copy[k])
            values.append(st_copy)
        return values

    def _insert_lines(self, move_store):
        """ Do raw insert into database because ORM is awfully slow
            when doing batch write. It is a shame that batch function
            does not exist"""
        move_line_obj = self.env['account.move.line']
        move_line_obj.check_access_rule('create')
        move_line_obj.check_access_rights('create', raise_exception=True)
        cols = self._get_available_columns(
            move_store, include_serializable=True)
        move_store = self._prepare_manyinsert(move_store, cols)
        tmp_vals = (', '.join(cols), ', '.join(['%%(%s)s' % i for i in cols]))
        sql = "INSERT INTO account_move_line (%s) " \
              "VALUES (%s);" % tmp_vals
        import pdb; pdb.set_trace()
        try:
            self._cr.executemany(sql, tuple(move_store))
            # TODO handle serialized fields
            # sql, tuple(self._serialize_sparse_fields(cols, move_store)))
        except psycopg2.Error as sql_err:
            self._cr.rollback()
            raise except_orm(_("ORM bypass error"), sql_err.pgerror)

    def _update_line(self, vals):
        """ Do raw update into database because ORM is awfully slow
            when cheking security.
        TODO / WARM: sparse fields are skipped by the method. IOW, if your
        completion rule update an sparse field, the updated value will never
        be stored in the database. It would be safer to call the update method
        from the ORM for records updating this kind of fields.
        """
        cols = self._get_available_columns([vals])
        vals = self._prepare_insert(vals, cols)
        tmp_vals = (', '.join(['%s = %%(%s)s' % (i, i) for i in cols]))
        sql = "UPDATE account_move_line " \
              "SET %s where id = %%(id)s;" % tmp_vals
        try:
            self._cr.execute(sql, vals)
        except psycopg2.Error as sql_err:
            self._cr.rollback()
            raise except_orm(_("ORM bypass error"), sql_err.pgerror)
