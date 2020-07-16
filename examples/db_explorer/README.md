# DB Explorer

This is a simple Flask web application that connects to ClickHouse and displays the list of existing databases. Clicking on a database name drills down into it, showing its list of tables. Clicking on a table drills down further, showing details about the table and its columns.

For each table or column, the application displays the compressed size on disk, the uncompressed size, and the ratio between them. Additionally, several pie charts are shown - top tables by size, top tables by rows, and top columns by size (in a table).

The pie charts are generated using the `pygal` charting library.

ORM concepts that are demonstrated by this example:

- Creating ORM models from existing tables using `Database.get_model_for_table`
- Queryset filtering
- Queryset aggregation

## Running the code

Create a virtualenv and install the required libraries:
```
virtualenv -p python3.6 env
source env/bin/activate
pip install -r requirements.txt
```

Run the server and open http://127.0.0.1:5000/ in your browser:
```
python server.py
```

By default the server connects to ClickHouse running on http://localhost:8123/ without a username or password, but you can change this using command line arguments:
```
python server.py http://myclickhouse:8123/
```
or:
```
python server.py http://myclickhouse:8123/ admin secret123
```
