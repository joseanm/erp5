# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2009 Nexedi SA and Contributors. All Rights Reserved.
#                     Nicolas Delaby <nicolas@nexedi.com>
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

from AccessControl import ClassSecurityInfo
from Products.ERP5Type.XMLObject import XMLObject
from Products.ERP5Type import PropertySheet
from Products.ERP5Type import Permissions
from Products.ERP5Type.Tool.MemcachedTool import memcached_dict_pool

class MemcachedPlugin(XMLObject):
  """Memcached Plugin authorise Memcached Tool to connect several backends.
  """

  meta_type = 'ERP5 Memcached Plugin'
  portal_type = 'Memcached Plugin'

  allowed_types = ()

  security = ClassSecurityInfo()
  security.declareProtected(Permissions.ManagePortal,
                            'manage_editProperties',
                            'manage_changeProperties',
                            'manage_propertiesForm',
                            )

  property_sheets = ( PropertySheet.Base
                    , PropertySheet.SimpleItem
                    , PropertySheet.Folder
                    , PropertySheet.MemcachedPlugin
                    , PropertySheet.SortIndex
                    , PropertySheet.Url
                    )

  def manage_beforeDelete(self, *args, **kw):
    try:
      del(memcached_dict_pool.memcached_dict)
    except AttributeError:
      pass
    XMLObject.manage_beforeDelete(self, *args, **kw)

  def manage_afterAdd(self, *args, **kw):
    try:
      del(memcached_dict_pool.memcached_dict)
    except AttributeError:
      pass
    XMLObject.manage_afterAdd(self, *args, **kw)
