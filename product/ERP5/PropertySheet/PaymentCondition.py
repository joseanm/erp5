##############################################################################
#
# Copyright (c) 2002 Coramy SAS and Contributors. All Rights Reserved.
#          Thierry Faucher <Thierry_Faucher@coramy.com>
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################


class PaymentCondition:
  """
    Payment Conditions are used to define all the parameters of a payment
  """

  _properties = (
        {   'id'          : 'payment_term',
            'description' : 'payment term in a number of days',
            'type'        : 'int',
            'mode'        : 'w' },
        {   'id'          : 'payment_date',
            'description' : 'An absolute payment date',
            'type'        : 'date',
            'mode'        : 'w' },
        {   'id'          : 'payment_end_of_month',
            'description' : 'is the payment required on the end of month',
            'type'        : 'boolean',
            'mode'        : 'w' },
        {   'id'          : 'payment_additional_term',
            'description' : 'additionnal term in a number of days',
            'type'        : 'int',
            'mode'        : 'w' },
      )

  _categories = ( 'trade_date', 'payment_mode',
                  'source_payment', 'destination_payment', )

