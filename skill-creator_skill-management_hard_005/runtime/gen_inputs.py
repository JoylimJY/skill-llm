import csv
import os
import random

# Set deterministic seed
random.seed(42)

# Create sample sales data
sales_data = [
    ['Date', 'Product', 'Category', 'Sales', 'Region', 'Customer_Type'],
    ['2024-01-15', 'Laptop Pro', 'Electronics', '1299.99', 'North', 'Business'],
    ['2024-01-16', 'Office Chair', 'Furniture', '249.50', 'South', 'Individual'],
    ['2024-01-17', 'Smartphone X', 'Electronics', '899.00', 'East', 'Business'],
    ['2024-01-18', 'Desk Lamp', 'Furniture', '89.99', 'West', 'Individual'],
    ['2024-01-19', 'Tablet Mini', 'Electronics', '399.99', 'North', 'Individual'],
    ['2024-01-20', 'Ergonomic Mouse', 'Electronics', '79.99', 'South', 'Business'],
    ['2024-01-21', 'Standing Desk', 'Furniture', '599.00', 'East', 'Business'],
    ['2024-01-22', 'Monitor 4K', 'Electronics', '449.99', 'West', 'Individual'],
    ['2024-01-23', 'Keyboard Pro', 'Electronics', '129.99', 'North', 'Business'],
    ['2024-01-24', 'Book Shelf', 'Furniture', '179.99', 'South', 'Individual']
]

with open('sales_data.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerows(sales_data)

# Create employee performance data
performance_data = [
    ['Employee_ID', 'Name', 'Department', 'Performance_Score', 'Years_Experience', 'Salary'],
    ['EMP001', 'John Smith', 'Engineering', '8.5', '5', '85000'],
    ['EMP002', 'Sarah Johnson', 'Marketing', '9.2', '3', '72000'],
    ['EMP003', 'Mike Chen', 'Engineering', '7.8', '7', '95000'],
    ['EMP004', 'Lisa Brown', 'Sales', '9.5', '4', '78000'],
    ['EMP005', 'David Wilson', 'Marketing', '8.1', '2', '65000'],
    ['EMP006', 'Emma Davis', 'Engineering', '9.0', '6', '92000'],
    ['EMP007', 'Tom Miller', 'Sales', '8.8', '8', '89000'],
    ['EMP008', 'Anna Garcia', 'Marketing', '7.9', '1', '58000']
]

with open('employee_performance.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerows(performance_data)

print('Generated input CSV files: sales_data.csv, employee_performance.csv')