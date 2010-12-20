from boto.ec2.ec2object import EC2Object


class FPSResponse(object):
	def __init__(self):
		self.response_metadata = ResponseMetadata()
	def startElement(self, name, attrs, connection):
		if name == "ResponseMetadata":
			return self.response_metadata
		else:
			return None


class ResponseMetadata(object):
	def __init__(self):
		self.request_id = None
	def __repr__(self):
		return 'ResponseMetada:%s' % self.request_id
	def startElement(self, name, attrs, connection):
		if name == "RequestId":
			return self
		else:
			return None
	def endElement(self, name, value, connection):
		if name == "RequestId":
			self.request_id = value

class CurrencyValue(object):
	def __init__(self):
		self.currency_code = None
		self.value = None
	def __repr__(self):
		return 'CurrencyValue:%s %s' % (self.value, self.currency_code)
	def startElement(self, name, attrs, connection):
		if name in ["AvailableBalance", "PendingOutBalance"]:
			return self
		else:
			return None
	def endElement(self, name, value, connection):
		if name == "CurrencyCode":
			self.currency_code = value
		if name == "Value":
			self.value = value



class Token(FPSResponse):
	def __init__(self):
		FPSResponse.__init__(self)
		self.token_id = None
		self.friendly_name = None
		self.token_status = None
		self.date_installed = None
		self.caller_reference = None
		self.token_type = None
		self.old_token_id = None
		self.payment_reason = None
	def __repr__(self):
		return 'Token:%s' % self.token_id
	def endElement(self, name, value, connection):
		if name == "TokenId":
			self.token_id = value
		elif name == "FriendlyName":
			self.friendly_name = value
		elif name == "TokenStatus":
			self.token_status = value
		elif name == "DateInstalled":
			self.date_installed = value
		elif name == "CallerReference":
			self.caller_reference = value
		elif name == "TokenType":
			self.token_type = value
		elif name == "OldTokenId":
			self.old_token_id = value
		elif name == "PaymentReason":
			self.payment_reason = value
		elif name == "PaymentReason":
			self.payment_reason = value
		else:
			print name, value

class PayResponse(FPSResponse):
	def __init__(self):
		FPSResponse.__init__(self)
		self.transaction_id = None
		self.transaction_status = None
	def __repr__(self):
		return 'PayResponse:%s' % self.transaction_id
	def endElement(self, name, value, connection):
		if name == "TransactionId":
			self.transaction_id = value
		elif name == "TransactionStatus":
			self.transaction_status = value		


class DebtBalanceResponse(FPSResponse):
	def __init__(self):
		FPSResponse.__init__(self)
		self.available_balance = CurrencyValue()
		self.pending_out_balance = CurrencyValue()
	def __repr__(self):
		return 'DebtBalanceResponse'
	def startElement(self, name, attrs, connection):
		if name == "AvailableBalance":
			return self.available_balance
		elif name == "PendingOutBalance":
			return self.pending_out_balance
		else:
			return FPSResponse.startElement(self, name, attrs, connection)
	def endElement(self, name, value, connection):
		if name == "AvailableBalance":
			self.available_balance= value
		elif name == "TransactionStatus":
			self.transaction_status = value		


