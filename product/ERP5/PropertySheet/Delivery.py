##############################################################################
#
# Copyright (c) 2002 Nexedi SARL and Contributors. All Rights Reserved.
#                    Jean-Paul Smets-Solanes <jp@nexedi.com>
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

from Products.CMFCore.Expression import Expression

class Delivery:
    """
        Properties which allow to define a generic Delivery.

        Delivery objects usually have a causality.
    """

    _properties = (
    { 'id'          : 'causality_id',
      'description' : 'ids of the documents which are in causality relation with delivery',
      'type'        : 'lines',
      'override'    : 1,
      'acquisition_base_category' : ('causality',),
      'acquisition_portal_type'   : Expression('python: portal.getPortalOrderTypeList() + portal.getPortalDeliveryTypeList()'),
      'acquisition_copy_value'    : 0,
      'acquisition_mask_value'    : 0,
      'acquisition_accessor_id'   : 'getId',
      'acquisition_depends'       : None,
      'mode'        : 'w' },
    { 'id'          : 'causality_title',
      'description' : 'titles of the documents which are in causality relation with delivery',
      'type'        : 'lines',
      'override'    : 1,
      'acquisition_base_category' : ('causality',),
      'acquisition_portal_type'   : Expression('python: portal.getPortalOrderTypeList() + portal.getPortalDeliveryTypeList()'),
      'acquisition_copy_value'    : 0,
      'acquisition_mask_value'    : 0,
      'acquisition_accessor_id'   : 'getTitle',
      'acquisition_depends'       : None,
      'mode'        : 'w' },
    )

    _categories = ( 'causality', 'incoterm', 'delivery_mode')

