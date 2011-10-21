import zope
from AccessControl import ClassSecurityInfo
from Products.ERP5Type import Permissions, PropertySheet, interfaces
from Products.ERP5Type.XMLObject import XMLObject
from Products.ERP5Type.Document import newTempDocument
import hashlib
import datetime
from zLOG import LOG, WARNING

try:
  import suds
except ImportError:
  class PayzenSOAP:
    pass
else:
  import time
  class PayzenSOAP:
    """SOAP communication

    Methods are returning list of:
      * parsed response
      * signature check (True or False)
      * sent XML
      * received XML

    SOAP protocol is assumed as untrusted and dangerous, users of those methods
    are encouraged to log such messages for future debugging."""
    def _check_transcationInfoSignature(self, data):
      """Checks transactionInfo signature
      Can raise.
      """
      received_sorted_keys = ['errorCode', 'extendedErrorCode',
        'transactionStatus', 'shopId', 'paymentMethod', 'contractNumber',
        'orderId', 'orderInfo', 'orderInfo2', 'orderInfo3', 'transmissionDate',
        'transactionId', 'sequenceNb', 'amount', 'initialAmount', 'devise',
        'cvAmount', 'cvDevise', 'presentationDate', 'type', 'multiplePaiement',
        'ctxMode', 'cardNumber', 'cardNetwork', 'cardType', 'cardCountry',
        'cardExpirationDate', 'customerId', 'customerTitle', 'customerName',
        'customerPhone', 'customerMail', 'customerAddress', 'customerZipCode',
        'customerCity', 'customerCountry', 'customerLanguage', 'customerIP',
        'transactionCondition', 'vadsEnrolled', 'vadsStatus', 'vadsECI',
        'vadsXID', 'vadsCAVVAlgorithm', 'vadsCAVV', 'vadsSignatureValid',
        'directoryServer', 'authMode', 'markAmount', 'markDevise', 'markDate',
        'markNb', 'markResult', 'markCVV2_CVC2', 'authAmount', 'authDevise',
        'authDate', 'authNb', 'authResult', 'authCVV2_CVC2', 'warrantlyResult',
        'captureDate', 'captureNumber', 'rapprochementStatut', 'refoundAmount',
        'refundDevise', 'litige', 'timestamp']
      signature = ''
      for k in received_sorted_keys:
        v = getattr(data, k, None)
        if v is None:
          # empty or not transmitted: add as empty string
          v = ''
        elif k in ['transmissionDate', 'presentationDate', 'cardExpirationDate',
          'markDate', 'authDate', 'captureDate'] \
          or isinstance(v, datetime.datetime):
          # dates (or field like dates) shall be converted to YYYYMMDD
          if isinstance(v, datetime.datetime):
            v = v.strftime('%Y%m%d')
          else:
            # defensive: maybe date-like field is represented not as datetime?
            v = time.strftime('%Y%m%d', time.strptime(str(v),
                '%Y-%m-%d %H:%M:%S'))
        # convert to string (there could be ints, longs, etc)
        v = str(v)
        signature += v + '+'
      signature += self.getServicePassword()
      signature = hashlib.sha1(signature).hexdigest()
      return signature == data.signature

    def soap_getInfo(self, transmissionDate, transactionId):
      """Returns getInfo as dict, booelan, string, string

      transmissionDate is "raw" date in format YYYYMMDD, without any marks
      transactionId is id of transaction for this date

      As soon as communication happeneded does not raise.
      """
      client = suds.client.Client(self.wsdl_link.getUrlString())
      sorted_keys = ('shopId', 'transmissionDate', 'transactionId',
        'sequenceNb', 'ctxMode')
      kw = dict(
        transactionId=transactionId,
        ctxMode=self.getPayzenVadsCtxMode(),
        shopId=self.getServiceUsername(),
        sequenceNb=1,
      )
      date = time.strptime(transmissionDate, '%Y%m%d')
      signature = ''
      for k in sorted_keys:
        if k == 'transmissionDate':
          # craziness: date format in signature is different then in sent message
          v = time.strftime('%Y%m%d', date)
          kw['transmissionDate'] = time.strftime('%Y-%m-%dT%H:%M:%S', date)
        else:
          v = kw[k]
        signature += str(v) + '+'
      signature += self.getServicePassword()
      kw['wsSignature'] = hashlib.sha1(signature).hexdigest()

      # Note: Code shall not raise since now, as communication begin and caller
      #       will have to log sent/received messages.
      data = client.service.getInfo(**kw)
      try:
        data_kw = dict(data)
        for k in data_kw.keys():
          v = data_kw[k]
          if not isinstance(v, str):
            data_kw[k] = str(v)
      except Exception:
        data_kw = {}
        signature = False
        LOG('PayzenService', WARNING,
          'Issue during processing data_kw:', error=True)
      else:
        try:
          signature = self._check_transcationInfoSignature(data)
        except Exception:
          LOG('PayzenService', WARNING, 'Issue during signature calculation:',
            error=True)
          signature = False

      try:
        last_sent = str(client.last_sent())
      except Exception:
        LOG('PayzenService', WARNING,
          'Issue during converting last_sent to string:', error=True)
        signature = False

      try:
        last_received = str(client.last_received())
      except Exception:
        LOG('PayzenService', WARNING,
          'Issue during converting last_received to string:', error=True)
        signature = False

      return [data_kw, signature, last_sent, last_received]

class PayzenService(XMLObject, PayzenSOAP):
  meta_type = 'Payzen Service'
  portal_type = 'Payzen Service'

  zope.interface.implements(interfaces.IPaymentService)

  # Declarative security
  security = ClassSecurityInfo()
  security.declareObjectProtected(Permissions.AccessContentsInformation)

  # Declarative properties
  property_sheets = ( PropertySheet.Base
                    , PropertySheet.XMLObject
                    , PropertySheet.Reference
                    )
  def initialize(self, REQUEST=None, **kw):
    """See Payment Service Interface Documentation"""
    pass

  def _getSignature(self, field_list):
    field_list.sort()
    signature = ''
    for k, v in field_list:
      signature += v + '+'
    signature += self.getServicePassword()
    return hashlib.sha1(signature).hexdigest()

  def _getFieldList(self, payzen_dict):
    field_list = [
      ('vads_action_mode', self.getPayzenVadsActionMode()),
      ('vads_ctx_mode', self.getPayzenVadsCtxMode()),
      ('vads_contrib', 'ERP5'),
      ('vads_page_action', self.getPayzenVadsPageAction()),
      ('vads_payment_config', 'SINGLE'),
      ('vads_site_id', self.getServiceUsername()),
      ('vads_version', self.getPayzenVadsVersion())
    ]
    # fetch all prepared vads_ values and remove them from dict
    for k,v in payzen_dict.iteritems():
      field_list.append((k, v))
    signature = self._getSignature(field_list)
    field_list.append(('signature', signature))
    return field_list

  def navigate(self, page_template, payzen_dict, REQUEST=None, **kw):
    """Returns configured template used to do the payment"""
    self.Base_checkConsistency()
    temp_document = newTempDocument(self, 'id')
    temp_document.edit(
      link_url_string=self.getLinkUrlString(),
      title='title',
      field_list=self._getFieldList(payzen_dict),
      # append the rest of transmitted parameters page template
      **kw
    )
    return getattr(temp_document, page_template)()

  def notifySuccess(self, REQUEST=None, **kw):
    """See Payment Service Interface Documentation"""
    raise NotImplementedError
    return self._getTypeBasedMethod("acceptPayment")(**kw)

  def notifyFail(self, REQUEST=None, **kw):
    """See Payment Service Interface Documentation"""
    raise NotImplementedError
    return self._getTypeBasedMethod("failInPayment")(**kw)

  def notifyCancel(self, REQUEST=None, **kw):
    """See Payment Service Interface Documentation"""
    raise NotImplementedError
    return self._getTypeBasedMethod("abortPayment")(**kw)