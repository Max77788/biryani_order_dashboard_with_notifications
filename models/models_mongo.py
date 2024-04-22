from mongoengine import Document, StringField, IntField, ListField, EmbeddedDocument, EmbeddedDocumentField

class Item(EmbeddedDocument):
    name = StringField(required=True)
    quantity = IntField(required=True)

class Order(Document):
    orderNumber = IntField(required=True, unique=True)
    items = ListField(EmbeddedDocumentField(Item))

    def add_item(self, name, quantity):
        self.items.append(Item(name=name, quantity=quantity))