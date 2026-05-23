# sqlsift

> Python library for detecting schema drift between SQL database snapshots

---

## Installation

```bash
pip install sqlsift
```

---

## Usage

```python
from sqlsift import SchemaSnapshot, SchemaDiff

# Capture two snapshots of your database schema
snapshot_before = SchemaSnapshot.from_connection(conn, label="v1.0")
snapshot_after = SchemaSnapshot.from_connection(conn, label="v1.1")

# Compare and detect drift
diff = SchemaDiff(snapshot_before, snapshot_after)
report = diff.analyze()

# View a summary of changes
print(report.summary())
# Added tables:   ['user_sessions']
# Dropped tables: []
# Modified tables: ['orders'] → column 'total' type changed: INT → DECIMAL

# Export the full report
report.to_json("schema_drift_report.json")
```

---

## Features

- Compare schema snapshots across time or environments
- Detect added, removed, and modified tables, columns, and indexes
- Export drift reports as JSON or plain text
- Supports PostgreSQL, MySQL, and SQLite

---

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

---

## License

This project is licensed under the [MIT License](LICENSE).