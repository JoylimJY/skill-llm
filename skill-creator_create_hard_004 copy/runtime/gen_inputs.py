import csv
import json
import os

# Create sample CSV data with sales information
sales_data = [
    ['Month', 'Revenue', 'Costs', 'Region'],
    ['January', '50000', '30000', 'North'],
    ['February', '55000', '32000', 'North'],
    ['March', '48000', '29000', 'South'],
    ['April', '62000', '35000', 'East'],
    ['May', '58000', '33000', 'West'],
    ['June', '67000', '38000', 'North']
]

with open('sales_data.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerows(sales_data)

# Create employee performance data
performance_data = [
    ['Employee', 'Department', 'Score', 'Projects'],
    ['Alice Smith', 'Engineering', '92', '8'],
    ['Bob Johnson', 'Marketing', '87', '5'],
    ['Carol Davis', 'Engineering', '95', '12'],
    ['David Wilson', 'Sales', '89', '7'],
    ['Eva Brown', 'Marketing', '91', '6']
]

with open('employee_performance.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerows(performance_data)

# Create inventory data
inventory_data = [
    ['Product', 'Category', 'Stock', 'Price'],
    ['Laptop Pro', 'Electronics', '45', '1299.99'],
    ['Office Chair', 'Furniture', '23', '249.50'],
    ['Smartphone X', 'Electronics', '78', '699.00'],
    ['Desk Lamp', 'Furniture', '56', '89.99'],
    ['Tablet Mini', 'Electronics', '34', '399.00']
]

with open('inventory.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerows(inventory_data)

print('Generated input files: sales_data.csv, employee_performance.csv, inventory.csv')