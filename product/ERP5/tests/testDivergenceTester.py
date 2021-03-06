##############################################################################
#
# Copyright (c) 2006 Nexedi SARL and Contributors. All Rights Reserved.
#          Romain Courteaud <romain@nexedi.com>
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#
##############################################################################

import unittest
from Products.ERP5Type.tests.ERP5TypeTestCase import ERP5TypeTestCase
from Products.ERP5Type.tests.Sequence import Sequence
from Products.ERP5.tests.testPackingList import TestPackingListMixin
from Products.ERP5.tests.utils import newSimulationExpectedFailure

class TestDivergenceTester(TestPackingListMixin, ERP5TypeTestCase):
  """
  Check isDivergent method on movement, delivery
  """
  run_all_test = 1
  quiet = 0

  divergence_test_sequence_suffix = '''
    SetPackingListMovementAndSimulationMovement
    ResetDeliveringRule
    CheckPackingListIsNotDivergent
  '''
  divergence_test_sequence = (TestPackingListMixin.default_sequence +
                              divergence_test_sequence_suffix)

  def getTitle(self):
    return "Divergence Tester"

  def getDeliveringRule(self):
    return self.getRule(reference='default_delivering_rule',
                        validation_state="validated")

  def beforeTearDown(self):
    self.abort()
    portal_rules = self.portal.portal_rules
    rule_id_list = [rule_id for rule_id in portal_rules.objectIds()
                    if rule_id.startswith('testDivergenceTester_')]
    if rule_id_list:
      portal_rules.deleteContent(rule_id_list)
      self.tic()

  def stepResetDeliveringRule(self, sequence):
    original_rule = rule = self.getDeliveringRule()
    self.assertEqual(rule.getId(), 'new_delivery_simulation_rule')
    # We clone the rule and clean it up to be able to experiment with it
    portal_rules = self.portal.portal_rules
    prefix = 'testDivergenceTester_'
    new_rule_id = prefix + rule.getId()
    new_rule_reference = prefix + rule.getReference()
    rule = portal_rules.manage_clone(rule, new_rule_id)
    rule.setVersion(str(int(rule.getVersion()) + 1))
    rule.setReference(new_rule_reference)
    tester_list = rule.contentValues(
             portal_type=rule.getPortalDivergenceTesterTypeList())
    rule.deleteContent([x.getId() for x in tester_list])
    rule.validate()
    # override the rule that oversees the packing_list_lines if possible:
    movement = sequence.get('packing_list_line')
    if movement is not None:
      applied_rule = movement.getDeliveryRelatedValue().getParentValue()
      applied_rule.setSpecialiseValue(rule)
    self.tic()
    sequence.edit(rule=rule)

  def stepSetPackingListMovementAndSimulationMovement(self, sequence):
    """
    Set the packing movement, delivery
    """
    packing_list = sequence['packing_list']
    # XXX-Leo can't we just use sequence['packing_list_line']?
    movement = packing_list.getMovementList()[0]
    rule = self.getDeliveringRule()
    sequence.edit(
        packing_list=packing_list,
        movement=movement,
        sim_mvt=movement.getDeliveryRelatedValueList()[0])

  def stepSetNewQuantity(self, sequence=None, 
                         sequence_list=None, **kw):
    """
    Modify the quantity of the delivery movement
    """
    packing_list = sequence.get('packing_list')
    movement = sequence.get('movement')
    movement.setQuantity(movement.getQuantity()+1234)

  def stepSetPreviousQuantity(self, sequence=None, 
                              sequence_list=None, **kw):
    """
    Reset the quantity of the delivery movement
    """
    sim_mvt = sequence.get('sim_mvt')
    movement = sequence.get('movement')
    movement.setQuantity(sim_mvt.getQuantity())

  def stepSetPreviousQuantityWithEpsilon(self, sequence=None, 
                                         sequence_list=None, **kw):
    sim_mvt = sequence.get('sim_mvt')
    movement = sequence.get('movement')
    prevision = sim_mvt.getQuantity()
    decision = prevision * (1 + 1e-15)
    self.assertNotEqual(prevision, decision)
    movement.setQuantity(decision)

  def _addDivergenceTester(self, sequence, tester_type, tester_name, **kw):
    """
    Add a divergence tester to the rule
    """
    kw.setdefault('tested_property', tester_name)
    rule = sequence.get('rule')
    divergence_tester = rule.newContent(id=tester_name,
                                        portal_type=tester_type,
                                        **kw)
    sequence[tester_name + '_divergence_tester'] = divergence_tester
    return divergence_tester

  def stepAddQuantityDivergenceTester(self, sequence):
    self._addDivergenceTester(
      sequence,
      tester_name='quantity',
      tester_type='Net Converted Quantity Divergence Tester',
      quantity_range_max=0.0,
    )

  def stepAddSourceCategoryDivergenceTester(self, sequence):
    self._addDivergenceTester(
      sequence,
      tester_name='source',
      tester_type='Category Membership Divergence Tester',
    )

  def stepAddAggregateCategoryDivergenceTester(self, sequence):
    self._addDivergenceTester(
      sequence,
      tester_name='aggregate',
      tester_type='Category Membership Divergence Tester',
    )

  def stepAddStartDateDivergenceTester(self, sequence):
    self._addDivergenceTester(
      sequence,
      tester_name='start_date',
      tester_type='DateTime Divergence Tester',
      quantity=0,
    )

  def test_01_QuantityDivergenceTester(self, quiet=quiet, run=run_all_test):
    """
    Test the quantity divergence tester
    """
    if not run: return
    sequence_string = self.divergence_test_sequence + """
          SetNewQuantity
          Tic
          CheckPackingListIsNotDivergent
          AddQuantityDivergenceTester
          CheckPackingListIsDivergent
          SetPreviousQuantity
          CheckPackingListIsNotDivergent
          SetPreviousQuantityWithEpsilon
          CheckPackingListIsNotDivergent
          Tic
    """
    sequence = Sequence(self)
    sequence(sequence_string, quiet=self.quiet)

  def stepSetNewSource(self, sequence=None, 
                       sequence_list=None, **kw):
    """
    Modify the source of the delivery
    """
    packing_list = sequence.get('packing_list')
    packing_list.setSource(None)

  def stepSetPreviousSource(self, sequence=None, 
                            sequence_list=None, **kw):
    """
    Reset the quantity of the delivery
    """
    sim_mvt = sequence.get('sim_mvt')
    packing_list = sequence.get('packing_list')
    packing_list.setSource(sim_mvt.getSource())

  def test_02_CategoryDivergenceTester(self, quiet=quiet, run=run_all_test):
    """
    Test the category divergence tester
    """
    if not run: return
    sequence_string = self.divergence_test_sequence + """
          SetNewSource
          Tic
          CheckPackingListIsNotDivergent
          AddSourceCategoryDivergenceTester
          CheckPackingListIsDivergent
          SetPreviousSource
          CheckPackingListIsNotDivergent
          Tic
    """
    sequence = Sequence(self)
    sequence(sequence_string, quiet=self.quiet)

  def stepSetNewStartDate(self, sequence=None, 
                       sequence_list=None, **kw):
    """
    Modify the source of the delivery
    """
    packing_list = sequence.get('packing_list')
    packing_list.setStartDate(packing_list.getStartDate()+10)

  def stepSetPreviousStartDate(self, sequence=None, 
                               sequence_list=None, **kw):
    """
    Reset the quantity of the delivery
    """
    sim_mvt = sequence.get('sim_mvt')
    packing_list = sequence.get('packing_list')
    packing_list.setStartDate(sim_mvt.getStartDate())

  def test_03_PropertyDivergenceTester(self, quiet=quiet, run=run_all_test):
    """
    Test the property divergence tester
    """
    if not run: return
    sequence_string = self.divergence_test_sequence + """
          SetNewStartDate
          CheckPackingListIsNotDivergent
          AddStartDateDivergenceTester
          CheckPackingListIsDivergent
          SetPreviousStartDate
          CheckPackingListIsNotDivergent
          Tic
    """
    sequence = Sequence(self)
    sequence(sequence_string, quiet=self.quiet)

  def stepSetNewAggregate(self, sequence=None, 
                          sequence_list=None, **kw):
    """
    Modify the aggregate of the delivery movement
    """
    movement = sequence.get('movement')
    # Set an aggregate value which does not exist
    # but it should not be a problem for testing the divergence
    movement.setAggregate('a_great_module/a_random_id')

  def stepSetPreviousAggregate(self, sequence=None, 
                            sequence_list=None, **kw):
    """
    Reset the quantity of the delivery
    """
    movement = sequence.get('movement')
    movement.setAggregate(None)

  def test_04_CategoryDivergenceTester(self, quiet=quiet, run=run_all_test):
    """
    Test the category divergence tester
    """
    if not run: return
    sequence_string = self.divergence_test_sequence + """
          SetNewAggregate
          CheckPackingListIsNotDivergent
          AddAggregateCategoryDivergenceTester
          CheckPackingListIsDivergent
          SetPreviousAggregate
          CheckPackingListIsNotDivergent
          Tic
    """
    sequence = Sequence(self)
    sequence(sequence_string, quiet=self.quiet)

  def test_QuantityDivergenceTesterCompareMethod(self):
    # XXX-Leo this test is actually just testing
    # FloatEquivalenceTester, and is incomplete. It should test also
    # with:
    # 
    #  * divergence_test_sequence.setProperty('quantity_range_min', ...)
    #  * divergence_test_sequence.setProperty('tolerance_base', ...)
    #    * including all variants like resources, prices and precisions
    sequence = Sequence(self)
    sequence(self.confirmed_order_without_packing_list + '''
      ResetDeliveringRule
      AddQuantityDivergenceTester
    ''')
    divergence_tester = sequence['quantity_divergence_tester']

    decision = sequence['order_line']
    prevision = decision.getDeliveryRelatedValue(
      portal_type=self.simulation_movement_portal_type)
    def divergence_tester_compare(prevision_value, decision_value):
      prevision.setQuantity(prevision_value)
      decision.setQuantity(decision_value)
      return divergence_tester.compare(prevision, decision)

    self.assertFalse(divergence_tester.isDecimalAlignmentEnabled())
    self.assertFalse(divergence_tester_compare(3.0, 3.001))
    self.assertTrue(divergence_tester_compare(3.0, 3.0))

    divergence_tester.setDecimalAlignmentEnabled(True)
    divergence_tester.setDecimalRoundingOption('ROUND_DOWN')
    divergence_tester.setDecimalExponent('0.01')

    self.assertTrue(divergence_tester_compare(3.0, 3.001))
    self.assertTrue(divergence_tester_compare(3.0, 3.0))

    divergence_tester.setDecimalExponent('0.001')
    self.assertFalse(divergence_tester_compare(3.0, 3.001))

    divergence_tester.setDecimalRoundingOption('ROUND_UP')
    divergence_tester.setDecimalExponent('0.01')
    self.assertFalse(divergence_tester_compare(3.0, 3.001))

    divergence_tester.setDecimalRoundingOption('ROUND_HALF_UP')
    divergence_tester.setDecimalExponent('0.01')
    self.assertTrue(divergence_tester_compare(3.0, 3.001))


def test_suite():
  suite = unittest.TestSuite()
  suite.addTest(unittest.makeSuite(TestDivergenceTester))
  return suite
