##############################################################################
#
# Copyright (c) 2002, 2005 Nexedi SARL and Contributors. All Rights Reserved.
#                    Jean-Paul Smets-Solanes <jp@nexedi.com>
#                    Romain Courteaud <romain@nexedi.com>
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

from TargetSolver import TargetSolver

class CopyToTarget(TargetSolver):
  """
  Copy values simulation movement as target. This is
  only acceptable for root movements. The meaning of
  this solver of other movements is far from certain.
  """
  def _generateValueDeltaDict(self, movement):
    """
    Get interesting value
    """
    # Get interesting value
    old_quantity = movement.getQuantity()
    old_start_date = movement.getStartDate()
    old_stop_date = movement.getStopDate()
    new_quantity = movement.getDeliveryQuantity() * \
                   movement.getDeliveryRatio()
    new_start_date = movement.getDeliveryStartDateList()[0]
    new_stop_date = movement.getDeliveryStopDateList()[0]
    # Calculate delta
    quantity_ratio = 0
    if old_quantity not in (None,0.0):
      quantity_ratio = new_quantity / old_quantity
    start_date_delta = 0
    stop_date_delta = 0
    if new_start_date is not None and old_start_date is not None:
      start_date_delta = new_start_date - old_start_date
    if new_stop_date is not None and old_stop_date is not None:
      stop_date_delta = new_stop_date - old_stop_date
    return {
      'quantity_ratio': quantity_ratio,
      'start_date_delta': start_date_delta,
      'stop_date_delta': stop_date_delta,
    }

  def solve(self, movement):
    """
    Adopt values as new target
    """
    value_dict = self._generateValueDeltaDict(movement)
    # Modify recursively simulation movement
    self._recursivelySolve(movement, **value_dict)

  def _generateValueDict(self, movement, quantity_ratio=1, 
                         start_date_delta=0, stop_date_delta=0,
                         **value_delta_dict):
    """
    Generate values to save on movement.
    """
    value_dict = {}
    # Modify quantity, start_date, stop_date
    start_date = movement.getStartDate()
    if start_date is not None:
      value_dict['start_date'] = start_date + start_date_delta
    stop_date = movement.getStopDate()
    if stop_date is not None:
      value_dict['stop_date'] = stop_date + stop_date_delta
    value_dict['quantity'] = movement.getQuantity() * quantity_ratio
    return value_dict

  def _getParentParameters(self, movement, 
                           **value_delta_dict):
    """
    Get parent movement, and its value delta dict.
    """
    applied_rule = movement.getParent()
    parent_movement = applied_rule.getParent()
    if parent_movement.getPortalType() != "Simulation Movement":
      parent_movement = None
    return parent_movement, value_delta_dict

  def _recursivelySolve(self, movement, **value_delta_dict):
    """
    Update value of the current simulation movement, and update his parent
    movement.
    """
    value_dict = self._generateValueDict(movement, **value_delta_dict)
    movement.edit(**value_dict)
    parent_movement, parent_value_delta_dict = \
                self._getParentParameters(movement, **value_delta_dict)
    if parent_movement is not None:
      # Modify the parent movement
      self._recursivelySolve(parent_movement, **parent_value_delta_dict)
