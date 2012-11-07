# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2008 Nexedi SARL and Contributors. All Rights Reserved.
#                    Aurelien Calonne <aurel@nexedi.com>
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

import socket

from AccessControl import ClassSecurityInfo
from Products.ERP5Type.Globals import InitializeClass, DTMLFile, get_request
from Products.ERP5Type.Tool.BaseTool import BaseTool
from Products.ERP5Type import Permissions
from Products.ERP5 import _dtmldir
from zLOG import LOG, INFO
import time, random
from hashlib import md5
from DateTime import DateTime
from Products.ERP5Type.Message import translateString
from Products.ERP5Type.Globals import PersistentMapping
from urllib import urlencode

class PasswordTool(BaseTool):
  """
    PasswordTool is used to allow a user to change its password
  """
  title = 'Password Tool'
  id = 'portal_password'
  meta_type = 'ERP5 Password Tool'
  portal_type = 'Password Tool'
  allowed_types = ()

  # Declarative Security
  security = ClassSecurityInfo()

  security.declareProtected(Permissions.ManagePortal, 'manage_overview' )
  manage_overview = DTMLFile( 'explainPasswordTool', _dtmldir )


  _expiration_day = 1
  _password_request_dict = {}

  def __init__(self, id=None):
    if id is None:
      id = self.__class__.id
    self._password_request_dict = PersistentMapping()
    # XXX no call to BaseTool.__init__ ?
    # BaseTool.__init__(self, id)

  security.declareProtected('Manage users', 'getResetPasswordKey')
  def getResetPasswordKey(self, user_login, expiration_date=None):
    if expiration_date is None:
      # generate expiration date
      expiration_date = DateTime() + self._expiration_day

    # generate a random string
    key = self._generateUUID()
    # XXX before r26093, _password_request_dict was initialized by an OOBTree and
    # replaced by a dict on each request, so if it's data structure is not up
    # to date, we update it if needed
    if not isinstance(self._password_request_dict, PersistentMapping):
      LOG('ERP5.PasswordTool', INFO, 'Updating password_request_dict to'
                                     ' PersistentMapping')
      self._password_request_dict = PersistentMapping()

    # register request
    self._password_request_dict[key] = (user_login, expiration_date)
    return key

  security.declareProtected('Manage users', 'getResetPasswordUrl')
  def getResetPasswordUrl(self, user_login=None, key=None, site_url=None):
    if user_login is not None:
      # XXX Backward compatibility
      key = self.getResetPasswordKey(user_login)

    parameter = urlencode(dict(reset_key=key))
    method = self._getTypeBasedMethod("getSiteUrl")
    if method is not None:
      base_url = method()
    else:
      base_url = "%s/portal_password/PasswordTool_viewResetPassword" % (
        site_url,)
    url = "%s?%s" %(base_url, parameter)
    return url

  security.declareProtected('Manage users', 'getResetPasswordUrl')
  def getExpirationDateForKey(self, key=None):
    return self._password_request_dict[key][1]


  def mailPasswordResetRequest(self, user_login=None, REQUEST=None,
                               notification_message=None, sender=None,
                               store_as_event=False,
                               expiration_date=None,
                               substitution_method_parameter_dict=None):
    """
    Create a random string and expiration date for request
    Parameters:
    user_login -- Reference of the user to send password reset link
    REQUEST -- Request object
    notification_message -- Notification Message Document used to build the email.
                            As default, a standart text will be used.
    sender -- Sender (Person or Organisation) of the email.
            As default, the default email address will be used
    store_as_event -- whenever CRM is available, store
                        notifications as events
    expiration_date -- If not set, expiration date is current date + 1 day.
    substitution_method_parameter_dict -- additional substitution dict for
                                          creating an email.
    """
    if REQUEST is None:
      REQUEST = get_request()

    if user_login is None:
      user_login = REQUEST["user_login"]

    site_url = self.getPortalObject().absolute_url()
    if REQUEST and 'came_from' in REQUEST:
      site_url = REQUEST.came_from

    msg = None
    # check user exists, and have an email
    user_list = self.getPortalObject().acl_users.\
                      erp5_users.getUserByLogin(user_login)
    if len(user_list) == 0:
      msg = translateString("User ${user} does not exist.",
                            mapping={'user':user_login})
    else:
      # We use checked_permission to prevent errors when trying to acquire
      # email from organisation
      user = user_list[0]
      email_value = user.getDefaultEmailValue(
              checked_permission='Access content information')
      if email_value is None or not email_value.asText():
        msg = translateString(
            "User ${user} does not have an email address, please contact site "
            "administrator directly", mapping={'user':user_login})
    if msg:
      if REQUEST is not None:
        parameter = urlencode(dict(portal_status_message=msg))
        ret_url = '%s/login_form?%s' % \
                  (site_url, parameter)
        return REQUEST.RESPONSE.redirect( ret_url )
      return msg

    key = self.getResetPasswordKey(user_login=user_login,
                                   expiration_date=expiration_date)
    url = self.getResetPasswordUrl(key=key, site_url=site_url)

    # send mail
    message_dict = {'instance_name':self.getPortalObject().getTitle(),
                    'reset_password_link':url,
                    'expiration_date':self.getExpirationDateForKey(key)}
    if substitution_method_parameter_dict is not None:
      message_dict.update(substitution_method_parameter_dict)

    if notification_message is None:
      subject = translateString("[${instance_name}] Reset of your password",
          mapping={'instance_name': self.getPortalObject().getTitle()})
      subject = subject.translate()
      message = translateString("\nYou requested to reset your ${instance_name}"\
                " account password.\n\n" \
                "Please copy and paste the following link into your browser: \n"\
                "${reset_password_link}\n\n" \
                "Please note that this link will be valid only one time, until "\
                "${expiration_date}.\n" \
                "After this date, or after having used this link, you will have to make " \
                "a new request\n\n" \
                "Thank you",
                mapping=message_dict)
      message = message.translate()
      event_keyword_argument_dict={}
    else:
      subject = notification_message.getTitle()
      if notification_message.getContentType() == "text/html":
        message = notification_message.asEntireHTML(substitution_method_parameter_dict=message_dict)
      else:
        message = notification_message.asText(substitution_method_parameter_dict=message_dict)
      event_keyword_argument_dict={
        'resource':notification_message.getSpecialise(),
        'language':notification_message.getLanguage(),
      }

    self.getPortalObject().portal_notifications.sendMessage(sender=sender, recipient=[user,],
                                                            subject=subject, message=message,
                                                            store_as_event=store_as_event,
                                                            event_keyword_argument_dict=event_keyword_argument_dict)
    if REQUEST is not None:
      msg = translateString("An email has been sent to you.")
      parameter = urlencode(dict(portal_status_message=msg))
      ret_url = '%s/login_form?%s' % (site_url, parameter)
      return REQUEST.RESPONSE.redirect( ret_url )

  def _generateUUID(self, args=""):
    """
    Generate a unique id that will be used as url for password
    """
    # this code is based on
    # http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/213761
    # by Carl Free Jr
    # as uuid module is only available in pyhton 2.5
    t = long( time.time() * 1000 )
    r = long( random.random()*100000000000000000L )
    try:
      a = socket.gethostbyname( socket.gethostname() )
    except:
      # if we can't get a network address, just imagine one
      a = random.random()*100000000000000000L
    data = ' '.join((str(t), str(r), str(a), str(args)))
    return md5(data).hexdigest()

  def resetPassword(self, reset_key=None, REQUEST=None):
    """
    """
    # XXX-Aurel : is it used ?
    if REQUEST is None:
      REQUEST = get_request()
    user_login, expiration_date = self._password_request_dict.get(reset_key, (None, None))
    site_url = self.getPortalObject().absolute_url()
    if REQUEST and 'came_from' in REQUEST:
      site_url = REQUEST.came_from
    if reset_key is None or user_login is None:
      ret_url = '%s/login_form' % site_url
      return REQUEST.RESPONSE.redirect( ret_url )

    # check date
    current_date = DateTime()
    if current_date > expiration_date:
      msg = translateString("Date has expire.")
      parameter = urlencode(dict(portal_status_message=msg))
      ret_url = '%s/login_form?%s' % (site_url, parameter)
      return REQUEST.RESPONSE.redirect( ret_url )

    # redirect to form as all is ok
    REQUEST.set("password_key", reset_key)
    return self.reset_password_form(REQUEST=REQUEST)


  def removeExpiredRequests(self, **kw):
    """
    Browse dict and remove expired request
    """
    current_date = DateTime()
    for key, (login, date) in self._password_request_dict.items():
      if date < current_date:
        self._password_request_dict.pop(key)


  def changeUserPassword(self, password, password_key, password_confirm=None,
                         user_login=None, REQUEST=None, **kw):
    """
    Reset the password for a given login
    """
    # check the key
    register_user_login, expiration_date = self._password_request_dict.get(
                                                    password_key, (None, None))

    current_date = DateTime()
    msg = None
    if REQUEST is None:
      REQUEST = get_request()
    site_url = self.getPortalObject().absolute_url()
    if REQUEST and 'came_from' in REQUEST:
      site_url = REQUEST.came_from
    if self.getWebSiteValue():
      site_url = self.getWebSiteValue().absolute_url()
    if register_user_login is None:
      msg = "Key not known. Please ask reset password."
    elif user_login is not None and register_user_login != user_login:
      msg = translateString("Bad login provided.")
    elif current_date > expiration_date:
      msg = translateString("Date has expire.")
    if msg is not None:
      if REQUEST is not None:
        parameter = urlencode(dict(portal_status_message=msg))
        ret_url = '%s/login_form?%s' % (site_url, parameter)
        return REQUEST.RESPONSE.redirect( ret_url )
      else:
        return msg

    # all is OK, change password and remove it from request dict
    self._password_request_dict.pop(password_key)
    persons = self.getPortalObject().acl_users.erp5_users.getUserByLogin(register_user_login)
    person = persons[0]
    person._forceSetPassword(password)
    person.reindexObject()
    if REQUEST is not None:
      msg = translateString("Password changed.")
      parameter = urlencode(dict(portal_status_message=msg))
      ret_url = '%s/login_form?%s' % (site_url, parameter)
      return REQUEST.RESPONSE.redirect( ret_url )

InitializeClass(PasswordTool)
