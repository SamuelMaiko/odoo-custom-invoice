# 🛠️ Odoo 18 Custom Purchase Workflow

This project contains custom Odoo 18 modules for extending the Purchase workflow — including support for multi-vendor RFQs, bid submissions, winner selection, and employee purchase requests.

---


## 🧱 Requirements

- ✅ **Ubuntu 24.04** / **Kubuntu**
- ✅ **PostgreSQL ≥ 15**
- ✅ **Python 3**
- ✅ [Odoo 18 source code](https://github.com/odoo/odoo/archive/18.0.zip)
- ✅ (Optional) **Docker** — if using Docker for postgres instance, make sure to configure your database IP (like `172.18.0.2`). You can find it using:
  
  ```bash
  docker inspect <container_name> | grep IPAddress
    ```
## 📦 Folder Structure


![My Image](readme-images/folder-structure.png)
- `custom-addons` and `conf` folder - download from the archive of this repo
- `odoo-18.0` - can be any name i.e from the Odoo instance you downloaded above (from requirements above)

## 🛠️ Setup Instructions
With the requirements in 

1. **Set up the database**  
   Ensure PostgreSQL is installed. Use the credentials of your user to update the credentials in `conf/odoo.conf`.
2. **Update addons path** in `conf/odoo.conf`:
   ```ini
   addons_path = /path/to/odoo-18.0/addons, /path/to/odoo-18.0/odoo/addons, /path/to/custom_addons
    ```
3. **Install Python requirements** (if needed):
   ```bash
   pip install -r /path/to/odoo-18.0/requirements.txt
    ```
4. **Run Odoo with custom config**  
   From the project root directory:

   ```bash
   python3 /path/to/odoo-18.0/odoo-bin -c conf/odoo.conf
    ```
   
    ✅ Tip: You can use relative paths if possible, e.g.:
    ```bash
   python3 ../odoo-18.0/odoo-bin -c conf/odoo.conf
    ```
5. **Visit Odoo in your browser**  
   After running the command, you can access the Odoo platform on your local machine by visiting [http://localhost:8001](http://localhost:8001).  
   If you wish, you can modify the port in `conf/odoo.conf` under the `http_port` option.

## Tip
 **Set up with PyCharm**  
   If you'd like to set up the project with PyCharm, you can follow the steps in this [YouTube tutorial](https://youtu.be/fbEsjurG7sQ?si=PqhGt7lVRbtJXvYM).