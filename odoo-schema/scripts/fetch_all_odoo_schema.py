#!/usr/bin/env python3
"""
Fetch all Odoo models and their fields via XML-RPC API.
Saves each model to a separate markdown file in odoo-schema/ folder.
Creates an index file _ALL_MODELS_INDEX.md with all model names.
"""

import xmlrpc.client
import os
import sys

# Connection details (modify as needed)
ODOO_URL = "http://172.30.1.6:8069/"
DB_NAME = "DB_BBCNS"
USERNAME = "bbadmin"
PASSWORD = "bbp@ssw0rd"

def main():
    """Main function to fetch and save Odoo models."""
    # Ensure output directory exists
    output_dir = 'odoo-schema'
    os.makedirs(output_dir, exist_ok=True)
    
    # Connect to Odoo
    print(f"Connecting to Odoo at {ODOO_URL}...")
    common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(ODOO_URL))
    models_endpoint = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(ODOO_URL))
    
    # Authenticate and get UID
    print(f"Authenticating to database '{DB_NAME}' as user '{USERNAME}'...")
    uid = common.authenticate(DB_NAME, USERNAME, PASSWORD, {})
    
    if not uid:
        print("ERROR: Authentication failed. Please check your credentials.")
        sys.exit(1)
    
    print(f"Authenticated successfully (UID: {uid})")
    
    # Get all models from ir.model
    print("Fetching all models from ir.model...")
    models_data = models_endpoint.execute_kw(
        DB_NAME, uid, PASSWORD, 
        'ir.model', 'search_read', 
        [[]], 
        {'fields': ['model', 'name']}
    )
    models = [model['model'] for model in models_data]
    print(f"Found {len(models)} models")
    
    # Generate markdown files for each model
    for idx, model in enumerate(models, 1):
        print(f"[{idx}/{len(models)}] Processing {model}...")
        # Get fields for each model
        try:
            fields = models_endpoint.execute_kw(
                DB_NAME, uid, PASSWORD, 
                model, 'fields_get'
            )
            
            # Create safe filename
            safe_filename = model.replace('.', '_') + '.md'
            
            with open(f'{output_dir}/{safe_filename}', 'w') as f:
                # Find model metadata
                model_info = next((m for m in models_data if m['model'] == model), {})
                
                f.write(f"# {model}\n\n")
                if model_info.get('name'):
                    f.write(f"**Name:** {model_info['name']}\n\n")
                
                f.write("## Fields\n\n")
                f.write("| Field Name | Type | Required | Store |\n")
                f.write("|------------|------|----------|--------|\n")
                
                for field_name, field_info in fields.items():
                    ftype = field_info.get('type', 'unknown')
                    required = 'Yes' if field_info.get('required') else 'No'
                    store = 'Yes' if field_info.get('store') else 'No'
                    f.write(f"| {field_name} | {ftype} | {required} | {store} |\n")
                    
        except Exception as e:
            print(f"  Warning: Could not fetch fields for {model}: {e}")
    
    # Create index file
    print("Creating index file...")
    with open(f'{output_dir}/_ALL_MODELS_INDEX.md', 'w') as f:
        f.write("# All Odoo Models\n\n")
        f.write(f"Total: {len(models)} models\n\n")
        
        # Group by module (first part before the dot)
        modules = {}
        for model in models:
            module = model.split('.')[0] if '.' in model else 'base'
            if module not in modules:
                modules[module] = []
            modules[module].append(model)
        
        for module in sorted(modules.keys()):
            f.write(f"## {module}\n\n")
            for model in sorted(modules[module]):
                safe_filename = model.replace('.', '_') + '.md'
                f.write(f"- [{model}]({safe_filename})\n")
            f.write("\n")
    
    print(f"\nDone! Generated {len(models)} markdown files in {output_dir}/")
    print(f"Index file: {output_dir}/_ALL_MODELS_INDEX.md")

if __name__ == '__main__':
    try:
        main()
    except xmlrpc.client.Error as e:
        print(f"XML-RPC Error: {e}")
        print("\nMake sure Odoo server is running at the specified URL.")
        print("Edit ODOO_URL, DB_NAME, USERNAME, and PASSWORD in this script to configure.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
