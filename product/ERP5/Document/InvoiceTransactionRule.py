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

from AccessControl import ClassSecurityInfo
from Products.ERP5Type import Permissions, PropertySheet, Constraint, Interface
from Products.ERP5.Document.Rule import Rule
from Products.ERP5Type.XMLMatrix import XMLMatrix
from Products.CMFCore.utils import getToolByName
from UserDict import UserDict

from zLOG import LOG

class InvoiceTransactionRule(Rule, XMLMatrix):
    """
      Invoice Transaction Rule object generates accounting movements
      for each invoice movement based on category membership and
      other predicated. Template accounting movements are stored
      in cells inside an instance of the InvoiceTransactionRule.

      WARNING: what to do with movement split ?
    """

    # CMF Type Definition
    meta_type = 'ERP5 Invoice Transaction Rule'
    portal_type = 'Invoice Transaction Rule'
    add_permission = Permissions.AddPortalContent
    isPortalContent = 1
    isRADContent = 1

    # Declarative security
    security = ClassSecurityInfo()
    security.declareObjectProtected(Permissions.View)

    # Default Properties
    property_sheets = ( PropertySheet.Base
                      , PropertySheet.XMLObject
                      , PropertySheet.CategoryCore
                      , PropertySheet.DublinCore
                      )

    def _getMatchingCell(self, movement):
      """
        Browse all cells and test them until match found
      """
      for cell in self.getCellValueList(base_id = 'vat_per_region'):
        if cell.test(movement):
          LOG('Found Cell' ,0, cell.getRelativeUrl())
          return cell
      return None          
    
    def _getMatchingCell_AlternateImpl(self, movement):
      """
        Browse all predicates and make sur all dimensions match
        An alternate implementation left as example
      """
      dimension_dict = {}   # Possible dimensions
      tdimension_dict = {}  # Dimensions which responded 1 on test
      for predicate in self.contentValues():        
        if predicate.is_predicate:
          if predicate.getStringIndex() not in tdimension_dict.keys() \
              and predicate.test(movement):
            tdimension_dict[predicate.getStringIndex()] = predicate.getRelativeUrl()
          dimension_dict[predicate.getStringIndex()] = 1
      if len(dimension_dict) == len(tdimension_dict):
        # If all dimesions are satisfied, then return 1
        cell_key = []
        for matrix_range_item in self.getCellRange(base_id = 'vat_per_region'):
          for range_item in matrix_range_item:
            if range_item in tdimension_dict.values():
              cell_key.append(range_item)
              break # Just in case, make sure only one range_item per matrix_range_item
        kwd = {'base_id': 'vat_per_region'}                      
        return self.getCell(*cell_key, **kwd)
      return None          
                    
    def test(self, movement):
      """
        Tests if the rule (still) applies
      """
      # An invoice transaction rule applies when the movement's parent is an invoice rule
      parent = movement.getParentValue()
      parent_rule_value = parent.getSpecialiseValue()
      if parent_rule_value is None:
        return 0        
      if parent_rule_value.getPortalType() in ('Invoicing Rule', 'Invoice Rule'):
        if self._getMatchingCell(movement) is not None:
          return 1
      return 0

    # Simulation workflow
    security.declareProtected(Permissions.ModifyPortalContent, 'expand')
    def expand(self, applied_rule, force=0, **kw):
      """
        Expands the current movement downward.

        -> new status -> expanded

        An applied rule can be expanded only if its parent movement
        is expanded.
      """

      invoice_transaction_line_type = 'Simulation Movement'

      # First, get the simulation movement we were expanded from
      my_invoice_line_simulation = applied_rule.getParentValue()

      # Next, we can try to expand the rule
      if force or \
         (applied_rule.getLastExpandSimulationState() not in self.getPortalReservedInventoryStateList() and \
         applied_rule.getLastExpandSimulationState() not in self.getPortalCurrentInventoryStateList()):

        # Find a matching cell
        my_cell = self._getMatchingCell(my_invoice_line_simulation)

        if my_cell is not None :
          my_cell_transaction_id_list = my_cell.contentIds()
        else :
          my_cell_transaction_id_list = []

        if my_cell is not None : # else, we do nothing
          # check each contained movement and delete
          # those that we don't need
          for movement in applied_rule.objectValues():
            if movement.getId() not in my_cell_transaction_id_list :
              # movement.flushActivity(invoke=0) XXX never use it
              applied_rule.deleteContent(movement.getId())
          
          # get the resource (in that order):
          #  resource from the invoice (using deliveryValue)
          #  price_currency from the invoice
          #  price_currency from the [parent]+ simulation movement's deliveryValue
          #  price_currency from the top level simulation movement's orderValue
          invoice_line = my_invoice_line_simulation.getDeliveryValue()
          invoice = invoice_line.getExplanationValue()
	  resource = None
          if invoice.getResource() is not None : 
            resource = invoice.getResource()
          elif hasattr(invoice, 'getPriceCurrency') and \
                invoice.getPriceCurrency() is not None :
             resource = invoice.getPriceCurrency()
             
          # still TODO: search resource on parents 
          if resource is None :
            LOG("InvoiceTransactionRule", 100, 
                "Unable to expand %s: no resource"%applied_rule.getPath())
	        
          # Add every movement from the Matrix to the Simulation
          for transaction_line in my_cell.objectValues() :
            if transaction_line.getId() in applied_rule.objectIds() :
              simulation_movement = applied_rule[transaction_line.getId()]
            else :
              simulation_movement = applied_rule.newContent(id=transaction_line.getId()
                  , portal_type=invoice_transaction_line_type)
	    simulation_movement._edit(
		  source = transaction_line.getSource()
                , destination = transaction_line.getDestination()
                , source_section = my_invoice_line_simulation.getSourceSection()
                , destination_section = my_invoice_line_simulation.getDestinationSection()
                , resource = resource
                , quantity = (my_invoice_line_simulation.getQuantity() * my_invoice_line_simulation.getPrice())
                  * transaction_line.getQuantity()
                  # calculate (quantity * price) * cell_quantity
                , force_update = 1
              )

        # Now we can set the last expand simulation state to the current state
        #XXX Note : this is wrong, as there isn't always a sale invoice when we expand this rule.
        #applied_rule.setLastExpandSimulationState(my_invoice.getSimulationState())

      # Pass to base class
      Rule.expand(self, applied_rule, force=force, **kw)

    security.declareProtected(Permissions.ModifyPortalContent, 'solve')
    def solve(self, applied_rule, solution_list):
      """
        Solve inconsitency according to a certain number of solutions
        templates. This updates the

        -> new status -> solved

        This applies a solution to an applied rule. Once
        the solution is applied, the parent movement is checked.
        If it does not diverge, the rule is reexpanded. If not,
        diverge is called on the parent movement.
      """

    security.declareProtected(Permissions.ModifyPortalContent, 'diverge')
    def diverge(self, applied_rule):
      """
        -> new status -> diverged

        This basically sets the rule to "diverged"
        and blocks expansion process
      """

    # Solvers
    security.declareProtected(Permissions.View, 'isDivergent')
    def isDivergent(self, applied_rule):
      """
        Returns 1 if divergent rule
      """

    security.declareProtected(Permissions.View, 'getDivergenceList')
    def getDivergenceList(self, applied_rule):
      """
        Returns a list Divergence descriptors
      """

    security.declareProtected(Permissions.View, 'getSolverList')
    def getSolverList(self, applied_rule):
      """
        Returns a list Divergence solvers
      """

    # Deliverability / orderability
    def isOrderable(self, m):
      return 1

    def isDeliverable(self, m):
      if m.getSimulationState() in self.getPortalDraftOrderStateList():
        return 0
      return 1

    # Matrix related
    security.declareProtected( Permissions.ModifyPortalContent, 'newCellContent' )
    def newCellContent(self, id,**kw):
      """
          This method can be overriden
      """
      self.invokeFactory(type_name='Accounting Rule Cell',id=id)
      new_cell = self.get(id)
      return new_cell

    security.declareProtected(Permissions.ModifyPortalContent, 'updateMatrix')
    def updateMatrix(self) :
      """
      Makes sure that the cells are consistent with the predicates.
      """
      base_id = 'vat_per_region'
      kwd = {'base_id': base_id}
      new_range = self.InvoiceTransactionRule_asCellRange() # This is a site dependent script
      #LOG('InvoiceTransactionRule.updateMatrix :', 0, repr(( new_range, self.contentIds(), [x for x in self.searchFolder()], )))

      self._setCellRange(*new_range, **kwd)
      cell_range_key_list = self.getCellRangeKeyList(base_id = base_id)
      if cell_range_key_list <> [[None, None]] :
        for k in cell_range_key_list :
          c = self.newCell(*k, **kwd)
          c.edit( mapped_value_property_list = ( 'title',),
                  predicate_category_list = filter(lambda k_item: k_item is not None, k),
                  title = 'Transaction %s' % repr(map(lambda k_item : self.restrictedTraverse(k_item).getTitle(), k)),
                  force_update = 1
                )
      else :
        # If empty matrix, delete all cells
        cell_range_id_list = self.getCellRangeIdList(base_id = base_id)
        for k in cell_range_id_list :
          if self.get(k) is not None :
            self.deleteContent(k)
