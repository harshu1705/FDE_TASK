-- Create Database Schema for an ERP Order-to-Cash system.

CREATE TABLE customers (
  customer_id TEXT PRIMARY KEY,
  name TEXT,
  city TEXT,
  postal_code TEXT
);

CREATE TABLE products (
  product_id TEXT PRIMARY KEY,
  description TEXT
);

CREATE TABLE orders (
  order_id TEXT PRIMARY KEY,
  customer_id TEXT REFERENCES customers(customer_id),
  created_at TIMESTAMP
);

CREATE TABLE order_items (
  id SERIAL PRIMARY KEY,
  order_id TEXT REFERENCES orders(order_id),
  product_id TEXT REFERENCES products(product_id),
  quantity INT
);

CREATE TABLE deliveries (
  delivery_id TEXT PRIMARY KEY,
  order_id TEXT REFERENCES orders(order_id),
  created_at TIMESTAMP
);

CREATE TABLE invoices (
  invoice_id TEXT PRIMARY KEY,
  delivery_id TEXT REFERENCES deliveries(delivery_id),
  order_id TEXT REFERENCES orders(order_id),
  total_amount NUMERIC
);

CREATE TABLE payments (
  payment_id TEXT PRIMARY KEY,
  invoice_id TEXT REFERENCES invoices(invoice_id),
  amount NUMERIC
);

-- Add indexes on foreign keys
CREATE INDEX idx_orders_customer_id ON orders(customer_id);
CREATE INDEX idx_order_items_order_id ON order_items(order_id);
CREATE INDEX idx_order_items_product_id ON order_items(product_id);
CREATE INDEX idx_deliveries_order_id ON deliveries(order_id);
CREATE INDEX idx_invoices_delivery_id ON invoices(delivery_id);
CREATE INDEX idx_invoices_order_id ON invoices(order_id);
CREATE INDEX idx_payments_invoice_id ON payments(invoice_id);
