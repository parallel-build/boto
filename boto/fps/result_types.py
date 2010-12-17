from boto.ec2.ec2object import EC2Object


class FPSResponse(EC2Object):
	def __init__(self, connection = None):
		EC2Object.__init__(self, connection)
		self.response_metadata = ResponseMetadata(connection)
	def startElement(self, name, attrs, connection):
		if name == "ResponseMetadata":
			return self.response_metadata
		else:
			return None


class ResponseMetadata(EC2Object):
	def __init__(self, connection = None):
		EC2Object.__init__(self, connection)
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



class Token(FPSResponse):
	def __init__(self, connection = None):
		FPSResponse.__init__(self, connection)
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

class PayResponse(FPSResponse):
	def __init__(self, connection = None):
		FPSResponse.__init__(self, connection)
		self.transaction_id = None
		self.transaction_status = None
	def __repr__(self):
		return 'PayResponse:%s' % self.transaction_id
	def endElement(self, name, value, connection):
		if name == "TransactionId":
			self.transaction_id = value
		elif name == "TransactionStatus":
			self.transaction_status = value		

