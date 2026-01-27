
import csv
import re
import os

def parse_price(price_str):
    """Extract min and max price from string like '2920.0-3281.0' or '2640.0'"""
    if not price_str:
        return None, None
    
    # Remove any non-numeric chars except . and -
    price_str = re.sub(r'[^\d\.\-]', '', str(price_str))
    
    if '-' in price_str:
        try:
            parts = price_str.split('-')
            min_p = float(parts[0])
            max_p = float(parts[1])
            return max_p, min_p # Marked (High), Discounted (Low)
        except:
            return None, None
    else:
        try:
            val = float(price_str)
            return val, val
        except:
            return None, None

def prepare_csv(input_path, output_path):
    print(f"Reading {input_path}...")
    
    with open(input_path, 'r', encoding='utf-8') as f_in:
        reader = csv.DictReader(f_in)
        
        with open(output_path, 'w', encoding='utf-8', newline='') as f_out:
            fieldnames = ['Category', 'Name', 'Marked Price', 'Min Discounted Price', 'Description', 'Image URLs']
            writer = csv.DictWriter(f_out, fieldnames=fieldnames)
            writer.writeheader()
            
            count = 0
            for row in reader:
                # Map fields
                name = row.get('name', '').strip()
                description = row.get('description', '').strip()
                
                # Category: use 'category' or 'categories'
                category = row.get('category', '').strip()
                if not category:
                    # Try to get from categories list
                    cats = row.get('categories', '')
                    if cats:
                        category = cats.split(',')[0].strip()
                if not category:
                    category = "Uncategorized"
                    
                # Price Logic
                price_raw = row.get('price', '')
                reg_raw = row.get('regular_price', '')
                sale_raw = row.get('sale_price', '')
                
                marked_price = None
                discounted_price = None
                
                if reg_raw and sale_raw:
                    try:
                        marked_price = float(reg_raw)
                        discounted_price = float(sale_raw)
                    except:
                        pass
                elif price_raw:
                    marked_price, discounted_price = parse_price(price_raw)
                
                # Image URLs - Keep only the FIRST one
                images = row.get('images', '').strip()
                final_image = ""
                if images:
                    # Split by comma and take the first one
                    first_image = images.split(',')[0].strip()
                    if first_image:
                        final_image = first_image
                
                writer.writerow({
                    'Category': category,
                    'Name': name,
                    'Marked Price': marked_price if marked_price is not None else '',
                    'Min Discounted Price': discounted_price if discounted_price is not None else '',
                    'Description': description,
                    'Image URLs': final_image
                })
                count += 1
                
    print(f"Successfully converted {count} rows to {output_path}")

if __name__ == "__main__":
    input_file = "/Users/dimanjan/imagehost/data (1).csv"
    output_file = "/Users/dimanjan/imagehost/ready_for_upload.csv"
    prepare_csv(input_file, output_file)
