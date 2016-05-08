### This is Catalog application v.1.0
**Prerequisites:**

1. Installed *Python v2.7.x*
2. Installed *PostgreSQL 9.3.12*

**To work with DB and application:**

1. Download Catalog.zip file and unzip it OR Fork the repository:
    https://github.com/NadiiaLukianenko/catalog-app.git

**To create DB and populate data - run:**
```sh
>>> python database_setup.py
>>> python db_populate.py
```
**To run application:**
```sh
>>> python __init__.py
```
**API endpoints:**

***JSON:***

* */catalog.JSON* - Fetches and returns all data in json format
* */catalog/\<category_name\>.JSON* - Fetches and returns items for *\<category_name\>*

***XML:***

* */catalog.XML* - Fetches and returns all data in xml format
* */catalog/\<category_name\>.XML* - Fetches and returns items for *\<category_name\>*

**What are included:**
```
catalogApp/
/- image
/- static
    |- style.css
/- templates
    |- add_item.html
    |- catalog.html
    |- catalog_selected.html
    |- delete_item.html
    |- edit_item.html
    |- footer.html
    |- header.html
    |- item.html
    |- login.html
|- __init__.py
|- database_setup.py
|- db_populate.py
|- client_secrets.json
|- Readme.md
```

**Main functionality:**

* Login/Logout
* View categories
* View/Create/Update/Delete items

**Creator:**

Nadiia Lukianenko: Nadiia.Lukianenko@gmail.com
