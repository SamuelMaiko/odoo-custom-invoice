# Odoo 18 Custom Invoice Meter

This project contains a custom Odoo 18 module for extending the Accounting module to include support for creating invoices for metered products using the previous and new meter readings.

---

## Requirements

- ✅ **PostgreSQL** or **docker postgres image**
- ✅ **Python 3**
- ✅ [Odoo 18 source code](https://github.com/odoo/odoo/archive/18.0.zip)

## Setup Instructions

With the requirements in

1. **Set up the database**  
   Ensure PostgreSQL is installed.
2. **Create your Odoo config from the example**  
   Use the template and fill in your own database, addons, and port values:
   ```bash
   cp odoo.conf.example odoo.conf
   ```
3. **Update configurations** in the generated `odoo.conf` with your own
4. **Create a virtual environment and install requirements**  
   From the Odoo instance root (e.g. `/path/to/odoo-18.0`):
   ```bash
   python3 -m venv .venv
   . .venv/bin/activate
   pip install -r requirements.txt
   ```
5. **Run Odoo with your config**  
   From the project root directory:

   ```bash
   python3 /path/to/odoo-18.0/odoo-bin -c odoo.conf
   ```

   ✅ Tip: You can use relative paths if possible, e.g.:

   ```bash
   python3 ../odoo-18.0/odoo-bin -c odoo.conf
   ```

6. **Visit Odoo in your browser**  
   After running the command, open Odoo on the port set in `odoo.conf` (e.g. [http://localhost:8001](http://localhost:8001)).
