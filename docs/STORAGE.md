# Storage

A simple postgres implementation is provided to build from

```mermaid
classDiagram

class Events {
 - id
 + store_id
 + delivery_id
}

class Delivery {
 - id
 + order_data
}

class OrderData {
 - external_order_id
}

class CreateOrderData {
 - status
}

OrderData <|-- CreateOrderData
```
<img width="798" height="630" alt="image" src="https://github.com/user-attachments/assets/8f1edf97-ea6a-4eaa-bbe8-d2cc3795c054" />