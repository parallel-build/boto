# Copyright (c) 2008 Chris Moyer http://coredumped.org/
# Copyringt (c) 2010 Jason R. Coombs http://www.jaraco.com/
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish, dis-
# tribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the fol-
# lowing conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABIL-
# ITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT
# SHALL THE AUTHOR BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, 
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.

import base64
import urllib
import xml.sax
import uuid
import boto
import boto.utils

from boto import handler
from boto.connection import AWSQueryConnection
from boto.resultset import ResultSet
from boto.exception import FPSResponseError
from boto.fps.result_types import Token
from boto.fps.result_types import PayResponse
from boto.fps.result_types import DebtBalanceResponse
from boto.fps.result_types import VerifySignatureResponse
from boto.fps.result_types import TransactionStatusResponse
class FPSConnection(AWSQueryConnection):

    APIVersion = '2010-08-28'

    SignatureVersion = '2'

    def __init__(self, aws_access_key_id=None, aws_secret_access_key=None,
                 is_secure=True, port=None, proxy=None, proxy_port=None,
                 proxy_user=None, proxy_pass=None,
                 host='fps.sandbox.amazonaws.com', debug=0,
                 https_connection_factory=None, path="/"):
        AWSQueryConnection.__init__(self, aws_access_key_id, aws_secret_access_key,
                                    is_secure, port, proxy, proxy_port,
                                    proxy_user, proxy_pass, host, debug,
                                    https_connection_factory, path)
        self.cbui_endpoint = 'authorize.payments-sandbox.amazon.com' if 'sandbox' in host else 'authorize.payments.amazon.com'
    
   
    def make_url(self, returnURL, paymentReason, pipelineName, **params):
        """
        Generate the URL with the signature required for a transaction
        """
        params['callerKey'] = str(self.aws_access_key_id)
        params['returnURL'] = str(returnURL)
        params['paymentReason'] = str(paymentReason)
        params['pipelineName'] = pipelineName
        params['signatureMethod']='HmacSHA256'
        params['signatureVersion'] = '2'
        params['version'] = '2009-01-09'        
        if(not params.has_key('callerReference')):
            params['callerReference'] = str(uuid.uuid4())

        header = 'GET\n' + self.cbui_endpoint + '\n' + '/cobranded-ui/actions/start\n'

        # generate the signature here...
        keys = sorted(params.keys())
        pairs = []
        for key in keys:
            val = self.get_utf8_value(params[key])
            pairs.append(urllib.quote(key, safe='') + '=' + urllib.quote(val, safe='-_~'))
        qs = '&'.join(pairs)
        toSign = header + qs
        url = "/cobranded-ui/actions/start?%s" % (qs)
        hmac = self.hmac_256.copy()
        hmac.update(toSign)
        signature = urllib.quote_plus(base64.encodestring(hmac.digest()).strip())
        

        return 'https://' + self.cbui_endpoint + url + '&signature=' + signature

    def pay(self, transactionAmount, senderTokenId,
            recipientTokenId=None, callerTokenId=None,
            chargeFeeTo="Recipient",
            callerReference=None, senderReference=None, recipientReference=None,
            senderDescription=None, recipientDescription=None, callerDescription=None,
            metadata=None, transactionDate=None, reserve=False, **params):
        """
        Make a payment transaction. You must specify the amount.
        This can also perform a Reserve request if 'reserve' is set to True.
        """
        params['SenderTokenId'] = senderTokenId
        params['TransactionAmount.Value'] = str(transactionAmount)
        params['TransactionAmount.CurrencyCode'] = "USD"
        if(senderDescription != None):
            params['SenderDescription'] = senderDescription
        if(callerDescription != None):
            params['CallerDescription'] = callerDescription
        if(callerReference == None):
            callerReference = uuid.uuid4()
        params['CallerReference'] = callerReference
        
        if reserve:
            response = self.make_request("Reserve", params)
        else:
            response = self.make_request("Pay", params)
        body = response.read()
        if(response.status == 200):
            r = PayResponse()
            h = handler.XmlHandler(r, self)
            xml.sax.parseString(body, h)
            return r
        else:
            raise FPSResponseError(response.status, response.reason, body)
    
    def get_transaction_status(self, transactionId):
        """
        Returns the status of a given transaction.
        """
        params = {}
        params['TransactionId'] = transactionId
    
        response = self.make_request("GetTransactionStatus", params)
        body = response.read()
        if(response.status == 200):
            r = TransactionStatusResponse()
            h = handler.XmlHandler(r, self)
            xml.sax.parseString(body, h)
            return r
        else:
            raise FPSResponseError(response.status, response.reason, body)
    
    def cancel(self, transactionId, description=None):
        """
        Cancels a reserved or pending transaction.
        """
        params = {}
        params['transactionId'] = transactionId
        if(description != None):
            params['description'] = description
        
        response = self.make_request("Cancel", params)
        body = response.read()
        if(response.status == 200):
            rs = ResultSet()
            h = handler.XmlHandler(rs, self)
            xml.sax.parseString(body, h)
            return rs
        else:
            raise FPSResponseError(response.status, response.reason, body)
    
    def settle_debt(self, callerReference, creditInstrumentId, settlementTokenId, amount):
        """
        Settles debt on postpaid tokens
        """
        params = {}
        params['CallerReference'] = callerReference
        params['CreditInstrumentId'] = creditInstrumentId
        params['SenderTokenId'] = settlementTokenId
        params['SettlementAmount.Value'] = str(amount)
        params['SettlementAmount.CurrencyCode'] = "USD"
        
        response = self.make_request("SettleDebt", params)
        body = response.read()
        if(response.status == 200):
            r = PayResponse()
            h = handler.XmlHandler(r, self)
            xml.sax.parseString(body, h)
            return r
        else:
            raise FPSResponseError(response.status, response.reason, body)

    
    def settle(self, reserveTransactionId, transactionAmount=None):
        """
        Charges for a reserved payment.
        """
        params = {}
        params['ReserveTransactionId'] = reserveTransactionId
        if(transactionAmount != None):
            params['TransactionAmount'] = transactionAmount
        
        response = self.make_request("Settle", params)
        body = response.read()
        if(response.status == 200):
            #rs = ResultSet()
            #h = handler.XmlHandler(rs, self)
            #xml.sax.parseString(body, h)
            return None
        else:
            raise FPSResponseError(response.status, response.reason, body)
    
    def refund(self, callerReference, transactionId, refundAmount=None, callerDescription=None):
        """
        Refund a transaction. This refunds the full amount by default unless 'refundAmount' is specified.
        """
        params = {}
        params['CallerReference'] = callerReference
        params['TransactionId'] = transactionId
        if(refundAmount != None):
            params['RefundAmount'] = refundAmount
        if(callerDescription != None):
            params['CallerDescription'] = callerDescription
        
        response = self.make_request("Refund", params)
        body = response.read()
        if(response.status == 200):
            rs = ResultSet()
            h = handler.XmlHandler(rs, self)
            xml.sax.parseString(body, h)
            return rs
        else:
            raise FPSResponseError(response.status, response.reason, body)
    

    def view_debt(self, creditInstrumentId):
        """
        Returns debt incurred with creditInstrumentId.
        """
        params ={}
        params['CreditInstrumentId'] = creditInstrumentId
        response = self.make_request("GetDebtBalance", params)
        body = response.read()
        if(response.status == 200):
            r = DebtBalanceResponse()
            h = handler.XmlHandler(r, self)
            xml.sax.parseString(body, h)
            return r
        else:
            raise FPSResponseError(response.status, response.reason, body)



    def get_recipient_verification_status(self, recipientTokenId):
        """
        Test that the intended recipient has a verified Amazon Payments account.
        """
        params ={}
        params['RecipientTokenId'] = recipientTokenId
        
        response = self.make_request("GetRecipientVerificationStatus", params)
        body = response.read()
        if(response.status == 200):
            rs = ResultSet()
            h = handler.XmlHandler(rs, self)
            xml.sax.parseString(body, h)
            return rs
        else:
            raise FPSResponseError(response.status, response.reason, body)
    
    def get_token_by_caller_reference(self, callerReference):
        """
        Returns details about the token specified by 'callerReference'.
        """
        params ={}
        params['CallerReference'] = callerReference
        
        response = self.make_request("GetTokenByCaller", params)
        body = response.read()
        if(response.status == 200):
            t = Token()
            h = handler.XmlHandler(t, self)
            xml.sax.parseString(body, h)
            return t
        else:
            raise FPSResponseError(response.status, response.reason, body)
    def get_token_by_caller_token(self, tokenId):
        """
        Returns details about the token specified by 'tokenId'.
        """
        params ={}
        params['TokenId'] = tokenId
        
        response = self.make_request("GetTokenByCaller", params)
        body = response.read()
        if(response.status == 200):
            t = Token()
            h = handler.XmlHandler(t, self)
            xml.sax.parseString(body, h)
            return t
        else:
            raise FPSResponseError(response.status, response.reason, body)

    def verify_signature(self, end_point_url, http_parameters):
        params = dict(
            UrlEndPoint = end_point_url,
            HttpParameters = http_parameters,
            )
        response = self.make_request("VerifySignature", params)
        body = response.read()
        if(response.status != 200):
            raise FPSResponseError(response.status, response.reason, body)
        r = VerifySignatureResponse()
        h = handler.XmlHandler(r, self)
        xml.sax.parseString(body, h)
        return r
